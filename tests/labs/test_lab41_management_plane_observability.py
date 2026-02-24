"""Exercise tests for Lab 41 management-plane observability."""

from __future__ import annotations

import pytest

from pycie.protocols.management_plane_observability import ManagementPlaneObservabilityProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab41]


def test_learn_lldp_and_age_removes_expired_neighbor() -> None:
    proc = ManagementPlaneObservabilityProcess()
    proc.learn_lldp(local_if="eth0", remote_device="sw1", remote_if="eth1", now_ms=100, ttl_ms=20)
    assert len(proc.lldp_neighbors) == 1

    proc.age_lldp(now_ms=119)
    assert len(proc.lldp_neighbors) == 1
    proc.age_lldp(now_ms=120)
    assert len(proc.lldp_neighbors) == 0


def test_log_syslog_respects_max_severity_filter() -> None:
    proc = ManagementPlaneObservabilityProcess(syslog_max_severity=4)

    assert proc.log_syslog(severity="warning", message="link flap", now_ms=10)
    assert not proc.log_syslog(severity="info", message="bgp up", now_ms=11)
    assert len(proc.syslog_records) == 1
    assert proc.syslog_records[0].message == "link flap"


def test_snmp_poll_returns_value_after_set() -> None:
    proc = ManagementPlaneObservabilityProcess()
    oid = "1.3.6.1.2.1.1.3.0"
    proc.set_snmp_oid(oid, 12345)

    assert proc.poll_snmp_oid(oid) == 12345
    assert proc.poll_snmp_oid("1.3.6.1.2.1.999.0") is None


def test_check_service_readiness_passes_with_ntp_and_dns() -> None:
    proc = ManagementPlaneObservabilityProcess()
    proc.set_clock_offset(25)
    proc.learn_dns(hostname="api.example.net", ip="192.0.2.44", now_ms=100, ttl_ms=1_000)

    ready, reason = proc.check_service_readiness("api.example.net", now_ms=150, max_ntp_offset_ms=50)
    assert ready
    assert reason == "ready"
