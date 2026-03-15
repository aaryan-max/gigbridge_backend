# categories.py (FINAL CATEGORY LIST)

# Reusable constant for freelancer profile validation and CLI display
ALLOWED_FREELANCER_CATEGORIES = [
    "Photographer",
    "Videographer",
    "DJ",
    "Singer",
    "Dancer",
    "Anchor",
    "Makeup Artist",
    "Mehendi Artist",
    "Decorator",
    "Wedding Planner",
    "Choreographer",
    "Band / Live Music",
    "Magician / Entertainer",
    "Artist",
    "Event Organizer"
]

# Legacy aliases for backward compatibility
VALID_CATEGORIES = ALLOWED_FREELANCER_CATEGORIES
CATEGORIES = VALID_CATEGORIES

def normalize(text):
    return str(text).strip().lower()

_CATS_SET = {normalize(c) for c in CATEGORIES}

def is_valid_category(cat):
    return normalize(cat) in _CATS_SET

def get_all_categories():
    """Returns the final list of all valid categories"""
    return ALLOWED_FREELANCER_CATEGORIES.copy()