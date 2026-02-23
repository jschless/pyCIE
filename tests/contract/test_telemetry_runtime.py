"""Contract tests for simulator/device runtime telemetry boundaries."""

from __future__ import annotations

from pycie.core.node import Device
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.sim.network import Frame, Interface, NetworkSimulator, Topology
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.trace import MemoryTraceSink


def _build_two_node_runtime() -> tuple[NetworkSimulator, Device, Device, MemoryTraceSink]:
    sink = MemoryTraceSink()

    topo = Topology()
    topo.add_node("r1")
    topo.add_node("r2")
    topo.add_interface(Interface("r1", "eth0", "02:00:00:00:00:01"))
    topo.add_interface(Interface("r2", "eth0", "02:00:00:00:00:02"))
    topo.connect(("r1", "eth0"), ("r2", "eth0"), latency_ms=5)

    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    r1 = Device("r1", sim)
    r2 = Device("r2", sim)
    r1.add_interface(topo.get_interface(("r1", "eth0")))
    r2.add_interface(topo.get_interface(("r2", "eth0")))
    return sim, r1, r2, sink


def test_runtime_tx_enqueue_deliver_rx_sequence() -> None:
    sim, r1, _r2, sink = _build_two_node_runtime()

    payload = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", ttl=64, protocol=6)])
    frame = Frame(src_mac="aa:aa:aa:aa:aa:01", dst_mac="bb:bb:bb:bb:bb:02", ethertype="0x0800", payload=payload)

    r1.send_frame("eth0", frame)
    sim.run()

    event_types = [event.event_type for event in sink.events]
    assert event_types == [
        EventType.FRAME_TX,
        EventType.FRAME_ENQUEUE,
        EventType.FRAME_DELIVER,
        EventType.FRAME_RX,
    ]
    packet_ids = {event.packet_id for event in sink.events}
    assert len(packet_ids) == 1
    assert sink.events[1].layer == Layer.SIM
    assert sink.events[1].details["dst_node"] == "r2"


def test_runtime_drop_reason_no_link() -> None:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node("r1")
    topo.add_interface(Interface("r1", "eth0", "02:00:00:00:00:01"))

    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    r1 = Device("r1", sim)
    r1.add_interface(topo.get_interface(("r1", "eth0")))

    frame = Frame(src_mac="aa", dst_mac="bb", ethertype="0x0800", payload=PacketStack())
    r1.send_frame("eth0", frame)

    assert [event.event_type for event in sink.events] == [EventType.FRAME_TX, EventType.FRAME_DROP]
    assert sink.events[-1].layer == Layer.SIM
    assert sink.events[-1].details["drop_reason"] == "no_link"


def test_runtime_drop_reason_loss_probability() -> None:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node("r1")
    topo.add_node("r2")
    topo.add_interface(Interface("r1", "eth0", "02:00:00:00:00:01"))
    topo.add_interface(Interface("r2", "eth0", "02:00:00:00:00:02"))
    topo.connect(("r1", "eth0"), ("r2", "eth0"), loss_prob=1.0)

    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    r1 = Device("r1", sim)
    r1.add_interface(topo.get_interface(("r1", "eth0")))

    frame = Frame(src_mac="aa", dst_mac="bb", ethertype="0x0800", payload=PacketStack())
    r1.send_frame("eth0", frame)

    assert [event.event_type for event in sink.events] == [EventType.FRAME_TX, EventType.FRAME_DROP]
    assert sink.events[-1].details["drop_reason"] == "loss_prob"
