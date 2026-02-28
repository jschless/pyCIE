"""Contract tests for IPsec and RIB/FIB route-programming telemetry."""

from __future__ import annotations

from pathlib import Path

from pycie.core.node import Device
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipsec import IPsecProcess, IPSecPolicyAction, SecurityAssociation, SecurityPolicy
from pycie.protocols.rib_fib_pipeline import NextHopResolution, PipelineRoute, RIBFIBPipeline
from pycie.sim.network import Interface, NetworkSimulator, Topology
from pycie.telemetry.events import EventType
from pycie.telemetry.trace import MemoryTraceSink, close_env_recorders, load_trace_events


def _build_device(node_id: str = "r1") -> tuple[Device, MemoryTraceSink]:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node(node_id)
    topo.add_interface(Interface(node_id, "eth0", "02:00:00:00:00:01"))
    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    dev = Device(node_id, sim)
    dev.add_interface(topo.get_interface((node_id, "eth0")))
    return dev, sink


def test_ipsec_emits_policy_and_sa_lookup_events() -> None:
    dev, sink = _build_device("ipsec1")
    process = IPsecProcess()
    process.install_sa(SecurityAssociation(spi=101, src_ip="198.51.100.1", dst_ip="198.51.100.2"))
    process.install_policy(
        SecurityPolicy(
            policy_id="protect-web",
            src_prefix="10.0.0.0/24",
            dst_prefix="203.0.113.0/24",
            action=IPSecPolicyAction.PROTECT,
            sa_spi=101,
        )
    )
    dev.register_protocol("ipsec", process)

    packet = PacketStack(headers=[IPv4Header(src_ip="10.0.0.10", dst_ip="203.0.113.80", ttl=64, protocol=6)])
    action, protected = process.outbound(packet)

    assert action == IPSecPolicyAction.PROTECT
    assert protected is not None
    event_types = [event.event_type for event in sink.events]
    assert EventType.IPSEC_POLICY_EVALUATE in event_types
    assert EventType.IPSEC_SA_LOOKUP in event_types
    assert EventType.CRYPTO_ENCRYPT in event_types
    assert EventType.ENCAP_PUSH in event_types


def test_rib_fib_pipeline_emits_candidate_skip_and_install_events(
    monkeypatch,
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "rib_fib.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    pipeline = RIBFIBPipeline(trace_node="rib-fib-1")
    pipeline.install_route(PipelineRoute("10.9.0.0/24", "192.0.2.1", "static", 1, 0))
    pipeline.install_route(PipelineRoute("10.9.0.0/24", "192.0.2.2", "ospf", 110, 20))
    pipeline.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.2", egress_if="eth7"))
    pipeline.recompute()

    close_env_recorders()
    events = load_trace_events(trace_path)
    event_types = [event.event_type for event in events]
    assert EventType.RIB_CANDIDATE_EVALUATE in event_types
    assert EventType.RIB_ROUTE_SKIP in event_types
    assert EventType.RIB_ROUTE_INSTALL in event_types

    installed = [event for event in events if event.event_type == EventType.RIB_ROUTE_INSTALL]
    assert installed
    assert installed[0].details["prefix"] == "10.9.0.0/24"
    assert installed[0].details["egress_if"] == "eth7"


def test_rib_fib_pipeline_keeps_positional_routes_constructor_compatibility() -> None:
    routes = [PipelineRoute("10.10.0.0/24", "192.0.2.1", "ospf", 110, 10)]
    pipeline = RIBFIBPipeline(routes)
    assert pipeline.routes == routes
