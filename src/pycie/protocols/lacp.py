"""Lab 29: simplified LACP bundle negotiation and member selection."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import ProtocolBase


@dataclass(frozen=True)
class LACPPortState:
    if_name: str
    key: int
    port_priority: int
    up: bool = True
    partner_system: str | None = None
    partner_key: int | None = None
    synchronized: bool = False
    collecting: bool = False
    distributing: bool = False
    last_rx_ms: int | None = None


@dataclass
class LACPProcess(ProtocolBase):
    """Deterministic LACP actor/partner state for learning labs."""

    name: str = "lacp"
    system_id: str = "00:00:00:00:00:01"
    admin_key: int = 1
    ports: dict[str, LACPPortState] = field(default_factory=dict)

    def add_port(self, if_name: str, *, key: int | None = None, port_priority: int = 128, now_ms: int = 0) -> None:
        """Register local member candidate for bundle."""
        self.ports[if_name] = LACPPortState(
            if_name=if_name,
            key=self.admin_key if key is None else key,
            port_priority=port_priority,
            last_rx_ms=now_ms,
        )

    def receive_lacpdu(
        self,
        if_name: str,
        *,
        partner_system: str,
        partner_key: int,
        now_ms: int,
    ) -> None:
        """Update partner state and synchronization status on one port."""
        port = self.ports.get(if_name)
        if port is None:
            self.add_port(if_name, now_ms=now_ms)
            port = self.ports[if_name]

        synchronized = bool(port.up and port.key == partner_key)
        self.ports[if_name] = LACPPortState(
            if_name=if_name,
            key=port.key,
            port_priority=port.port_priority,
            up=port.up,
            partner_system=partner_system,
            partner_key=partner_key,
            synchronized=synchronized,
            collecting=synchronized,
            distributing=synchronized,
            last_rx_ms=now_ms,
        )

    def active_members(self) -> list[str]:
        """Return sorted list of forwarding-eligible bundle members."""
        members = [
            port.if_name
            for port in self.ports.values()
            if port.up and port.synchronized and port.collecting and port.distributing
        ]
        return sorted(members, key=lambda if_name: (self.ports[if_name].port_priority, if_name))

    def select_egress(self, flow_hash: int) -> str | None:
        """Select egress member by deterministic modulo over active ports."""
        members = self.active_members()
        if not members:
            return None
        return members[flow_hash % len(members)]

    def age_sessions(self, *, now_ms: int, timeout_ms: int = 90_000) -> None:
        """Age out stale partner state and remove synchronization."""
        for if_name, port in list(self.ports.items()):
            if port.last_rx_ms is None:
                continue
            if now_ms - port.last_rx_ms < timeout_ms:
                continue
            self.ports[if_name] = LACPPortState(
                if_name=port.if_name,
                key=port.key,
                port_priority=port.port_priority,
                up=port.up,
                partner_system=port.partner_system,
                partner_key=port.partner_key,
                synchronized=False,
                collecting=False,
                distributing=False,
                last_rx_ms=port.last_rx_ms,
            )

    def set_port_up(self, if_name: str, *, up: bool) -> None:
        """Change local port up/down state while preserving partner metadata."""
        port = self.ports.get(if_name)
        if port is None:
            return
        synchronized = bool(up and port.partner_key == port.key and port.partner_system is not None)
        self.ports[if_name] = LACPPortState(
            if_name=port.if_name,
            key=port.key,
            port_priority=port.port_priority,
            up=up,
            partner_system=port.partner_system,
            partner_key=port.partner_key,
            synchronized=synchronized,
            collecting=synchronized,
            distributing=synchronized,
            last_rx_ms=port.last_rx_ms,
        )
