import requests

API_URL = "http://127.0.0.1:5000/ai/chat"

USER_ID = 1
ROLE = "client"

print("=== GigBridge AI Chat ===")
print("Type 'exit' to quit\n")

while True:
    message = input("You: ")

    if message.lower() == "exit":
        break

    payload = {
        "user_id": USER_ID,
        "role": ROLE,
        "message": message
    }

    try:
        r = requests.post(API_URL, json=payload)

        if r.status_code == 200:
            data = r.json()
            print("AI:", data.get("answer"))
        else:
            print("Error:", r.text)

    except Exception as e:
        print("Connection error:", e)