"""Lab 38: explicit control-plane database models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OSPFLSA:
    lsa_id: str
    advertising_router: str
    sequence: int
    body: tuple[tuple[str, int], ...]
    updated_at_ms: float


@dataclass
class OSPFLSDB:
    records: dict[tuple[str, str], OSPFLSA] = field(default_factory=dict)

    def install(self, lsa: OSPFLSA) -> bool:
        key = (lsa.advertising_router, lsa.lsa_id)
        current = self.records.get(key)
        if current is None or lsa.sequence > current.sequence:
            self.records[key] = lsa
            return True
        return False

    def withdraw(self, advertising_router: str, lsa_id: str) -> None:
        self.records.pop((advertising_router, lsa_id), None)


@dataclass(frozen=True)
class BGPPath:
    prefix: str
    next_hop: str
    as_path: tuple[int, ...]
    local_pref: int
    med: int
    peer: str
    updated_at_ms: float


@dataclass
class BGPDatabase:
    adj_rib_in: dict[str, dict[str, BGPPath]] = field(default_factory=dict)
    loc_rib: dict[str, BGPPath] = field(default_factory=dict)

    def install_path(self, path: BGPPath) -> None:
        peer_bucket = self.adj_rib_in.setdefault(path.peer, {})
        current = peer_bucket.get(path.prefix)
        if current is None or path.updated_at_ms >= current.updated_at_ms:
            peer_bucket[path.prefix] = path
        self.recompute_loc_rib()

    def withdraw_path(self, peer: str, prefix: str) -> None:
        peer_bucket = self.adj_rib_in.get(peer)
        if peer_bucket is None:
            return
        peer_bucket.pop(prefix, None)
        self.recompute_loc_rib()

    def candidates(self, prefix: str) -> list[BGPPath]:
        out: list[BGPPath] = []
        for peer_bucket in self.adj_rib_in.values():
            route = peer_bucket.get(prefix)
            if route is not None:
                out.append(route)
        return sorted(out, key=lambda path: (path.peer, path.next_hop))

    def best_path(self, prefix: str) -> BGPPath | None:
        candidates = self.candidates(prefix)
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda path: (
                -path.local_pref,
                len(path.as_path),
                path.med,
                path.next_hop,
                path.peer,
            ),
        )[0]

    def recompute_loc_rib(self) -> None:
        prefixes = {
            prefix
            for peer_bucket in self.adj_rib_in.values()
            for prefix in peer_bucket
        }
        self.loc_rib = {}
        for prefix in sorted(prefixes):
            best = self.best_path(prefix)
            if best is not None:
                self.loc_rib[prefix] = best


@dataclass(frozen=True)
class LDPBinding:
    fec: str
    label: int
    peer: str
    updated_at_ms: float


@dataclass
class LDPDatabase:
    bindings: dict[tuple[str, str], LDPBinding] = field(default_factory=dict)

    def install_binding(self, binding: LDPBinding) -> None:
        key = (binding.peer, binding.fec)
        current = self.bindings.get(key)
        if current is None or binding.updated_at_ms >= current.updated_at_ms:
            self.bindings[key] = binding

    def withdraw_binding(self, peer: str, fec: str) -> None:
        self.bindings.pop((peer, fec), None)

    def bindings_for_fec(self, fec: str) -> list[LDPBinding]:
        return sorted(
            (binding for binding in self.bindings.values() if binding.fec == fec),
            key=lambda binding: (binding.label, binding.peer),
        )

    def best_binding(self, fec: str) -> LDPBinding | None:
        candidates = self.bindings_for_fec(fec)
        return None if not candidates else candidates[0]
