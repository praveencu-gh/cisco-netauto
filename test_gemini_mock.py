import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load local environment configuration from your hidden .env file
load_dotenv()

# Basic validation to ensure your free tier setup is correct
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("❌ Missing GEMINI_API_KEY in your .env file! Please check your configuration.")

# 2. Initialize the Google GenAI Client (Picks up the API key automatically)
client = genai.Client()

# 3. Simulated/Mocked output of the Cisco command "show interfaces description"
mock_cisco_output = """
Interface                  Status         Protocol       Description
Interface                  Status         Protocol       Description
GigabitEthernet1           up             up             Uplink_to_Core
GigabitEthernet2           down           down           Link_to_BranchOffice
GigabitEthernet3           up             down           Test_Lab_Interface
Loopback0                  up             up             Management_Loopback
"""

# 4. Define engineering guidelines for the AI agent
system_instruction = (
    "You are a network automation reliability agent. Analyze the provided Cisco text output. "
    "Identify any interfaces where the Status or Protocol is 'down'. List them under a bold "
    "'⚠️ SECURITY/OPERATIONAL ALERTS' header with a short, 1-sentence recommended action. "
    "If all interfaces are up, state 'All clear' plainly."
)

print("🤖 Passing simulated network logs to the active Gemini 3.8 Flash free tier...")

try:
    # 5. Make the API Call to the updated free-tier target model
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=f"Analyze this routing command data:\n\n{mock_cisco_output}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1  # Low temperature keeps output predictable and accurate
        )
    )
    
    # 6. Print the generated engineering report to your terminal screen
    print("\n📋 ================== GEMINI AI REPORT ==================")
    print(response.text.strip())
    print("=========================================================")

except Exception as e:
    print(f"\n❌ Gemini API Call failed: {e}")
