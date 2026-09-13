import requests

url = "http://127.0.0.1:5000/triage"
payload = {"complaint": "I spilled water on my laptop and the screen is completely dead."}

response = requests.post(url, json=payload)
print(response.json())