"""Lab 18: OSPF multi-area ABR and summary route model."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class AreaPrefixLSA:
    advertising_router: str
    area_id: int
    prefix: str
    cost: int
    sequence: int = 1


@dataclass(frozen=True)
class SummaryLSA:
    advertising_router: str
    from_area: int
    to_area: int
    prefix: str
    cost: int
    sequence: int = 1


@dataclass(frozen=True)
class OSPFRoute:
    prefix: str
    cost: int
    next_hop: str
    route_type: str
    source_area: int


@dataclass
class OSPFMultiAreaProcess(ProtocolBase):
    """Deterministic multi-area OSPF model with ABR summary behavior."""

    name: str = "ospf_multi_area"
    router_id: str = "0.0.0.0"
    attached_areas: set[int] = field(default_factory=lambda: {0})
    backbone_area: int = 0
    area_lsdb: dict[int, dict[tuple[str, str], AreaPrefixLSA]] = field(default_factory=dict)
    summary_lsdb: dict[int, dict[tuple[str, str, int], SummaryLSA]] = field(default_factory=dict)
    _summary_sequences: dict[tuple[int, int, str], int] = field(default_factory=dict)

    def on_start(self) -> None:
        self.run_abr()

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        del ingress_if
        if isinstance(frame.payload, AreaPrefixLSA):
            self.install_area_lsa(frame.payload)
        elif isinstance(frame.payload, SummaryLSA):
            self.install_summary_lsa(frame.payload)

    def is_abr(self) -> bool:
        return len(self.attached_areas) > 1

    def install_area_lsa(self, lsa: AreaPrefixLSA) -> bool:
        bucket = self.area_lsdb.setdefault(lsa.area_id, {})
        key = (lsa.advertising_router, lsa.prefix)
        current = bucket.get(key)
        if current is None or lsa.sequence > current.sequence:
            bucket[key] = lsa
            return True
        return False

    def install_summary_lsa(self, lsa: SummaryLSA) -> bool:
        bucket = self.summary_lsdb.setdefault(lsa.to_area, {})
        key = (lsa.advertising_router, lsa.prefix, lsa.from_area)
        current = bucket.get(key)
        if current is None or lsa.sequence > current.sequence:
            bucket[key] = lsa
            return True
        return False

    def compute_intra_area_routes(self, area_id: int) -> dict[str, OSPFRoute]:
        entries = self.area_lsdb.get(area_id, {})
        best_by_prefix: dict[str, OSPFRoute] = {}
        for lsa in entries.values():
            candidate = OSPFRoute(
                prefix=lsa.prefix,
                cost=lsa.cost,
                next_hop=lsa.advertising_router,
                route_type="intra",
                source_area=area_id,
            )
            current = best_by_prefix.get(candidate.prefix)
            if current is None or self._prefer(candidate, current):
                best_by_prefix[candidate.prefix] = candidate
        return best_by_prefix

    def originate_summaries_for_target(self, target_area: int) -> list[SummaryLSA]:
        if not self.is_abr():
            return []
        if target_area not in self.attached_areas:
            return []

        known_local = set(self.compute_intra_area_routes(target_area))
        summaries: list[SummaryLSA] = []
        for source_area in sorted(self.attached_areas):
            if source_area == target_area:
                continue
            # Transit between non-backbone areas must flow through area 0.
            if source_area != self.backbone_area and target_area != self.backbone_area:
                continue
            for route in sorted(
                self.compute_intra_area_routes(source_area).values(),
                key=lambda value: (value.prefix, value.cost, value.next_hop),
            ):
                if route.prefix in known_local:
                    continue
                seq_key = (source_area, target_area, route.prefix)
                sequence = self._summary_sequences.get(seq_key, 0) + 1
                self._summary_sequences[seq_key] = sequence
                lsa = SummaryLSA(
                    advertising_router=self.router_id,
                    from_area=source_area,
                    to_area=target_area,
                    prefix=route.prefix,
                    cost=route.cost + 1,
                    sequence=sequence,
                )
                self.install_summary_lsa(lsa)
                summaries.append(lsa)
        return summaries

    def run_abr(self) -> list[SummaryLSA]:
        if not self.is_abr():
            return []
        generated: list[SummaryLSA] = []
        for area_id in sorted(self.attached_areas):
            generated.extend(self.originate_summaries_for_target(area_id))
        return generated

    def compute_routing_table(self, area_id: int) -> dict[str, OSPFRoute]:
        intra = self.compute_intra_area_routes(area_id)
        selected = dict(intra)

        summary_entries = self.summary_lsdb.get(area_id, {})
        for lsa in summary_entries.values():
            candidate = OSPFRoute(
                prefix=lsa.prefix,
                cost=lsa.cost,
                next_hop=lsa.advertising_router,
                route_type="inter",
                source_area=lsa.from_area,
            )
            current = selected.get(candidate.prefix)
            if current is None:
                selected[candidate.prefix] = candidate
                continue
            if current.route_type == "intra":
                continue
            if self._prefer(candidate, current):
                selected[candidate.prefix] = candidate

        return {prefix: selected[prefix] for prefix in sorted(selected)}

    def _prefer(self, left: OSPFRoute, right: OSPFRoute) -> bool:
        return (left.cost, left.next_hop, left.source_area) < (
            right.cost,
            right.next_hop,
            right.source_area,
        )
