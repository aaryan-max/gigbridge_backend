# categories.py (FULL UPDATED - cleaned category names, no slashes)
CATEGORIES = [
    "Graphic Designer",
    "Video Editor",
    "Photographer",
    "Singer",
    "Dancer",
    "Illustrator",
    "Content Creator"
]

def normalize(text):
    return str(text).strip().lower()

_CATS_SET = {normalize(c) for c in CATEGORIES}

def is_valid_category(cat):
    return normalize(cat) in _CATS_SET