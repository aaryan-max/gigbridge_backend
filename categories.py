CATEGORIES = [
    "Graphic Designer",
    "Video Editor",
    "Photographer",
    "Singer / Musician",
    "Dancer / Performer",
    "Illustrator / Digital Artist",
    "Content Creator"
]

def normalize(text: str):
    return text.strip().lower()

def is_valid_category(cat: str):
    return normalize(cat) in [normalize(c) for c in CATEGORIES]
