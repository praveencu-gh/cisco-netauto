import os
import sys
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from netmiko import ConnectHandler

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv()

# Initialize MCPServer (compatible with mcp 2.x)
mcp = MCPServer(name="Cisco-Sandbox-Controller")

# Fixed Sandbox Target parameters
SANDBOX_DEVICE = {
    "device_type": "cisco_ios",
    "host": os.getenv("CISCO_HOST", "devnetsandboxiosxec9k.cisco.com"),
    "username": os.getenv("CISCO_USERNAME", "praveen_"),
    "password": os.getenv("CISCO_PASSWORD", "S7W&3P7jn!*i"),
    "secret": os.getenv("CISCO_SECRET", "S7W&3P7jn!*i"),
    "port": int(os.getenv("CISCO_PORT", 22)),
    "conn_timeout": 30,
}

@mcp.tool()
def run_sandbox_show_command(command: str) -> str:
    """
    Executes a read-only show command on the Cisco Always-On Sandbox 
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
    # Run the server using the standard stdio protocol
    mcp.run(transport="stdio")

