import json
import math
import sys
from collections import Counter

def diff_paths(a, b, path="$"):
    if type(a) is not type(b):
        yield path
    elif isinstance(a, dict):
        for key in sorted(set(a) | set(b), key=str):
            if key not in a or key not in b:
                yield f"{path}.{key}"
            else:
                yield from diff_paths(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield f"{path}.length"
        for i, (x, y) in enumerate(zip(a, b)):
            yield from diff_paths(x, y, f"{path}[{i}]")
    else:
        both_nan = isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b)
        if not both_nan and a != b:
            yield path

def find_named(obj, name, path="$"):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}"
            if k == name:
                found.append((here, v))
            found.extend(find_named(v, name, here))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(find_named(v, name, f"{path}[{i}]"))
    return found

with open(sys.argv[1], encoding="utf-8-sig") as f: base = json.load(f)
with open(sys.argv[2], encoding="utf-8-sig") as f: other = json.load(f)
paths = list(diff_paths(base, other))
print("total_changed_paths", len(paths))
print("top_level_changed", sorted({p.split(".")[1].split("[")[0] for p in paths if p.startswith("$.")}))
for p in paths[:40]: print("changed", p)
left = find_named(base, "T_log_by_estimator")
right = find_named(other, "T_log_by_estimator")
print("tlog_nodes", len(left), len(right))
print("tlog_equal", [(p, v) for p,v in left] == [(p, v) for p,v in right])
for p, v in left:
    print("tlog_node", p, "n_estimators", len(v) if isinstance(v,dict) else None)
