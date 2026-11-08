# Cisco Network Automation (`cisco-netauto`)

Automated Cisco IOS XE configuration generation and multi-VRF BGP & Interface health monitoring with rich terminal visualization and automated unit testing.

---

## 📁 Repository Structure

```
cisco-netauto/
├── bgp_monitor.py          # BGP & Interface monitoring engine with Rich dashboard
├── mock_data.py            # Simulated topology & Cisco CLI outputs (VRF-A, VRF-B, VRF-C)
├── test_bgp_monitoring.py  # Automated unit test suite verifying monitoring logic
├── config_generator.py     # AI-assisted Cisco IOS XE CLI config generator
└── README.md               # Project documentation
```

---

## 🌐 Simulated Topology Overview

Simulates a Cisco Provider Edge (PE) router with 3 customer/service VRFs:

| VRF | Description | Interfaces | BGP Neighbors | Operational State |
|---|---|---|---|---|
| **VRF-A** | Enterprise Data (Cust A) | `Gi0/1`, `Gi0/2`, `Loopback10` | `10.1.1.2` (AS 65001)<br>`10.1.1.6` (AS 65001) | `10.1.1.2` Established<br>`10.1.1.6` **Active** (Degraded) |
| **VRF-B** | Voice & Multimedia (Cust B) | `Gi0/3`, `Gi0/4`, `Loopback20` | `10.2.1.2` (AS 65002)<br>`10.2.1.6` (AS 65002) | `Gi0/4` Down<br>`10.2.1.6` **Idle** (Link Outage) |
| **VRF-C** | Cloud Interconnect (Partner C) | `Gi0/5`, `Gi0/6`, `Loopback30` | `10.3.1.2` (AS 65003)<br>`10.3.1.6` (AS 65003) | `Gi0/6` Line down<br>`10.3.1.6` **Connect** (Flapping) |

---

## 🚀 Usage

### 1. Run BGP & Interface Health Monitor
Launch the interactive terminal dashboard:
```bash
python3 bgp_monitor.py
```

### 2. Run with Gemini AI Incident Diagnostics
Include automated root cause analysis and remediation suggestions:
```bash
python3 bgp_monitor.py --ai
```

### 3. Run Automated Tests
Execute the unit test suite to validate health detection algorithms:
```bash
python3 -m unittest -v test_bgp_monitoring.py
```

### 4. Run Configuration Generator
Generate deterministic Cisco IOS XE CLI configurations:
```bash
python3 config_generator.py
```
