"""Replace placeholder .onion addresses with valid-format ones."""
import re
import secrets
import string

with open("O:/opencode-repo/darktrace/scripts/seed_300_targets.py", "r") as f:
    content = f.read()

alphabet = string.ascii_lowercase + "234567"

def gen_onion():
    return "".join(secrets.choice(alphabet) for _ in range(56))

# Find all .onion URLs and replace the hash portion
def replace_onion(match):
    prefix = match.group(1)  # http:// or https://
    # The onion address is everything before .onion
    full = match.group(0)
    # Replace the middle (the 56-char hash) with a valid one
    return f"{prefix}{gen_onion()}.onion"

# Match .onion URLs: http(s)://<prefix><56chars>.onion
# The existing pattern has varying lengths after the prefix
pattern = r'(https?://)([a-z0-9]+)\.onion'
new_content = re.sub(pattern, replace_onion, content)

with open("O:/opencode-repo/darktrace/scripts/seed_300_targets.py", "w") as f:
    f.write(new_content)

# Count
old_count = len(re.findall(r'\.onion', content))
new_count = len(re.findall(r'\.onion', new_content))
print(f"Fixed {old_count} .onion URLs with valid-format addresses")
print(f"Total .onion URLs: {new_count}")
