"""Print a sample of targets from each category."""
import re

with open("O:/opencode-repo/darktrace/scripts/seed_300_targets.py") as f:
    lines = f.readlines()

in_targets = False
current_target = []
depth = 0
targets_in_order = []

for line in lines:
    s = line.strip()
    if s.startswith("TARGETS = ["):
        in_targets = True
        continue
    if not in_targets:
        continue
    if s == "]":
        break
    
    if "make_target(" in s:
        current_target = [s]
        depth = s.count("(") - s.count(")")
    elif depth > 0:
        current_target.append(s)
        depth += s.count("(") - s.count(")")
        if depth == 0:
            targets_in_order.append(" ".join(current_target))
            current_target = []

# Extract categories and first few from each
seen_cats = {}
for t in targets_in_order:
    parts = re.findall(r'"([^"]+)"', t)
    if len(parts) >= 4:
        cat = parts[3]
        url = parts[0]
        name = parts[1]
        if cat not in seen_cats:
            seen_cats[cat] = []
        if len(seen_cats[cat]) < 3:
            seen_cats[cat].append((name, url))

print("=== Sample Targets (3 per category) ===\n")
for cat, items in sorted(seen_cats.items()):
    print(f"\n{cat.upper()} ({len([t for t in targets_in_order if cat in t])} total):")
    for name, url in items:
        print(f"  - {name}")
        print(f"    {url[:100]}")
