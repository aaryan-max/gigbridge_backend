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
    "Event Organizer",
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


# ============================================================
# PRICING TYPE MAPPING (CENTRAL CONFIG)
# ============================================================
#
# NOTE: Pricing types here are a NEW, higher-level abstraction
# and are intentionally separate from legacy contract_type
# values like FIXED/HOURLY/EVENT used in existing APIs.

PRICING_TYPE_HOURLY = "hourly"
PRICING_TYPE_PER_PERSON = "per_person"
PRICING_TYPE_PACKAGE = "package"
PRICING_TYPE_PROJECT = "project"


_CATEGORY_PRICING_MAP = {
    # HOURLY
    normalize("DJ"): PRICING_TYPE_HOURLY,
    normalize("Singer"): PRICING_TYPE_HOURLY,
    normalize("Anchor"): PRICING_TYPE_HOURLY,
    normalize("Band / Live Music"): PRICING_TYPE_HOURLY,
    normalize("Dancer"): PRICING_TYPE_HOURLY,
    normalize("Magician / Entertainer"): PRICING_TYPE_HOURLY,

    # PER_PERSON
    normalize("Makeup Artist"): PRICING_TYPE_PER_PERSON,
    normalize("Mehendi Artist"): PRICING_TYPE_PER_PERSON,

    # PACKAGE
    normalize("Photographer"): PRICING_TYPE_PACKAGE,
    normalize("Videographer"): PRICING_TYPE_PACKAGE,
    normalize("Choreographer"): PRICING_TYPE_PACKAGE,
    # Business spec mentions "Painter" but current category list
    # uses "Artist". Treat "Artist" as the painter-equivalent.
    normalize("Artist"): PRICING_TYPE_PACKAGE,

    # PROJECT
    normalize("Decorator"): PRICING_TYPE_PROJECT,
    normalize("Wedding Planner"): PRICING_TYPE_PROJECT,
    normalize("Event Organizer"): PRICING_TYPE_PROJECT,
}


def get_pricing_type_for_category(category: str):
    """
    Return normalized pricing type for a given category.

    Raises ValueError if category is invalid or not mapped.
    """
    if not is_valid_category(category):
        raise ValueError("Invalid category")

    key = normalize(category)
    pt = _CATEGORY_PRICING_MAP.get(key)
    if not pt:
        # Hard fail rather than silently misclassifying – caller
        # should decide how to handle unmapped categories.
        raise ValueError(f"No pricing type mapping for category: {category}")
    return pt


def is_category_pricing_type(category: str, pricing_type: str) -> bool:
    """Helper to check if a category belongs to a specific pricing type."""
    try:
        return get_pricing_type_for_category(category) == normalize(pricing_type)
    except Exception:
        return False