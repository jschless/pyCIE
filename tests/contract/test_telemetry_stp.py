"""Contract tests for STP election telemetry."""

from __future__ import annotations

from pycie.core.node import Device
from pycie.protocols.stp import BPDU, BridgeId, STPPort, STPProcess
from pycie.sim.network import Frame, Interface, NetworkSimulator, Topology
from pycie.telemetry.events import EventType
from pycie.telemetry.trace import MemoryTraceSink


def _build_stp_process() -> tuple[STPProcess, MemoryTraceSink]:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node("sw1")
    topo.add_interface(Interface("sw1", "eth0", "02:00:00:00:00:01"))
    topo.add_interface(Interface("sw1", "eth1", "02:00:00:00:00:02"))

    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    dev = Device("sw1", sim)
    dev.add_interface(topo.get_interface(("sw1", "eth0")))
    dev.add_interface(topo.get_interface(("sw1", "eth1")))

    process = STPProcess(bridge_priority=32768, bridge_mac="00:00:00:00:00:0a")
    process.ports = {
        "eth0": STPPort(if_name="eth0", port_id=1),
        "eth1": STPPort(if_name="eth1", port_id=2),
    }
    dev.register_protocol("stp", process)
    return process, sink


def _events(sink: MemoryTraceSink, event_type: EventType) -> list:
    return [event for event in sink.events if event.event_type == event_type]


def test_stp_root_change_emits_event_on_superior_bpdu() -> None:
    process, sink = _build_stp_process()
    superior = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=4,
        bridge_id=BridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
    )

    process.process_bpdu("eth0", superior)

    root_events = _events(sink, EventType.STP_ROOT_CHANGE)
    assert len(root_events) == 1
    assert root_events[0].details["old_root_id"] == "32768:00:00:00:00:00:0a"
    assert root_events[0].details["new_root_id"] == "32768:00:00:00:00:00:01"
    assert root_events[0].details["root_port"] == "eth0"


def test_stp_inferior_bpdu_does_not_emit_root_change() -> None:
    process, sink = _build_stp_process()
    process.root_id = BridgeId(32768, "00:00:00:00:00:01")
    process.root_cost = 8
    process.root_port = "eth0"

    inferior = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:ff"),
        root_path_cost=1,
        bridge_id=BridgeId(32768, "00:00:00:00:00:ff"),
        port_id=3,
    )
    process.process_bpdu("eth1", inferior)

    assert not _events(sink, EventType.STP_ROOT_CHANGE)


def test_stp_tiebreak_and_root_port_reselection_are_deterministic() -> None:
    process, sink = _build_stp_process()

    first = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=6,
        bridge_id=BridgeId(32768, "00:00:00:00:00:03"),
        port_id=20,
    )
    better = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=6,
        bridge_id=BridgeId(32768, "00:00:00:00:00:02"),
        port_id=10,
    )

    process.process_bpdu("eth0", first)
    process.process_bpdu("eth1", better)

    assert process.root_port == "eth1"
    role_events = _events(sink, EventType.STP_PORT_ROLE_CHANGE)
    assert role_events
    last_change = role_events[-1]
    assert last_change.details["if_name"] in {"eth0", "eth1"}


def test_stp_bpdu_rx_and_tx_events_include_fields() -> None:
    process, sink = _build_stp_process()

    outbound = process.build_bpdu("eth0")
    inbound_frame = Frame(
        src_mac="01:80:c2:00:00:00",
        dst_mac="01:80:c2:00:00:00",
        ethertype="0x0026",
        payload=outbound,
    )
    process.on_frame("eth1", inbound_frame)

    tx_events = _events(sink, EventType.STP_BPDU_TX)
    rx_events = _events(sink, EventType.STP_BPDU_RX)
    assert len(tx_events) == 1
    assert len(rx_events) == 1
    assert tx_events[0].details["port_id"] == 1
    assert rx_events[0].details["root_path_cost"] == outbound.root_path_cost
