import requests
import time

url = "http://127.0.0.1:5000/triage"

# 15 Highly realistic IT complaints spanning Hardware, Software, Access, and Network
complaints = [
    "I spilled water on my laptop and the screen is completely dead.",
    "I forgot my password to the main HR portal and am locked out.",
    "The office WiFi keeps dropping every 5 minutes in conference room B.",
    "My external monitor won't turn on, I think the power cable is broken.",
    "I need access granted to the AWS production database for my new project.",
    "Outlook keeps crashing every time I try to attach a PDF.",
    "The printer on the 4th floor is out of toner and has a paper jam.",
    "Someone cracked the glass on my company iPhone.",
    "I'm getting a 404 error when trying to reach the internal company wiki site.",
    "Can you install Adobe Photoshop on my machine? I need it for marketing.",
    "My Dell keyboard is missing the spacebar key.",
    "I can't connect to the company VPN from my home network.",
    "The billing software is freezing and running extremely slow today.",
    "My laptop battery dies after 10 minutes when it is unplugged.",
    "I need a new guest Wi-Fi code generated for our visitors today."
]

print("Starting to seed database. This will take about 30 seconds to avoid API rate limits...")

for i, text in enumerate(complaints, 1):
    payload = {"complaint": text}
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        category = data.get('structured_data', {}).get('category', 'Unknown')
        urgency = data.get('structured_data', {}).get('urgency', 'Unknown')
        print(f"[{i}/15] Success: Ticket #{data.get('ticket_id')} | {category} | {urgency}")
    except Exception as e:
        print(f"[{i}/15] Failed to process: {e}")
        
    # Wait 2 seconds to respect Groq's free tier rate limits
    time.sleep(2)

print("\nDatabase successfully seeded! Go check your analytics endpoint.")