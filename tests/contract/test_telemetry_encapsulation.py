"""Contract tests for encapsulation/encryption telemetry."""

from __future__ import annotations

from pathlib import Path

from pycie.forwarding.encapsulation import EncapsulationPipeline, TunnelConfig, TunnelMode
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.telemetry.events import EventType
from pycie.telemetry.trace import close_env_recorders, load_trace_events


def test_nested_encap_and_decap_emit_ordered_events(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "encap_order.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    pipe = EncapsulationPipeline(trace_node="r1")
    inner = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", ttl=64, protocol=6)])

    gre_packet = pipe.encapsulate(
        inner,
        TunnelConfig(tunnel_src="192.0.2.1", tunnel_dst="192.0.2.2", mode=TunnelMode.GRE, key=7),
    )
    ipsec_packet = pipe.encapsulate(
        gre_packet,
        TunnelConfig(tunnel_src="198.51.100.1", tunnel_dst="198.51.100.2", mode=TunnelMode.IPSEC, ipsec_spi=101),
    )
    after_ipsec = pipe.decapsulate(ipsec_packet, TunnelMode.IPSEC)
    _after_gre = pipe.decapsulate(after_ipsec, TunnelMode.GRE)

    close_env_recorders()
    events = load_trace_events(trace_path)
    event_types = [event.event_type for event in events]

    assert event_types == [
        EventType.ENCAP_PUSH,
        EventType.CRYPTO_ENCRYPT,
        EventType.ENCAP_PUSH,
        EventType.CRYPTO_DECRYPT,
        EventType.ENCAP_POP,
        EventType.ENCAP_POP,
    ]


def test_ipsec_decrypt_happens_before_ipsec_pop(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "ipsec_decrypt_then_pop.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    pipe = EncapsulationPipeline(trace_node="r1")
    inner = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", ttl=64, protocol=17)])
    protected = pipe.encapsulate(
        inner,
        TunnelConfig(tunnel_src="198.51.100.1", tunnel_dst="198.51.100.2", mode=TunnelMode.IPSEC, ipsec_spi=500),
    )
    pipe.decapsulate(protected, TunnelMode.IPSEC)

    close_env_recorders()
    events = load_trace_events(trace_path)

    decrypt_idx = next(i for i, event in enumerate(events) if event.event_type == EventType.CRYPTO_DECRYPT)
    pop_idx = next(
        i
        for i, event in enumerate(events)
        if event.event_type == EventType.ENCAP_POP and event.details.get("tunnel_type") == TunnelMode.IPSEC.value
    )
    assert decrypt_idx < pop_idx


def test_malformed_tunnel_packet_emits_drop_event(monkeypatch, tmp_path: Path) -> None:
    trace_path = tmp_path / "encap_drop.jsonl"
    monkeypatch.setenv("PYCIE_TRACE_OUT", str(trace_path))
    close_env_recorders()

    pipe = EncapsulationPipeline(trace_node="r1")
    malformed = PacketStack(headers=[IPv4Header(src_ip="1.1.1.1", dst_ip="2.2.2.2", ttl=64, protocol=47)])

    pipe.decapsulate(malformed, TunnelMode.GRE)

    close_env_recorders()
    events = load_trace_events(trace_path)

    assert len(events) == 1
    assert events[0].event_type == EventType.FRAME_DROP
    assert events[0].details["drop_reason"] in {
        "gre_truncated",
        "gre_header_missing",
        "gre_missing_outer_ipv4",
        "gre_wrong_ipv4_protocol",
    }
