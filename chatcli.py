import requests

API_URL = "http://127.0.0.1:5000/ai/chat"

print("====================================")
print(" GigBridge AI Chat (type exit to quit)")
print("====================================")

# Ask user role and id once
role = input("Enter role (client/freelancer): ").strip().lower()
user_id = input("Enter your user_id: ").strip()

try:
    user_id = int(user_id)
except:
    print("Invalid user_id")
    exit()

print("\nYou can now chat with the AI.\n")

while True:
    message = input("You: ")

    if message.lower() in ("exit", "quit"):
        print("Goodbye.")
        break

    try:
        response = requests.post(
            API_URL,
            json={
                "user_id": user_id,
                "role": role,
                "message": message
            },
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("mode") == "action":
                result = data.get("result")

                if isinstance(result, dict) and "text" in result:
                    print("AI:", result["text"])
                else:
                    print("AI:", result)
            else:
                print("AI:", data.get("answer", "No response"))

        else:
            print("Error:", response.text)

    except Exception as e:
        print("Connection error:", str(e))
