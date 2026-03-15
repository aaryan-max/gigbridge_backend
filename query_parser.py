import os
import json
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Configure Gemini if available
if genai:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

SYSTEM_PROMPT = """
You are a query parser for a freelancer marketplace.

Extract structured search filters from user queries.

Return ONLY JSON.

Fields:
category
location
max_budget
min_budget
tags

Example:

User: "photographer near ghatkopar under 3000"

Output:
{
 "category": "photographer",
 "location": "ghatkopar",
 "max_budget": 3000
}
"""

def parse_query(user_query: str) -> dict:
    """
    Parse natural language query about freelancers using Gemini AI.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        dict: Structured filters extracted from query
              Returns empty dict if parsing fails
    """
    try:
        # Check if model is available
        if not model:
            print("Gemini model not available")
            return {}
            
        # Check if API key is available
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY environment variable not found")
            return {}
        
        # Generate response
        response = model.generate_content(
            SYSTEM_PROMPT + "\n\nUser query:\n'" + user_query + "'\n\nOutput:"
        )
        
        # Extract and parse JSON response
        response_text = response.text.strip()
        
        # Clean up response text
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        filters = json.loads(response_text)
        
        # Validate and clean filters
        validated_filters = {}
        
        # Validate category
        if 'category' in filters and filters['category']:
            validated_filters['category'] = str(filters['category']).strip().lower()
        
        # Validate location
        if 'location' in filters and filters['location']:
            validated_filters['location'] = str(filters['location']).strip().lower()
        
        # Validate min_budget
        if 'min_budget' in filters and filters['min_budget'] is not None:
            try:
                validated_filters['min_budget'] = float(filters['min_budget'])
            except (ValueError, TypeError):
                pass
        
        # Validate max_budget
        if 'max_budget' in filters and filters['max_budget'] is not None:
            try:
                validated_filters['max_budget'] = float(filters['max_budget'])
            except (ValueError, TypeError):
                pass
        
        # Validate tags
        if 'tags' in filters and isinstance(filters['tags'], list):
            validated_tags = []
            for tag in filters['tags']:
                if tag and isinstance(tag, str):
                    validated_tags.append(str(tag).strip().lower())
            if validated_tags:
                validated_filters['tags'] = validated_tags
        
        return validated_filters
        
    except Exception as e:
        print(f"Error parsing query with Gemini: {e}")
        return {}