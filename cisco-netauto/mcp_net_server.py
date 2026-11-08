"""
Cisco NOC Copilot - Model Context Protocol (MCP) Server
Connects AI agents directly to Cisco IOS XE network infrastructure (Catalyst 9000).
Provides specialized network troubleshooting, interface audits, routing telemetry,
and AI-assisted incident triage tools.
"""

import os
import sys
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from netmiko import ConnectHandler

# Load environment configuration (parent and local)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv()

# Initialize MCPServer instance (MCP 2.x standard)
mcp = MCPServer(
    name="Cisco-NOC-Copilot",
    description="Automated Cisco Catalyst 9000 diagnostic and telemetry tools for NOC engineers."
)

# Cisco Catalyst 9000 Sandbox Target Parameters
SANDBOX_DEVICE = {
    "device_type": "cisco_ios",
    "host": os.getenv("CISCO_HOST", "devnetsandboxiosxec9k.cisco.com"),
    "username": os.getenv("CISCO_USERNAME", "praveen_"),
    "password": os.getenv("CISCO_PASSWORD", "S7W&3P7jn!*i"),
    "secret": os.getenv("CISCO_SECRET", "S7W&3P7jn!*i"),
    "port": int(os.getenv("CISCO_PORT", 22)),
    "conn_timeout": 30,
}


def _execute_cli_commands(commands: List[str]) -> Dict[str, str]:
    """Helper that connects via SSH once and executes a batch of commands."""
    results = {}
    try:
        with ConnectHandler(**SANDBOX_DEVICE) as ssh_conn:
            ssh_conn.enable()
            for cmd in commands:
                # Defensive guardrail: only read-only show commands
                if not cmd.strip().lower().startswith("show"):
                    results[cmd] = "Error: Only read-only 'show' commands are permitted."
                else:
                    results[cmd] = ssh_conn.send_command(cmd)
        return results
    except Exception as e:
        return {"error": f"SSH Connection Failure: {str(e)}"}


@mcp.tool()
def audit_interface_health(interface_name: str = "all") -> str:
    """
    Audits interface operational health and packet error counters on the Cisco switch.
    
    Args:
        interface_name: 'all' to audit all switchports, or a specific interface (e.g. 'GigabitEthernet0/0', 'Vlan1').
    """
    if interface_name.strip().lower() == "all":
        data = _execute_cli_commands(["show ip interface brief", "show interfaces status"])
        if "error" in data:
            return data["error"]
        
        ip_brief = data.get("show ip interface brief", "")
        lines = ip_brief.strip().split("\n")
        
        up_interfaces = []
        down_interfaces = []
        admin_down_interfaces = []
        
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 5:
                iface, ip, ok, method, status = parts[0], parts[1], parts[2], parts[3], parts[4]
                proto = parts[5] if len(parts) > 5 else "unknown"
                entry = f"{iface} (IP: {ip}, Status: {status}, Protocol: {proto})"
                
                if status.lower() == "up" and proto.lower() == "up":
                    up_interfaces.append(entry)
                elif "admin" in status.lower():
                    admin_down_interfaces.append(entry)
                else:
                    down_interfaces.append(entry)
                    
        report = [
            "📋 === INTERFACE FLEET HEALTH AUDIT ===",
            f"• Operational Interfaces (Up/Up): {len(up_interfaces)}",
            f"• Degraded/Down Interfaces: {len(down_interfaces)}",
            f"• Administratively Disabled Ports: {len(admin_down_interfaces)}",
            "\n🟢 [ACTIVE OPERATIONAL PORTS]"
        ]
        report.extend([f"  ✔ {i}" for i in up_interfaces] or ["  (None)"])
        
        if down_interfaces:
            report.append("\n🚨 [ALERT: DOWN/DEGRADED INTERFACES]")
            report.extend([f"  ❌ {i}" for i in down_interfaces])
            
        if admin_down_interfaces:
            report.append("\n🔒 [ADMINISTRATIVELY SHUTDOWN PORTS]")
            report.extend([f"  ⏸ {i}" for i in admin_down_interfaces[:5]])
            if len(admin_down_interfaces) > 5:
                report.append(f"  ...and {len(admin_down_interfaces) - 5} more.")
                
        return "\n".join(report)
    
    else:
        # Audit a specific interface for physical-layer errors
        cmd = f"show interfaces {interface_name.strip()}"
        data = _execute_cli_commands([cmd])
        if "error" in data:
            return data["error"]
            
        output = data.get(cmd, "")
        if "Invalid input" in output:
            return f"❌ Interface '{interface_name}' not found on switch."
            
        # Parse error metrics
        crc_match = re.search(r"(\d+)\s+CRC", output)
        input_err_match = re.search(r"(\d+)\s+input errors", output)
        output_err_match = re.search(r"(\d+)\s+output errors", output)
        drops_match = re.search(r"Total output drops:\s*(\d+)", output) or re.search(r"(\d+)\s+dropped", output)
        
        crc = crc_match.group(1) if crc_match else "0"
        in_err = input_err_match.group(1) if input_err_match else "0"
        out_err = output_err_match.group(1) if output_err_match else "0"
        drops = drops_match.group(1) if drops_match else "0"
        
        report = [
            f"🔌 === INTERFACE DIAGNOSTIC: {interface_name} ===",
            f"• CRC Errors: {crc}",
            f"• Total Input Errors: {in_err}",
            f"• Total Output Errors: {out_err}",
            f"• Packet Drops: {drops}",
        ]
        
        if int(crc) > 0 or int(in_err) > 0:
            report.append("⚠️ PHYSICAL LAYER WARNING: CRC/Input errors detected. Check optical SFP transceiver, cable seating, or duplex mismatch.")
        else:
            report.append("✅ Physical layer counters are clean (Zero CRC or packet drop anomalies).")
            
        return "\n".join(report)


@mcp.tool()
def audit_routing_health() -> str:
    """
    Audits dynamic routing protocols (OSPF, BGP, Static) and routing table health.
    """
    commands = [
        "show ip protocols",
        "show ip route summary",
        "show ip ospf neighbor",
        "show ip bgp summary"
    ]
    data = _execute_cli_commands(commands)
    if "error" in data:
        return data["error"]
        
    report = ["🌐 === ROUTING & PROTOCOL HEALTH AUDIT ==="]
    
    # 1. Routing Protocols
    proto_out = data.get("show ip protocols", "")
    if "Routing Protocol is" in proto_out:
        active_protocols = re.findall(r'Routing Protocol is "(.*?)"', proto_out)
        router_ids = re.findall(r'Router ID (.*?)\n', proto_out)
        report.append(f"• Active Routing Protocols: {', '.join(active_protocols)}")
        if router_ids:
            report.append(f"• Router IDs: {', '.join(router_ids)}")
    else:
        report.append("• Active Routing Protocols: None detected")
        
    # 2. OSPF Neighbor state
    ospf_out = data.get("show ip ospf neighbor", "")
    if ospf_out.strip():
        report.append(f"\n[OSPF NEIGHBORS]\n{ospf_out}")
    else:
        report.append("• OSPF Adjacencies: No active OSPF neighbors formed.")
        
    # 3. BGP Neighbor state
    bgp_out = data.get("show ip bgp summary", "")
    if "Invalid input" in bgp_out or not bgp_out.strip():
        report.append("• BGP Status: BGP routing process is not enabled on this device.")
    else:
        report.append(f"\n[BGP SUMMARY]\n{bgp_out}")
        
    # 4. Route summary
    route_sum = data.get("show ip route summary", "")
    report.append(f"\n[ROUTING TABLE SUMMARY]\n{route_sum}")
    
    return "\n".join(report)


@mcp.tool()
def get_hardware_telemetry() -> str:
    """
    Retrieves real-time CPU, DRAM, flash memory, and platform resource telemetry.
    """
    commands = [
        "show platform resources",
        "show processes cpu | include CPU utilization",
        "show memory statistics"
    ]
    data = _execute_cli_commands(commands)
    if "error" in data:
        return data["error"]
        
    res_out = data.get("show platform resources", "")
    cpu_out = data.get("show processes cpu | include CPU utilization", "").strip()
    mem_out = data.get("show memory statistics", "")
    
    report = [
        "⚡ === SYSTEM HARDWARE TELEMETRY ===",
        f"• CPU Load: {cpu_out or 'Nominal'}",
        "\n[PLATFORM RESOURCE UTILIZATION]",
        res_out.strip()
    ]
    
    # Extract processor memory
    proc_mem = re.search(r"Processor\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)", mem_out)
    if proc_mem:
        total = int(proc_mem.group(1)) / (1024 * 1024)
        used = int(proc_mem.group(2)) / (1024 * 1024)
        free = int(proc_mem.group(3)) / (1024 * 1024)
        pct = (used / total) * 100 if total > 0 else 0
        report.append(f"\n[CONTROL PLANE MEMORY (HEAP)]")
        report.append(f"• Total: {total:.1f} MB | Used: {used:.1f} MB ({pct:.1f}%) | Free: {free:.1f} MB")
        
    return "\n".join(report)


@mcp.tool()
def generate_noc_incident_summary(incident_context: str = "Routine health audit") -> str:
    """
    Synthesizes live network telemetry using Gemini 3.8 Flash to generate an executive NOC Incident & Health Report.
    
    Args:
        incident_context: Short description of the user report (e.g. 'Slow application performance', 'Packet loss report').
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    # 1. Gather all live facts from switch
    telemetry_bundle = {
        "interfaces": audit_interface_health("all"),
        "routing": audit_routing_health(),
        "hardware": get_hardware_telemetry(),
    }
    
    raw_telemetry = (
        f"--- CONTEXT: {incident_context} ---\n\n"
        f"--- INTERFACES ---\n{telemetry_bundle['interfaces']}\n\n"
        f"--- ROUTING ---\n{telemetry_bundle['routing']}\n\n"
        f"--- HARDWARE ---\n{telemetry_bundle['hardware']}"
    )
    
    if not api_key:
        return f"Telemetry Collected:\n{raw_telemetry}\n\n(Note: Set GEMINI_API_KEY in .env for AI synthesis)."
        
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client()
        system_prompt = (
            "You are a Principal Network Operations Center (NOC) Architect. "
            "Analyze the multi-domain Cisco Catalyst 9000 telemetry provided. "
            "Generate an executive incident triage brief with: "
            "1. Health Score (1-10) and Status (Healthy/Degraded/Critical) "
            "2. Identified Anomalies or Bottlenecks "
            "3. Immediate Remediation Steps (exact Cisco CLI commands to resolve or verify)."
        )
        
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=f"Analyze this switch telemetry:\n\n{raw_telemetry}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"AI Generation Warning: {e}\n\nRaw Telemetry:\n{raw_telemetry}"


@mcp.tool()
def run_sandbox_show_command(command: str) -> str:
    """
    Executes an ad-hoc read-only show command on the Cisco Always-On Sandbox 
    and returns the raw CLI string output.
    """
    # Defensive validation to keep the shared sandbox clean
    if not command.strip().lower().startswith("show"):
        return "Error: Only read-only 'show' commands are permitted on this shared sandbox."
        
    try:
        with ConnectHandler(**SANDBOX_DEVICE) as ssh_conn:
            ssh_conn.enable()
            output = ssh_conn.send_command(command)
            return output
    except Exception as e:
        return f"SSH Connection Failure: {str(e)}"


if __name__ == "__main__":
    # If invoked with --test, allow testing individual tool capabilities
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_type = sys.argv[2] if len(sys.argv) > 2 else "interfaces"
        print(f"🧪 Testing Cisco NOC Copilot MCP Tool: '{test_type}'...")
        
        if test_type == "interfaces":
            print(audit_interface_health("all"))
        elif test_type == "routing":
            print(audit_routing_health())
        elif test_type == "hardware":
            print(get_hardware_telemetry())
        elif test_type == "noc":
            print(generate_noc_incident_summary("Testing NOC automated triage"))
        else:
            # Custom command fallback
            print(run_sandbox_show_command(test_type))
    else:
        # Standard MCP Server mode listening on STDIN for JSON-RPC from AI clients
        mcp.run(transport="stdio")
