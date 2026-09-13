import requests

# Put your actual Groq key here again for the test
api_key = "gsk_your_actual_long_api_key_here"  
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
models = response.json()

print("AVAILABLE MODELS FOR YOUR KEY:")
for model in models.get("data", []):
    print("-", model["id"])