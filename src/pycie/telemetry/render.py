"""Trace filtering and textual rendering helpers."""

from __future__ import annotations

from collections import defaultdict
from itertools import groupby
from typing import Iterable, Literal, Sequence

from .events import EventType, Layer, TraceEvent

DetailLevel = Literal["compact", "packet", "full"]


def filter_events(
    events: Iterable[TraceEvent],
    *,
    layers: set[Layer] | None = None,
    event_types: set[EventType] | None = None,
    node: str | None = None,
    packet_id: str | None = None,
    from_ms: int | None = None,
    to_ms: int | None = None,
) -> list[TraceEvent]:
    """Return events that satisfy all provided filters."""
    filtered: list[TraceEvent] = []
    for event in events:
        if layers is not None and event.layer not in layers:
            continue
        if event_types is not None and event.event_type not in event_types:
            continue
        if node is not None and event.node != node:
            continue
        if packet_id is not None and event.packet_id != packet_id:
            continue
        if from_ms is not None and event.sim_time_ms < from_ms:
            continue
        if to_ms is not None and event.sim_time_ms > to_ms:
            continue
        filtered.append(event)

    return sorted(filtered, key=lambda event: (event.sim_time_ms, event.seq))


def render_timeline(events: Sequence[TraceEvent], *, detail_level: DetailLevel = "compact") -> list[str]:
    """Render trace events in deterministic timeline format."""
    lines: list[str] = []
    for event in events:
        lines.append(_event_line(event))
        lines.extend(_packet_detail_lines(event, detail_level=detail_level, indent="    "))
    return lines


def render_packet_path(
    events: Sequence[TraceEvent],
    packet_id: str,
    *,
    detail_level: DetailLevel = "packet",
) -> list[str]:
    """Render a packet-centric path timeline."""
    packet_events = [event for event in events if event.packet_id == packet_id]
    if not packet_events:
        return [f"No events found for packet_id={packet_id}"]

    lines = [f"Packet {packet_id} ({len(packet_events)} events)"]
    for event in packet_events:
        lines.append("  " + _sequence_line(event))
        lines.extend(_packet_detail_lines(event, detail_level=detail_level, indent="      "))
    return lines


def render_sequence(
    events: Sequence[TraceEvent],
    *,
    packet_id: str | None = None,
    detail_level: DetailLevel = "compact",
) -> list[str]:
    """Render grouped sequence playback by simulation timestamp."""
    scoped = list(events)
    if packet_id is not None:
        scoped = [event for event in scoped if event.packet_id == packet_id]

    if not scoped:
        suffix = "" if packet_id is None else f" for packet_id={packet_id}"
        return [f"No events found{suffix}."]

    scoped.sort(key=lambda event: (event.sim_time_ms, event.seq))
    lines: list[str] = []
    previous_time: int | None = None

    for sim_time_ms, grouped in groupby(scoped, key=lambda event: event.sim_time_ms):
        delta = 0 if previous_time is None else sim_time_ms - previous_time
        lines.append(f"t={sim_time_ms:06d}ms (+{delta}ms)")
        for event in grouped:
            lines.append("  " + _sequence_line(event))
            lines.extend(_packet_detail_lines(event, detail_level=detail_level, indent="    "))
        previous_time = sim_time_ms

    return lines


def render_topology_snapshot(
    events: Sequence[TraceEvent],
    *,
    at_seq: int | None = None,
    packet_id: str | None = None,
) -> list[str]:
    """Render topology-oriented snapshot and current packet location."""
    scoped = sorted(events, key=lambda event: event.seq)
    if at_seq is not None:
        scoped = [event for event in scoped if event.seq <= at_seq]

    if not scoped:
        return ["No events available for topology snapshot."]

    nodes: set[str] = set()
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"tx": 0, "rx": 0, "drop": 0})
    links: dict[tuple[tuple[str, str], tuple[str, str]], dict[str, object]] = {}

    for event in scoped:
        nodes.add(event.node)

        if event.event_type == EventType.FRAME_TX:
            stats[event.node]["tx"] += 1
        elif event.event_type == EventType.FRAME_RX:
            stats[event.node]["rx"] += 1
        elif event.event_type == EventType.FRAME_DROP:
            stats[event.node]["drop"] += 1

        src_node = event.details.get("src_node")
        src_if = event.details.get("src_if")
        dst_node = event.details.get("dst_node")
        dst_if = event.details.get("dst_if")
        if isinstance(src_node, str):
            nodes.add(src_node)
        if isinstance(dst_node, str):
            nodes.add(dst_node)

        if (
            event.event_type == EventType.FRAME_ENQUEUE
            and isinstance(src_node, str)
            and isinstance(src_if, str)
            and isinstance(dst_node, str)
            and isinstance(dst_if, str)
        ):
            left = (src_node, src_if)
            right = (dst_node, dst_if)
            key = (left, right) if left <= right else (right, left)
            links[key] = {"latency_ms": event.details.get("latency_ms")}

    lines: list[str] = []
    current = scoped[-1]
    lines.append(
        "Topology snapshot "
        f"(seq={current.seq}, sim={current.sim_time_ms}ms, events={len(scoped)})"
    )
    lines.append("Nodes:")
    for node in sorted(nodes):
        node_stats = stats[node]
        lines.append(
            f"  {node}: tx={node_stats['tx']} rx={node_stats['rx']} drop={node_stats['drop']}"
        )

    lines.append("Links:")
    if links:
        for (left, right), meta in sorted(links.items()):
            latency = meta.get("latency_ms")
            if isinstance(latency, (int, float)):
                lines.append(
                    f"  {left[0]}:{left[1]} <-> {right[0]}:{right[1]} latency={latency}ms"
                )
            else:
                lines.append(f"  {left[0]}:{left[1]} <-> {right[0]}:{right[1]}")
    else:
        lines.append("  (no discovered links yet)")

    lines.append("Current event:")
    lines.append("  " + _event_line(current))

    focus = packet_id
    if focus is not None:
        packet_events = [event for event in scoped if event.packet_id == focus]
        if packet_events:
            lines.append(f"Packet {focus} location:")
            lines.append("  " + _packet_location_line(packet_events[-1]))
        else:
            lines.append(f"Packet {focus} location:")
            lines.append("  (packet not seen in selected event window)")

    return lines


def render_stp_summary(events: Sequence[TraceEvent], bridge_id: str | None = None) -> list[str]:
    """Render STP-focused election and role transition summary."""
    stp_events = [event for event in events if event.layer == Layer.STP]
    if bridge_id is not None:
        stp_events = [
            event
            for event in stp_events
            if str(event.details.get("bridge_id", "")) == bridge_id
            or str(event.details.get("new_root_id", "")) == bridge_id
            or str(event.details.get("root_id", "")) == bridge_id
        ]

    if not stp_events:
        return ["No STP events matched the provided filters."]

    lines: list[str] = []
    role_state_by_port: dict[tuple[str, str], tuple[str, str]] = {}
    root_by_node: dict[str, str] = {}

    for event in stp_events:
        if event.event_type == EventType.STP_ROOT_CHANGE:
            root = str(event.details.get("new_root_id", "unknown"))
            root_by_node[event.node] = root
            lines.append(
                f"[{event.sim_time_ms:06d}ms] {event.node} root_change "
                f"old={event.details.get('old_root_id')} new={root} "
                f"cost={event.details.get('new_cost')} root_port={event.details.get('root_port')}"
            )
        elif event.event_type == EventType.STP_PORT_ROLE_CHANGE:
            if_name = str(event.details.get("if_name", event.ingress_if or event.egress_if or "?"))
            new_role = str(event.details.get("new_role", "?"))
            new_state = str(event.details.get("new_state", "?"))
            role_state_by_port[(event.node, if_name)] = (new_role, new_state)
            lines.append(
                f"[{event.sim_time_ms:06d}ms] {event.node}:{if_name} role {event.details.get('old_role')} -> {new_role} "
                f"state {event.details.get('old_state')} -> {new_state}"
            )

    if root_by_node:
        lines.append("Final root view:")
        for node in sorted(root_by_node):
            lines.append(f"  {node}: root={root_by_node[node]}")

    if role_state_by_port:
        lines.append("Final port roles:")
        grouped: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        for (node, if_name), (role, state) in sorted(role_state_by_port.items()):
            grouped[node].append((if_name, role, state))
        for node in sorted(grouped):
            for if_name, role, state in grouped[node]:
                lines.append(f"  {node}:{if_name} role={role} state={state}")

    return lines


def _event_line(event: TraceEvent) -> str:
    parts = [
        f"seq={event.seq:05d}",
        f"sim={event.sim_time_ms:06d}ms",
        f"node={event.node}",
        f"layer={event.layer.value}",
        f"event={event.event_type.value}",
    ]
    if event.ingress_if is not None:
        parts.append(f"in={event.ingress_if}")
    if event.egress_if is not None:
        parts.append(f"out={event.egress_if}")
    if event.packet_id is not None:
        parts.append(f"packet={event.packet_id}")

    for key in sorted(event.details):
        if key in {"packet_summary", "packet_tree"}:
            continue
        value = event.details[key]
        if isinstance(value, list):
            rendered = ",".join(str(item) for item in value)
            parts.append(f"{key}=[{rendered}]")
            continue
        parts.append(f"{key}={value}")

    return " ".join(parts)


def _sequence_line(event: TraceEvent) -> str:
    packet = f"[{event.packet_id}] " if event.packet_id else ""
    if event.event_type == EventType.FRAME_ENQUEUE:
        src_node = str(event.details.get("src_node", event.node))
        src_if = str(event.details.get("src_if", event.egress_if or "?"))
        dst_node = str(event.details.get("dst_node", "?"))
        dst_if = str(event.details.get("dst_if", "?"))
        latency = event.details.get("latency_ms")
        latency_part = f" latency={latency}ms" if isinstance(latency, (int, float)) else ""
        return f"{packet}{src_node}:{src_if} --> {dst_node}:{dst_if}{latency_part}"

    suffix = []
    if event.ingress_if is not None:
        suffix.append(f"in={event.ingress_if}")
    if event.egress_if is not None:
        suffix.append(f"out={event.egress_if}")
    if "drop_reason" in event.details:
        suffix.append(f"drop_reason={event.details['drop_reason']}")

    suffix_text = "" if not suffix else " " + " ".join(suffix)
    return f"{packet}{event.node} {event.layer.value}/{event.event_type.value}{suffix_text}"


def _packet_detail_lines(
    event: TraceEvent,
    *,
    detail_level: DetailLevel,
    indent: str,
) -> list[str]:
    if detail_level == "compact":
        return []

    lines: list[str] = []
    packet_summary = event.details.get("packet_summary")
    if isinstance(packet_summary, str):
        lines.append(f"{indent}packet: {packet_summary}")

    if detail_level != "full":
        return lines

    packet_tree = event.details.get("packet_tree")
    if isinstance(packet_tree, list) and packet_tree:
        lines.append(f"{indent}packet_tree:")
        for tree_line in packet_tree:
            lines.append(f"{indent}  {tree_line}")

    return lines


def _packet_location_line(event: TraceEvent) -> str:
    packet = event.packet_id or "(unknown)"

    if event.event_type == EventType.FRAME_ENQUEUE:
        src_node = str(event.details.get("src_node", event.node))
        src_if = str(event.details.get("src_if", event.egress_if or "?"))
        dst_node = str(event.details.get("dst_node", "?"))
        dst_if = str(event.details.get("dst_if", "?"))
        return f"{packet} in transit {src_node}:{src_if} -> {dst_node}:{dst_if}"

    if event.ingress_if is not None:
        return f"{packet} at {event.node} ingress {event.ingress_if}"

    if event.egress_if is not None:
        return f"{packet} leaving {event.node} egress {event.egress_if}"

    return f"{packet} at node {event.node}"
