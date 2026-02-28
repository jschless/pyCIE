"""Generate an offline web trace viewer from telemetry events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from .events import EventType, TraceEvent
from .pedagogy import (
    lab_checkpoints,
    lab_overview_line,
    lab_phase_coverage,
    lab_phase_label,
    normalize_lab_id,
)


def normalize_trace_for_web(
    events: Sequence[TraceEvent],
    *,
    trace_path: Path | None = None,
    lab: str | None = None,
) -> dict[str, Any]:
    """Return deterministic viewer payload from trace events."""
    ordered = sorted(events, key=lambda event: (event.sim_time_ms, event.seq))
    normalized_lab = normalize_lab_id(lab)

    nodes: set[str] = set()
    links: dict[str, dict[str, Any]] = {}
    packet_index: dict[str, dict[str, Any]] = {}
    normalized_events: list[dict[str, Any]] = []

    for event in ordered:
        nodes.add(event.node)
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
            key = _link_key(src_node, src_if, dst_node, dst_if)
            link = links.get(key)
            if link is None:
                left, right = _canonical_link_ends(src_node, src_if, dst_node, dst_if)
                link = {
                    "a_node": left[0],
                    "a_if": left[1],
                    "b_node": right[0],
                    "b_if": right[1],
                    "first_seq": event.seq,
                    "last_seq": event.seq,
                    "enqueue_count": 0,
                    "latency_ms": None,
                }
                links[key] = link
            link["last_seq"] = event.seq
            link["enqueue_count"] = int(link["enqueue_count"]) + 1
            latency = event.details.get("latency_ms")
            if isinstance(latency, (int, float)):
                link["latency_ms"] = latency

        phase = None
        if normalized_lab is not None:
            phase = lab_phase_label(normalized_lab, event)
        normalized_event = _normalize_event(event, phase=phase)
        normalized_events.append(normalized_event)

        if event.packet_id is not None:
            packet = packet_index.get(event.packet_id)
            if packet is None:
                packet = {
                    "event_count": 0,
                    "first_seq": event.seq,
                    "last_seq": event.seq,
                    "first_sim_time_ms": event.sim_time_ms,
                    "last_sim_time_ms": event.sim_time_ms,
                }
                packet_index[event.packet_id] = packet
            packet["event_count"] = int(packet["event_count"]) + 1
            packet["first_seq"] = min(int(packet["first_seq"]), event.seq)
            packet["last_seq"] = max(int(packet["last_seq"]), event.seq)
            packet["first_sim_time_ms"] = min(int(packet["first_sim_time_ms"]), event.sim_time_ms)
            packet["last_sim_time_ms"] = max(int(packet["last_sim_time_ms"]), event.sim_time_ms)

    packets_by_id: dict[str, dict[str, Any]] = {}
    for packet_id in sorted(packet_index):
        packets_by_id[packet_id] = packet_index[packet_id]

    lab_payload: dict[str, Any] | None = None
    if normalized_lab is not None:
        lab_payload = {
            "id": normalized_lab,
            "goal": lab_overview_line(normalized_lab),
            "checkpoints": list(lab_checkpoints(normalized_lab)),
            "phase_summary": [
                {"phase": phase, "count": count}
                for phase, count in lab_phase_coverage(ordered, normalized_lab)
            ],
        }

    payload = {
        "schema_version": 1,
        "trace_source": str(trace_path) if trace_path is not None else None,
        "event_count": len(normalized_events),
        "lab": lab_payload,
        "topology": {
            "nodes": sorted(nodes),
            "links": [links[key] for key in sorted(links)],
        },
        "events": normalized_events,
        "packets": {
            "ids": sorted(packet_index),
            "by_id": packets_by_id,
        },
    }
    return payload


def write_web_visualization(
    events: Sequence[TraceEvent],
    *,
    output_dir: Path,
    trace_path: Path | None = None,
    lab: str | None = None,
) -> dict[str, Path]:
    """Write static web viewer assets and return output paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = normalize_trace_for_web(events, trace_path=trace_path, lab=lab)

    serialized = json.dumps(payload, indent=2, sort_keys=True)
    data_json = output_dir / "data.json"
    data_js = output_dir / "data.js"
    index_html = output_dir / "index.html"
    styles_css = output_dir / "styles.css"
    viewer_js = output_dir / "viewer.js"

    data_json.write_text(serialized + "\n", encoding="utf-8")
    data_js.write_text(f"window.PYCIE_WEB_VIZ_DATA = {serialized};\n", encoding="utf-8")
    index_html.write_text(_INDEX_HTML, encoding="utf-8")
    styles_css.write_text(_STYLES_CSS, encoding="utf-8")
    viewer_js.write_text(_VIEWER_JS, encoding="utf-8")

    return {
        "index": index_html,
        "styles": styles_css,
        "viewer": viewer_js,
        "data_json": data_json,
        "data_js": data_js,
    }


def _normalize_event(event: TraceEvent, *, phase: str | None = None) -> dict[str, Any]:
    packet_tree = event.details.get("packet_tree")
    if isinstance(packet_tree, list):
        rendered_packet_tree = [str(line) for line in packet_tree]
    else:
        rendered_packet_tree = []

    packet_summary = event.details.get("packet_summary")
    if not isinstance(packet_summary, str):
        packet_summary = None

    return {
        "seq": event.seq,
        "sim_time_ms": event.sim_time_ms,
        "ts_ms": event.ts_ms,
        "node": event.node,
        "layer": event.layer.value,
        "event_type": event.event_type.value,
        "phase_label": phase,
        "packet_id": event.packet_id,
        "ingress_if": event.ingress_if,
        "egress_if": event.egress_if,
        "details": _sorted_copy(event.details),
        "packet_summary": packet_summary,
        "packet_tree": rendered_packet_tree,
    }


def _canonical_link_ends(
    src_node: str,
    src_if: str,
    dst_node: str,
    dst_if: str,
) -> tuple[tuple[str, str], tuple[str, str]]:
    left = (src_node, src_if)
    right = (dst_node, dst_if)
    if left <= right:
        return left, right
    return right, left


def _link_key(src_node: str, src_if: str, dst_node: str, dst_if: str) -> str:
    left, right = _canonical_link_ends(src_node, src_if, dst_node, dst_if)
    return f"{left[0]}:{left[1]}|{right[0]}:{right[1]}"


def _sorted_copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sorted_copy(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_copy(item) for item in value]
    return value


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>pyCIE Trace Viewer</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <h1>pyCIE Trace Viewer</h1>
    <p>Single-pane timeline, topology, and packet decode playback.</p>
  </header>

  <section class="controls">
    <label>
      Node
      <select id="node-filter"></select>
    </label>
    <label>
      Layer
      <select id="layer-filter"></select>
    </label>
    <label>
      Event
      <select id="event-filter"></select>
    </label>
    <label>
      Phase
      <select id="phase-filter"></select>
    </label>
    <label>
      Drop Reason
      <select id="drop-filter"></select>
    </label>
    <label>
      Packet
      <select id="packet-filter"></select>
    </label>
    <label>
      From ms
      <input id="from-ms-filter" type="number" min="0" step="1" placeholder="start">
    </label>
    <label>
      To ms
      <input id="to-ms-filter" type="number" min="0" step="1" placeholder="end">
    </label>
    <button type="button" id="play-toggle">Play</button>
    <label class="scrubber-wrap">
      Timeline
      <input id="timeline-scrubber" type="range" min="0" max="0" value="0" step="1">
    </label>
    <span id="scrubber-position">0 / 0</span>
  </section>

  <p id="status-line" class="status-line"></p>
  <section class="workbook pane">
    <h2>Workbook</h2>
    <div id="workbook-pane"></div>
  </section>

  <main class="layout">
    <section class="pane">
      <h2>Topology</h2>
      <div id="topology-pane"></div>
    </section>
    <section class="pane pane-wide">
      <h2>Timeline</h2>
      <div id="timeline-pane" class="timeline"></div>
    </section>
    <section class="pane">
      <h2>Packet Decode</h2>
      <div id="decode-pane"></div>
    </section>
  </main>

  <script src="data.js"></script>
  <script src="viewer.js"></script>
</body>
</html>
"""

_STYLES_CSS = """:root {
  --bg: #f6f7f5;
  --bg-accent: #e4ece6;
  --panel: #ffffff;
  --ink: #1f2a24;
  --muted: #60756a;
  --line: #cad6cf;
  --accent: #126b4c;
  --accent-soft: #d7efe4;
  --alert: #8f3200;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
  color: var(--ink);
  background:
    radial-gradient(1200px 500px at 10% 0%, #ffffff 0%, rgba(255, 255, 255, 0) 70%),
    linear-gradient(160deg, var(--bg) 0%, var(--bg-accent) 100%);
}

.hero {
  padding: 1.2rem 1.4rem 0.6rem 1.4rem;
}

.hero h1 {
  margin: 0;
  letter-spacing: 0.02em;
}

.hero p {
  margin: 0.3rem 0 0 0;
  color: var(--muted);
}

.controls {
  display: grid;
  grid-template-columns: repeat(11, minmax(0, 1fr));
  gap: 0.7rem;
  padding: 0.6rem 1.4rem 0.2rem 1.4rem;
  align-items: end;
}

.controls label {
  display: flex;
  flex-direction: column;
  font-size: 0.88rem;
  gap: 0.25rem;
}

.controls select,
.controls button,
.controls input[type="range"],
.controls input[type="number"] {
  border: 1px solid var(--line);
  border-radius: 0.45rem;
  padding: 0.42rem 0.48rem;
  background: var(--panel);
  color: var(--ink);
}

.controls button {
  font-weight: 600;
  cursor: pointer;
}

.controls button:hover {
  border-color: var(--accent);
}

.scrubber-wrap {
  grid-column: span 2;
}

#scrubber-position {
  align-self: center;
  color: var(--muted);
  font-size: 0.9rem;
}

.status-line {
  margin: 0.2rem 1.4rem 0.8rem 1.4rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.workbook {
  margin: 0 1.4rem 0.8rem 1.4rem;
  min-height: auto;
}

.workbook ul {
  margin: 0.4rem 0 0 0;
  padding-left: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.workbook .phase-chip {
  display: inline-block;
  margin: 0.2rem 0.4rem 0.2rem 0;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
  font-size: 0.78rem;
  background: #fbfcfb;
}

.layout {
  display: grid;
  gap: 0.8rem;
  grid-template-columns: 1fr 1.3fr 1fr;
  padding: 0 1.4rem 1.4rem 1.4rem;
}

.pane {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 0.7rem;
  box-shadow: 0 12px 24px rgba(20, 35, 28, 0.06);
  min-height: 420px;
  display: flex;
  flex-direction: column;
}

.pane h2 {
  margin: 0;
  padding: 0.8rem 0.9rem;
  border-bottom: 1px solid var(--line);
  font-size: 1rem;
}

.pane > div {
  padding: 0.8rem 0.9rem;
  overflow: auto;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 0.34rem;
  max-height: 66vh;
}

.timeline-row {
  border: 1px solid var(--line);
  background: #fbfcfb;
  border-radius: 0.5rem;
  cursor: pointer;
  text-align: left;
  font: inherit;
  font-size: 0.84rem;
  line-height: 1.3;
  padding: 0.46rem 0.56rem;
}

.timeline-row:hover {
  border-color: var(--accent);
}

.timeline-row.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.node-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.node-pill {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0.18rem 0.54rem;
  font-size: 0.83rem;
  background: #fbfcfb;
}

.node-pill.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.link-list {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.28rem;
}

.link-list li {
  font-size: 0.84rem;
}

.link-list li.active-link {
  color: var(--accent);
  font-weight: 600;
}

.kv {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.6rem;
  font-family: "JetBrains Mono", "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 0.77rem;
}

.kv th,
.kv td {
  border: 1px solid var(--line);
  padding: 0.35rem 0.44rem;
  vertical-align: top;
}

.kv th {
  width: 34%;
  text-align: left;
  background: #f6f9f7;
  color: #31433a;
}

.decode-summary {
  margin: 0 0 0.5rem 0;
  color: var(--muted);
  font-size: 0.88rem;
}

pre {
  margin: 0.6rem 0 0 0;
  padding: 0.65rem;
  background: #f4f7f5;
  border: 1px solid var(--line);
  border-radius: 0.45rem;
  overflow: auto;
  font-family: "JetBrains Mono", "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 0.76rem;
}

.empty {
  color: var(--muted);
  font-size: 0.9rem;
}

.warning {
  color: var(--alert);
  font-weight: 600;
}

@media (max-width: 1180px) {
  .controls {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .scrubber-wrap {
    grid-column: span 4;
  }

  .layout {
    grid-template-columns: 1fr;
  }

  .pane {
    min-height: 280px;
  }
}
"""

_VIEWER_JS = """(function () {
  "use strict";

  const data = window.PYCIE_WEB_VIZ_DATA;
  const state = {
    events: [],
    filteredEvents: [],
    selectedIndex: 0,
    timer: null,
  };

  const refs = {
    nodeFilter: document.getElementById("node-filter"),
    layerFilter: document.getElementById("layer-filter"),
    eventFilter: document.getElementById("event-filter"),
    phaseFilter: document.getElementById("phase-filter"),
    dropFilter: document.getElementById("drop-filter"),
    packetFilter: document.getElementById("packet-filter"),
    fromMsFilter: document.getElementById("from-ms-filter"),
    toMsFilter: document.getElementById("to-ms-filter"),
    playToggle: document.getElementById("play-toggle"),
    scrubber: document.getElementById("timeline-scrubber"),
    scrubberPosition: document.getElementById("scrubber-position"),
    timelinePane: document.getElementById("timeline-pane"),
    topologyPane: document.getElementById("topology-pane"),
    decodePane: document.getElementById("decode-pane"),
    workbookPane: document.getElementById("workbook-pane"),
    statusLine: document.getElementById("status-line"),
  };

  if (!data || !Array.isArray(data.events)) {
    refs.statusLine.textContent = "Viewer data missing. Re-run pycie viz web to regenerate assets.";
    refs.statusLine.classList.add("warning");
    return;
  }

  state.events = data.events.slice();
  init();

  function init() {
    populateFilters();

    refs.nodeFilter.addEventListener("change", () => applyFilters(true));
    refs.layerFilter.addEventListener("change", () => applyFilters(true));
    refs.eventFilter.addEventListener("change", () => applyFilters(true));
    refs.phaseFilter.addEventListener("change", () => applyFilters(true));
    refs.dropFilter.addEventListener("change", () => applyFilters(true));
    refs.packetFilter.addEventListener("change", () => applyFilters(true));
    refs.fromMsFilter.addEventListener("input", () => applyFilters(true));
    refs.toMsFilter.addEventListener("input", () => applyFilters(true));
    refs.scrubber.addEventListener("input", () => {
      selectEvent(Number(refs.scrubber.value));
    });
    refs.playToggle.addEventListener("click", togglePlayback);

    applyFilters(true);
  }

  function populateFilters() {
    addOptions(refs.nodeFilter, "All nodes", (data.topology && data.topology.nodes) || []);

    const layerSet = new Set();
    const eventSet = new Set();
    const phaseSet = new Set();
    const dropSet = new Set();
    for (const event of state.events) {
      if (typeof event.layer === "string" && event.layer.length > 0) {
        layerSet.add(event.layer);
      }
      if (typeof event.event_type === "string" && event.event_type.length > 0) {
        eventSet.add(event.event_type);
      }
      if (typeof event.phase_label === "string" && event.phase_label.length > 0) {
        phaseSet.add(event.phase_label);
      }
      if (event.details && typeof event.details.drop_reason === "string" && event.details.drop_reason.length > 0) {
        dropSet.add(event.details.drop_reason);
      }
    }
    addOptions(refs.layerFilter, "All layers", Array.from(layerSet).sort());
    addOptions(refs.eventFilter, "All events", Array.from(eventSet).sort());
    addOptions(refs.phaseFilter, "All phases", Array.from(phaseSet).sort());
    addOptions(refs.dropFilter, "All drop reasons", Array.from(dropSet).sort());

    addOptions(refs.packetFilter, "All packets", (data.packets && data.packets.ids) || []);
  }

  function addOptions(select, allLabel, values) {
    select.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = allLabel;
    select.appendChild(allOption);

    for (const value of values) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    }
  }

  function applyFilters(resetSelection) {
    const node = refs.nodeFilter.value;
    const layer = refs.layerFilter.value;
    const eventType = refs.eventFilter.value;
    const phase = refs.phaseFilter.value;
    const dropReason = refs.dropFilter.value;
    const packetId = refs.packetFilter.value;
    const fromMs = parseOptionalNumber(refs.fromMsFilter.value);
    const toMs = parseOptionalNumber(refs.toMsFilter.value);

    state.filteredEvents = state.events.filter((event) => {
      if (node && event.node !== node) {
        return false;
      }
      if (layer && event.layer !== layer) {
        return false;
      }
      if (eventType && event.event_type !== eventType) {
        return false;
      }
      if (phase && event.phase_label !== phase) {
        return false;
      }
      if (dropReason) {
        const eventDropReason =
          event.details && typeof event.details.drop_reason === "string" ? event.details.drop_reason : "";
        if (eventDropReason !== dropReason) {
          return false;
        }
      }
      if (packetId && event.packet_id !== packetId) {
        return false;
      }
      if (fromMs !== null && Number(event.sim_time_ms) < fromMs) {
        return false;
      }
      if (toMs !== null && Number(event.sim_time_ms) > toMs) {
        return false;
      }
      return true;
    });

    stopPlayback();
    renderTimeline();

    if (resetSelection) {
      state.selectedIndex = 0;
    }
    if (state.selectedIndex >= state.filteredEvents.length) {
      state.selectedIndex = Math.max(state.filteredEvents.length - 1, 0);
    }

    refs.scrubber.max = String(Math.max(state.filteredEvents.length - 1, 0));
    refs.scrubber.disabled = state.filteredEvents.length === 0;

    if (state.filteredEvents.length === 0) {
      refs.scrubber.value = "0";
      refs.scrubberPosition.textContent = "0 / 0";
      refs.statusLine.textContent = "No events matched current filters.";
      refs.statusLine.classList.add("warning");
      refs.topologyPane.innerHTML = '<p class="empty">No topology for current filter set.</p>';
      refs.decodePane.innerHTML = '<p class="empty">No event selected.</p>';
      renderWorkbook(null);
      return;
    }

    refs.statusLine.classList.remove("warning");
    const labTip =
      data.lab && data.lab.goal
        ? ` Lab goal: ${data.lab.goal}`
        : "";
    refs.statusLine.textContent =
      `Showing ${state.filteredEvents.length} of ${state.events.length} events.` +
      " Tip: click a row to see field-level decode and explanation." +
      labTip;
    selectEvent(state.selectedIndex);
  }

  function renderTimeline() {
    refs.timelinePane.innerHTML = "";
    if (state.filteredEvents.length === 0) {
      refs.timelinePane.innerHTML = '<p class="empty">No events matched current filters.</p>';
      return;
    }

    const fragment = document.createDocumentFragment();
    state.filteredEvents.forEach((event, index) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "timeline-row";
      row.dataset.index = String(index);
      const phasePrefix = event.phase_label ? `[${event.phase_label}] ` : "";
      row.textContent = `${phasePrefix}${formatEventLine(event)} | ${explainEvent(event)}`;
      row.addEventListener("click", () => selectEvent(index));
      fragment.appendChild(row);
    });

    refs.timelinePane.appendChild(fragment);
  }

  function selectEvent(index) {
    if (state.filteredEvents.length === 0) {
      return;
    }

    const clampedIndex = Math.max(0, Math.min(index, state.filteredEvents.length - 1));
    state.selectedIndex = clampedIndex;
    refs.scrubber.value = String(clampedIndex);
    refs.scrubberPosition.textContent = `${clampedIndex + 1} / ${state.filteredEvents.length}`;

    const event = state.filteredEvents[clampedIndex];

    for (const row of refs.timelinePane.querySelectorAll(".timeline-row")) {
      row.classList.toggle("active", Number(row.dataset.index) === clampedIndex);
    }

    renderTopology(event);
    renderDecode(event);
    renderWorkbook(event);
  }

  function renderTopology(currentEvent) {
    refs.topologyPane.innerHTML = "";

    const nodeGrid = document.createElement("div");
    nodeGrid.className = "node-grid";
    const nodes = (data.topology && data.topology.nodes) || [];
    for (const node of nodes) {
      const pill = document.createElement("span");
      pill.className = "node-pill";
      if (node === currentEvent.node) {
        pill.classList.add("active");
      }
      pill.textContent = node;
      nodeGrid.appendChild(pill);
    }
    refs.topologyPane.appendChild(nodeGrid);

    const links = (data.topology && data.topology.links) || [];
    if (links.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = "No discovered inter-device links in this trace.";
      refs.topologyPane.appendChild(empty);
      return;
    }

    const activeLinkKey = eventLinkKey(currentEvent);
    const list = document.createElement("ul");
    list.className = "link-list";
    for (const link of links) {
      const item = document.createElement("li");
      item.textContent = `${link.a_node}:${link.a_if} <-> ${link.b_node}:${link.b_if} (events=${link.enqueue_count})`;
      const key = canonicalLinkKey(link.a_node, link.a_if, link.b_node, link.b_if);
      if (activeLinkKey && key === activeLinkKey) {
        item.classList.add("active-link");
      }
      list.appendChild(item);
    }
    refs.topologyPane.appendChild(list);
  }

  function renderDecode(event) {
    refs.decodePane.innerHTML = "";

    const summary = document.createElement("p");
    summary.className = "decode-summary";
    const packetId = event.packet_id || "(none)";
    summary.textContent = `seq=${event.seq} sim=${event.sim_time_ms}ms node=${event.node} layer=${event.layer} event=${event.event_type} packet=${packetId}`;
    refs.decodePane.appendChild(summary);

    const explanation = document.createElement("p");
    explanation.className = "decode-summary";
    explanation.textContent = `why: ${explainEvent(event)}`;
    refs.decodePane.appendChild(explanation);

    const rows = [
      ["node", event.node],
      ["layer", event.layer],
      ["event_type", event.event_type],
      ["packet_id", packetId],
      ["ingress_if", event.ingress_if || "(none)"],
      ["egress_if", event.egress_if || "(none)"],
    ];

    const detailRows = flattenFields(event.details || {}, "");
    for (const row of detailRows) {
      rows.push(row);
    }

    const table = document.createElement("table");
    table.className = "kv";
    const body = document.createElement("tbody");
    for (const [field, value] of rows) {
      const tr = document.createElement("tr");
      const th = document.createElement("th");
      const td = document.createElement("td");
      th.textContent = field;
      td.textContent = String(value);
      tr.appendChild(th);
      tr.appendChild(td);
      body.appendChild(tr);
    }
    table.appendChild(body);
    refs.decodePane.appendChild(table);

    if (Array.isArray(event.packet_tree) && event.packet_tree.length > 0) {
      const pre = document.createElement("pre");
      pre.textContent = event.packet_tree.join("\\n");
      refs.decodePane.appendChild(pre);
    }
  }

  function renderWorkbook(currentEvent) {
    refs.workbookPane.innerHTML = "";

    if (!data.lab) {
      refs.workbookPane.innerHTML = '<p class="empty">No lab workbook selected. Re-run with --lab labXX.</p>';
      return;
    }

    const goal = document.createElement("p");
    goal.className = "decode-summary";
    goal.textContent = data.lab.goal ? `goal: ${data.lab.goal}` : `lab: ${data.lab.id || "(unknown)"}`;
    refs.workbookPane.appendChild(goal);

    const checkpoints = Array.isArray(data.lab.checkpoints) ? data.lab.checkpoints : [];
    if (checkpoints.length > 0) {
      const heading = document.createElement("p");
      heading.className = "decode-summary";
      heading.textContent = "checkpoints:";
      refs.workbookPane.appendChild(heading);

      const list = document.createElement("ul");
      for (const checkpoint of checkpoints) {
        const item = document.createElement("li");
        item.textContent = String(checkpoint);
        list.appendChild(item);
      }
      refs.workbookPane.appendChild(list);
    }

    const phaseSummary = Array.isArray(data.lab.phase_summary) ? data.lab.phase_summary : [];
    if (phaseSummary.length > 0) {
      const phaseHeading = document.createElement("p");
      phaseHeading.className = "decode-summary";
      phaseHeading.textContent = "phase coverage:";
      refs.workbookPane.appendChild(phaseHeading);

      const wrap = document.createElement("div");
      for (const entry of phaseSummary) {
        const chip = document.createElement("span");
        chip.className = "phase-chip";
        const phaseName = entry && entry.phase ? entry.phase : "Phase";
        const count = entry && entry.count !== undefined ? entry.count : "?";
        chip.textContent = `${phaseName}: ${count}`;
        if (currentEvent && currentEvent.phase_label === phaseName) {
          chip.style.borderColor = "var(--accent)";
          chip.style.background = "var(--accent-soft)";
          chip.style.fontWeight = "700";
        }
        wrap.appendChild(chip);
      }
      refs.workbookPane.appendChild(wrap);
    }

    if (currentEvent && currentEvent.phase_label) {
      const active = document.createElement("p");
      active.className = "decode-summary";
      active.textContent = `current phase: ${currentEvent.phase_label}`;
      refs.workbookPane.appendChild(active);
    }
  }

  function flattenFields(value, prefix) {
    const rows = [];
    if (value === null || value === undefined) {
      return rows;
    }

    if (Array.isArray(value)) {
      const rendered = value.map((item) => formatScalar(item)).join(", ");
      rows.push([prefix || "details", rendered]);
      return rows;
    }

    if (typeof value !== "object") {
      rows.push([prefix || "details", formatScalar(value)]);
      return rows;
    }

    const keys = Object.keys(value).sort();
    for (const key of keys) {
      const child = value[key];
      const field = prefix ? `${prefix}.${key}` : key;
      if (child !== null && typeof child === "object" && !Array.isArray(child)) {
        rows.push(...flattenFields(child, field));
        continue;
      }
      if (Array.isArray(child)) {
        const rendered = child.map((item) => formatScalar(item)).join(", ");
        rows.push([field, rendered]);
        continue;
      }
      rows.push([field, formatScalar(child)]);
    }
    return rows;
  }

  function formatScalar(value) {
    if (value === null || value === undefined) {
      return "(null)";
    }
    if (typeof value === "object") {
      return JSON.stringify(value);
    }
    return String(value);
  }

  function formatEventLine(event) {
    const packet = event.packet_id ? ` packet=${event.packet_id}` : "";
    return `seq=${event.seq} t=${event.sim_time_ms}ms ${event.node} ${event.layer}/${event.event_type}${packet}`;
  }

  function explainEvent(event) {
    const details = event.details || {};

    if (event.event_type === "FRAME_DROP") {
      const reason = details.drop_reason || "unspecified reason";
      return `frame dropped because ${reason}`;
    }
    if (event.event_type === "FRAME_ENQUEUE") {
      const srcNode = details.src_node || event.node;
      const srcIf = details.src_if || event.egress_if || "?";
      const dstNode = details.dst_node || "?";
      const dstIf = details.dst_if || "?";
      return `queued from ${srcNode}:${srcIf} to ${dstNode}:${dstIf}`;
    }
    if (event.event_type === "ROUTE_SELECT") {
      if (!details.selected_prefix) {
        return "no route selected";
      }
      return `selected ${details.selected_prefix} using deterministic tie-break`;
    }
    if (event.event_type === "FIB_FORWARD") {
      const egress = details.egress_if || event.egress_if || "?";
      return `forwarded via ${egress}`;
    }
    if (event.event_type === "ENCAP_PUSH") {
      return `encapsulated inner ${details.inner_proto || "payload"} with ${details.outer_proto || "tunnel header"}`;
    }
    if (event.event_type === "ENCAP_POP") {
      return `removed outer ${details.outer_proto || "tunnel header"} to expose ${details.inner_proto || "payload"}`;
    }
    if (event.event_type === "CRYPTO_ENCRYPT") {
      return `encrypted packet with ${details.transform || "crypto transform"} (spi=${details.spi || "?"})`;
    }
    if (event.event_type === "CRYPTO_DECRYPT") {
      return `decrypted packet with ${details.transform || "crypto transform"} (spi=${details.spi || "?"})`;
    }
    if (event.event_type === "L2_FLOOD") {
      return "flooded due to unknown or broadcast destination";
    }
    if (event.event_type === "L2_UNICAST_FORWARD") {
      return `unicast forwarding decision to ${details.egress_interface || event.egress_if || "known egress"}`;
    }
    if (event.event_type === "STP_ROOT_CHANGE") {
      return `STP root changed to ${details.new_root_id || "unknown root"}`;
    }
    if (event.event_type === "STP_PORT_ROLE_CHANGE") {
      return `STP role/state update on ${details.if_name || event.ingress_if || event.egress_if || "port"}`;
    }
    if (event.event_type === "MAC_LEARN") {
      return `learned source MAC ${details.mac || "unknown"} on ${details.interface || event.ingress_if || "port"}`;
    }
    if (event.event_type === "BGP_OPEN_RX") {
      return `received BGP OPEN from ${details.peer_id || "peer"} (asn=${details.open_asn || "?"})`;
    }
    if (event.event_type === "BGP_SESSION_CHANGE") {
      return `BGP peer ${details.peer_id || "peer"} changed ${details.old_state || "?"}->${details.new_state || "?"}`;
    }
    if (event.event_type === "BGP_UPDATE_RX") {
      return `BGP update received for ${details.prefix || "prefix"} via ${details.next_hop || "next-hop"}`;
    }
    if (event.event_type === "BGP_BEST_PATH") {
      if (!details.selected_next_hop) {
        return `no BGP best-path candidate for ${details.prefix || "prefix"}`;
      }
      return `selected BGP best path for ${details.prefix || "prefix"} via ${details.selected_next_hop}`;
    }
    if (event.event_type === "BGP_UPDATE_EXPORT") {
      return `exported BGP route ${details.prefix || "prefix"} to ${details.peer_id || "peer"}`;
    }
    if (event.event_type === "OSPF_HELLO_RX") {
      return `OSPF hello from ${details.neighbor_id || "neighbor"} (${details.result || "processed"})`;
    }
    if (event.event_type === "OSPF_NEIGHBOR_CHANGE") {
      return `OSPF neighbor ${details.neighbor_id || "neighbor"} ${details.old_state || "?"}->${details.new_state || "?"}`;
    }
    if (event.event_type === "OSPF_LSA_INSTALL") {
      return `OSPF LSA install decision for ${details.advertising_router || "router"} (installed=${details.installed})`;
    }
    if (event.event_type === "OSPF_SPF_RUN") {
      return `OSPF SPF run complete (reachable=${details.reachable_nodes || "?"})`;
    }
    if (event.event_type === "ISIS_LSP_INSTALL") {
      return `IS-IS LSP level ${details.level || "?"} from ${details.system_id || "system"} (installed=${details.installed})`;
    }
    if (event.event_type === "ISIS_SPF_RUN") {
      return `IS-IS SPF level ${details.level || "?"} complete (reachable=${details.reachable_nodes || "?"})`;
    }
    if (event.event_type === "NAT_SESSION_CREATE") {
      return `created NAT session ${details.inside_ip || "inside"}:${details.inside_port || "?"} -> ${details.translated_ip || "public"}:${details.translated_port || "?"}`;
    }
    if (event.event_type === "NAT_TRANSLATE_OUTBOUND") {
      if (details.action === "translate") {
        return `translated outbound flow to ${details.translated_ip || "public"}:${details.translated_port || "?"}`;
      }
      return `outbound NAT ${details.action || "decision"} because ${details.reason || "policy"}`;
    }
    if (event.event_type === "NAT_TRANSLATE_INBOUND") {
      if (details.action === "translate") {
        return `translated inbound flow using ${details.decision || "session/rule"}`;
      }
      return `inbound NAT drop because ${details.reason || "validation failed"}`;
    }
    if (event.event_type === "NAT_SESSION_EXPIRE") {
      return `expired NAT session ${details.inside_ip || "inside"}:${details.inside_port || "?"}`;
    }
    if (event.event_type === "ACL_EVALUATE") {
      if (details.matched_seq === null || details.matched_seq === undefined) {
        return `ACL decision ${details.decision || "deny"} via implicit deny`;
      }
      return `ACL decision ${details.decision || "permit"} matched rule ${details.matched_seq}`;
    }
    if (event.event_type === "QOS_REMARK") {
      return `remarked DSCP ${details.old_dscp || "?"} -> ${details.new_dscp || "?"}`;
    }
    if (event.event_type === "QOS_ENQUEUE") {
      if (details.action === "enqueue") {
        return `enqueued into ${details.queue || "queue"} (depth=${details.depth || "?"})`;
      }
      return `queue drop in ${details.queue || "queue"} because ${details.reason || "queue_full"}`;
    }
    if (event.event_type === "QOS_DEQUEUE") {
      return `dequeued from ${details.queue || "queue"} (remaining=${details.remaining_depth || "?"})`;
    }
    if (event.event_type === "ARP_CACHE_LEARN") {
      return `learned ARP ${details.sender_ip || "ip"} -> ${details.sender_mac || "mac"}`;
    }
    if (event.event_type === "ARP_REQUEST_RX") {
      return `received ARP request for ${details.target_ip || "target"}`;
    }
    if (event.event_type === "ARP_REPLY_TX") {
      return `sent ARP reply ${details.sender_ip || "ip"} is-at ${details.sender_mac || "mac"}`;
    }
    if (event.event_type === "BFD_CONTROL_RX") {
      return `BFD control rx from ${details.peer_id || "peer"} (${details.result || "processed"})`;
    }
    if (event.event_type === "BFD_CONTROL_TX") {
      return `BFD control tx to ${details.peer_id || "peer"} state=${details.state || "?"}`;
    }
    if (event.event_type === "BFD_STATE_CHANGE") {
      return `BFD state ${details.old_state || "?"}->${details.new_state || "?"} for ${details.peer_id || "peer"}`;
    }
    if (event.event_type === "BFD_TIMEOUT") {
      return `BFD timeout for ${details.peer_id || "peer"} (detect=${details.detect_time_ms || "?"}ms)`;
    }
    if (event.event_type === "IPSEC_POLICY_EVALUATE") {
      return `IPsec ${details.direction || "flow"} policy decision=${details.action || "?"} (${details.reason || "policy"})`;
    }
    if (event.event_type === "IPSEC_SA_LOOKUP") {
      return `IPsec SA lookup spi=${details.spi === null || details.spi === undefined ? "none" : details.spi} result=${details.result || "?"}`;
    }
    if (event.event_type === "RIB_CANDIDATE_EVALUATE") {
      if (details.candidate_rank === null || details.candidate_rank === undefined) {
        return `RIB has ${details.candidate_count || 0} candidate(s) for ${details.prefix || "prefix"}`;
      }
      return `RIB candidate #${details.candidate_rank} for ${details.prefix || "prefix"} (${details.protocol || "protocol"})`;
    }
    if (event.event_type === "RIB_ROUTE_INSTALL") {
      return `installed ${details.prefix || "prefix"} into FIB via ${details.egress_if || "egress"} nh=${details.resolved_next_hop || "?"}`;
    }
    if (event.event_type === "RIB_ROUTE_SKIP") {
      return `skipped route for ${details.prefix || "prefix"} because ${details.reason || "validation failed"}`;
    }
    return "event recorded for trace correlation";
  }

  function parseOptionalNumber(rawValue) {
    if (typeof rawValue !== "string" || rawValue.trim() === "") {
      return null;
    }
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed)) {
      return null;
    }
    return parsed;
  }

  function togglePlayback() {
    if (state.timer !== null) {
      stopPlayback();
      return;
    }
    if (state.filteredEvents.length === 0) {
      return;
    }
    refs.playToggle.textContent = "Pause";
    state.timer = window.setInterval(() => {
      if (state.selectedIndex >= state.filteredEvents.length - 1) {
        stopPlayback();
        return;
      }
      selectEvent(state.selectedIndex + 1);
    }, 650);
  }

  function stopPlayback() {
    if (state.timer !== null) {
      clearInterval(state.timer);
      state.timer = null;
    }
    refs.playToggle.textContent = "Play";
  }

  function eventLinkKey(event) {
    if (!event || event.event_type !== "FRAME_ENQUEUE" || !event.details) {
      return null;
    }
    const srcNode = event.details.src_node;
    const srcIf = event.details.src_if;
    const dstNode = event.details.dst_node;
    const dstIf = event.details.dst_if;
    if (!srcNode || !srcIf || !dstNode || !dstIf) {
      return null;
    }
    return canonicalLinkKey(srcNode, srcIf, dstNode, dstIf);
  }

  function canonicalLinkKey(aNode, aIf, bNode, bIf) {
    const left = `${aNode}:${aIf}`;
    const right = `${bNode}:${bIf}`;
    if (left <= right) {
      return `${left}|${right}`;
    }
    return `${right}|${left}`;
  }
})();
"""
