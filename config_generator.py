import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the root-level .env file containing your key
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("❌ Missing GEMINI_API_KEY in your configuration setup!")

# Initialize the Gemini free-tier client
client = genai.Client()

# System instructions to lock the AI into a deterministic Cisco engineer persona
system_instruction = (
    "You are an expert Cisco Network Engineer. Generate ONLY valid, clean Cisco IOS XE "
    "configuration commands. Do not include conversational preambles, markdown formatting "
    "(such as ```), notes, or explanations. Provide only the raw CLI execution lines."
)

# User intent defining the changes needed on the target infrastructure
user_intent = (
    "Create a bulk configuration: Add VLAN 10 named 'Data_VLAN' and VLAN 20 named 'VoIP_VLAN'. "
    "Configure GigabitEthernet0/1 as an access port in VLAN 10 with spanning-tree portfast enabled. "
    "Configure GigabitEthernet0/2 as a trunk port allowing VLANs 10 and 20."
)

print("🤖 Requesting exact Cisco deployment commands from Gemini 3.8 Flash...")

try:
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=user_intent,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0  # Keeps the execution steps highly strict and deterministic
        )
    )
    
    print("\n📋 ================= GENERATED CISCO CONFIG =================")
    print(response.text.strip())
    print("=============================================================")

except Exception as e:
    print(f"❌ Automation runtime block encountered: {e}")
