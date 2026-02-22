"""Routing Information Base (RIB) scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Route:
    """A candidate route for a prefix."""

    prefix: str
    next_hop: str | None
    admin_distance: int
    metric: int
    source: str
    attributes: dict[str, Any] = field(default_factory=dict)


class RIB:
    """Container for candidate routes and deterministic best-path selection."""

    def __init__(self) -> None:
        self._routes: dict[str, list[Route]] = {}

    def install_route(self, route: Route) -> None:
        bucket = self._routes.setdefault(route.prefix, [])
        if route not in bucket:
            bucket.append(route)

    def withdraw_route(self, route: Route) -> None:
        bucket = self._routes.get(route.prefix)
        if not bucket:
            return
        self._routes[route.prefix] = [r for r in bucket if r != route]
        if not self._routes[route.prefix]:
            del self._routes[route.prefix]

    def candidates(self, prefix: str) -> list[Route]:
        return list(self._routes.get(prefix, []))

    def best_route(self, prefix: str) -> Route | None:
        routes = self._routes.get(prefix, [])
        if not routes:
            return None
        ordered = sorted(
            routes,
            key=lambda r: (
                r.admin_distance,
                r.metric,
                "" if r.next_hop is None else r.next_hop,
                r.source,
            ),
        )
        return ordered[0]

    def all_best_routes(self) -> dict[str, Route]:
        output: dict[str, Route] = {}
        for prefix in self._routes:
            best = self.best_route(prefix)
            if best is not None:
                output[prefix] = best
        return output
