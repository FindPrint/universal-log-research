import numpy as np
import timeit

def old(numerator, denominator, zero_value=np.nan):
    a = np.asarray(numerator, dtype=float)
    b = np.asarray(denominator, dtype=float)
    if a.ndim == 0 and b.ndim == 0:
        av, bv = float(a), float(b)
        if not np.isfinite(bv) or bv == 0.0:
            return float(zero_value)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            return float(np.divide(av, bv))
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return np.divide(
            a, b,
            out=np.full(np.broadcast_shapes(a.shape, b.shape), zero_value, dtype=float),
            where=np.isfinite(b) & (b != 0),
        )

def new(numerator, denominator, zero_value=np.nan):
    if np.isscalar(numerator) and np.isscalar(denominator):
        av, bv = float(numerator), float(denominator)
        if not np.isfinite(bv) or bv == 0.0:
            return float(zero_value)
        return av / bv
    a = np.asarray(numerator, dtype=float)
    b = np.asarray(denominator, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return np.divide(
            a, b,
            out=np.full(np.broadcast_shapes(a.shape, b.shape), zero_value, dtype=float),
            where=np.isfinite(b) & (b != 0),
        )

cases = [
    (3.0, 2.0), (-3.0, 2.0), (1e308, 1e-308),
    (float("nan"), 2.0), (float("inf"), 2.0),
    (2.0, float("inf")), (2.0, 0.0),
]
print("scalar_semantic_cases")
for a, b in cases:
    with np.errstate(all="ignore"):
        old_value, new_value = old(a, b), new(a, b)
    same = (np.isnan(old_value) and np.isnan(new_value)) or old_value == new_value
    print(repr(a), repr(b), repr(old_value), repr(new_value), "same=", same)
for label, function in [("old", old), ("new", new)]:
    values = timeit.repeat(lambda: function(3.0, 2.0), number=50000, repeat=5)
    print(label, "repeat_seconds=", values, "median_seconds=", float(np.median(values)))
