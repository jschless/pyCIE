"""Lab 33: DHCP services model (server and relay)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import IPv4Address, ip_network


class DHCPMessageType(StrEnum):
    DISCOVER = "discover"
    OFFER = "offer"
    REQUEST = "request"
    ACK = "ack"
    NAK = "nak"
    RELEASE = "release"


@dataclass(frozen=True)
class DHCPMessage:
    msg_type: "DHCPMessageType | str"
    client_id: str
    requested_ip: str | None = None
    yiaddr: str | None = None
    giaddr: str | None = None
    lease_time_s: int = 600


@dataclass(frozen=True)
class DHCPLease:
    ip: str
    client_id: str
    expires_at_ms: float


@dataclass
class DHCPServer:
    """Deterministic DHCPv4 pool allocator with relay helper."""

    pool_cidr: str = "192.0.2.0/29"
    lease_time_ms: int = 600_000
    leases: dict[str, DHCPLease] = field(default_factory=dict)
    offers: dict[str, str] = field(default_factory=dict)

    def handle_discover(self, client_id: str, *, now_ms: float) -> DHCPMessage | None:
        """Return OFFER for a discover request or None when pool exhausted."""
        self.age_leases(now_ms=now_ms)

        existing = self.leases.get(client_id)
        if existing is not None and existing.expires_at_ms > now_ms:
            self.offers[client_id] = existing.ip
            return DHCPMessage(
                msg_type=DHCPMessageType.OFFER,
                client_id=client_id,
                yiaddr=existing.ip,
                lease_time_s=self.lease_time_ms // 1000,
            )

        ip = self._lowest_available_ip()
        if ip is None:
            return None
        self.offers[client_id] = ip
        return DHCPMessage(
            msg_type=DHCPMessageType.OFFER,
            client_id=client_id,
            yiaddr=ip,
            lease_time_s=self.lease_time_ms // 1000,
        )

    def handle_request(self, client_id: str, requested_ip: str | None, *, now_ms: float) -> DHCPMessage:
        """ACK valid request, otherwise NAK."""
        self.age_leases(now_ms=now_ms)

        target_ip = requested_ip or self.offers.get(client_id)
        if target_ip is None:
            return DHCPMessage(msg_type=DHCPMessageType.NAK, client_id=client_id)

        if not self._is_ip_in_pool(target_ip):
            return DHCPMessage(msg_type=DHCPMessageType.NAK, client_id=client_id, requested_ip=target_ip)

        # Allow renewal of existing lease by same client.
        existing = self.leases.get(client_id)
        if existing is not None and existing.ip == target_ip:
            self.leases[client_id] = DHCPLease(
                ip=target_ip,
                client_id=client_id,
                expires_at_ms=now_ms + self.lease_time_ms,
            )
            return DHCPMessage(
                msg_type=DHCPMessageType.ACK,
                client_id=client_id,
                yiaddr=target_ip,
                lease_time_s=self.lease_time_ms // 1000,
            )

        if target_ip in {lease.ip for lease in self.leases.values()}:
            return DHCPMessage(msg_type=DHCPMessageType.NAK, client_id=client_id, requested_ip=target_ip)

        self.leases[client_id] = DHCPLease(
            ip=target_ip,
            client_id=client_id,
            expires_at_ms=now_ms + self.lease_time_ms,
        )
        self.offers.pop(client_id, None)
        return DHCPMessage(
            msg_type=DHCPMessageType.ACK,
            client_id=client_id,
            yiaddr=target_ip,
            lease_time_s=self.lease_time_ms // 1000,
        )

    def renew(self, client_id: str, *, now_ms: float) -> DHCPMessage | None:
        """Renew an existing lease."""
        self.age_leases(now_ms=now_ms)
        lease = self.leases.get(client_id)
        if lease is None:
            return None
        self.leases[client_id] = DHCPLease(
            ip=lease.ip,
            client_id=lease.client_id,
            expires_at_ms=now_ms + self.lease_time_ms,
        )
        return DHCPMessage(
            msg_type=DHCPMessageType.ACK,
            client_id=client_id,
            yiaddr=lease.ip,
            lease_time_s=self.lease_time_ms // 1000,
        )

    def release(self, client_id: str) -> None:
        """Release client lease and pending offer."""
        self.leases.pop(client_id, None)
        self.offers.pop(client_id, None)

    def age_leases(self, *, now_ms: float) -> None:
        """Purge expired leases."""
        self.leases = {
            client_id: lease
            for client_id, lease in self.leases.items()
            if lease.expires_at_ms > now_ms
        }

    @staticmethod
    def relay(message: DHCPMessage, relay_ip: str) -> DHCPMessage:
        """Attach relay-agent address."""
        return DHCPMessage(
            msg_type=message.msg_type,
            client_id=message.client_id,
            requested_ip=message.requested_ip,
            yiaddr=message.yiaddr,
            giaddr=relay_ip,
            lease_time_s=message.lease_time_s,
        )

    def _lowest_available_ip(self) -> str | None:
        in_use = {lease.ip for lease in self.leases.values()}
        for ip in self._pool_host_ips():
            if ip not in in_use:
                return ip
        return None

    def _pool_host_ips(self) -> list[str]:
        pool = ip_network(self.pool_cidr, strict=False)
        return [str(host) for host in pool.hosts()]

    def _is_ip_in_pool(self, value: str) -> bool:
        pool = ip_network(self.pool_cidr, strict=False)
        ip = IPv4Address(value)
        return ip in pool and ip not in {pool.network_address, pool.broadcast_address}
