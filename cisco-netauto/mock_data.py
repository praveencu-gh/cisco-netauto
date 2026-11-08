"""
Mock Network Infrastructure Data
Simulates Cisco IOS XE BGP neighbors and interfaces across VRFs: VRF-A, VRF-B, and VRF-C.
Provides both structured Python models and raw Cisco CLI command outputs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Interface:
    name: str
    ip_address: str
    admin_status: str       # "up" or "administratively down"
    protocol_status: str    # "up" or "down"
    description: str
    vrf: str

    @property
    def is_healthy(self) -> bool:
        return self.admin_status.lower() == "up" and self.protocol_status.lower() == "up"


@dataclass
class BGPNeighbor:
    neighbor_ip: str
    remote_as: int
    vrf: str
    state: str              # "Established", "Active", "Idle", "Connect"
    uptime_down: str
    prefixes_received: int
    peer_interface: str
    description: str = ""

    @property
    def is_established(self) -> bool:
        return self.state.strip().lower() == "established"


@dataclass
class VRFData:
    name: str
    rd: str
    description: str
    interfaces: List[Interface] = field(default_factory=list)
    bgp_neighbors: List[BGPNeighbor] = field(default_factory=list)


def get_mock_network_topology() -> Dict[str, VRFData]:
    """Returns structured VRF data containing interfaces and BGP neighbors for VRF-A, VRF-B, and VRF-C."""
    return {
        "VRF-A": VRFData(
            name="VRF-A",
            rd="65000:100",
            description="Enterprise Data Services - Customer A",
            interfaces=[
                Interface(
                    name="GigabitEthernet0/1",
                    ip_address="10.1.1.1/30",
                    admin_status="up",
                    protocol_status="up",
                    description="PE-CE Link to Customer_A Primary",
                    vrf="VRF-A",
                ),
                Interface(
                    name="GigabitEthernet0/2",
                    ip_address="10.1.1.5/30",
                    admin_status="up",
                    protocol_status="up",
                    description="PE-CE Link to Customer_A Secondary",
                    vrf="VRF-A",
                ),
                Interface(
                    name="Loopback10",
                    ip_address="10.10.10.10/32",
                    admin_status="up",
                    protocol_status="up",
                    description="VRF-A Management Loopback",
                    vrf="VRF-A",
                ),
            ],
            bgp_neighbors=[
                BGPNeighbor(
                    neighbor_ip="10.1.1.2",
                    remote_as=65001,
                    vrf="VRF-A",
                    state="Established",
                    uptime_down="04:22:10",
                    prefixes_received=15,
                    peer_interface="GigabitEthernet0/1",
                    description="CustA-HQ-Primary",
                ),
                BGPNeighbor(
                    neighbor_ip="10.1.1.6",
                    remote_as=65001,
                    vrf="VRF-A",
                    state="Active",  # Neighbor failed / TCP SYN failing
                    uptime_down="00:02:15",
                    prefixes_received=0,
                    peer_interface="GigabitEthernet0/2",
                    description="CustA-HQ-Secondary (Degraded)",
                ),
            ],
        ),
        "VRF-B": VRFData(
            name="VRF-B",
            rd="65000:200",
            description="Voice & Multimedia Services - Customer B",
            interfaces=[
                Interface(
                    name="GigabitEthernet0/3",
                    ip_address="10.2.1.1/30",
                    admin_status="up",
                    protocol_status="up",
                    description="PE-CE Link to Customer_B Core",
                    vrf="VRF-B",
                ),
                Interface(
                    name="GigabitEthernet0/4",
                    ip_address="10.2.1.5/30",
                    admin_status="down",
                    protocol_status="down",
                    description="PE-CE Link to Customer_B Branch (Physical Outage)",
                    vrf="VRF-B",
                ),
                Interface(
                    name="Loopback20",
                    ip_address="10.20.20.20/32",
                    admin_status="up",
                    protocol_status="up",
                    description="VRF-B Router-ID Loopback",
                    vrf="VRF-B",
                ),
            ],
            bgp_neighbors=[
                BGPNeighbor(
                    neighbor_ip="10.2.1.2",
                    remote_as=65002,
                    vrf="VRF-B",
                    state="Established",
                    uptime_down="12d08h",
                    prefixes_received=42,
                    peer_interface="GigabitEthernet0/3",
                    description="CustB-Voice-Core",
                ),
                BGPNeighbor(
                    neighbor_ip="10.2.1.6",
                    remote_as=65002,
                    vrf="VRF-B",
                    state="Idle",  # Idle because physical interface is down
                    uptime_down="never",
                    prefixes_received=0,
                    peer_interface="GigabitEthernet0/4",
                    description="CustB-Branch-Office (Down)",
                ),
            ],
        ),
        "VRF-C": VRFData(
            name="VRF-C",
            rd="65000:300",
            description="Public Cloud Interconnect - Partner C",
            interfaces=[
                Interface(
                    name="GigabitEthernet0/5",
                    ip_address="10.3.1.1/30",
                    admin_status="up",
                    protocol_status="up",
                    description="Direct Connect Gateway Primary",
                    vrf="VRF-C",
                ),
                Interface(
                    name="GigabitEthernet0/6",
                    ip_address="10.3.1.5/30",
                    admin_status="up",
                    protocol_status="down",
                    description="Direct Connect Gateway Backup (Line Flapping)",
                    vrf="VRF-C",
                ),
                Interface(
                    name="Loopback30",
                    ip_address="10.30.30.30/32",
                    admin_status="up",
                    protocol_status="up",
                    description="VRF-C Cloud Interconnect Loopback",
                    vrf="VRF-C",
                ),
            ],
            bgp_neighbors=[
                BGPNeighbor(
                    neighbor_ip="10.3.1.2",
                    remote_as=65003,
                    vrf="VRF-C",
                    state="Established",
                    uptime_down="1d18h",
                    prefixes_received=8,
                    peer_interface="GigabitEthernet0/5",
                    description="AWS-DirectConnect-Primary",
                ),
                BGPNeighbor(
                    neighbor_ip="10.3.1.6",
                    remote_as=65003,
                    vrf="VRF-C",
                    state="Connect",  # Stuck in Connect state
                    uptime_down="00:00:45",
                    prefixes_received=0,
                    peer_interface="GigabitEthernet0/6",
                    description="AWS-DirectConnect-Secondary (Down)",
                ),
            ],
        ),
    }


def get_mock_cisco_cli_output() -> str:
    """Returns raw Cisco IOS XE CLI text output for 'show ip bgp vpnv4 all summary' and 'show ip interface brief'."""
    return """
Router# show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol VRF
GigabitEthernet0/1     10.1.1.1        YES NVRAM  up                    up       VRF-A
GigabitEthernet0/2     10.1.1.5        YES NVRAM  up                    up       VRF-A
Loopback10             10.10.10.10     YES NVRAM  up                    up       VRF-A
GigabitEthernet0/3     10.2.1.1        YES NVRAM  up                    up       VRF-B
GigabitEthernet0/4     10.2.1.5        YES NVRAM  down                  down     VRF-B
Loopback20             10.20.20.20     YES NVRAM  up                    up       VRF-B
GigabitEthernet0/5     10.3.1.1        YES NVRAM  up                    up       VRF-C
GigabitEthernet0/6     10.3.1.5        YES NVRAM  up                    down     VRF-C
Loopback30             10.30.30.30     YES NVRAM  up                    up       VRF-C

Router# show ip bgp vpnv4 all summary
BGP router identifier 10.0.0.1, local AS number 65000
BGP table version is 128, main routing table version 128

For address family: VPNv4 Unicast
VRF VRF-A;
Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.1.1.2        4        65001    2410    2415      128    0    0 04:22:10           15
10.1.1.6        4        65001      12      24        0    0    0 00:02:15 Active

VRF VRF-B;
Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.2.1.2        4        65002   18420   18430      128    0    0 12d08h             42
10.2.1.6        4        65002       0       0        0    0    0 never    Idle

VRF VRF-C;
Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.3.1.2        4        65003    4200    4210      128    0    0 1d18h               8
10.3.1.6        4        65003       5       8        0    0    0 00:00:45 Connect
"""
