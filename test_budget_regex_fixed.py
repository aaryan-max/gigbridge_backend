import re

# Fixed pattern - use lazy quantifier and word boundary
pattern = r'^hire\s+(?:freelancer\s+)?(\w+(?:\s+\w+)*?)(?:\s+with\s+(?:my\s+)?(?:proposed\s+)?budget\s+(\d+))?$'

test_commands = [
    "hire john with budget 300",
    "hire freelancer john with my proposed budget 300",
    "hire john",
    "hire john budget 500",
    "hire alex smith with budget 750"
]

print(f"Pattern: {pattern}")
print()

for cmd in test_commands:
    match = re.match(pattern, cmd, re.IGNORECASE)
    if match:
        name = match.group(1).strip() if match.group(1) else ""
        budget = match.group(2).strip() if match.group(2) else ""
        print(f"'{cmd}' -> Name: '{name}', Budget: '{budget}'")
    else:
        print(f"'{cmd}' -> No match")
