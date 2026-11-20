import json
import math
import sys

def walk(a, b, path="$"):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b), key=str):
            if key not in a or key not in b:
                out.append((f"{path}.{key}", "missing-key"))
            else:
                out.extend(walk(a[key], b[key], f"{path}.{key}"))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((f"{path}.length", (len(a), len(b))))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(walk(x, y, f"{path}[{i}]"))
    else:
        try:
            equal = (math.isnan(a) and math.isnan(b)) or a == b
        except (TypeError, ValueError):
            equal = a == b
        if not equal:
            out.append((path, (a, b)))
    return out

with open(sys.argv[1], encoding="utf-8-sig") as f:
    left = json.load(f)
with open(sys.argv[2], encoding="utf-8-sig") as f:
    right = json.load(f)
diffs = walk(left, right)
print("difference_count", len(diffs))
for item in diffs[:100]:
    print(item)
