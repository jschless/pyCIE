"""Contract tests for NAT/ACL/QoS/ARP/BFD telemetry instrumentation."""

from __future__ import annotations

from pathlib import Path

from pycie.core.node import Device
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.acl import ACL, ACLPacket, ACLRule
from pycie.protocols.arp import ARPMessage, ARPOpcode, ARPProcess
from pycie.protocols.bfd import BFDControl, BFDProcess, BFDState
from pycie.protocols.nat44_pipeline import NAT44Pipeline
from pycie.protocols.qos_marking_queueing import QoSMarkingQueueingProcess, QoSPacket
from pycie.sim.network import Frame, Interface, NetworkSimulator, Topology
from pycie.telemetry.events import EventType
from pycie.telemetry.trace import MemoryTraceSink, close_env_recorders, load_trace_events


def _build_device(node_id: str = "r1") -> tuple[Device, NetworkSimulator, MemoryTraceSink]:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node(node_id)
    topo.add_interface(Interface(node_id, "eth0", "02:00:00:00:00:01"))
    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    dev = Device(node_id, sim)
    dev.add_interface(topo.get_interface((node_id, "eth0")))
    return dev, sim, sink


def test_nat44_emits_session_and_translation_events() -> None:
    dev, _sim, sink = _build_device("nat1")
    process = NAT44Pipeline(public_ip="203.0.113.10")
    dev.register_protocol("nat44", process)

    outbound = PacketStack(
        headers=[IPv4Header(src_ip="10.0.0.10", dst_ip="198.51.100.9", ttl=64, protocol=6)],
        metadata={"l4_proto": "tcp", "src_port": 12345, "dst_port": 80},
    )
    translated, drop_reason = process.translate_outbound(outbound, now_ms=100)
    assert translated is not None
    assert drop_reason is None
    translated_port = int(translated.metadata["src_port"])

    inbound = PacketStack(
        headers=[IPv4Header(src_ip="198.51.100.9", dst_ip="203.0.113.10", ttl=64, protocol=6)],
        metadata={"l4_proto": "tcp", "src_port": 80, "dst_port": translated_port},
    )
    returned, inbound_drop = process.translate_inbound(inbound, now_ms=130)
    assert returned is not None
    assert inbound_drop is None

    event_types = [event.event_type for event in sink.events]
    assert EventType.NAT_SESSION_CREATE in event_types
    assert EventType.NAT_TRANSLATE_OUTBOUND in event_types
    assert EventType.NAT_TRANSLATE_INBOUND in event_types


def test_qos_emits_remark_enqueue_and_dequeue_events() -> None:
    dev, _sim, sink = _build_device("qos1")
    process = QoSMarkingQueueingProcess()
    dev.register_protocol("qos", process)

    packet = QoSPacket(packet_id="p-qos-1", dscp=0)
    remarked = process.remark(packet, new_dscp=46)
    accepted, reason = process.enqueue(remarked)
    dequeued = process.dequeue()

    assert accepted
    assert reason is None
    assert dequeued is not None
    assert dequeued.packet_id == "p-qos-1"

    event_types = [event.event_type for event in sink.events]
    assert EventType.QOS_REMARK in event_types
    assert EventType.QOS_ENQUEUE in event_types
    assert EventType.QOS_DEQUEUE in event_types


def test_arp_emits_learning_request_and_reply_events() -> None:
    dev, _sim, sink = _build_device("arp1")
    process = ARPProcess()
    process.local_ips["eth0"] = "10.0.0.1"
    process.local_macs["eth0"] = "aa:bb:cc:dd:ee:ff"
    dev.register_protocol("arp", process)

    request = ARPMessage(
        opcode=ARPOpcode.REQUEST,
        sender_ip="10.0.0.2",
        sender_mac="00:11:22:33:44:55",
        target_ip="10.0.0.1",
    )
    frame = Frame(
        src_mac="00:11:22:33:44:55",
        dst_mac="ff:ff:ff:ff:ff:ff",
        ethertype="0x0806",
        payload=request,
    )
    process.on_frame("eth0", frame)

    event_types = [event.event_type for event in sink.events]
    assert EventType.ARP_CACHE_LEARN in event_types
    assert EventType.ARP_REQUEST_RX in event_types
    assert EventType.ARP_REPLY_TX in event_types
    assert process.outbound_messages


def test_bfd_emits_control_state_and_timeout_events() -> None:
    dev, sim, sink = _build_device("bfd1")
    process = BFDProcess()
    dev.register_protocol("bfd", process)

    session = process.open_session("peer1")
    control = BFDControl(
        your_discriminator=session.local_discriminator,
        my_discriminator=2001,
        state=BFDState.INIT,
        desired_min_tx_ms=300,
        required_min_rx_ms=300,
        detect_mult=3,
    )
    process.receive_control("peer1", control)
    process.transmit_control("peer1")
    sim.clock.advance_to(1000)
    expired = process.check_timeouts()

    assert "peer1" in expired
    event_types = [event.event_type for event in sink.events]
    assert EventType.BFD_CONTROL_RX in event_types
    assert EventType.BFD_CONTROL_TX in event_types
    assert EventType.BFD_STATE_CHANGE in event_types
    assert EventType.BFD_TIMEOUT in event_types


def test_acl_emits_evaluation_events(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "acl_trace.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    acl = ACL(trace_node="acl1")
    acl.add_rule(ACLRule(seq=10, action="permit", src_prefix="10.0.0.0/24", dst_prefix="0.0.0.0/0"))
    decision_permit = acl.evaluate(ACLPacket(src_ip="10.0.0.5", dst_ip="198.51.100.1", protocol="tcp"))
    decision_deny = acl.evaluate(ACLPacket(src_ip="192.0.2.5", dst_ip="198.51.100.1", protocol="tcp"))
    close_env_recorders()

    events = load_trace_events(trace_path)
    acl_events = [event for event in events if event.event_type == EventType.ACL_EVALUATE]
    assert decision_permit.value == "permit"
    assert decision_deny.value == "deny"
    assert len(acl_events) == 2
    assert acl_events[0].details["decision"] == "permit"
    assert acl_events[1].details["decision"] == "deny"
