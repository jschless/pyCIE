"""Contract tests for route-forwarding telemetry events."""

from __future__ import annotations

from pathlib import Path

from pycie.forwarding.l3 import IPv4Forwarder, L3Route
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.telemetry.events import EventType
from pycie.telemetry.trace import close_env_recorders, load_trace_events


def _read_event_types(path: Path) -> list[EventType]:
    return [event.event_type for event in load_trace_events(path)]


def test_route_select_prefers_admin_distance_over_metric(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "l3_ad_vs_metric.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    forwarder = IPv4Forwarder(trace_node="r1")
    forwarder.install_route(L3Route("10.2.0.0/16", "192.0.2.1", "eth0", "ospf", 110, 50))
    forwarder.install_route(L3Route("10.2.0.0/16", "192.0.2.2", "eth1", "bgp", 200, 5))

    packet = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.2.1.1", ttl=32, protocol=6)])
    egress_if, out_packet, drop_reason = forwarder.forward(packet)

    close_env_recorders()
    events = load_trace_events(trace_path)

    assert (egress_if, drop_reason) == ("eth0", None)
    assert out_packet is not None
    assert _read_event_types(trace_path) == [
        EventType.ROUTE_LOOKUP,
        EventType.ROUTE_SELECT,
        EventType.FIB_FORWARD,
    ]
    assert events[1].details["selected_prefix"] == "10.2.0.0/16"
    assert events[1].details["ad"] == 110
    assert events[1].details["metric"] == 50


def test_route_select_prefers_longest_prefix(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "l3_lpm.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    forwarder = IPv4Forwarder(trace_node="r1")
    forwarder.install_route(L3Route("10.0.0.0/8", "192.0.2.1", "eth0", "static", 1, 10))
    forwarder.install_route(L3Route("10.1.0.0/16", "192.0.2.2", "eth1", "static", 1, 20))

    packet = PacketStack(headers=[IPv4Header(src_ip="1.1.1.1", dst_ip="10.1.2.3", ttl=64, protocol=17)])
    forwarder.forward(packet)

    close_env_recorders()
    events = load_trace_events(trace_path)
    route_select = next(event for event in events if event.event_type == EventType.ROUTE_SELECT)
    assert route_select.details["selected_prefix"] == "10.1.0.0/16"


def test_fib_drop_emits_reason_when_no_route(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "l3_drop.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    forwarder = IPv4Forwarder(trace_node="r1")
    packet = PacketStack(headers=[IPv4Header(src_ip="1.1.1.1", dst_ip="203.0.113.1", ttl=64, protocol=17)])

    egress_if, out_packet, drop_reason = forwarder.forward(packet)

    close_env_recorders()
    events = load_trace_events(trace_path)

    assert egress_if is None
    assert out_packet is None
    assert drop_reason == "no_route"

    drop_event = next(event for event in events if event.event_type == EventType.FIB_DROP)
    assert drop_event.details["drop_reason"] == "no_route"
