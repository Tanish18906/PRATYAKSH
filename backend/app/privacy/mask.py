"""Masking rules, docs/01_DATA_CONTRACT.md section 10. Everything leaving the API goes through here
except the audited POST /api/reveal.

Unknown columns are masked with "***": a column we have not classified is treated as personal.
"""
import re

_DOB = re.compile(r"^(\d{4})-\d{2}-\d{2}$")


def _keep(s: str, head: int, tail: int) -> str:
    """Keep the first `head` and last `tail` characters; mask everything if there is nothing to hide."""
    if len(s) <= head + tail:
        return "*" * len(s)
    return s[:head] + "*" * (len(s) - head - tail) + (s[-tail:] if tail else "")


def mask_value(column: str, value) -> str:
    if value is None or value == "":
        return ""
    s = str(value)
    if column == "email":
        local, at, domain = s.partition("@")
        if not at or not domain:
            return "***"
        return f"{local[:1]}***@{domain}"
    if column == "phone":
        return _keep(s, 6, 2)
    if column == "full_name":
        return " ".join(p[0].upper() + "." for p in s.split())
    if column == "policy_no":
        return _keep(s, 2, 2)
    if column == "customer_id":
        return _keep(s, 0, 3)
    if column == "dob":
        m = _DOB.match(s)
        return f"{m.group(1)}-**-**" if m else "***"
    return "***"


def mask_row(row: dict) -> dict:
    return {k: mask_value(k, v) for k, v in row.items()}
