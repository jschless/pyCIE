"""Lab 41: management-plane observability fundamentals."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .base import ProtocolBase


class SyslogSeverity(StrEnum):
    EMERG = "emerg"
    ALERT = "alert"
    CRIT = "crit"
    ERR = "err"
    WARNING = "warning"
    NOTICE = "notice"
    INFO = "info"
    DEBUG = "debug"


SEVERITY_VALUE: dict[SyslogSeverity, int] = {
    SyslogSeverity.EMERG: 0,
    SyslogSeverity.ALERT: 1,
    SyslogSeverity.CRIT: 2,
    SyslogSeverity.ERR: 3,
    SyslogSeverity.WARNING: 4,
    SyslogSeverity.NOTICE: 5,
    SyslogSeverity.INFO: 6,
    SyslogSeverity.DEBUG: 7,
}


@dataclass(frozen=True)
class LLDPNeighbor:
    local_if: str
    remote_device: str
    remote_if: str
    learned_at_ms: int
    ttl_ms: int = 120_000


@dataclass(frozen=True)
class SyslogRecord:
    severity: int
    message: str
    ts_ms: int


@dataclass(frozen=True)
class DNSRecord:
    hostname: str
    ip: str
    learned_at_ms: int
    ttl_ms: int = 60_000


@dataclass
class ManagementPlaneObservabilityProcess(ProtocolBase):
    """Model LLDP/NTP/Syslog/SNMP/DNS operational checks."""

    name: str = "management_plane_observability"
    lldp_neighbors: dict[tuple[str, str], LLDPNeighbor] = field(default_factory=dict)
    clock_offset_ms: int = 0
    syslog_max_severity: int = 6
    syslog_records: list[SyslogRecord] = field(default_factory=list)
    snmp_oids: dict[str, int | float | str] = field(default_factory=dict)
    dns_records: dict[str, DNSRecord] = field(default_factory=dict)

    def learn_lldp(
        self,
        *,
        local_if: str,
        remote_device: str,
        remote_if: str,
        now_ms: int,
        ttl_ms: int = 120_000,
    ) -> None:
        """Learn or refresh LLDP neighbor adjacency."""
        key = (local_if, remote_device)
        self.lldp_neighbors[key] = LLDPNeighbor(
            local_if=local_if,
            remote_device=remote_device,
            remote_if=remote_if,
            learned_at_ms=now_ms,
            ttl_ms=ttl_ms,
        )

    def age_lldp(self, *, now_ms: int) -> None:
        """Expire LLDP neighbors whose TTL elapsed."""
        expired = [
            key
            for key, neighbor in self.lldp_neighbors.items()
            if now_ms - neighbor.learned_at_ms >= neighbor.ttl_ms
        ]
        for key in expired:
            del self.lldp_neighbors[key]

    def log_syslog(self, *, severity: int | str, message: str, now_ms: int) -> bool:
        """Append syslog event when severity passes configured filter."""
        level = _normalize_severity(severity)
        if level > self.syslog_max_severity:
            return False
        self.syslog_records.append(SyslogRecord(severity=level, message=message, ts_ms=now_ms))
        return True

    def poll_snmp_oid(self, oid: str) -> int | float | str | None:
        """Return current SNMP OID value when present."""
        return self.snmp_oids.get(oid)

    def set_snmp_oid(self, oid: str, value: int | float | str) -> None:
        self.snmp_oids[oid] = value

    def set_clock_offset(self, offset_ms: int) -> None:
        self.clock_offset_ms = offset_ms

    def ntp_in_sync(self, *, max_offset_ms: int = 100) -> bool:
        return abs(self.clock_offset_ms) <= max_offset_ms

    def learn_dns(self, *, hostname: str, ip: str, now_ms: int, ttl_ms: int = 60_000) -> None:
        self.dns_records[hostname.lower()] = DNSRecord(
            hostname=hostname.lower(),
            ip=ip,
            learned_at_ms=now_ms,
            ttl_ms=ttl_ms,
        )

    def resolve_dns(self, hostname: str, *, now_ms: int) -> str | None:
        """Resolve DNS from local cache with TTL expiration."""
        key = hostname.lower()
        record = self.dns_records.get(key)
        if record is None:
            return None
        if now_ms - record.learned_at_ms >= record.ttl_ms:
            del self.dns_records[key]
            return None
        return record.ip

    def check_service_readiness(
        self,
        hostname: str,
        *,
        now_ms: int,
        max_ntp_offset_ms: int = 100,
    ) -> tuple[bool, str]:
        """Validate minimal service dependencies: NTP sync + DNS resolve."""
        if not self.ntp_in_sync(max_offset_ms=max_ntp_offset_ms):
            return False, "ntp_out_of_sync"
        if self.resolve_dns(hostname, now_ms=now_ms) is None:
            return False, "dns_unresolved"
        return True, "ready"


def _normalize_severity(value: int | str) -> int:
    if isinstance(value, int):
        if 0 <= value <= 7:
            return value
        raise ValueError("invalid_syslog_severity")

    name = value.strip().lower()
    try:
        return SEVERITY_VALUE[SyslogSeverity(name)]
    except ValueError as exc:
        raise ValueError("invalid_syslog_severity") from exc
