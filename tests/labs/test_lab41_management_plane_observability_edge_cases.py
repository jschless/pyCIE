"""Edge-case tests for Lab 41 management-plane observability."""

from __future__ import annotations

import pytest

from pycie.protocols.management_plane_observability import ManagementPlaneObservabilityProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab41]


def test_log_syslog_rejects_invalid_severity() -> None:
    proc = ManagementPlaneObservabilityProcess()
    with pytest.raises(ValueError, match="invalid_syslog_severity"):
        proc.log_syslog(severity="verbose", message="invalid", now_ms=0)


def test_resolve_dns_expires_record_after_ttl() -> None:
    proc = ManagementPlaneObservabilityProcess()
    proc.learn_dns(hostname="db.internal", ip="198.51.100.10", now_ms=100, ttl_ms=10)

    assert proc.resolve_dns("db.internal", now_ms=109) == "198.51.100.10"
    assert proc.resolve_dns("db.internal", now_ms=110) is None


def test_check_service_readiness_fails_when_ntp_out_of_sync() -> None:
    proc = ManagementPlaneObservabilityProcess()
    proc.set_clock_offset(500)
    proc.learn_dns(hostname="svc.example.net", ip="203.0.113.5", now_ms=0)

    ready, reason = proc.check_service_readiness("svc.example.net", now_ms=1, max_ntp_offset_ms=100)
    assert not ready
    assert reason == "ntp_out_of_sync"


def test_check_service_readiness_fails_when_dns_unresolved() -> None:
    proc = ManagementPlaneObservabilityProcess()
    proc.set_clock_offset(0)

    ready, reason = proc.check_service_readiness("missing.example.net", now_ms=1)
    assert not ready
    assert reason == "dns_unresolved"
