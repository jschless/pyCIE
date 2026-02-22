"""Lab 14: VRF management scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import ProtocolBase


@dataclass(frozen=True)
class VRFRouteTarget:
    import_rt: str
    export_rt: str


@dataclass
class VRF:
    name: str
    rd: str
    rt: VRFRouteTarget
    interfaces: set[str] = field(default_factory=set)
    routes: dict[str, str] = field(default_factory=dict)


@dataclass
class VRFProcess(ProtocolBase):
    """VRF route-container and leak-policy scaffolding.

    Reading:
    - RFC 4364 (L3VPN concepts)
    """

    name: str = "vrf"
    vrfs: dict[str, VRF] = field(default_factory=dict)

    def create_vrf(self, vrf: VRF) -> None:
        self.vrfs[vrf.name] = vrf

    def bind_interface(self, vrf_name: str, if_name: str) -> None:
        """Attach an interface to VRF."""
        if vrf_name not in self.vrfs:
            raise KeyError(f"unknown VRF {vrf_name!r}")
        self.vrfs[vrf_name].interfaces.add(if_name)

    def install_route(self, vrf_name: str, prefix: str, next_hop: str) -> None:
        """Install route inside selected VRF."""
        if vrf_name not in self.vrfs:
            raise KeyError(f"unknown VRF {vrf_name!r}")
        self.vrfs[vrf_name].routes[prefix] = next_hop

    def leak_route(self, src_vrf: str, dst_vrf: str, prefix: str) -> None:
        """Leak route if RT policy allows."""
        if src_vrf not in self.vrfs or dst_vrf not in self.vrfs:
            raise KeyError("source or destination VRF does not exist")

        src = self.vrfs[src_vrf]
        dst = self.vrfs[dst_vrf]

        if prefix not in src.routes:
            return
        if src.rt.export_rt != dst.rt.import_rt:
            return

        dst.routes[prefix] = src.routes[prefix]
