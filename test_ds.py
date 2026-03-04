import requests

key = "sk-95404bbfd4fe4d0792f17f7b2d3f6914"

resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={
        "model": "arcee-ai/trinity-large-preview:free",
        "messages": [{"role": "user", "content": "Hello"}],
    }
)
print(resp.status_code)
print(resp.text)
