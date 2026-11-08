"""
Automated Test Suite for BGP & VRF Interface Monitoring
Tests detection of BGP states, interface failures, and health metrics across VRFs A, B, and C.
"""

import unittest
from mock_data import get_mock_network_topology, VRFData, BGPNeighbor, Interface
from bgp_monitor import BGPMonitor


class TestBGPMonitoring(unittest.TestCase):
    """Test suite validating BGP and Interface monitoring logic."""

    def setUp(self):
        """Set up test environment with mock topology."""
        self.topology = get_mock_network_topology()
        self.monitor = BGPMonitor(self.topology)

    def test_vrf_existence(self):
        """Verify all target VRFs (VRF-A, VRF-B, VRF-C) are present."""
        expected_vrfs = {"VRF-A", "VRF-B", "VRF-C"}
        actual_vrfs = set(self.topology.keys())
        self.assertEqual(expected_vrfs, actual_vrfs, "All three VRFs (A, B, C) must exist in topology")

    def test_healthy_bgp_neighbors(self):
        """Verify established BGP neighbors with prefixes are detected as OK."""
        findings = self.monitor.analyze_bgp_health()
        established_neighbors = [b for b in findings if b["severity"] == "OK"]

        # Should have 3 healthy neighbors (one in each VRF: 10.1.1.2, 10.2.1.2, 10.3.1.2)
        self.assertEqual(len(established_neighbors), 3)
        healthy_ips = {b["neighbor_ip"] for b in established_neighbors}
        self.assertIn("10.1.1.2", healthy_ips)
        self.assertIn("10.2.1.2", healthy_ips)
        self.assertIn("10.3.1.2", healthy_ips)

    def test_unhealthy_bgp_neighbors_detected(self):
        """Verify non-established BGP neighbors are flagged with CRITICAL severity."""
        findings = self.monitor.analyze_bgp_health()
        alerts = [b for b in findings if b["severity"] == "CRITICAL"]

        # 3 neighbors have degraded states: 10.1.1.6 (Active), 10.2.1.6 (Idle), 10.3.1.6 (Connect)
        self.assertEqual(len(alerts), 3)

        states_by_ip = {b["neighbor_ip"]: b["state"] for b in alerts}
        self.assertEqual(states_by_ip.get("10.1.1.6"), "Active")
        self.assertEqual(states_by_ip.get("10.2.1.6"), "Idle")
        self.assertEqual(states_by_ip.get("10.3.1.6"), "Connect")

    def test_interface_failures_detected(self):
        """Verify physical down and line-protocol down interfaces are identified."""
        findings = self.monitor.analyze_interface_health()

        # GigabitEthernet0/4 in VRF-B is down/down (CRITICAL)
        gi0_4 = next((i for i in findings if i["interface"] == "GigabitEthernet0/4"), None)
        self.assertIsNotNone(gi0_4)
        self.assertEqual(gi0_4["severity"], "CRITICAL")
        self.assertEqual(gi0_4["vrf"], "VRF-B")

        # GigabitEthernet0/6 in VRF-C is up/down (WARNING)
        gi0_6 = next((i for i in findings if i["interface"] == "GigabitEthernet0/6"), None)
        self.assertIsNotNone(gi0_6)
        self.assertEqual(gi0_6["severity"], "WARNING")
        self.assertEqual(gi0_6["vrf"], "VRF-C")

    def test_summary_metrics(self):
        """Verify summary metric counts accurately reflect total topology state."""
        metrics = self.monitor.get_summary_metrics()

        self.assertEqual(metrics["total_vrfs"], 3)
        self.assertEqual(metrics["total_neighbors"], 6)
        self.assertEqual(metrics["established_neighbors"], 3)
        self.assertEqual(metrics["unhealthy_neighbors"], 3)
        self.assertEqual(metrics["total_interfaces"], 9)
        self.assertEqual(metrics["healthy_interfaces"], 7)
        self.assertEqual(metrics["unhealthy_interfaces"], 2)

    def test_all_healthy_topology_scenario(self):
        """Test monitoring response when all neighbors and interfaces are healthy."""
        healthy_topology = {
            "VRF-A": VRFData(
                name="VRF-A",
                rd="65000:100",
                description="All Healthy VRF",
                interfaces=[
                    Interface("GigabitEthernet0/1", "10.1.1.1/30", "up", "up", "Healthy Link", "VRF-A")
                ],
                bgp_neighbors=[
                    BGPNeighbor("10.1.1.2", 65001, "VRF-A", "Established", "10d", 20, "GigabitEthernet0/1")
                ],
            )
        }
        monitor = BGPMonitor(healthy_topology)
        metrics = monitor.get_summary_metrics()

        self.assertEqual(metrics["unhealthy_neighbors"], 0)
        self.assertEqual(metrics["unhealthy_interfaces"], 0)
        self.assertEqual(metrics["established_neighbors"], 1)
        self.assertEqual(metrics["healthy_interfaces"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
