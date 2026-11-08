import os
from dotenv import load_dotenv
from netmiko import ConnectHandler
from google import genai
from google.genai import types

# 1. Load Environment Variables securely from the .env file
load_dotenv()

# 2. Cisco DevNet Always-On Sandbox Connection Parameters
# Replace these values with the live dynamic ones from your DevNet Dashboard!
CISCO_DEVICE = {
    "device_type": "cisco_ios",
    "host": "://cisco.com",  # Example host
    "username": "developer",                      # Example username
    "password": "C1sco12345",                      # Example password
    "port": 22,
}

def fetch_network_data():
    """Connects to the Cisco Sandbox and extracts the live configuration state."""
    print("⏳ Connecting to Cisco IOS XE Always-On Sandbox...")
    
    # Establish a secure SSH channel using Netmiko ConnectHandler
    with ConnectHandler(**CISCO_DEVICE) as ssh_conn:
        # Enter enable mode if required by the sandbox profile
        ssh_conn.enable()
        
        print("📊 Running operational show commands...")
        # Execute the commands and save the raw CLI output text
        interface_output = ssh_conn.send_command("show ip interface brief")
        version_output = ssh_conn.send_command("show version")
        
        # Combine the text artifacts together
        combined_raw_data = f"--- SHOW IP INTERFACE BRIEF ---\n{interface_output}\n\n--- SHOW VERSION ---\n{version_output}"
        return combined_raw_data

def analyze_with_ai(raw_cli_text):
    """Feeds raw Cisco CLI text to Gemini and mandates a structured JSON response."""
    print("🤖 Sending operational logs to Gemini for AI analysis...")
    
    # Initialize the modern Google GenAI Client
    # It automatically picks up the GEMINI_API_KEY from your environment variables
    client = genai.Client()
    
    # Construct a clear prompt directing the AI exactly how to parse the text
    system_prompt = (
        "You are an expert AI Network Automation Engineer. Your job is to parse raw Cisco CLI outputs "
        "and return a highly structured health matrix report. You must identify any down interfaces, "
        "extract the hostname, software version, and uptime, and flag issues."
    )
    
    user_prompt = f"Analyze this network device data and organize it:\n\n{raw_cli_text}"
    
    # Call the lightning-fast free-tier flash model
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            # Force the model to output valid, structured JSON directly
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "hostname": types.Schema(type=types.Type.STRING),
                    "ios_version": types.Schema(type=types.Type.STRING),
                    "uptime": types.Schema(type=types.Type.STRING),
                    "total_interfaces": types.Schema(type=types.Type.INTEGER),
                    "down_interfaces_detected": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    ),
                    "summary_health_rating": types.Schema(type=types.Type.STRING, description="Scale of 1-10")
                },
                required=["hostname", "ios_version", "total_interfaces", "down_interfaces_detected"]
            )
        )
    )
    
    return response.text

if __name__ == "__main__":
    try:
        # Step A: Get the live data from Cisco
        raw_data = fetch_network_data()
        
        # Step B: Let AI parse and audit it
        json_report = analyze_with_ai(raw_data)
        
        print("\n🚀 SUCCESS! Structured AI Net-Audit Matrix:")
        print(json_report)
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
