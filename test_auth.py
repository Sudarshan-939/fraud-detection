import requests

# Test without OpenRouter format
resp1 = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": "Bearer sk-95404bbfd4fe4d0792f17f7b2d3f6914", "Content-Type": "application/json"},
    json={"model": "arcee-ai/trinity-large-preview:free", "messages": [{"role": "user", "content": "Hello"}]}
)
print("resp1:", resp1.text)

# Test with fake OpenRouter format
resp2 = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": "Bearer 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", "Content-Type": "application/json"},
    json={"model": "arcee-ai/trinity-large-preview:free", "messages": [{"role": "user", "content": "Hello"}]}
)
print("resp2:", resp2.text)
