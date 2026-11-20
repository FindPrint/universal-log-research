from pathlib import Path
import codecs
import hashlib

root = Path(__file__).resolve().parents[2]
source_path = root / "UNIVERSAL_LOG_v5.9.2.py"
target_path = root / "UNIVERSAL_LOG_v5.9.3.py"
raw = source_path.read_bytes()
bom = raw.startswith(codecs.BOM_UTF8)
text = raw.decode("utf-8-sig")
newline = "\r\n" if "\r\n" in text else "\n"
normalized = text.replace("\r\n", "\n")

start = normalized.index("def _safe_divide(")
end = normalized.index("\n\ndef _safe_log(", start)
replacement = """def _safe_divide(numerator, denominator, *, zero_value=np.nan):
    # Division sûre : NaN si dénominateur nul/non fini; conserve les zéros valides.
    # Le chemin scalaire évite les tableaux 0-D et le contexte np.errstate,
    # très fréquents dans les estimateurs. La branche tableau reste inchangée.
    if np.isscalar(numerator) and np.isscalar(denominator):
        av = float(numerator)
        bv = float(denominator)
        if not np.isfinite(bv) or bv == 0.0:
            return float(zero_value)
        return av / bv

    a = np.asarray(numerator, dtype=float)
    b = np.asarray(denominator, dtype=float)
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        out = np.divide(
            a, b,
            out=np.full(np.broadcast_shapes(a.shape, b.shape), zero_value, dtype=float),
            where=np.isfinite(b) & (b != 0),
        )
    if np.ndim(out) == 0:
        return float(out)
    return out
"""
normalized = normalized[:start] + replacement + normalized[end:]
old_version = 'VERSION_MASTER = "v5.9.2-L7aL7b-DKind-AuditFix-SeedTrace-CohenDOnly"'
new_version = 'VERSION_MASTER = "v5.9.3-L7aL7b-DKind-AuditFix-SeedTrace-CohenDOnly-FastScalarDivide"'
if old_version not in normalized:
    raise SystemExit("Expected base VERSION_MASTER string not found.")
normalized = normalized.replace(old_version, new_version, 1)
normalized = normalized.replace(
    'VERSION = VERSION_MASTER.split("-")[0]  # -> "v5.9.1"',
    'VERSION = VERSION_MASTER.split("-")[0]  # -> "v5.9.3"',
    1,
)
out = normalized.replace("\n", newline)
target_path.write_bytes((codecs.BOM_UTF8 if bom else b"") + out.encode("utf-8"))
print("source_sha256", hashlib.sha256(raw).hexdigest())
print("candidate", target_path)
print("candidate_sha256", hashlib.sha256(target_path.read_bytes()).hexdigest())
print("candidate_version", new_version.split('"')[1])
