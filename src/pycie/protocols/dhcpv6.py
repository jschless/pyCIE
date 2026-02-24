"""Lab 28: DHCPv6 server and relay fundamentals."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import IPv6Address, ip_network


class DHCPv6MessageType(StrEnum):
    SOLICIT = "solicit"
    ADVERTISE = "advertise"
    REQUEST = "request"
    REPLY = "reply"
    RENEW = "renew"
    RELEASE = "release"


@dataclass(frozen=True)
class DHCPv6Message:
    msg_type: "DHCPv6MessageType | str"
    client_duid: str
    requested_ip: str | None = None
    offered_ip: str | None = None
    relay_link_address: str | None = None
    lease_time_s: int = 600
    status: str = "success"


@dataclass(frozen=True)
class DHCPv6Lease:
    ip: str
    client_duid: str
    expires_at_ms: int


@dataclass
class DHCPv6Server:
    """Deterministic DHCPv6 IA_NA allocator with relay helper."""

    pool_cidr: str = "2001:db8:100::/120"
    lease_time_ms: int = 600_000
    leases: dict[str, DHCPv6Lease] = field(default_factory=dict)
    offers: dict[str, str] = field(default_factory=dict)

    def handle_solicit(self, client_duid: str, *, now_ms: int) -> DHCPv6Message | None:
        """Return ADVERTISE for available address, else None when exhausted."""
        self.age_leases(now_ms=now_ms)

        existing = self.leases.get(client_duid)
        if existing is not None and existing.expires_at_ms > now_ms:
            self.offers[client_duid] = existing.ip
            return DHCPv6Message(
                msg_type=DHCPv6MessageType.ADVERTISE,
                client_duid=client_duid,
                offered_ip=existing.ip,
                lease_time_s=self.lease_time_ms // 1000,
            )

        ip = self._lowest_available_ip()
        if ip is None:
            return None
        self.offers[client_duid] = ip
        return DHCPv6Message(
            msg_type=DHCPv6MessageType.ADVERTISE,
            client_duid=client_duid,
            offered_ip=ip,
            lease_time_s=self.lease_time_ms // 1000,
        )

    def handle_request(self, client_duid: str, requested_ip: str | None, *, now_ms: int) -> DHCPv6Message:
        """Return REPLY with accepted lease or noaddravail status."""
        self.age_leases(now_ms=now_ms)
        target_ip = requested_ip or self.offers.get(client_duid)
        if target_ip is None or not self._is_ip_in_pool(target_ip):
            return DHCPv6Message(
                msg_type=DHCPv6MessageType.REPLY,
                client_duid=client_duid,
                requested_ip=requested_ip,
                status="noaddravail",
            )

        current = self.leases.get(client_duid)
        if current is not None and current.ip == target_ip:
            self.leases[client_duid] = DHCPv6Lease(
                ip=target_ip,
                client_duid=client_duid,
                expires_at_ms=now_ms + self.lease_time_ms,
            )
            return DHCPv6Message(
                msg_type=DHCPv6MessageType.REPLY,
                client_duid=client_duid,
                offered_ip=target_ip,
                lease_time_s=self.lease_time_ms // 1000,
            )

        if target_ip in {lease.ip for lease in self.leases.values()}:
            return DHCPv6Message(
                msg_type=DHCPv6MessageType.REPLY,
                client_duid=client_duid,
                requested_ip=target_ip,
                status="noaddravail",
            )

        self.leases[client_duid] = DHCPv6Lease(
            ip=target_ip,
            client_duid=client_duid,
            expires_at_ms=now_ms + self.lease_time_ms,
        )
        self.offers.pop(client_duid, None)
        return DHCPv6Message(
            msg_type=DHCPv6MessageType.REPLY,
            client_duid=client_duid,
            offered_ip=target_ip,
            lease_time_s=self.lease_time_ms // 1000,
        )

    def renew(self, client_duid: str, *, now_ms: int) -> DHCPv6Message | None:
        """Renew active lease when present."""
        self.age_leases(now_ms=now_ms)
        lease = self.leases.get(client_duid)
        if lease is None:
            return None
        self.leases[client_duid] = DHCPv6Lease(
            ip=lease.ip,
            client_duid=lease.client_duid,
            expires_at_ms=now_ms + self.lease_time_ms,
        )
        return DHCPv6Message(
            msg_type=DHCPv6MessageType.REPLY,
            client_duid=client_duid,
            offered_ip=lease.ip,
            lease_time_s=self.lease_time_ms // 1000,
        )

    def release(self, client_duid: str) -> None:
        """Release assigned lease and pending offer."""
        self.leases.pop(client_duid, None)
        self.offers.pop(client_duid, None)

    def age_leases(self, *, now_ms: int) -> None:
        """Purge expired leases."""
        self.leases = {
            client_duid: lease
            for client_duid, lease in self.leases.items()
            if lease.expires_at_ms > now_ms
        }

    @staticmethod
    def relay(message: DHCPv6Message, relay_link_address: str) -> DHCPv6Message:
        """Stamp relay link-address onto downstream DHCPv6 message."""
        return DHCPv6Message(
            msg_type=message.msg_type,
            client_duid=message.client_duid,
            requested_ip=message.requested_ip,
            offered_ip=message.offered_ip,
            relay_link_address=relay_link_address,
            lease_time_s=message.lease_time_s,
            status=message.status,
        )

    def _lowest_available_ip(self) -> str | None:
        in_use = {lease.ip for lease in self.leases.values()}
        for ip in self._pool_host_ips():
            if ip not in in_use:
                return ip
        return None

    def _pool_host_ips(self) -> list[str]:
        pool = ip_network(self.pool_cidr, strict=False)
        return [str(host) for host in pool.hosts() if host != pool.network_address]

    def _is_ip_in_pool(self, value: str) -> bool:
        pool = ip_network(self.pool_cidr, strict=False)
        ip = IPv6Address(value)
        return ip in pool and ip != pool.network_address
