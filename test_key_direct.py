import requests
import json

key = "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"

print(f"Testing the new key: {key}")

try:
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:5000",
        },
        json={
            "model": "arcee-ai/trinity-large-preview:free",
            "messages": [{"role": "user", "content": "Hello! Is Earth flat?"}],
        }
    )
    print("\nStatus Code:", resp.status_code)
    try:
        print("Response JSON:", json.dumps(resp.json(), indent=2))
    except Exception:
        print("Raw Response:", resp.text)
except Exception as e:
    print("Request failed with exception:", str(e))
