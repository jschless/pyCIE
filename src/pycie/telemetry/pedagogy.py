"""Lab-oriented pedagogy helpers for explain and visualization views."""

from __future__ import annotations

from typing import Sequence

from .events import EventType, TraceEvent

_LAB_OVERVIEWS: dict[str, str] = {
    "lab01": "Goal: understand MAC learning and flood vs unicast forwarding.",
    "lab02": "Goal: understand STP election and loop-prevention state transitions.",
    "lab03": "Goal: understand OSPF neighbor/LSDB/SPF decision pipeline.",
    "lab04": "Goal: understand BGP session, path selection, and route export.",
    "lab06": "Goal: understand BFD liveliness detection and timeout-driven state.",
    "lab07": "Goal: understand deterministic L3 lookup/select/forward/drop behavior.",
    "lab08": "Goal: understand ARP cache learning and request/reply resolution.",
    "lab11": "Goal: understand encapsulation layering across GRE/IPIP/IPsec tunnels.",
    "lab12": "Goal: understand IPsec policy, encryption, and decapsulation outcomes.",
    "lab21": "Goal: understand stateful NAT session creation and return-flow matching.",
    "lab23": "Goal: understand IS-IS LSP install and per-level SPF outcomes.",
    "lab27": "Goal: understand QoS classification, queue admission, and scheduling.",
    "lab31": "Goal: understand ACL first-match ordering and implicit deny behavior.",
    "lab39": "Goal: understand route candidate ranking and deterministic RIB-to-FIB installation.",
}

_LAB_CHECKPOINTS: dict[str, tuple[str, ...]] = {
    "lab01": (
        "Which MAC addresses are learned before unknown-unicast flooding stops?",
        "What event proves the table now has enough state for deterministic unicast forwarding?",
    ),
    "lab02": (
        "Which BPDU event leads to a root change?",
        "Which port role/state transition prevents loops after convergence?",
    ),
    "lab03": (
        "When does adjacency become FULL and what triggers the transition?",
        "Which LSDB update causes SPF to run again?",
    ),
    "lab04": (
        "Which event confirms the session is established?",
        "What explains the chosen best path and export behavior?",
    ),
    "lab06": (
        "Which control exchanges are required before UP state?",
        "What timeout event proves liveliness detection and failure response?",
    ),
    "lab07": (
        "Which candidates were available during route lookup?",
        "Was the final outcome a forward or drop, and why?",
    ),
    "lab08": (
        "Which ARP learn event satisfied neighbor resolution?",
        "Where is the request/reply interaction that unblocks forwarding?",
    ),
    "lab11": (
        "What is the header order immediately after encapsulation?",
        "Where does decapsulation restore the original packet identity?",
    ),
    "lab12": (
        "Which policy/SA checks led to protect, bypass, or drop?",
        "Do decrypt and decap events occur in the expected order?",
    ),
    "lab21": (
        "Which packet created state and what translation tuple was assigned?",
        "What event shows return-path validation versus rejection?",
    ),
    "lab23": (
        "Which LSP updates were installed versus ignored?",
        "What SPF outcome demonstrates topology reachability?",
    ),
    "lab27": (
        "How did DSCP classification map into queues?",
        "Where does scheduling/dequeue show service order and backlog change?",
    ),
    "lab31": (
        "Which ACL sequence matched first and why?",
        "When no rule matched, how is implicit deny surfaced?",
    ),
    "lab39": (
        "Which route candidates were evaluated in deterministic order?",
        "Why was a candidate skipped, and what was finally installed in FIB?",
    ),
}


def normalize_lab_id(lab: str | None) -> str | None:
    if lab is None:
        return None
    token = lab.strip().lower()
    return token or None


def lab_overview_line(lab: str) -> str | None:
    return _LAB_OVERVIEWS.get(lab)


def lab_checkpoints(lab: str) -> tuple[str, ...]:
    return _LAB_CHECKPOINTS.get(lab, ())


def lab_phase_label(lab: str, event: TraceEvent) -> str:
    e = event.event_type
    if lab == "lab01":
        if e in {EventType.MAC_LEARN, EventType.MAC_AGE_OUT}:
            return "Phase 1: MAC Table State"
        if e in {EventType.L2_FLOOD, EventType.L2_UNICAST_FORWARD}:
            return "Phase 2: L2 Forwarding Decision"
        return "Phase 3: Frame Movement"
    if lab == "lab02":
        if e in {EventType.STP_BPDU_RX, EventType.STP_BPDU_TX}:
            return "Phase 1: BPDU Exchange"
        if e == EventType.STP_ROOT_CHANGE:
            return "Phase 2: Root Election"
        if e == EventType.STP_PORT_ROLE_CHANGE:
            return "Phase 3: Port Role/State Update"
        return "Phase 4: Data-Plane Consequence"
    if lab == "lab03":
        if e in {EventType.OSPF_HELLO_RX, EventType.OSPF_NEIGHBOR_CHANGE}:
            return "Phase 1: Neighbor Formation"
        if e == EventType.OSPF_LSA_INSTALL:
            return "Phase 2: LSDB Update"
        if e == EventType.OSPF_SPF_RUN:
            return "Phase 3: SPF Computation"
        return "Phase 4: Routing Outcome"
    if lab == "lab04":
        if e in {EventType.BGP_OPEN_RX, EventType.BGP_SESSION_CHANGE}:
            return "Phase 1: Session State"
        if e in {EventType.BGP_UPDATE_RX, EventType.BGP_BEST_PATH}:
            return "Phase 2: Best-Path Decision"
        if e == EventType.BGP_UPDATE_EXPORT:
            return "Phase 3: Export Policy"
        return "Phase 4: Routing Outcome"
    if lab == "lab06":
        if e in {EventType.BFD_CONTROL_RX, EventType.BFD_CONTROL_TX}:
            return "Phase 1: Control Exchange"
        if e == EventType.BFD_STATE_CHANGE:
            return "Phase 2: Session State Transition"
        if e == EventType.BFD_TIMEOUT:
            return "Phase 3: Timeout/Failure Detection"
        return "Phase 4: Link Health Outcome"
    if lab == "lab07":
        if e == EventType.ROUTE_LOOKUP:
            return "Phase 1: Candidate Lookup"
        if e == EventType.ROUTE_SELECT:
            return "Phase 2: Route Selection"
        if e in {EventType.FIB_FORWARD, EventType.FIB_DROP}:
            return "Phase 3: Forward or Drop Outcome"
        return "Phase 4: Packet Movement"
    if lab == "lab08":
        if e == EventType.ARP_CACHE_LEARN:
            return "Phase 1: Neighbor Learning"
        if e == EventType.ARP_REQUEST_RX:
            return "Phase 2: ARP Request Processing"
        if e == EventType.ARP_REPLY_TX:
            return "Phase 3: ARP Reply Action"
        return "Phase 4: Forwarding Dependency"
    if lab == "lab11":
        if e == EventType.ENCAP_PUSH:
            return "Phase 1: Encapsulation Stack Build"
        if e == EventType.ENCAP_POP:
            return "Phase 2: Decapsulation Stack Removal"
        if e in {EventType.CRYPTO_ENCRYPT, EventType.CRYPTO_DECRYPT}:
            return "Phase 3: Crypto Coupling"
        return "Phase 4: Packet Outcome"
    if lab == "lab12":
        if e in {EventType.IPSEC_POLICY_EVALUATE, EventType.IPSEC_SA_LOOKUP}:
            return "Phase 1: SPD/SAD Decision"
        if e in {EventType.CRYPTO_ENCRYPT, EventType.CRYPTO_DECRYPT}:
            return "Phase 2: Cryptographic Processing"
        if e in {EventType.ENCAP_PUSH, EventType.ENCAP_POP}:
            return "Phase 3: Tunnel Header Transformation"
        if e == EventType.FRAME_DROP:
            return "Phase 4: Validation/Drop Outcome"
        return "Phase 5: Packet Outcome"
    if lab == "lab21":
        if e == EventType.NAT_SESSION_CREATE:
            return "Phase 1: Session Allocation"
        if e in {EventType.NAT_TRANSLATE_OUTBOUND, EventType.NAT_TRANSLATE_INBOUND}:
            return "Phase 2: Translation Decision"
        if e == EventType.NAT_SESSION_EXPIRE:
            return "Phase 3: Session Aging"
        return "Phase 4: Return-Path Outcome"
    if lab == "lab23":
        if e == EventType.ISIS_LSP_INSTALL:
            return "Phase 1: LSP Database Update"
        if e == EventType.ISIS_SPF_RUN:
            return "Phase 2: SPF Computation"
        return "Phase 3: Route Outcome"
    if lab == "lab27":
        if e == EventType.QOS_REMARK:
            return "Phase 1: Marking"
        if e == EventType.QOS_ENQUEUE:
            return "Phase 2: Queue Admission"
        if e == EventType.QOS_DEQUEUE:
            return "Phase 3: Scheduling/Dequeue"
        return "Phase 4: Service Outcome"
    if lab == "lab31":
        if e == EventType.ACL_EVALUATE:
            return "Phase 1: Rule Evaluation"
        if e in {EventType.FIB_FORWARD, EventType.FIB_DROP}:
            return "Phase 2: Permit or Deny Outcome"
        return "Phase 3: Traffic Consequence"
    if lab == "lab39":
        if e == EventType.RIB_CANDIDATE_EVALUATE:
            return "Phase 1: Candidate Ranking"
        if e == EventType.RIB_ROUTE_SKIP:
            return "Phase 2: Resolution/Validation Skip"
        if e == EventType.RIB_ROUTE_INSTALL:
            return "Phase 3: FIB Programming"
        return "Phase 4: Lookup Outcome"
    return "Phase: Event Timeline"


def lab_phase_coverage(events: Sequence[TraceEvent], lab: str) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for event in events:
        phase = lab_phase_label(lab, event)
        counts[phase] = counts.get(phase, 0) + 1
    return list(counts.items())
