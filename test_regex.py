import re

pattern = r'^(?:message|msg)\s+(\w+)\s+(.+)$'
test = 'message alex hello how are you'
match = re.match(pattern, test, re.IGNORECASE)
if match:
    print(f'Name: "{match.group(1)}"')
    print(f'Message: "{match.group(2)}"')
else:
    print('No match')
