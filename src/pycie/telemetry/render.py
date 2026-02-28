"""Trace filtering and textual rendering helpers."""

from __future__ import annotations

from collections import defaultdict
from itertools import groupby
from typing import Iterable, Literal, Sequence

from .events import EventType, Layer, TraceEvent
from .pedagogy import (
    lab_checkpoints,
    lab_overview_line,
    lab_phase_coverage,
    lab_phase_label,
    normalize_lab_id,
)

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


def render_explain(
    events: Sequence[TraceEvent],
    *,
    packet_id: str | None = None,
    max_events: int | None = None,
    lab: str | None = None,
) -> list[str]:
    """Render a pedagogy-first causal explanation of trace events."""
    scoped = sorted(events, key=lambda event: (event.sim_time_ms, event.seq))
    if packet_id is not None:
        scoped = [event for event in scoped if event.packet_id == packet_id]

    if not scoped:
        suffix = "" if packet_id is None else f" for packet_id={packet_id}"
        return [f"No events found{suffix}."]

    lines: list[str] = []
    title = "Trace Explanation"
    if packet_id is not None:
        title += f" (packet={packet_id})"
    normalized_lab = normalize_lab_id(lab)
    if normalized_lab is not None:
        title += f" [{normalized_lab}]"
    lines.append(title)
    lines.append(f"events={len(scoped)}")
    if normalized_lab is not None:
        overview = lab_overview_line(normalized_lab)
        if overview is not None:
            lines.append(overview)
        checkpoints = lab_checkpoints(normalized_lab)
        if checkpoints:
            lines.append("Workbook checkpoints:")
            for idx, checkpoint in enumerate(checkpoints, start=1):
                lines.append(f"  {idx}. {checkpoint}")
        phase_counts = lab_phase_coverage(scoped, normalized_lab)
        if phase_counts:
            lines.append("Phase coverage:")
            for phase, count in phase_counts:
                lines.append(f"  {phase}: {count} event(s)")
    lines.append("")

    limit = len(scoped) if max_events is None else max(0, min(len(scoped), max_events))
    previous_phase: str | None = None
    for event in scoped[:limit]:
        if normalized_lab is not None:
            phase = lab_phase_label(normalized_lab, event)
            if phase != previous_phase:
                if previous_phase is not None:
                    lines.append("")
                lines.append(f"{phase}:")
                previous_phase = phase
        lines.append(
            f"[{event.sim_time_ms:06d}ms seq={event.seq:05d}] "
            f"{event.node}: {_explain_event(event)}"
        )

    if limit < len(scoped):
        remaining = len(scoped) - limit
        lines.append("")
        lines.append(f"... {remaining} more events not shown (increase --max-events)")

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


def _explain_event(event: TraceEvent) -> str:
    packet = f"packet {event.packet_id}" if event.packet_id else "packet"
    details = event.details

    if event.event_type == EventType.FRAME_TX:
        return f"transmitted {packet} on {event.egress_if or '(unknown egress)'}."
    if event.event_type == EventType.FRAME_RX:
        return f"received {packet} on {event.ingress_if or '(unknown ingress)'}."
    if event.event_type == EventType.FRAME_ENQUEUE:
        src_node = str(details.get("src_node", event.node))
        src_if = str(details.get("src_if", event.egress_if or "?"))
        dst_node = str(details.get("dst_node", "?"))
        dst_if = str(details.get("dst_if", "?"))
        latency = details.get("latency_ms")
        latency_suffix = f" with {latency}ms link latency" if isinstance(latency, (int, float)) else ""
        return f"queued {packet} from {src_node}:{src_if} to {dst_node}:{dst_if}{latency_suffix}."
    if event.event_type == EventType.FRAME_DELIVER:
        src_node = details.get("src_node")
        src_if = details.get("src_if")
        if isinstance(src_node, str) and isinstance(src_if, str):
            return f"delivered {packet} from {src_node}:{src_if} to ingress {event.ingress_if or '?'}."
        return f"delivered {packet} to ingress {event.ingress_if or '?'}."
    if event.event_type == EventType.FRAME_DROP:
        drop_reason = details.get("drop_reason")
        if isinstance(drop_reason, str):
            return f"dropped {packet} because {drop_reason}."
        return f"dropped {packet}."

    if event.event_type == EventType.MAC_LEARN:
        mac = details.get("mac")
        interface = details.get("interface", event.ingress_if)
        return f"learned source MAC {mac} on {interface}."
    if event.event_type == EventType.MAC_AGE_OUT:
        mac = details.get("mac")
        previous_if = details.get("previous_interface")
        return f"aged out MAC {mac} previously reachable via {previous_if}."
    if event.event_type == EventType.L2_FLOOD:
        dst_mac = details.get("dst_mac")
        return f"flooded {packet} because destination MAC {dst_mac} is unknown or broadcast."
    if event.event_type == EventType.L2_UNICAST_FORWARD:
        egress = details.get("egress_interface", event.egress_if)
        return f"forwarded {packet} as known unicast toward {egress}."

    if event.event_type == EventType.STP_BPDU_TX:
        return "sent BPDU to advertise current root and path cost."
    if event.event_type == EventType.STP_BPDU_RX:
        return "received BPDU and evaluated whether it is superior."
    if event.event_type == EventType.STP_ROOT_CHANGE:
        old_root = details.get("old_root_id")
        new_root = details.get("new_root_id")
        root_port = details.get("root_port")
        return f"updated root from {old_root} to {new_root}; selected root port {root_port}."
    if event.event_type == EventType.STP_PORT_ROLE_CHANGE:
        if_name = details.get("if_name", event.ingress_if or event.egress_if or "?")
        old_role = details.get("old_role")
        new_role = details.get("new_role")
        old_state = details.get("old_state")
        new_state = details.get("new_state")
        return (
            f"changed {if_name} role {old_role}->{new_role} and state {old_state}->{new_state} "
            "after STP recomputation."
        )

    if event.event_type == EventType.ROUTE_LOOKUP:
        dst = details.get("dst_ip")
        count = details.get("candidate_count")
        return f"performed route lookup for dst={dst}; found {count} candidate route(s)."
    if event.event_type == EventType.ROUTE_SELECT:
        selected = details.get("selected_prefix")
        if selected is None:
            return "route selection found no usable route."
        reason = details.get("reason")
        return f"selected route {selected} using deterministic tie-break ({reason})."
    if event.event_type == EventType.FIB_FORWARD:
        dst = details.get("dst_ip")
        egress = details.get("egress_if", event.egress_if)
        return f"forwarded {packet} toward {dst} via {egress}."
    if event.event_type == EventType.FIB_DROP:
        reason = details.get("drop_reason")
        return f"dropped {packet} in forwarding pipeline because {reason}."
    if event.event_type == EventType.BGP_OPEN_RX:
        peer = details.get("peer_id")
        open_asn = details.get("open_asn")
        return f"received BGP OPEN from {peer} with ASN {open_asn}."
    if event.event_type == EventType.BGP_SESSION_CHANGE:
        peer = details.get("peer_id")
        old_state = details.get("old_state")
        new_state = details.get("new_state")
        reason = details.get("reason")
        return f"peer {peer} session changed {old_state}->{new_state} because {reason}."
    if event.event_type == EventType.BGP_UPDATE_RX:
        prefix = details.get("prefix")
        next_hop = details.get("next_hop")
        return f"installed BGP update for {prefix} with next-hop {next_hop} into Adj-RIB-In."
    if event.event_type == EventType.BGP_BEST_PATH:
        prefix = details.get("prefix")
        selected = details.get("selected_next_hop")
        if selected is None:
            return f"found no best path candidates for {prefix}."
        return f"selected BGP best path for {prefix} via next-hop {selected}."
    if event.event_type == EventType.BGP_UPDATE_EXPORT:
        peer = details.get("peer_id")
        prefix = details.get("prefix")
        return f"exported BGP route {prefix} toward peer {peer}."
    if event.event_type == EventType.OSPF_HELLO_RX:
        peer = details.get("neighbor_id")
        result = details.get("result")
        return f"processed OSPF Hello from {peer} ({result})."
    if event.event_type == EventType.OSPF_NEIGHBOR_CHANGE:
        peer = details.get("neighbor_id")
        old_state = details.get("old_state")
        new_state = details.get("new_state")
        return f"OSPF neighbor {peer} transitioned {old_state}->{new_state}."
    if event.event_type == EventType.OSPF_LSA_INSTALL:
        router = details.get("advertising_router")
        sequence = details.get("sequence")
        installed = details.get("installed")
        return f"evaluated LSA from {router} seq={sequence}; installed={installed}."
    if event.event_type == EventType.OSPF_SPF_RUN:
        count = details.get("reachable_nodes")
        return f"completed OSPF SPF computation with {count} reachable node(s)."
    if event.event_type == EventType.ISIS_LSP_INSTALL:
        system_id = details.get("system_id")
        level = details.get("level")
        installed = details.get("installed")
        return f"evaluated IS-IS LSP level {level} from {system_id}; installed={installed}."
    if event.event_type == EventType.ISIS_SPF_RUN:
        level = details.get("level")
        count = details.get("reachable_nodes")
        return f"completed IS-IS SPF for level {level} with {count} reachable node(s)."
    if event.event_type == EventType.NAT_SESSION_CREATE:
        inside_ip = details.get("inside_ip")
        inside_port = details.get("inside_port")
        translated_ip = details.get("translated_ip")
        translated_port = details.get("translated_port")
        return (
            f"created NAT session for inside {inside_ip}:{inside_port} -> "
            f"translated {translated_ip}:{translated_port}."
        )
    if event.event_type == EventType.NAT_TRANSLATE_OUTBOUND:
        action = details.get("action")
        reason = details.get("reason")
        if action == "translate":
            return (
                "translated outbound flow "
                f"{details.get('inside_ip')}:{details.get('inside_port')} -> "
                f"{details.get('translated_ip')}:{details.get('translated_port')}."
            )
        if action == "bypass":
            return f"bypassed outbound NAT because {reason}."
        return f"dropped outbound NAT flow because {reason}."
    if event.event_type == EventType.NAT_TRANSLATE_INBOUND:
        action = details.get("action")
        reason = details.get("reason")
        if action == "translate":
            decision = details.get("decision")
            return f"translated inbound flow using {decision}."
        return f"dropped inbound NAT flow because {reason}."
    if event.event_type == EventType.NAT_SESSION_EXPIRE:
        return (
            "expired NAT session "
            f"{details.get('inside_ip')}:{details.get('inside_port')} -> "
            f"{details.get('translated_ip')}:{details.get('translated_port')}."
        )
    if event.event_type == EventType.ACL_EVALUATE:
        decision = details.get("decision")
        matched_seq = details.get("matched_seq")
        if matched_seq is None:
            return f"ACL decision {decision} via implicit deny."
        return f"ACL decision {decision} matched rule seq {matched_seq}."
    if event.event_type == EventType.QOS_REMARK:
        return f"remarked DSCP {details.get('old_dscp')} -> {details.get('new_dscp')}."
    if event.event_type == EventType.QOS_ENQUEUE:
        action = details.get("action")
        queue = details.get("queue")
        depth = details.get("depth")
        if action == "enqueue":
            return f"enqueued packet into {queue} queue (depth={depth})."
        return f"dropped packet at {queue} queue because {details.get('reason')}."
    if event.event_type == EventType.QOS_DEQUEUE:
        return (
            f"dequeued packet from {details.get('queue')} queue "
            f"(remaining={details.get('remaining_depth')})."
        )
    if event.event_type == EventType.ARP_CACHE_LEARN:
        return f"learned ARP mapping {details.get('sender_ip')} -> {details.get('sender_mac')}."
    if event.event_type == EventType.ARP_REQUEST_RX:
        return (
            f"received ARP request who-has {details.get('target_ip')} "
            f"from {details.get('sender_ip')}."
        )
    if event.event_type == EventType.ARP_REPLY_TX:
        return (
            f"sent ARP reply {details.get('sender_ip')} is-at {details.get('sender_mac')} "
            f"to {details.get('target_ip')}."
        )
    if event.event_type == EventType.BFD_CONTROL_RX:
        return (
            f"received BFD control from {details.get('peer_id')} "
            f"({details.get('old_state')}->{details.get('new_state')}, {details.get('result')})."
        )
    if event.event_type == EventType.BFD_CONTROL_TX:
        return f"sent BFD control to {details.get('peer_id')} with state {details.get('state')}."
    if event.event_type == EventType.BFD_STATE_CHANGE:
        return (
            f"BFD session {details.get('peer_id')} changed "
            f"{details.get('old_state')}->{details.get('new_state')} because {details.get('reason')}."
        )
    if event.event_type == EventType.BFD_TIMEOUT:
        return (
            f"BFD session {details.get('peer_id')} timed out "
            f"(elapsed={details.get('elapsed_ms')}ms detect={details.get('detect_time_ms')}ms)."
        )
    if event.event_type == EventType.IPSEC_POLICY_EVALUATE:
        direction = details.get("direction")
        action = details.get("action")
        policy_id = details.get("policy_id")
        reason = details.get("reason")
        if policy_id is None:
            return f"evaluated IPsec {direction} policy decision={action} ({reason})."
        return (
            f"evaluated IPsec {direction} policy {policy_id}; "
            f"decision={action} ({reason})."
        )
    if event.event_type == EventType.IPSEC_SA_LOOKUP:
        direction = details.get("direction")
        spi = details.get("spi")
        result = details.get("result")
        return f"looked up IPsec SA (dir={direction}, spi={spi}) and got result={result}."
    if event.event_type == EventType.RIB_CANDIDATE_EVALUATE:
        prefix = details.get("prefix")
        count = details.get("candidate_count")
        rank = details.get("candidate_rank")
        if rank is None:
            return f"evaluated {count} route candidate(s) for prefix {prefix}."
        return (
            f"evaluated candidate #{rank} for {prefix}: "
            f"{details.get('protocol')} ad={details.get('admin_distance')} "
            f"metric={details.get('metric')} nh={details.get('next_hop')}."
        )
    if event.event_type == EventType.RIB_ROUTE_INSTALL:
        return (
            f"installed FIB route for {details.get('prefix')} via "
            f"{details.get('egress_if')} next-hop {details.get('resolved_next_hop')} "
            f"(source={details.get('source_protocol')})."
        )
    if event.event_type == EventType.RIB_ROUTE_SKIP:
        return (
            f"skipped route candidate for {details.get('prefix')} because {details.get('reason')} "
            f"(next-hop {details.get('next_hop')})."
        )

    if event.event_type == EventType.ENCAP_PUSH:
        inner = details.get("inner_proto")
        outer = details.get("outer_proto")
        tunnel_type = details.get("tunnel_type")
        return f"encapsulated {packet} by pushing {outer} over {inner} ({tunnel_type})."
    if event.event_type == EventType.ENCAP_POP:
        inner = details.get("inner_proto")
        outer = details.get("outer_proto")
        tunnel_type = details.get("tunnel_type")
        return f"decapsulated {packet} by removing {outer}; next visible protocol is {inner} ({tunnel_type})."
    if event.event_type == EventType.CRYPTO_ENCRYPT:
        transform = details.get("transform")
        spi = details.get("spi")
        return f"encrypted {packet} with {transform} (spi={spi})."
    if event.event_type == EventType.CRYPTO_DECRYPT:
        transform = details.get("transform")
        spi = details.get("spi")
        return f"decrypted {packet} with {transform} (spi={spi})."

    return f"processed {packet} at {event.layer.value}/{event.event_type.value}."
