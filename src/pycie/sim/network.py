"""Network topology and simulator skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Callable

from .clock import SimClock
from .events import EventQueue, TimerHandle

NodeId = str
InterfaceName = str
Endpoint = tuple[NodeId, InterfaceName]
ReceiveHandler = Callable[[NodeId, InterfaceName, "Frame"], None]


@dataclass
class Packet:
    """Layer-3 packet placeholder used by protocol tests."""

    src_ip: str
    dst_ip: str
    protocol: str
    payload: Any = None


@dataclass
class Frame:
    """Layer-2 frame placeholder used by protocol tests."""

    src_mac: str
    dst_mac: str
    ethertype: str
    payload: Any = None


@dataclass
class Interface:
    """A node interface in the simulated topology."""

    node_id: NodeId
    name: InterfaceName
    mac: str
    ipv4: str | None = None
    cost: int = 1
    admin_up: bool = True


@dataclass
class Link:
    """A bidirectional link between two endpoints."""

    a: Endpoint
    b: Endpoint
    latency_ms: float = 1.0
    loss_prob: float = 0.0
    admin_up: bool = True

    def other(self, endpoint: Endpoint) -> Endpoint:
        if endpoint == self.a:
            return self.b
        if endpoint == self.b:
            return self.a
        raise ValueError(f"endpoint {endpoint!r} not on link")


@dataclass
class Topology:
    """Inventory for nodes, interfaces, and links."""

    nodes: set[NodeId] = field(default_factory=set)
    interfaces: dict[Endpoint, Interface] = field(default_factory=dict)
    links: dict[frozenset[Endpoint], Link] = field(default_factory=dict)

    def add_node(self, node_id: NodeId) -> None:
        self.nodes.add(node_id)

    def add_interface(self, interface: Interface) -> None:
        endpoint = (interface.node_id, interface.name)
        if interface.node_id not in self.nodes:
            raise KeyError(f"unknown node {interface.node_id!r}")
        self.interfaces[endpoint] = interface

    def connect(
        self,
        a: Endpoint,
        b: Endpoint,
        *,
        latency_ms: float = 1.0,
        loss_prob: float = 0.0,
    ) -> None:
        if a not in self.interfaces:
            raise KeyError(f"unknown interface {a!r}")
        if b not in self.interfaces:
            raise KeyError(f"unknown interface {b!r}")
        key = frozenset((a, b))
        self.links[key] = Link(a=a, b=b, latency_ms=latency_ms, loss_prob=loss_prob)

    def get_interface(self, endpoint: Endpoint) -> Interface:
        return self.interfaces[endpoint]

    def get_link(self, endpoint: Endpoint) -> Link | None:
        for key, link in self.links.items():
            if endpoint in key:
                return link
        return None

    def set_link_admin_state(self, a: Endpoint, b: Endpoint, *, up: bool) -> None:
        key = frozenset((a, b))
        if key not in self.links:
            raise KeyError(f"unknown link {a!r} <-> {b!r}")
        self.links[key].admin_up = up

    def neighbors(self, endpoint: Endpoint) -> list[Endpoint]:
        out: list[Endpoint] = []
        for link in self.links.values():
            if endpoint == link.a:
                out.append(link.b)
            elif endpoint == link.b:
                out.append(link.a)
        return out


@dataclass
class NetworkSimulator:
    """Discrete-event simulator for frame delivery and timers."""

    topology: Topology = field(default_factory=Topology)
    clock: SimClock = field(default_factory=SimClock)
    events: EventQueue = field(default_factory=EventQueue)
    random_seed: int = 7

    def __post_init__(self) -> None:
        self._rng = random.Random(self.random_seed)
        self._receivers: dict[NodeId, ReceiveHandler] = {}

    def register_receiver(self, node_id: NodeId, handler: ReceiveHandler) -> None:
        if node_id not in self.topology.nodes:
            raise KeyError(f"unknown node {node_id!r}")
        self._receivers[node_id] = handler

    def schedule_in(
        self,
        delay_ms: float,
        callback: Callable[..., None],
        *args: Any,
        priority: int = 100,
        **kwargs: Any,
    ) -> TimerHandle:
        if delay_ms < 0:
            raise ValueError("delay must be non-negative")
        at = self.clock.now_ms + delay_ms
        return self.events.schedule(at, callback, *args, priority=priority, **kwargs)

    def run(self, *, until_ms: float | None = None, max_events: int | None = None) -> int:
        """Run scheduled events and return how many executed."""
        executed = 0
        while self.events.has_events():
            next_time = self.events.peek_time()
            if next_time is None:
                break
            if until_ms is not None and next_time > until_ms:
                break
            event = self.events.pop_next()
            self.clock.advance_to(event.at)
            event.run()
            executed += 1
            if max_events is not None and executed >= max_events:
                break
        return executed

    def send_frame(self, from_node: NodeId, egress_if: InterfaceName, frame: Frame) -> None:
        """Queue delivery of a frame over a connected link."""
        src_endpoint = (from_node, egress_if)
        link = self.topology.get_link(src_endpoint)
        if link is None:
            return
        if not link.admin_up:
            return

        src_intf = self.topology.get_interface(src_endpoint)
        if not src_intf.admin_up:
            return

        if self._rng.random() < link.loss_prob:
            return

        dst_endpoint = link.other(src_endpoint)
        dst_intf = self.topology.get_interface(dst_endpoint)
        if not dst_intf.admin_up:
            return

        def deliver() -> None:
            node_id, if_name = dst_endpoint
            receiver = self._receivers.get(node_id)
            if receiver is None:
                return
            receiver(node_id, if_name, frame)

        self.schedule_in(link.latency_ms, deliver)

    def fail_link(self, a: Endpoint, b: Endpoint) -> None:
        self.topology.set_link_admin_state(a, b, up=False)

    def recover_link(self, a: Endpoint, b: Endpoint) -> None:
        self.topology.set_link_admin_state(a, b, up=True)
