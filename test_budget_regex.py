import re

# Test different regex patterns for budget parsing
test_patterns = [
    # Original pattern (too greedy)
    r'^hire\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*)(?:\s+(?:with\s+)?(?:my\s+)?(?:proposed\s+)?budget\s+(\d+))?$',
    
    # Fixed pattern (non-greedy name capture)
    r'^hire\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*?)(?:\s+(?:with\s+)?(?:my\s+)?(?:proposed\s+)?budget\s+(\d+))?$',
    
    # Better pattern (explicit word boundary)
    r'^hire\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*)(?:\s+with\s+(?:my\s+)?(?:proposed\s+)?budget\s+(\d+))?$',
]

test_commands = [
    "hire john with budget 300",
    "hire freelancer john with my proposed budget 300",
    "hire john",
    "hire john budget 500"
]

for i, pattern in enumerate(test_patterns):
    print(f"\n=== Pattern {i+1}: {pattern} ===")
    for cmd in test_commands:
        match = re.match(pattern, cmd, re.IGNORECASE)
        if match:
            name = match.group(1).strip() if match.group(1) else ""
            budget = match.group(2).strip() if match.group(2) else ""
            print(f"'{cmd}' -> Name: '{name}', Budget: '{budget}'")
        else:
            print(f"'{cmd}' -> No match")
