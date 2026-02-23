"""Contract tests for switching telemetry events."""

from __future__ import annotations

from pycie.core.node import Device
from pycie.protocols.switching import LearningSwitch, MacEntry
from pycie.sim.network import Frame, Interface, NetworkSimulator, Topology
from pycie.telemetry.events import EventType
from pycie.telemetry.packet import get_packet_id
from pycie.telemetry.trace import MemoryTraceSink


def _build_switch() -> tuple[NetworkSimulator, Device, LearningSwitch, MemoryTraceSink]:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node("sw1")
    for if_name, mac in (
        ("eth0", "02:00:00:00:00:01"),
        ("eth1", "02:00:00:00:00:02"),
        ("eth2", "02:00:00:00:00:03"),
    ):
        topo.add_interface(Interface("sw1", if_name, mac))

    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    dev = Device("sw1", sim)
    for iface in topo.interfaces.values():
        dev.add_interface(iface)

    process = LearningSwitch()
    dev.register_protocol("l2", process)
    return sim, dev, process, sink


def _events_by_type(sink: MemoryTraceSink, event_type: EventType) -> list:
    return [event for event in sink.events if event.event_type == event_type]


def test_unknown_unicast_emits_flood_event_with_full_egress_set() -> None:
    _sim, dev, process, sink = _build_switch()
    sent_packet_ids: list[str | None] = []
    dev.send_frame = lambda _if_name, frame: sent_packet_ids.append(get_packet_id(frame))  # type: ignore[method-assign]

    frame = Frame(
        src_mac="aa:aa:aa:aa:aa:01",
        dst_mac="bb:bb:bb:bb:bb:02",
        ethertype="0x0800",
        payload=b"payload",
    )
    process.on_frame("eth0", frame)

    flood_events = _events_by_type(sink, EventType.L2_FLOOD)
    assert len(flood_events) == 1
    assert flood_events[0].details["dst_mac"] == "bb:bb:bb:bb:bb:02"
    assert flood_events[0].details["egress_interfaces"] == ["eth1", "eth2"]
    assert sent_packet_ids == [flood_events[0].packet_id, flood_events[0].packet_id]


def test_known_unicast_emits_unicast_forward_only() -> None:
    _sim, dev, process, sink = _build_switch()
    sent_ports: list[str] = []
    dev.send_frame = lambda if_name, _frame: sent_ports.append(if_name)  # type: ignore[method-assign]

    process.mac_table["bb:bb:bb:bb:bb:02"] = MacEntry(
        mac="bb:bb:bb:bb:bb:02",
        interface="eth2",
        learned_at_ms=0,
    )

    frame = Frame(
        src_mac="aa:aa:aa:aa:aa:01",
        dst_mac="bb:bb:bb:bb:bb:02",
        ethertype="0x0800",
        payload=b"payload",
    )
    process.on_frame("eth0", frame)

    assert len(_events_by_type(sink, EventType.L2_UNICAST_FORWARD)) == 1
    assert not _events_by_type(sink, EventType.L2_FLOOD)
    assert sent_ports == ["eth2"]


def test_mac_move_emits_two_mac_learn_events() -> None:
    sim, _dev, process, sink = _build_switch()

    process.learn_source_mac("eth1", "aa:aa:aa:aa:aa:01")
    sim.clock.advance_by(5)
    process.learn_source_mac("eth2", "aa:aa:aa:aa:aa:01")

    learn_events = _events_by_type(sink, EventType.MAC_LEARN)
    assert len(learn_events) == 2
    assert [event.details["interface"] for event in learn_events] == ["eth1", "eth2"]


def test_mac_aging_emits_age_out_events_deterministically() -> None:
    sim, _dev, process, sink = _build_switch()
    process.mac_aging_ms = 10
    process.mac_table["aa:aa:aa:aa:aa:01"] = MacEntry("aa:aa:aa:aa:aa:01", "eth0", 0)
    process.mac_table["aa:aa:aa:aa:aa:02"] = MacEntry("aa:aa:aa:aa:aa:02", "eth1", 9)

    sim.clock.advance_to(11)
    process.age_mac_table()

    age_events = _events_by_type(sink, EventType.MAC_AGE_OUT)
    assert len(age_events) == 1
    assert age_events[0].details == {
        "mac": "aa:aa:aa:aa:aa:01",
        "previous_interface": "eth0",
    }
