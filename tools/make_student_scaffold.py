#!/usr/bin/env python3
"""Generate a student scaffold by stripping reference implementations.

Usage:
    python tools/make_student_scaffold.py \
      --input src/pycie \
      --output dist/student/src/pycie \
      --labs all

You can also target a subset of labs, for example:
    --labs lab07,lab08

Any block between:
    # BEGIN_SOLUTION: short description
    ...
    # END_SOLUTION
is replaced with a `NotImplementedError` TODO.

Additionally, configured methods for selected labs are replaced with TODO raises
while preserving function signatures and docstrings.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
from typing import Iterable

BEGIN = "# BEGIN_SOLUTION"
END = "# END_SOLUTION"


@dataclass(frozen=True)
class Target:
    lab: str
    rel_path: str
    qualname: str
    task: str


TARGETS: tuple[Target, ...] = (
    # lab01
    Target("lab01", "protocols/switching.py", "LearningSwitch.on_frame", "Implement learning switch forwarding pipeline"),
    Target("lab01", "protocols/switching.py", "LearningSwitch.learn_source_mac", "Implement source MAC learning"),
    Target("lab01", "protocols/switching.py", "LearningSwitch.lookup_egress_interfaces", "Implement MAC lookup and flood behavior"),
    Target("lab01", "protocols/switching.py", "LearningSwitch.age_mac_table", "Implement MAC aging"),
    Target("lab01", "protocols/switching.py", "LearningSwitch.should_flood", "Implement broadcast/unknown flood decision"),
    # lab02
    Target("lab02", "protocols/stp.py", "STPProcess.on_start", "Send initial BPDUs and bootstrap STP state"),
    Target("lab02", "protocols/stp.py", "STPProcess.on_frame", "Parse and process inbound BPDUs"),
    Target("lab02", "protocols/stp.py", "STPProcess.build_bpdu", "Build outbound BPDU based on current root view"),
    Target("lab02", "protocols/stp.py", "STPProcess.process_bpdu", "Implement BPDU comparison and root/port selection"),
    Target("lab02", "protocols/stp.py", "STPProcess.recompute_port_states", "Recompute DESIGNATED/ROOT/BLOCKING decisions"),
    Target("lab02", "protocols/stp.py", "STPProcess.should_forward_data", "Implement STP forwarding-state check"),
    # lab03
    Target("lab03", "protocols/ospf.py", "OSPFProcess.on_start", "Initialize OSPF hello and LSA flooding"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.on_frame", "Parse and handle OSPF control packets"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.send_hello", "Implement periodic OSPF hello transmission"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.process_hello", "Implement OSPF neighbor state transitions"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.originate_router_lsa", "Originate local router LSA"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.install_lsa", "Implement LSA sequence handling and LSDB update"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.run_spf", "Implement Dijkstra SPF over current LSDB graph"),
    Target("lab03", "protocols/ospf.py", "OSPFProcess.compute_routing_table", "Translate SPF tree into routing entries"),
    # lab04
    Target("lab04", "protocols/bgp.py", "BGPProcess.on_start", "Start BGP sessions for configured peers"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.on_frame", "Parse and process BGP message payloads"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.establish_session", "Implement BGP peer finite state machine"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.process_open", "Implement OPEN validation and peer negotiation"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.process_update", "Implement Adj-RIB-In update handling"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.best_path", "Implement deterministic BGP best-path algorithm"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.recompute_loc_rib", "Implement Loc-RIB recomputation"),
    Target("lab04", "protocols/bgp.py", "BGPProcess.export_updates_for_peer", "Implement export policy and outbound update build"),
    # lab05
    Target("lab05", "protocols/ldp.py", "LDPProcess.on_start", "Start LDP discovery and mapping advertisement"),
    Target("lab05", "protocols/ldp.py", "LDPProcess.on_frame", "Parse and process inbound LDP messages"),
    Target("lab05", "protocols/ldp.py", "LDPProcess.allocate_local_label", "Implement local label allocation policy"),
    Target("lab05", "protocols/ldp.py", "LDPProcess.advertise_bindings", "Build outbound label mapping advertisements"),
    Target("lab05", "protocols/ldp.py", "LDPProcess.process_label_mapping", "Install remote label binding and update forwarding view"),
    Target("lab05", "protocols/ldp.py", "LDPProcess.build_lfib", "Compute LFIB from local and remote bindings"),
    # lab06
    Target("lab06", "protocols/bfd.py", "BFDProcess.on_start", "Start BFD periodic control transmission"),
    Target("lab06", "protocols/bfd.py", "BFDProcess.on_frame", "Handle inbound BFD control packet"),
    Target("lab06", "protocols/bfd.py", "BFDProcess.open_session", "Create BFD session with local discriminator"),
    Target("lab06", "protocols/bfd.py", "BFDProcess.receive_control", "Implement BFD state machine transition logic"),
    Target("lab06", "protocols/bfd.py", "BFDProcess.transmit_control", "Build outbound BFD control packet fields"),
    Target("lab06", "protocols/bfd.py", "BFDProcess.detect_time_ms", "Compute BFD detection timer"),
    Target("lab06", "protocols/bfd.py", "BFDProcess.check_timeouts", "Implement timeout detection based on last receive time"),
    # lab07
    Target("lab07", "forwarding/l3.py", "IPv4Forwarder.install_route", "Implement route installation and replacement semantics"),
    Target("lab07", "forwarding/l3.py", "IPv4Forwarder.remove_route", "Implement route withdrawal semantics"),
    Target("lab07", "forwarding/l3.py", "IPv4Forwarder.lookup", "Implement IPv4 longest-prefix and tie-break lookup"),
    Target("lab07", "forwarding/l3.py", "IPv4Forwarder.forward", "Implement TTL handling and forward/drop decision"),
    # lab08
    Target("lab08", "protocols/arp.py", "ARPProcess.on_frame", "Parse ARP frames and dispatch request/reply handling"),
    Target("lab08", "protocols/arp.py", "ARPProcess.build_request", "Build ARP request payload"),
    Target("lab08", "protocols/arp.py", "ARPProcess.build_reply", "Build ARP reply payload"),
    Target("lab08", "protocols/arp.py", "ARPProcess.process_message", "Implement ARP request/reply handling behavior"),
    Target("lab08", "forwarding/arp.py", "ARPTable.lookup", "Implement ARP cache lookup with expiration"),
    Target("lab08", "forwarding/arp.py", "ARPTable.update", "Implement ARP cache update logic"),
    Target("lab08", "forwarding/arp.py", "ARPTable.enqueue_pending", "Implement pending packet queue for unresolved ARP"),
    Target("lab08", "forwarding/arp.py", "ARPTable.drain_pending", "Implement pending packet drain behavior"),
    Target("lab08", "forwarding/arp.py", "ARPTable.needs_request", "Implement ARP request trigger decision"),
    Target("lab08", "forwarding/arp.py", "ARPTable.age", "Implement ARP cache aging"),
    # lab09
    Target("lab09", "forwarding/l2.py", "BridgeDomain.ingress_vlan", "Implement access/trunk ingress VLAN classification"),
    Target("lab09", "forwarding/l2.py", "BridgeDomain.learn", "Implement VLAN-aware source MAC learning"),
    Target("lab09", "forwarding/l2.py", "BridgeDomain.lookup_egress", "Implement VLAN-aware unicast/flood forwarding lookup"),
    Target("lab09", "forwarding/l2.py", "BridgeDomain.egress_should_tag", "Implement VLAN egress tagging decision"),
    Target("lab09", "forwarding/l2.py", "BridgeDomain.age_fdb", "Implement VLAN FDB aging"),
    # lab10
    Target("lab10", "protocols/rstp.py", "RSTPProcess.on_start", "Implement RSTP bootstrap and initial BPDU transmission"),
    Target("lab10", "protocols/rstp.py", "RSTPProcess.on_frame", "Parse and process RSTP BPDU input"),
    Target("lab10", "protocols/rstp.py", "RSTPProcess.process_bpdu", "Implement RSTP proposal/agreement state transitions"),
    Target("lab10", "protocols/rstp.py", "RSTPProcess.transmit_bpdu", "Implement outbound RSTP BPDU construction"),
    # lab11
    Target("lab11", "forwarding/encapsulation.py", "EncapsulationPipeline.encapsulate", "Implement GRE/IPIP/IPsec encapsulation stack push"),
    Target("lab11", "forwarding/encapsulation.py", "EncapsulationPipeline.decapsulate", "Implement tunnel decapsulation stack pop"),
    Target("lab11", "protocols/gre.py", "GRETunnelProcess.encapsulate", "Implement GRE tunnel encapsulation"),
    Target("lab11", "protocols/gre.py", "GRETunnelProcess.decapsulate", "Implement GRE packet validation and decapsulation"),
    # lab12
    Target("lab12", "protocols/ipsec.py", "IPsecProcess.outbound", "Implement outbound SPD match and ESP encapsulation"),
    Target("lab12", "protocols/ipsec.py", "IPsecProcess.inbound", "Implement inbound ESP validation and decapsulation"),
    # lab13
    Target("lab13", "model/policy.py", "RoutePolicy.evaluate", "Implement ordered route-policy match and action execution"),
    Target("lab13", "model/policy.py", "RoutePolicy.matches", "Implement route-policy match conditions"),
    Target("lab13", "model/policy.py", "RoutePolicy.apply_action", "Implement route-policy attribute mutations"),
    Target("lab13", "protocols/policy.py", "PolicyProcess.apply_import", "Implement ordered import-policy chain evaluation"),
    Target("lab13", "protocols/policy.py", "PolicyProcess.apply_export", "Implement ordered export-policy chain evaluation"),
    # lab14
    Target("lab14", "protocols/vrf.py", "VRFProcess.bind_interface", "Implement VRF interface binding"),
    Target("lab14", "protocols/vrf.py", "VRFProcess.install_route", "Implement per-VRF route installation"),
    Target("lab14", "protocols/vrf.py", "VRFProcess.leak_route", "Implement VRF route leaking with RT checks"),
    # lab15
    Target("lab15", "forwarding/mpls.py", "MPLSForwarder.forward", "Implement MPLS LFIB lookup and label stack operations"),
    Target("lab15", "protocols/mpls.py", "MPLSProcess.allocate_label", "Implement deterministic local label allocation"),
    Target("lab15", "protocols/mpls.py", "MPLSProcess.install_remote_binding", "Implement remote MPLS binding store"),
    Target("lab15", "protocols/mpls.py", "MPLSProcess.build_lfib_view", "Implement MPLS LFIB derivation from bindings"),
    # lab16
    Target("lab16", "scenario/runner.py", "ScenarioRunner.run", "Implement scenario execution loop and expectation checks"),
    Target("lab16", "scenario/runner.py", "ScenarioRunner.apply_action", "Implement scenario action dispatch"),
    Target("lab16", "scenario/runner.py", "ScenarioRunner.evaluate_expectation", "Implement expectation evaluation logic"),
)


def strip_solution_blocks(text: str) -> str:
    lines = text.splitlines(keepends=True)
    output: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if BEGIN in line:
            indent = line.split("#", 1)[0]
            suffix = line.split(BEGIN, 1)[1].strip(" :\n")
            task = suffix if suffix else "implement this method"

            i += 1
            while i < len(lines) and END not in lines[i]:
                i += 1

            if i >= len(lines):
                raise ValueError("Unclosed solution block detected")

            output.append(
                f"{indent}raise NotImplementedError({json.dumps(f'TODO(student): {task}')})\n"
            )
            i += 1
            continue

        output.append(line)
        i += 1

    return "".join(output)


class _FunctionIndex(ast.NodeVisitor):
    def __init__(self) -> None:
        self._class_stack: list[str] = []
        self.nodes: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        qualname = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
        self.nodes[qualname] = node
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        qualname = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
        self.nodes[qualname] = node
        self.generic_visit(node)


def _leading_ws(line: str) -> str:
    match = re.match(r"\s*", line)
    return match.group(0) if match else ""


def _replace_function_body(
    lines: list[str],
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    task: str,
) -> tuple[int, int, str]:
    if not node.body:
        raise ValueError(f"cannot replace body for empty function {node.name!r}")

    first_stmt = node.body[0]
    has_docstring = (
        isinstance(first_stmt, ast.Expr)
        and isinstance(first_stmt.value, ast.Constant)
        and isinstance(first_stmt.value.value, str)
    )

    if has_docstring and len(node.body) > 1:
        body_start = node.body[1].lineno
    elif has_docstring and len(node.body) == 1:
        # Rare fallback: insert after docstring line.
        body_start = first_stmt.end_lineno + 1
    else:
        body_start = first_stmt.lineno

    body_end = node.end_lineno
    indent_source_line = lines[min(body_start - 1, len(lines) - 1)]
    indent = _leading_ws(indent_source_line)
    replacement = f"{indent}raise NotImplementedError({json.dumps(f'TODO(student): {task}')})\n"
    return body_start, body_end, replacement


def strip_target_functions(text: str, targets: dict[str, str], *, strict: bool = True) -> str:
    if not targets:
        return text

    module = ast.parse(text)
    index = _FunctionIndex()
    index.visit(module)

    lines = text.splitlines(keepends=True)
    replacements: list[tuple[int, int, str]] = []

    for qualname, task in sorted(targets.items()):
        node = index.nodes.get(qualname)
        if node is None:
            if strict:
                raise KeyError(f"target function {qualname!r} not found")
            continue
        replacements.append(_replace_function_body(lines, node, task))

    for start, end, replacement in sorted(replacements, key=lambda x: x[0], reverse=True):
        if start <= end:
            lines[start - 1 : end] = [replacement]
        else:
            lines.insert(start - 1, replacement)

    return "".join(lines)


def parse_labs(spec: str) -> set[str]:
    if spec.strip().lower() == "all":
        return {target.lab for target in TARGETS}

    labs = {item.strip() for item in spec.split(",") if item.strip()}
    known = {target.lab for target in TARGETS}
    unknown = sorted(lab for lab in labs if lab not in known)
    if unknown:
        raise ValueError(f"unknown labs in --labs: {', '.join(unknown)}")
    return labs


def selected_targets(labs: Iterable[str]) -> dict[str, dict[str, str]]:
    selected = set(labs)
    by_file: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        if target.lab not in selected:
            continue
        by_file.setdefault(target.rel_path, {})[target.qualname] = target.task
    return by_file


def build_scaffold(
    input_dir: Path,
    output_dir: Path,
    *,
    labs: set[str],
    strict: bool,
) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(input_dir, output_dir)

    targets_by_file = selected_targets(labs)

    for path in output_dir.rglob("*.py"):
        rel_path = path.relative_to(output_dir).as_posix()
        text = path.read_text(encoding="utf-8")
        text = strip_solution_blocks(text)
        text = strip_target_functions(text, targets_by_file.get(rel_path, {}), strict=strict)
        path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--labs",
        type=str,
        default="all",
        help="Comma-separated lab ids to strip (default: all)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Fail if a configured target function cannot be found",
    )
    parser.add_argument(
        "--list-labs",
        action="store_true",
        help="Print available lab ids and exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    labs_available = sorted({target.lab for target in TARGETS})
    if args.list_labs:
        for lab in labs_available:
            print(lab)
        return

    if args.input is None or args.output is None:
        raise SystemExit("--input and --output are required unless --list-labs is used")

    labs = parse_labs(args.labs)
    build_scaffold(args.input, args.output, labs=labs, strict=args.strict)


if __name__ == "__main__":
    main()
