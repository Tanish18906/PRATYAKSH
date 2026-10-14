"""Timestamp helpers. Contract: ISO-8601 UTC with trailing Z, seconds precision, no time zones."""
from datetime import datetime

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, _FMT)


def hours_between(a: str, b: str) -> float:
    """Hours from a to b (negative if b is earlier)."""
    return (parse_ts(b) - parse_ts(a)).total_seconds() / 3600.0
