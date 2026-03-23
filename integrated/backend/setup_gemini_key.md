# Gemini API Key Setup

Your current API key has been flagged as leaked. You need to:

1. Go to: https://makersuite.google.com/app/apikey
2. Create a new API key
3. Replace the key in gemini_agent.py line 9:

```python
# Replace this line:
api_key = "YOUR_NEW_API_KEY_HERE"
```

## Current Status:
- ✅ Gemini migration complete
- ✅ System prompt updated to be strict about tools
- ✅ Fallback logic improved
- ❌ API key flagged as leaked

## Next Steps:
1. Generate new API key from Google AI Studio
2. Update gemini_agent.py with new key
3. Test again with: python -c "from llm_chatbot import generate_ai_response; print(generate_ai_response(1, 'client', 'show all freelancers'))"
