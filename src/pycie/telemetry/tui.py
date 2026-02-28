"""Terminal UI rendering for packet/link visualization."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Sequence

from .events import EventType, TraceEvent


@dataclass
class NodeStats:
    """Per-node counters and last-seen packet metadata."""

    tx_count: int = 0
    rx_count: int = 0
    drop_count: int = 0
    last_packet: str | None = None
    last_event: str | None = None


@dataclass
class LinkStats:
    """Last observed transfer across an undirected link."""

    left: str
    right: str
    direction_src: str | None = None
    direction_dst: str | None = None
    packet_id: str | None = None
    event_type: str | None = None
    time_ms: float | None = None
    ethertype: str | None = None


def render_tui_snapshot(
    events: Sequence[TraceEvent],
    *,
    at_index: int = -1,
    paused: bool = True,
) -> str:
    """Return a snapshot view suitable for non-interactive output/tests."""
    lines = _build_screen_lines(events, at_index=at_index, paused=paused)
    return "\n".join(lines)


def run_tui(events: Sequence[TraceEvent], *, interval_ms: int = 400) -> int:
    """Run interactive TUI playback in a curses terminal."""
    import curses

    if interval_ms <= 0:
        raise ValueError("interval_ms must be positive")

    def _main(stdscr: Any) -> int:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(50)

        if not events:
            index = -1
            paused = True
        else:
            index = 0
            paused = False

        last_tick = time.monotonic()
        step_seconds = interval_ms / 1000.0

        while True:
            now = time.monotonic()
            if not paused and events and now - last_tick >= step_seconds:
                if index < len(events) - 1:
                    index += 1
                    last_tick = now
                else:
                    paused = True

            height, width = stdscr.getmaxyx()
            lines = _build_screen_lines(events, at_index=index, paused=paused)
            stdscr.erase()
            for row, line in enumerate(lines[:height]):
                try:
                    stdscr.addnstr(row, 0, line, max(0, width - 1))
                except curses.error:
                    continue
            stdscr.refresh()

            key = stdscr.getch()
            if key == -1:
                continue
            if key in (ord("q"), ord("Q")):
                return 0
            if key == ord(" "):
                paused = not paused
                last_tick = time.monotonic()
                continue
            if key in (ord("n"), ord("N")):
                paused = True
                if events:
                    index = min(index + 1, len(events) - 1)
                continue
            if key in (ord("b"), ord("B")):
                paused = True
                if events:
                    index = max(index - 1, 0)
                continue
            if key in (ord("r"), ord("R")):
                paused = True
                index = 0 if events else -1
                continue

    return curses.wrapper(_main)


def _build_screen_lines(events: Sequence[TraceEvent], *, at_index: int, paused: bool) -> list[str]:
    if not events:
        return [
            "pycie viz tui | q quit | space play/pause | n next | b back | r reset",
            "No events matched the provided filters.",
        ]

    max_index = _normalize_index(at_index, len(events))
    current = events[max_index]

    nodes, links = _extract_topology(events)
    node_stats = {node: NodeStats() for node in nodes}
    link_stats = {link: LinkStats(left=link[0], right=link[1]) for link in links}

    for event in events[: max_index + 1]:
        _apply_event(event, node_stats, link_stats)

    lines: list[str] = []
    mode = "paused" if paused else "playing"
    lines.append(f"pycie viz tui | q quit | space play/pause | n next | b back | r reset | {mode}")
    lines.append(
        f"Event {max_index + 1}/{len(events)} at t={current.sim_time_ms}ms | current={_format_event_brief(current)}"
    )
    lines.append("")
    lines.append("Topology")
    if not link_stats:
        lines.append("  (no inter-device link events discovered in trace)")
    else:
        for link in sorted(link_stats):
            state = link_stats[link]
            lines.append(f"  {_format_link_line(state)}")

    lines.append("")
    lines.append("Devices")
    for node in sorted(node_stats):
        stat = node_stats[node]
        packet = stat.last_packet if stat.last_packet is not None else "-"
        event_name = stat.last_event if stat.last_event is not None else "-"
        lines.append(
            f"  [{node}] tx={stat.tx_count} rx={stat.rx_count} drop={stat.drop_count} "
            f"last_packet={packet} last_event={event_name}"
        )

    lines.append("")
    lines.append("Packet Detail")
    summary = current.details.get("packet_summary")
    if isinstance(summary, str) and summary:
        lines.append(f"  summary: {summary}")
    protocol_stack = current.details.get("protocol_stack")
    if isinstance(protocol_stack, list) and protocol_stack:
        stack = " > ".join(str(item) for item in protocol_stack)
        lines.append(f"  stack: {stack}")
    packet_tree = current.details.get("packet_tree")
    if isinstance(packet_tree, list) and packet_tree:
        for line in packet_tree:
            lines.append(f"  {line}")
    if not isinstance(summary, str) and not (
        isinstance(packet_tree, list) and packet_tree
    ):
        lines.append("  (no packet decode available for current event)")

    lines.append("")
    lines.append("Recent Events")
    start = max(0, max_index - 8)
    for idx in range(start, max_index + 1):
        marker = ">" if idx == max_index else " "
        lines.append(f"{marker} {idx + 1:03d}: {_format_event_brief(events[idx])}")

    return lines


def _format_event_brief(event: TraceEvent) -> str:
    parts = [f"{event.sim_time_ms}ms", event.event_type.value, f"node={event.node}"]
    if event.packet_id is not None:
        parts.append(f"packet={event.packet_id}")
    decision = event.details.get("decision")
    if isinstance(decision, str):
        parts.append(f"decision={decision}")
    reason = event.details.get("reason")
    if isinstance(reason, str):
        parts.append(f"reason={reason}")
    drop_reason = event.details.get("drop_reason")
    if isinstance(drop_reason, str):
        parts.append(f"drop_reason={drop_reason}")
    src, dst = _infer_link_endpoints(event)
    if src is not None and dst is not None:
        parts.append(f"path={src}->{dst}")
    stack = event.details.get("protocol_stack")
    if isinstance(stack, list) and stack:
        parts.append(f"stack={'>'.join(str(item) for item in stack)}")
    return " ".join(parts)


def _format_link_line(state: LinkStats) -> str:
    if state.direction_src is None or state.direction_dst is None:
        return f"[{state.left}] -------- [{state.right}] (idle)"

    packet = state.packet_id if state.packet_id is not None else "-"
    details: list[str] = []
    if state.ethertype is not None:
        details.append(state.ethertype)
    if state.event_type is not None:
        details.append(state.event_type)
    if state.time_ms is not None:
        details.append(f"t={state.time_ms:.3f}ms")
    suffix = f" {' '.join(details)}" if details else ""
    return f"[{state.direction_src}] --({packet})-> [{state.direction_dst}]{suffix}"


def _extract_topology(events: Sequence[TraceEvent]) -> tuple[list[str], list[tuple[str, str]]]:
    nodes: set[str] = set()
    links: set[tuple[str, str]] = set()
    for event in events:
        nodes.add(event.node)

        src, dst = _infer_link_endpoints(event)
        if src is None or dst is None:
            continue
        nodes.add(src)
        nodes.add(dst)
        links.add(tuple(sorted((src, dst))))
    return sorted(nodes), sorted(links)


def _apply_event(
    event: TraceEvent,
    node_stats: dict[str, NodeStats],
    link_stats: dict[tuple[str, str], LinkStats],
) -> None:
    stat = node_stats.setdefault(event.node, NodeStats())
    if event.event_type == EventType.FRAME_TX:
        stat.tx_count += 1
    if event.event_type == EventType.FRAME_RX:
        stat.rx_count += 1
    if event.event_type == EventType.FRAME_DROP:
        stat.drop_count += 1
    stat.last_event = event.event_type.value
    if event.packet_id is not None:
        stat.last_packet = event.packet_id

    src, dst = _infer_link_endpoints(event)
    if src is None or dst is None:
        return
    key = tuple(sorted((src, dst)))
    link = link_stats.setdefault(key, LinkStats(left=key[0], right=key[1]))
    link.direction_src = src
    link.direction_dst = dst
    link.packet_id = event.packet_id
    link.event_type = event.event_type.value
    link.time_ms = event.sim_time_ms

    ethertype = event.details.get("ethertype")
    if isinstance(ethertype, str):
        link.ethertype = ethertype


def _infer_link_endpoints(event: TraceEvent) -> tuple[str | None, str | None]:
    if event.event_type == EventType.FRAME_ENQUEUE:
        src = event.details.get("src_node")
        dst = event.details.get("dst_node")
        if isinstance(src, str) and isinstance(dst, str):
            return src, dst
        if isinstance(dst, str):
            return event.node, dst

    if event.event_type == EventType.FRAME_DELIVER:
        src = event.details.get("src_node")
        if isinstance(src, str):
            return src, event.node

    return None, None


def _normalize_index(at_index: int, length: int) -> int:
    if length <= 0:
        return -1
    if at_index < 0:
        return length - 1
    if at_index >= length:
        return length - 1
    return at_index
