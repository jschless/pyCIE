"""Lab 40: first-hop gateway redundancy (VRRP-like) fundamentals."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .base import ProtocolBase


@dataclass(frozen=True)
class FHRPRouter:
    router_id: str
    priority: int = 100
    preempt: bool = True
    up: bool = True


@dataclass
class FHRPProcess(ProtocolBase):
    """Elect active gateway and model failover/preemption behavior."""

    name: str = "fhrp"
    group_id: int = 1
    virtual_ip: str = "192.0.2.1"
    routers: dict[str, FHRPRouter] = field(default_factory=dict)
    master_id: str | None = None
    _last_failover_start_ms: int | None = None

    def register_router(
        self,
        router_id: str,
        *,
        priority: int = 100,
        preempt: bool = True,
        up: bool = True,
    ) -> None:
        """Register one router candidate in FHRP group."""
        self.routers[router_id] = FHRPRouter(router_id=router_id, priority=priority, preempt=preempt, up=up)
        self.elect_master()

    def elect_master(self) -> str | None:
        """Elect active master with deterministic tie-break behavior."""
        candidates = [
            router
            for router in self.routers.values()
            if router.up
        ]
        if not candidates:
            self.master_id = None
            return None

        best = sorted(candidates, key=lambda item: (-item.priority, item.router_id), reverse=False)[0]
        current = self.routers.get(self.master_id) if self.master_id is not None else None
        if current is None or not current.up:
            self.master_id = best.router_id
            return self.master_id

        if best.router_id == current.router_id:
            self.master_id = current.router_id
            return self.master_id

        if best.priority > current.priority and best.preempt:
            self.master_id = best.router_id
            return self.master_id

        if best.priority == current.priority and best.router_id < current.router_id and best.preempt:
            self.master_id = best.router_id
            return self.master_id

        return self.master_id

    def update_router(
        self,
        router_id: str,
        *,
        up: bool | None = None,
        priority: int | None = None,
        preempt: bool | None = None,
        now_ms: int | None = None,
    ) -> str | None:
        """Apply state changes and return current elected master."""
        current = self.routers.get(router_id)
        if current is None:
            raise ValueError(f"unknown_router {router_id!r}")

        updated = replace(
            current,
            up=current.up if up is None else up,
            priority=current.priority if priority is None else priority,
            preempt=current.preempt if preempt is None else preempt,
        )
        self.routers[router_id] = updated

        if self.master_id == router_id and not updated.up and now_ms is not None:
            self._last_failover_start_ms = now_ms

        previous_master = self.master_id
        elected = self.elect_master()
        if previous_master != elected and now_ms is not None and self._last_failover_start_ms is None:
            self._last_failover_start_ms = now_ms
        return elected

    def current_virtual_mac(self) -> str:
        """Return deterministic virtual MAC derived from group-id."""
        group = max(0, min(255, self.group_id))
        return f"00:00:5e:00:01:{group:02x}"

    def failover_elapsed_ms(self, *, now_ms: int) -> int:
        """Return elapsed milliseconds since failover start marker."""
        if self._last_failover_start_ms is None:
            return 0
        return max(0, now_ms - self._last_failover_start_ms)
