"""Lab 35: VXLAN overlay data-plane model."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.sim.network import Frame


@dataclass(frozen=True)
class VXLANHeader:
    vni: int
    src_vtep: str
    dst_vtep: str


@dataclass(frozen=True)
class VXLANPacket:
    header: VXLANHeader
    inner_frame: Frame


@dataclass
class VXLANBridge:
    """Minimal VXLAN bridge model with VNI-scoped learning."""

    local_vtep_ip: str
    access_ports: dict[int, set[str]] = field(default_factory=dict)
    remote_vteps: dict[int, set[str]] = field(default_factory=dict)
    mac_table: dict[tuple[int, str], str] = field(default_factory=dict)

    def add_access_port(self, vni: int, if_name: str) -> None:
        self.access_ports.setdefault(vni, set()).add(if_name)

    def add_remote_vtep(self, vni: int, vtep_ip: str) -> None:
        self.remote_vteps.setdefault(vni, set()).add(vtep_ip)

    def learn_local(self, vni: int, mac: str, if_name: str) -> None:
        self.mac_table[(vni, mac.lower())] = f"if:{if_name}"

    def learn_remote(self, vni: int, mac: str, vtep_ip: str) -> None:
        self.mac_table[(vni, mac.lower())] = f"vtep:{vtep_ip}"

    def lookup_egress(self, vni: int, ingress_if: str, dst_mac: str) -> list[str]:
        """Return local and/or remote egress targets for destination MAC."""
        key = (vni, dst_mac.lower())
        location = self.mac_table.get(key)
        if location is None or dst_mac.lower() == "ff:ff:ff:ff:ff:ff":
            local = sorted(
                if_name
                for if_name in self.access_ports.get(vni, set())
                if if_name != ingress_if
            )
            remote = [f"vtep:{ip}" for ip in sorted(self.remote_vteps.get(vni, set()))]
            return local + remote

        if location.startswith("if:"):
            if_name = location.split(":", 1)[1]
            if if_name == ingress_if:
                return []
            return [if_name]

        return [location]

    def encapsulate(self, vni: int, dst_vtep: str, frame: Frame) -> VXLANPacket:
        """Build VXLAN packet from an inner Ethernet frame."""
        return VXLANPacket(
            header=VXLANHeader(vni=vni, src_vtep=self.local_vtep_ip, dst_vtep=dst_vtep),
            inner_frame=frame,
        )

    def decapsulate(self, packet: VXLANPacket) -> Frame:
        """Extract inner Ethernet frame."""
        return packet.inner_frame
