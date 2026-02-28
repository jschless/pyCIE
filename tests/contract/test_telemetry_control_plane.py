"""Contract tests for control-plane telemetry events."""

from __future__ import annotations

from pycie.core.node import Device
from pycie.protocols.bgp import BGPOpen, BGPPeer, BGPProcess, BGPUpdate
from pycie.protocols.isis import ISISLSP, ISISNeighbor, ISISProcess
from pycie.protocols.ospf import OSPFHello, OSPFProcess, RouterLSA
from pycie.sim.network import Interface, NetworkSimulator, Topology
from pycie.telemetry.events import EventType
from pycie.telemetry.trace import MemoryTraceSink


def _build_device(node_id: str) -> tuple[Device, MemoryTraceSink]:
    sink = MemoryTraceSink()
    topo = Topology()
    topo.add_node(node_id)
    topo.add_interface(Interface(node_id, "eth0", "02:00:00:00:00:01"))
    sim = NetworkSimulator(topology=topo, trace_sink=sink)
    dev = Device(node_id, sim)
    dev.add_interface(topo.get_interface((node_id, "eth0")))
    return dev, sink


def test_bgp_emits_session_update_best_path_and_export_events() -> None:
    dev, sink = _build_device("r1")
    process = BGPProcess(local_as=65000, router_id="1.1.1.1")
    process.peers["peer1"] = BGPPeer(peer_id="peer1", peer_as=65100, is_ibgp=False)
    dev.register_protocol("bgp", process)

    process.establish_session("peer1")
    process.process_open("peer1", BGPOpen(asn=65100, router_id="2.2.2.2", hold_time_s=90))
    process.process_update(
        "peer1",
        BGPUpdate(prefix="10.10.0.0/24", next_hop="192.0.2.1", as_path=(65200,), local_pref=200),
    )
    exports = process.export_updates_for_peer("peer1")

    event_types = [event.event_type for event in sink.events]
    assert EventType.BGP_SESSION_CHANGE in event_types
    assert EventType.BGP_OPEN_RX in event_types
    assert EventType.BGP_UPDATE_RX in event_types
    assert EventType.BGP_BEST_PATH in event_types
    assert EventType.BGP_UPDATE_EXPORT in event_types
    assert len(exports) == 1

    best_path = next(event for event in sink.events if event.event_type == EventType.BGP_BEST_PATH)
    assert best_path.details["prefix"] == "10.10.0.0/24"
    assert best_path.details["selected_next_hop"] == "192.0.2.1"


def test_ospf_emits_hello_neighbor_lsa_and_spf_events() -> None:
    dev, sink = _build_device("r1")
    process = OSPFProcess(router_id="1.1.1.1", area_id=0)
    dev.register_protocol("ospf", process)

    process.on_start()
    process.process_hello(
        "eth0",
        OSPFHello(
            router_id="2.2.2.2",
            area_id=0,
            hello_interval_ms=10_000,
            dead_interval_ms=40_000,
            neighbors=("1.1.1.1",),
        ),
    )
    process.install_lsa(
        RouterLSA(
            advertising_router="2.2.2.2",
            lsa_id="2.2.2.2",
            sequence=1,
            links=(("1.1.1.1", 10),),
        )
    )
    process.run_spf()

    event_types = [event.event_type for event in sink.events]
    assert EventType.OSPF_HELLO_RX in event_types
    assert EventType.OSPF_NEIGHBOR_CHANGE in event_types
    assert EventType.OSPF_LSA_INSTALL in event_types
    assert EventType.OSPF_SPF_RUN in event_types

    neighbor_change = next(
        event for event in sink.events if event.event_type == EventType.OSPF_NEIGHBOR_CHANGE
    )
    assert neighbor_change.details["neighbor_id"] == "2.2.2.2"
    assert neighbor_change.details["new_state"] == "FULL"


def test_isis_emits_lsp_install_and_spf_events() -> None:
    dev, sink = _build_device("r1")
    process = ISISProcess(system_id="0000.0000.0001", level1_enabled=True, level2_enabled=False)
    dev.register_protocol("isis", process)

    process.set_neighbor(ISISNeighbor(system_id="0000.0000.0002", metric=10, levels=(1,)))
    process.on_start()
    process.install_lsp(
        ISISLSP(
            system_id="0000.0000.0002",
            level=1,
            sequence=1,
            links=(("0000.0000.0001", 10),),
        )
    )
    process.run_spf(1)

    event_types = [event.event_type for event in sink.events]
    assert EventType.ISIS_LSP_INSTALL in event_types
    assert EventType.ISIS_SPF_RUN in event_types

    spf_event = next(event for event in sink.events if event.event_type == EventType.ISIS_SPF_RUN)
    assert spf_event.details["level"] == 1
    assert spf_event.details["reachable_nodes"] >= 1
