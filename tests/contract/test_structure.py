"""Contract tests that should pass for the scaffold at all times."""

from __future__ import annotations

import inspect

from pycie.core.fib import FIB
from pycie.core.rib import RIB, Route
from pycie.protocols.bfd import BFDProcess
from pycie.protocols.bgp import BGPProcess
from pycie.protocols.ldp import LDPProcess
from pycie.protocols.ospf import OSPFProcess
from pycie.protocols.stp import STPProcess
from pycie.protocols.switching import LearningSwitch
from pycie.sim.network import Frame, Interface, NetworkSimulator, Topology


def test_protocol_public_methods_exist() -> None:
    expected = {
        LearningSwitch: [
            "on_frame",
            "learn_source_mac",
            "lookup_egress_interfaces",
            "age_mac_table",
            "should_flood",
        ],
        STPProcess: [
            "on_start",
            "on_frame",
            "build_bpdu",
            "process_bpdu",
            "recompute_port_states",
            "should_forward_data",
        ],
        OSPFProcess: [
            "send_hello",
            "process_hello",
            "originate_router_lsa",
            "install_lsa",
            "run_spf",
            "compute_routing_table",
        ],
        BGPProcess: [
            "establish_session",
            "process_open",
            "process_update",
            "best_path",
            "recompute_loc_rib",
            "export_updates_for_peer",
        ],
        LDPProcess: [
            "allocate_local_label",
            "advertise_bindings",
            "process_label_mapping",
            "build_lfib",
        ],
        BFDProcess: [
            "open_session",
            "receive_control",
            "transmit_control",
            "detect_time_ms",
            "check_timeouts",
        ],
    }

    for cls, methods in expected.items():
        for method in methods:
            assert hasattr(cls, method), f"{cls.__name__}.{method} is missing"
            assert inspect.isfunction(getattr(cls, method))


def test_rib_and_fib_baseline_behavior() -> None:
    rib = RIB()
    fib = FIB()

    rib.install_route(Route("10.0.0.0/24", "192.0.2.1", 110, 20, "ospf"))
    rib.install_route(Route("10.0.0.0/24", "192.0.2.2", 200, 10, "ibgp"))
    fib.recompute(rib)

    entry = fib.lookup("10.0.0.0/24")
    assert entry is not None
    assert entry.next_hop == "192.0.2.1"


def test_simulator_delivers_frame_over_link() -> None:
    topo = Topology()
    topo.add_node("r1")
    topo.add_node("r2")
    topo.add_interface(Interface("r1", "eth0", "02:00:00:00:00:01"))
    topo.add_interface(Interface("r2", "eth0", "02:00:00:00:00:02"))
    topo.connect(("r1", "eth0"), ("r2", "eth0"), latency_ms=5)

    sim = NetworkSimulator(topology=topo)
    received: list[tuple[str, str, Frame]] = []

    sim.register_receiver("r1", lambda *_: None)
    sim.register_receiver("r2", lambda node, if_name, frame: received.append((node, if_name, frame)))

    frame = Frame(src_mac="aa", dst_mac="bb", ethertype="0x0800", payload=b"hello")
    sim.send_frame("r1", "eth0", frame)
    ran = sim.run()

    assert ran == 1
    assert len(received) == 1
    assert received[0][0] == "r2"
    assert received[0][1] == "eth0"
    assert received[0][2].payload == b"hello"
