"""Thirty days of normal activity for the fictional company."""

from datetime import UTC, datetime
from math import exp, log

import numpy as np

from .base_table import BaseTable, seconds, seeded_rng, timestamp
from .lossy import new_event


ROLE_ACTIVITY = {
    "analyst": (3, "query", "ds:customers", "sys:bi-warehouse", 300, 0.6, 8, 18),
    "bi-admin": (3, "read", "ds:customers", "sys:bi-warehouse", 60, 0.5, 8, 18),
    "engineer": (3, "query", "ds:customers", "sys:customer-db", 20, 0.8, 8, 19),
    "marketing": (1, "query", "ds:marketing-leads", "sys:crm", 2000, 0.5, 9, 17),
    "support": (4, "read", "ds:claims", "sys:claims-api", 5, 0.5, 9, 18),
    "contractor": (2, "query", "ds:customers", "sys:customer-db", 50, 0.7, 9, 16),
}


def make_background(company: dict, base: BaseTable, found_ts: str, seed: int) -> list[dict]:
    rng = seeded_rng("background", seed)
    found = seconds(found_ts)
    first_day = found // 86400 - 30
    events = []
    users = [actor for actor in company["actors"] if actor["kind"] == "user"]
    admins = [actor for actor in users if actor["role"] == "bi-admin"]
    for day in range(31):
        midnight = (first_day + day) * 86400
        weekend = datetime.fromtimestamp(midnight, UTC).weekday() >= 5
        for actor in users:
            count, action, object_id, location, median, sigma, first_hour, last_hour = ROLE_ACTIVITY[actor["role"]]
            for _ in range(count):
                if weekend and rng.random() >= 0.2:
                    continue
                ts = midnight + int(rng.integers(first_hour, last_hour + 1)) * 3600 + int(rng.integers(0, 3600))
                if ts > found:
                    continue
                rows = max(1, round(exp(float(rng.normal(log(median), sigma)))))
                events.append(new_event(timestamp(ts), actor["id"], action, object_id,
                                        location, None, rows))
            if actor["role"] == "engineer" and (not weekend or rng.random() < 0.2):
                ts = midnight + int(rng.integers(8, 20)) * 3600 + int(rng.integers(0, 3600))
                if ts <= found:
                    rows = max(1, round(exp(float(rng.normal(log(100), 0.7)))))
                    events.append(new_event(timestamp(ts), actor["id"], "api_call", "ds:claims",
                                            "sys:claims-api", "ext:unknown-host", rows,
                                            {"client_ip": "198.51.100.10"}))

        if day % 10 == 0:
            for admin in admins:
                ts = midnight + 12 * 3600
                if ts <= found:
                    grantee = users[int(rng.integers(len(users)))]["id"]
                    events.append(new_event(timestamp(ts), admin["id"], "permission_change", None,
                                            None, None, 0,
                                            {"grantee": grantee, "scope": "sys:bi-warehouse",
                                             "change": "grant" if rng.random() < 0.5 else "revoke"},
                                            "src:bi-warehouse"))

        etl_ts = midnight + 2 * 3600 + 9 * 60
        if etl_ts <= found:
            matching = int(np.count_nonzero((base.created <= etl_ts) &
                                            (base.created >= seconds("2025-01-01T00:00:00Z")) &
                                            (base.states == 0)))
            events.append(new_event(timestamp(etl_ts), "act:etl-nightly", "query", "ds:customers",
                                    "sys:customer-db", None, matching))
        backup_ts = midnight + 3 * 3600
        if backup_ts <= found:
            existing = int(np.searchsorted(base.created, backup_ts, side="right"))
            events.append(new_event(timestamp(backup_ts), "act:backup-svc", "read", "ds:customers",
                                    "sys:customer-db", None, existing))
        for _ in range(2):
            ts = midnight + int(rng.integers(0, 86400))
            if ts <= found:
                events.append(new_event(timestamp(ts), "act:partner-api-key-7", "api_call",
                                        "ds:marketing-leads", "sys:crm", "ext:unknown-host", 0,
                                        {"client_ip": "198.51.100.10"}))
    return events
