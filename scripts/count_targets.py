"""Count targets in the seed script."""
import re

with open("O:/opencode-repo/darktrace/scripts/seed_300_targets.py") as f:
    lines = f.readlines()

# Find the TARGETS list and parse make_target calls
in_targets = False
targets = []
current = []
depth = 0

for line in lines:
    stripped = line.strip()
    if stripped.startswith("TARGETS = ["):
        in_targets = True
        continue
    if not in_targets:
        continue
    if stripped == "]":
        break
    
    # Track make_target calls
    if "make_target(" in stripped:
        depth = stripped.count("(") - stripped.count(")")
        current = [stripped]
    elif depth > 0:
        current.append(stripped)
        depth += stripped.count("(") - stripped.count(")")
        if depth == 0:
            targets.append(" ".join(current))
            current = []

print(f"Total targets: {len(targets)}")

# Extract category (4th positional arg or keyword)
cats = {}
for t in targets:
    # Try to find category keyword
    m = re.search(r'category\s*=\s*["\']([^"\']+)["\']', t)
    if m:
        c = m.group(1)
    else:
        # Positional: split by commas and find 4th string value
        parts = re.findall(r'["\']([^"\']+)["\']', t)
        if len(parts) >= 4:
            c = parts[3]  # 4th string = category
        else:
            c = "unknown"
    cats[c] = cats.get(c, 0) + 1

print(f"\nCategories ({len(cats)}):")
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")
