import requests
import json

# Test OpenRouter API directly
api_key = "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"
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://gigbridge.com",
    "X-Title": "GigBridge"
}

payload = {
    "model": "moonshotai/kimi-k2-0711-preview",
    "messages": [
        {"role": "user", "content": "test"}
    ],
    "max_tokens": 10
}

print("Testing OpenRouter API...")
print(f"URL: {url}")
print(f"Headers: {json.dumps(headers, indent=2)}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Success!")
    else:
        print("❌ Error occurred")
        
except Exception as e:
    print(f"Exception: {e}")

# Try with a different model
print("\n" + "="*50)
print("Trying with Claude model...")

payload["model"] = "anthropic/claude-3-haiku"

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
except Exception as e:
    print(f"Exception: {e}")
