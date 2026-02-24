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
    # lab06a
    Target("lab06a", "model/packet.py", "PacketStack.validate_stack_order", "Implement packet header-order validation"),
    Target("lab06a", "model/packet.py", "PacketStack.compute_payload_length", "Implement payload length helper"),
    Target("lab06a", "protocols/packet_construction.py", "PacketConstructionProcess.build_packet", "Implement packet construction with stack validation"),
    Target("lab06a", "protocols/packet_construction.py", "PacketConstructionProcess.build_ipv4_udp", "Implement IPv4/UDP packet builder"),
    Target("lab06a", "protocols/packet_construction.py", "PacketConstructionProcess.build_ipv4_tcp", "Implement IPv4/TCP packet builder"),
    Target("lab06a", "protocols/packet_construction.py", "PacketConstructionProcess.insert_vlan_tag", "Implement deterministic VLAN tag insertion"),
    Target("lab06a", "protocols/packet_construction.py", "PacketConstructionProcess.normalize_transport_lengths", "Implement transport-length normalization"),
    Target("lab06a", "protocols/packet_construction.py", "PacketConstructionProcess.validate_packet", "Expose packet validation helper"),
    # lab06b
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TCPConnection.send_syn", "Implement TCP SYN transition from CLOSED"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TCPConnection.send_fin", "Implement TCP FIN transition from ESTABLISHED"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TCPConnection.receive", "Implement deterministic TCP receive transitions"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TransportFundamentalsProcess.open_session", "Implement TCP session open helper"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TransportFundamentalsProcess.close_session", "Implement TCP session close helper"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TransportFundamentalsProcess.receive_segment", "Implement inbound segment dispatch"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TransportFundamentalsProcess.extract_flow_tuple", "Implement transport 5-tuple extraction"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TransportFundamentalsProcess.compute_udp_checksum", "Implement deterministic UDP checksum helper"),
    Target("lab06b", "protocols/tcp_udp_fundamentals.py", "TransportFundamentalsProcess.build_udp_header", "Implement UDP header construction helper"),
    # lab06c
    Target("lab06c", "protocols/ip_mac_basics.py", "IPMacBasicsProcess.add_interface", "Implement interface prefix and MAC store"),
    Target("lab06c", "protocols/ip_mac_basics.py", "IPMacBasicsProcess.add_static_route", "Implement static route installation and replacement"),
    Target("lab06c", "protocols/ip_mac_basics.py", "IPMacBasicsProcess.learn_arp", "Implement ARP adjacency learning"),
    Target("lab06c", "protocols/ip_mac_basics.py", "IPMacBasicsProcess.explain_lookup", "Implement explainable longest-prefix lookup"),
    Target("lab06c", "protocols/ip_mac_basics.py", "IPMacBasicsProcess.forward_decision", "Implement forwarding decision with MAC resolution dependency"),
    Target("lab06c", "protocols/ip_mac_basics.py", "IPMacBasicsProcess.prefix_details", "Implement subnet detail helper"),
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
    # lab17
    Target("lab17", "protocols/bgp_fsm_transport.py", "BGPTransportSession.start", "Implement BGP FSM start transition"),
    Target("lab17", "protocols/bgp_fsm_transport.py", "BGPTransportSession.on_tcp_up", "Implement TCP-up OPEN emission"),
    Target("lab17", "protocols/bgp_fsm_transport.py", "BGPTransportSession.receive_open", "Implement OPEN validation and hold-time negotiation"),
    Target("lab17", "protocols/bgp_fsm_transport.py", "BGPTransportSession.receive_keepalive", "Implement KEEPALIVE handling and established transition"),
    Target("lab17", "protocols/bgp_fsm_transport.py", "BGPTransportSession.receive_update", "Implement UPDATE validation and Adj-RIB-In state"),
    Target("lab17", "protocols/bgp_fsm_transport.py", "BGPTransportSession.tick", "Implement timer-driven keepalive and hold checks"),
    # lab18
    Target("lab18", "protocols/ospf_multi_area.py", "OSPFMultiAreaProcess.install_area_lsa", "Implement area LSA install with sequence checks"),
    Target("lab18", "protocols/ospf_multi_area.py", "OSPFMultiAreaProcess.install_summary_lsa", "Implement summary LSA install with sequence checks"),
    Target("lab18", "protocols/ospf_multi_area.py", "OSPFMultiAreaProcess.compute_intra_area_routes", "Implement area-local route computation"),
    Target("lab18", "protocols/ospf_multi_area.py", "OSPFMultiAreaProcess.originate_summaries_for_target", "Implement ABR summary origination"),
    Target("lab18", "protocols/ospf_multi_area.py", "OSPFMultiAreaProcess.compute_routing_table", "Implement intra/inter-area route preference"),
    # lab19
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.initiate", "Implement IKE proposal acceptance logic"),
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.respond", "Implement responder negotiation behavior"),
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.establish_child_sa", "Implement child SA creation and selector validation"),
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.rekey_child_sa", "Implement child SA rekey lifecycle"),
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.age_rekey_overlap", "Implement overlap aging behavior"),
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.active_child_sas", "Implement active child SA view"),
    Target("lab19", "protocols/ikev2_for_ipsec.py", "IKEv2Session.delete_session", "Implement session delete and SA teardown"),
    # lab20
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.install_route", "Implement IPv6 route installation"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.lookup_route", "Implement IPv6 longest-prefix route lookup"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.learn_neighbor", "Implement ND neighbor cache updates"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.age_neighbors", "Implement ND neighbor aging"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.queue_pending", "Implement pending queue for unresolved next hops"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.resolve_neighbor", "Implement queued packet drain on ND resolution"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.forward", "Implement IPv6 forwarding and drop reasons"),
    Target("lab20", "protocols/ipv6_nd_forwarding.py", "IPv6NDForwarder.should_solicit", "Implement ND solicitation trigger helper"),
    # lab21
    Target("lab21", "protocols/nat44_pipeline.py", "NAT44Pipeline.install_static_rule", "Implement NAT static rule install"),
    Target("lab21", "protocols/nat44_pipeline.py", "NAT44Pipeline.translate_outbound", "Implement NAT outbound SNAT/PAT translation"),
    Target("lab21", "protocols/nat44_pipeline.py", "NAT44Pipeline.translate_inbound", "Implement NAT inbound DNAT/session return translation"),
    Target("lab21", "protocols/nat44_pipeline.py", "NAT44Pipeline.age_sessions", "Implement NAT session aging"),
    # lab22
    Target("lab22", "protocols/icmp_control_plane_basics.py", "ICMPControlPlaneProcess.build_echo_request", "Implement ICMP echo request builder"),
    Target("lab22", "protocols/icmp_control_plane_basics.py", "ICMPControlPlaneProcess.build_echo_reply", "Implement ICMP echo reply generation"),
    Target("lab22", "protocols/icmp_control_plane_basics.py", "ICMPControlPlaneProcess.build_time_exceeded", "Implement ICMP time-exceeded generation"),
    Target("lab22", "protocols/icmp_control_plane_basics.py", "ICMPControlPlaneProcess.build_destination_unreachable", "Implement ICMP destination-unreachable generation"),
    Target("lab22", "protocols/icmp_control_plane_basics.py", "ICMPControlPlaneProcess.traceroute_probe", "Implement traceroute probe builder"),
    Target("lab22", "protocols/icmp_control_plane_basics.py", "ICMPControlPlaneProcess.traceroute_hop_result", "Implement traceroute hop result behavior"),
    # lab23
    Target("lab23", "protocols/isis.py", "ISISProcess.on_start", "Originate initial IS-IS LSPs"),
    Target("lab23", "protocols/isis.py", "ISISProcess.on_frame", "Process inbound IS-IS LSP payloads"),
    Target("lab23", "protocols/isis.py", "ISISProcess.originate_lsp", "Build local LSP with deterministic link ordering"),
    Target("lab23", "protocols/isis.py", "ISISProcess.install_lsp", "Implement IS-IS LSP sequence comparison"),
    Target("lab23", "protocols/isis.py", "ISISProcess.run_spf", "Implement per-level IS-IS SPF"),
    Target("lab23", "protocols/isis.py", "ISISProcess.compute_routing_table", "Build level-aware routing table output"),
    # lab24
    Target("lab24", "protocols/ipv4_fragmentation_reassembly.py", "IPv4FragmentationReassemblyProcess.fragment", "Implement IPv4 packet fragmentation by MTU"),
    Target("lab24", "protocols/ipv4_fragmentation_reassembly.py", "IPv4FragmentationReassemblyProcess.reassemble", "Implement deterministic IPv4 reassembly"),
    Target("lab24", "protocols/ipv4_fragmentation_reassembly.py", "IPv4FragmentationReassemblyProcess.ingest_fragment", "Implement fragment-buffer ingest and completion checks"),
    Target("lab24", "protocols/ipv4_fragmentation_reassembly.py", "IPv4FragmentationReassemblyProcess.age_reassembly_buffers", "Implement reassembly buffer timeout aging"),
    # lab25
    Target("lab25", "protocols/pmtud_mss.py", "PMTUDMSSProcess.evaluate_forward", "Implement PMTUD fragmentation-needed evaluation"),
    Target("lab25", "protocols/pmtud_mss.py", "PMTUDMSSProcess.learn_path_mtu", "Implement PMTU cache update helper"),
    Target("lab25", "protocols/pmtud_mss.py", "PMTUDMSSProcess.effective_path_mtu", "Implement PMTU cache lookup helper"),
    Target("lab25", "protocols/pmtud_mss.py", "PMTUDMSSProcess.clamp_syn_mss", "Implement SYN MSS clamp helper"),
    Target("lab25", "protocols/pmtud_mss.py", "PMTUDMSSProcess.age_path_mtu_cache", "Implement PMTU cache aging"),
    # lab26
    Target("lab26", "protocols/ipv6_slaac.py", "IPv6SLAACProcess.configure_router", "Implement per-interface RA configuration"),
    Target("lab26", "protocols/ipv6_slaac.py", "IPv6SLAACProcess.trigger_rs", "Implement RS trigger scheduling"),
    Target("lab26", "protocols/ipv6_slaac.py", "IPv6SLAACProcess.emit_due_ra", "Implement deterministic delayed RA emission"),
    Target("lab26", "protocols/ipv6_slaac.py", "IPv6SLAACProcess.autoconfigure_from_ra", "Implement SLAAC address derivation from RA"),
    Target("lab26", "protocols/ipv6_slaac.py", "IPv6SLAACProcess.complete_dad", "Implement DAD completion/conflict handling"),
    # lab27
    Target("lab27", "protocols/qos_marking_queueing.py", "QoSMarkingQueueingProcess.classify_dscp", "Implement DSCP to queue classification"),
    Target("lab27", "protocols/qos_marking_queueing.py", "QoSMarkingQueueingProcess.remark", "Implement packet DSCP remark helper"),
    Target("lab27", "protocols/qos_marking_queueing.py", "QoSMarkingQueueingProcess.enqueue", "Implement queue admission and drop behavior"),
    Target("lab27", "protocols/qos_marking_queueing.py", "QoSMarkingQueueingProcess.dequeue", "Implement weighted queue scheduling"),
    Target("lab27", "protocols/qos_marking_queueing.py", "QoSMarkingQueueingProcess.queue_depth", "Implement queue depth helper"),
    Target("lab27", "protocols/qos_marking_queueing.py", "QoSMarkingQueueingProcess.snapshot_depths", "Implement queue snapshot helper"),
    # lab28
    Target("lab28", "protocols/dhcpv6.py", "DHCPv6Server.handle_solicit", "Implement deterministic DHCPv6 advertise allocation"),
    Target("lab28", "protocols/dhcpv6.py", "DHCPv6Server.handle_request", "Implement DHCPv6 request/reply handling"),
    Target("lab28", "protocols/dhcpv6.py", "DHCPv6Server.renew", "Implement DHCPv6 lease renewal"),
    Target("lab28", "protocols/dhcpv6.py", "DHCPv6Server.release", "Implement DHCPv6 lease release"),
    Target("lab28", "protocols/dhcpv6.py", "DHCPv6Server.age_leases", "Implement DHCPv6 lease aging"),
    Target("lab28", "protocols/dhcpv6.py", "DHCPv6Server.relay", "Implement DHCPv6 relay helper behavior"),
    # lab29
    Target("lab29", "protocols/lacp.py", "LACPProcess.add_port", "Implement LACP local port registration"),
    Target("lab29", "protocols/lacp.py", "LACPProcess.receive_lacpdu", "Implement LACP partner state processing"),
    Target("lab29", "protocols/lacp.py", "LACPProcess.active_members", "Implement active bundle membership selection"),
    Target("lab29", "protocols/lacp.py", "LACPProcess.select_egress", "Implement deterministic bundle egress selection"),
    Target("lab29", "protocols/lacp.py", "LACPProcess.age_sessions", "Implement LACP session timeout aging"),
    # lab30
    Target("lab30", "protocols/route_selection.py", "RouteSelectionEngine.install_route", "Implement route candidate install/replace semantics"),
    Target("lab30", "protocols/route_selection.py", "RouteSelectionEngine.withdraw_route", "Implement route candidate withdrawal"),
    Target("lab30", "protocols/route_selection.py", "RouteSelectionEngine.best_route", "Implement LPM and tie-break route selection"),
    Target("lab30", "protocols/route_selection.py", "RouteSelectionEngine.explain", "Implement route-decision explain trace"),
    Target("lab30", "protocols/route_selection.py", "RouteSelectionEngine.redistribute", "Implement redistribution with loop-prevention tags"),
    # lab31
    Target("lab31", "protocols/acl.py", "ACLRule.matches", "Implement ACL packet-to-rule matching"),
    Target("lab31", "protocols/acl.py", "ACL.add_rule", "Implement ACL sequence insertion/replacement"),
    Target("lab31", "protocols/acl.py", "ACL.remove_rule", "Implement ACL rule removal"),
    Target("lab31", "protocols/acl.py", "ACL.evaluate", "Implement first-match ACL evaluation with implicit deny"),
    # lab32
    Target("lab32", "protocols/aaa.py", "AAAService.login", "Implement AAA login flow with backend/local fallback"),
    Target("lab32", "protocols/aaa.py", "AAAService.authorize", "Implement role-based command authorization"),
    Target("lab32", "protocols/aaa.py", "AAAService.logout", "Implement AAA session teardown"),
    Target("lab32", "protocols/aaa.py", "AAAService._authenticate_backend", "Implement backend AAA decision handling"),
    # lab33
    Target("lab33", "protocols/dhcp.py", "DHCPServer.handle_discover", "Implement deterministic DHCP offer allocation"),
    Target("lab33", "protocols/dhcp.py", "DHCPServer.handle_request", "Implement DHCP request ACK/NAK logic"),
    Target("lab33", "protocols/dhcp.py", "DHCPServer.renew", "Implement DHCP lease renewal"),
    Target("lab33", "protocols/dhcp.py", "DHCPServer.release", "Implement DHCP lease release"),
    Target("lab33", "protocols/dhcp.py", "DHCPServer.age_leases", "Implement DHCP lease aging"),
    Target("lab33", "protocols/dhcp.py", "DHCPServer.relay", "Implement DHCP relay helper behavior"),
    # lab34
    Target("lab34", "protocols/multicast.py", "MulticastProcess.join_group", "Implement multicast group join behavior"),
    Target("lab34", "protocols/multicast.py", "MulticastProcess.leave_group", "Implement multicast group leave behavior"),
    Target("lab34", "protocols/multicast.py", "MulticastProcess.install_rpf_route", "Implement RPF route installation"),
    Target("lab34", "protocols/multicast.py", "MulticastProcess.expected_rpf_interface", "Implement longest-prefix RPF lookup"),
    Target("lab34", "protocols/multicast.py", "MulticastProcess.compute_egress_interfaces", "Implement multicast egress interface selection"),
    Target("lab34", "protocols/multicast.py", "MulticastProcess.process_data", "Implement (S,G) forwarding-state update"),
    # lab35
    Target("lab35", "protocols/vxlan.py", "VXLANBridge.learn_local", "Implement local VXLAN MAC learning"),
    Target("lab35", "protocols/vxlan.py", "VXLANBridge.learn_remote", "Implement remote VXLAN MAC learning"),
    Target("lab35", "protocols/vxlan.py", "VXLANBridge.lookup_egress", "Implement VNI-aware VXLAN forwarding lookup"),
    Target("lab35", "protocols/vxlan.py", "VXLANBridge.encapsulate", "Implement VXLAN encapsulation"),
    Target("lab35", "protocols/vxlan.py", "VXLANBridge.decapsulate", "Implement VXLAN decapsulation"),
    # lab36
    Target("lab36", "protocols/evpn.py", "EVPNControlPlane.import_route", "Implement EVPN route import policy"),
    Target("lab36", "protocols/evpn.py", "EVPNControlPlane.withdraw_route", "Implement EVPN route withdrawal"),
    Target("lab36", "protocols/evpn.py", "EVPNControlPlane.recompute", "Implement EVPN best-path recomputation"),
    Target("lab36", "protocols/evpn.py", "EVPNControlPlane.resolve_mac", "Implement EVPN MAC next-hop resolution"),
    Target("lab36", "protocols/evpn.py", "EVPNControlPlane.resolve_prefix", "Implement EVPN IP-prefix next-hop resolution"),
    # lab37
    Target("lab37", "protocols/macsec.py", "MACsecProcess.configure_interface", "Implement per-interface MACsec policy installation"),
    Target("lab37", "protocols/macsec.py", "MACsecProcess.install_secure_association", "Implement MACsec secure association installation"),
    Target("lab37", "protocols/macsec.py", "MACsecProcess.validate_ingress", "Implement ingress MACsec policy and replay checks"),
    Target("lab37", "protocols/macsec.py", "MACsecProcess.protect_egress", "Implement egress MACsec protection behavior"),
    # lab38
    Target("lab38", "protocols/control_plane_db.py", "OSPFLSDB.install", "Implement OSPF LSDB install with sequence checks"),
    Target("lab38", "protocols/control_plane_db.py", "OSPFLSDB.withdraw", "Implement OSPF LSDB withdrawal"),
    Target("lab38", "protocols/control_plane_db.py", "BGPDatabase.install_path", "Implement BGP Adj-RIB-In installation"),
    Target("lab38", "protocols/control_plane_db.py", "BGPDatabase.withdraw_path", "Implement BGP Adj-RIB-In withdrawal"),
    Target("lab38", "protocols/control_plane_db.py", "BGPDatabase.best_path", "Implement BGP best-path selection"),
    Target("lab38", "protocols/control_plane_db.py", "BGPDatabase.recompute_loc_rib", "Implement BGP Loc-RIB recomputation"),
    Target("lab38", "protocols/control_plane_db.py", "LDPDatabase.install_binding", "Implement LDP binding installation"),
    Target("lab38", "protocols/control_plane_db.py", "LDPDatabase.withdraw_binding", "Implement LDP binding withdrawal"),
    Target("lab38", "protocols/control_plane_db.py", "LDPDatabase.best_binding", "Implement best LDP binding selection"),
    # lab39
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.install_route", "Implement route install in RIB->FIB pipeline"),
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.withdraw_route", "Implement route withdrawal in RIB->FIB pipeline"),
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.best_route_for_prefix", "Implement per-prefix best-route selection"),
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.resolve_next_hop", "Implement recursive next-hop resolution"),
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.recompute", "Implement RIB-to-FIB recompute pipeline"),
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.lookup", "Implement FIB longest-prefix lookup"),
    Target("lab39", "protocols/rib_fib_pipeline.py", "RIBFIBPipeline.explain", "Implement route-programming explain output"),
    # lab40
    Target("lab40", "protocols/fhrp.py", "FHRPProcess.register_router", "Implement FHRP member registration"),
    Target("lab40", "protocols/fhrp.py", "FHRPProcess.elect_master", "Implement FHRP master election"),
    Target("lab40", "protocols/fhrp.py", "FHRPProcess.update_router", "Implement FHRP failover/preemption updates"),
    Target("lab40", "protocols/fhrp.py", "FHRPProcess.current_virtual_mac", "Implement deterministic virtual MAC helper"),
    Target("lab40", "protocols/fhrp.py", "FHRPProcess.failover_elapsed_ms", "Implement failover timing helper"),
    # lab41
    Target("lab41", "protocols/management_plane_observability.py", "ManagementPlaneObservabilityProcess.learn_lldp", "Implement LLDP neighbor learning"),
    Target("lab41", "protocols/management_plane_observability.py", "ManagementPlaneObservabilityProcess.age_lldp", "Implement LLDP neighbor aging"),
    Target("lab41", "protocols/management_plane_observability.py", "ManagementPlaneObservabilityProcess.log_syslog", "Implement syslog severity filtering"),
    Target("lab41", "protocols/management_plane_observability.py", "ManagementPlaneObservabilityProcess.poll_snmp_oid", "Implement SNMP poll helper"),
    Target("lab41", "protocols/management_plane_observability.py", "ManagementPlaneObservabilityProcess.resolve_dns", "Implement DNS cache resolve helper"),
    Target("lab41", "protocols/management_plane_observability.py", "ManagementPlaneObservabilityProcess.check_service_readiness", "Implement service dependency checks"),
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
