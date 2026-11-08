"""
BGP & Interface VRF Health Monitor
Monitors BGP neighbors and interfaces across VRFs A, B, and C.
Detects operational anomalies, displays Rich terminal dashboards, and provides incident diagnostics.
"""

import os
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv

# Try importing rich for dashboard visualization; fallback gracefully if unavailable
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from mock_data import get_mock_network_topology, get_mock_cisco_cli_output, VRFData, BGPNeighbor, Interface

# Load environment configuration (looks in current dir and parent dir for .env)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv()


class BGPMonitor:
    """Network Automation Monitoring Engine for Multi-VRF BGP and Interfaces."""

    def __init__(self, topology: Dict[str, VRFData] = None):
        self.topology = topology if topology is not None else get_mock_network_topology()
        self.console = Console() if HAS_RICH else None

    def analyze_bgp_health(self) -> List[Dict[str, Any]]:
        """Evaluates health of all BGP neighbors across all VRFs."""
        findings = []
        for vrf_name, vrf_data in self.topology.items():
            for neighbor in vrf_data.bgp_neighbors:
                state = neighbor.state.strip()
                status_entry = {
                    "vrf": vrf_name,
                    "neighbor_ip": neighbor.neighbor_ip,
                    "remote_as": neighbor.remote_as,
                    "state": state,
                    "uptime_down": neighbor.uptime_down,
                    "prefixes_received": neighbor.prefixes_received,
                    "peer_interface": neighbor.peer_interface,
                    "description": neighbor.description,
                }

                if state.lower() == "established":
                    if neighbor.prefixes_received == 0:
                        status_entry["severity"] = "WARNING"
                        status_entry["issue"] = "Established but receiving 0 prefixes (possible routing policy drop)"
                        status_entry["action"] = f"Check route-map / prefix-list for neighbor {neighbor.neighbor_ip}"
                    else:
                        status_entry["severity"] = "OK"
                        status_entry["issue"] = "Neighbor is healthy and exchanging routes"
                        status_entry["action"] = "None"
                else:
                    status_entry["severity"] = "CRITICAL"
                    if state.lower() == "active":
                        status_entry["issue"] = f"BGP session is ACTIVE (TCP SYN failed, peer unreachable or port 179 blocked)"
                        status_entry["action"] = f"Verify IP reachability: 'ping vrf {vrf_name} {neighbor.neighbor_ip}' and check ACLs"
                    elif state.lower() == "idle":
                        status_entry["issue"] = f"BGP session is IDLE (Underlying interface down or neighbor shutdown)"
                        status_entry["action"] = f"Inspect interface {neighbor.peer_interface} and verify 'no neighbor {neighbor.neighbor_ip} shutdown'"
                    elif state.lower() == "connect":
                        status_entry["issue"] = f"BGP session stuck in CONNECT (Retrying TCP handshake)"
                        status_entry["action"] = f"Check MTU mismatch or routing loops on {neighbor.peer_interface}"
                    else:
                        status_entry["issue"] = f"Abnormal state: {state}"
                        status_entry["action"] = f"Run 'show ip bgp vpnv4 vrf {vrf_name} neighbors {neighbor.neighbor_ip}'"

                findings.append(status_entry)
        return findings

    def analyze_interface_health(self) -> List[Dict[str, Any]]:
        """Evaluates health of all interfaces across all VRFs."""
        findings = []
        for vrf_name, vrf_data in self.topology.items():
            for iface in vrf_data.interfaces:
                entry = {
                    "vrf": vrf_name,
                    "interface": iface.name,
                    "ip_address": iface.ip_address,
                    "admin_status": iface.admin_status,
                    "protocol_status": iface.protocol_status,
                    "description": iface.description,
                }

                if iface.admin_status.lower() == "up" and iface.protocol_status.lower() == "up":
                    entry["severity"] = "OK"
                    entry["issue"] = "Interface operational"
                elif iface.admin_status.lower() == "down" and iface.protocol_status.lower() == "down":
                    entry["severity"] = "CRITICAL"
                    entry["issue"] = "Physical link or interface is down"
                elif iface.admin_status.lower() == "up" and iface.protocol_status.lower() == "down":
                    entry["severity"] = "WARNING"
                    entry["issue"] = "Line protocol down (Layer 2 framing / keepalive / carrier issue)"
                else:
                    entry["severity"] = "WARNING"
                    entry["issue"] = f"Admin {iface.admin_status} / Protocol {iface.protocol_status}"

                findings.append(entry)
        return findings

    def get_summary_metrics(self) -> Dict[str, int]:
        """Calculates aggregate health metrics."""
        bgp_results = self.analyze_bgp_health()
        iface_results = self.analyze_interface_health()

        total_neighbors = len(bgp_results)
        established_neighbors = sum(1 for b in bgp_results if b["severity"] == "OK")
        unhealthy_neighbors = total_neighbors - established_neighbors

        total_interfaces = len(iface_results)
        healthy_interfaces = sum(1 for i in iface_results if i["severity"] == "OK")
        unhealthy_interfaces = total_interfaces - healthy_interfaces

        return {
            "total_vrfs": len(self.topology),
            "total_neighbors": total_neighbors,
            "established_neighbors": established_neighbors,
            "unhealthy_neighbors": unhealthy_neighbors,
            "total_interfaces": total_interfaces,
            "healthy_interfaces": healthy_interfaces,
            "unhealthy_interfaces": unhealthy_interfaces,
        }

    def display_dashboard(self):
        """Renders an interactive Rich terminal monitoring dashboard."""
        if not HAS_RICH:
            self._display_plain_dashboard()
            return

        metrics = self.get_summary_metrics()
        bgp_findings = self.analyze_bgp_health()
        iface_findings = self.analyze_interface_health()

        # Header Panel
        self.console.print(
            Panel(
                Text(
                    f"🚀 CISCO VRF BGP & INTERFACE MONITORING DASHBOARD\n"
                    f"VRFs Monitored: {metrics['total_vrfs']} (VRF-A, VRF-B, VRF-C) | "
                    f"BGP: {metrics['established_neighbors']}/{metrics['total_neighbors']} Up | "
                    f"Interfaces: {metrics['healthy_interfaces']}/{metrics['total_interfaces']} Up",
                    justify="center",
                    style="bold cyan",
                ),
                border_style="bright_blue",
            )
        )

        # 1. BGP Neighbors Table
        bgp_table = Table(title="🌐 Multi-VRF BGP Neighbor Status", show_header=True, header_style="bold magenta")
        bgp_table.add_column("VRF", style="bold yellow")
        bgp_table.add_column("Neighbor IP", style="cyan")
        bgp_table.add_column("Remote AS", justify="right")
        bgp_table.add_column("State", justify="center")
        bgp_table.add_column("Uptime/Down", justify="center")
        bgp_table.add_column("Prefixes", justify="right")
        bgp_table.add_column("Interface", style="blue")
        bgp_table.add_column("Health", justify="center")

        for b in bgp_findings:
            if b["severity"] == "OK":
                health_text = "[bold green]HEALTHY[/bold green]"
                state_text = f"[green]{b['state']}[/green]"
            elif b["severity"] == "WARNING":
                health_text = "[bold yellow]WARNING[/bold yellow]"
                state_text = f"[yellow]{b['state']}[/yellow]"
            else:
                health_text = "[bold red]CRITICAL[/bold red]"
                state_text = f"[bold red]{b['state']}[/bold red]"

            bgp_table.add_row(
                b["vrf"],
                b["neighbor_ip"],
                str(b["remote_as"]),
                state_text,
                b["uptime_down"],
                str(b["prefixes_received"]),
                b["peer_interface"],
                health_text,
            )
        self.console.print(bgp_table)

        # 2. Interfaces Table
        iface_table = Table(title="🔌 VRF Interface Operational Status", show_header=True, header_style="bold magenta")
        iface_table.add_column("VRF", style="bold yellow")
        iface_table.add_column("Interface", style="cyan")
        iface_table.add_column("IP Address")
        iface_table.add_column("Admin Status", justify="center")
        iface_table.add_column("Line Protocol", justify="center")
        iface_table.add_column("Health", justify="center")
        iface_table.add_column("Description", style="dim")

        for i in iface_findings:
            if i["severity"] == "OK":
                health_text = "[bold green]UP[/bold green]"
                admin_col = "[green]up[/green]"
                proto_col = "[green]up[/green]"
            elif i["severity"] == "WARNING":
                health_text = "[bold yellow]DEGRADED[/bold yellow]"
                admin_col = f"[green]{i['admin_status']}[/green]"
                proto_col = f"[red]{i['protocol_status']}[/red]"
            else:
                health_text = "[bold red]DOWN[/bold red]"
                admin_col = f"[red]{i['admin_status']}[/red]"
                proto_col = f"[red]{i['protocol_status']}[/red]"

            iface_table.add_row(
                i["vrf"],
                i["interface"],
                i["ip_address"],
                admin_col,
                proto_col,
                health_text,
                i["description"],
            )
        self.console.print(iface_table)

        # 3. Active Incidents / Alerts Panel
        alerts = [b for b in bgp_findings if b["severity"] != "OK"] + [i for i in iface_findings if i["severity"] != "OK"]
        if alerts:
            alert_text = Text()
            for alert in alerts:
                target = alert.get("neighbor_ip") or alert.get("interface")
                alert_text.append(f"• [{alert['severity']}] [{alert['vrf']}] {target}: {alert['issue']}\n", style="bold red" if alert['severity'] == "CRITICAL" else "yellow")
                if "action" in alert:
                    alert_text.append(f"  👉 Remediation: {alert['action']}\n", style="white")
            self.console.print(Panel(alert_text, title="⚠️ ACTIVE MONITORING ALERTS & REMEDIATION", border_style="bold red"))
        else:
            self.console.print(Panel("[bold green]✅ All VRF BGP neighbors and interfaces are operating normally.[/bold green]", title="Status"))

    def _display_plain_dashboard(self):
        """Plain-text fallback when rich is not available."""
        metrics = self.get_summary_metrics()
        print(f"\n=== CISCO VRF BGP & INTERFACE MONITORING ===")
        print(f"VRFs: {metrics['total_vrfs']} | BGP Up: {metrics['established_neighbors']}/{metrics['total_neighbors']} | Ifaces Up: {metrics['healthy_interfaces']}/{metrics['total_interfaces']}")
        for b in self.analyze_bgp_health():
            print(f"[{b['severity']}] VRF: {b['vrf']} | Neighbor: {b['neighbor_ip']} (AS {b['remote_as']}) | State: {b['state']} | {b['issue']}")
        for i in self.analyze_interface_health():
            print(f"[{i['severity']}] VRF: {i['vrf']} | Interface: {i['interface']} | Admin: {i['admin_status']} | Line: {i['protocol_status']}")

    def run_ai_diagnostics(self) -> str:
        """Runs Gemini AI incident diagnostics on the mocked CLI output if API key is present."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "ℹ️ GEMINI_API_KEY not configured in .env. Skipping AI diagnostics."

        try:
            from google import genai
            from google.genai import types

            client = genai.Client()
            cli_data = get_mock_cisco_cli_output()
            system_instruction = (
                "You are an expert Cisco Network Operations Center (NOC) Automation Engineer. "
                "Analyze the provided VRF BGP and Interface command outputs. "
                "Summarize root causes for down neighbors/interfaces across VRFs A, B, and C. "
                "List specific IOS XE verification/troubleshooting commands to resolve each incident."
            )

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"Analyze this VRF BGP and interface data:\n\n{cli_data}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1
                )
            )
            return response.text.strip()
        except Exception as e:
            return f"❌ AI Diagnostics error: {e}"


if __name__ == "__main__":
    monitor = BGPMonitor()
    monitor.display_dashboard()

    # If run with --ai flag or requested, run AI analysis
    if "--ai" in sys.argv:
        print("\n🤖 Running Gemini AI Incident Analysis...")
        print(monitor.run_ai_diagnostics())
