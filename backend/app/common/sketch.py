"""Keyed bottom-k MinHash sketches. Spec: docs/01_DATA_CONTRACT.md section 6.

Shared by the simulator and the engine. Neither may reimplement it.
"""
import hashlib
import hmac
import re

K_DEFAULT = 512
IDENTIFIER_COLUMNS = ["customer_id", "email", "phone", "policy_no"]


def normalize(column: str, value) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if column == "email":
        return s.lower()
    if column == "phone":
        digits = re.sub(r"\D", "", s)
        return digits[-10:] if len(digits) >= 10 else digits
    if column == "policy_no":
        return s.upper()
    if column == "customer_id":
        return s
    if column == "full_name":
        return " ".join(s.lower().split())
    return s


def h64(key: bytes, s: str) -> int:
    return int.from_bytes(hmac.new(key, s.encode("utf-8"), hashlib.sha256).digest()[:8], "big")


def make_sketch(column: str, values, key: bytes, k: int = K_DEFAULT) -> dict:
    hs = {h64(key, normalize(column, v)) for v in values}
    hs.discard(h64(key, ""))               # empty values never count
    ordered = sorted(hs)
    return {"k": k, "distinct": len(hs), "hashes": [f"{x:016x}" for x in ordered[:k]]}


def jaccard(a: list[str], b: list[str], k: int = K_DEFAULT) -> float:
    A = {int(x, 16) for x in a}
    B = {int(x, 16) for x in b}
    union = sorted(A | B)[:k]
    if not union:
        return 0.0
    inter = sum(1 for x in union if x in A and x in B)
    return inter / len(union)


def containment(leak: dict, export: dict) -> float:
    """Fraction of the leak's distinct values that also appear in the export."""
    J = jaccard(leak["hashes"], export["hashes"], leak["k"])
    nL, nE = leak["distinct"], export["distinct"]
    if nL == 0:
        return 0.0
    c = J * (nL + nE) / ((1.0 + J) * nL)
    return max(0.0, min(1.0, c))
