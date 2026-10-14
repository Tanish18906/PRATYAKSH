"""A1 insider scenario planting; later archetypes are separate phase work."""

import numpy as np

from .base_table import BaseTable, seconds, seeded_rng, timestamp
from .company import CUSTOMER_COLUMNS
from .exports import make_artifact, nightly_indices
from .lossy import new_event


def a1_times(seed: int, scale: str):
    rng = seeded_rng("archetype", seed)
    if seed == 42 and scale == "demo":
        return "2026-10-12T08:30:00Z", rng
    offset = int(rng.integers(0, 11)) * 86400 + int(rng.integers(0, 601)) * 60
    return timestamp(seconds("2026-10-12T08:30:00Z") + offset), rng


def plant_a1(base: BaseTable, company: dict, seed: int, scale: str,
             found_ts: str, rng) -> dict:
    fixed = seed == 42 and scale == "demo"
    found_day = seconds(found_ts) // 86400 * 86400
    nights_back = 3 if fixed else int(rng.choice((2, 3)))
    origin_day = found_day - nights_back * 86400
    nightly_times = [timestamp(day + 2 * 3600 + 10 * 60)
                     for day in range(origin_day, found_day + 1, 86400)]
    contractor_ts = "2026-10-02T11:00:00Z" if fixed else timestamp(found_day - 10 * 86400 + 11 * 3600)
    marketing_ts = "2026-10-06T09:30:00Z" if fixed else timestamp(found_day - 6 * 86400 + 9 * 3600 + 30 * 60)

    recipes = [("nightly", ts) for ts in nightly_times]
    recipes.insert(1, ("contractor", contractor_ts))
    recipes.insert(2, ("marketing", marketing_ts))
    ids = list(range(1, len(recipes) + 1)) if fixed else list(
        seeded_rng("ids", seed).permutation(np.arange(1, len(recipes) + 1)))

    artifacts = []
    events = []
    origin_indices = None
    origin_event = None
    origin_id = None
    for position, (kind, created_ts) in enumerate(recipes):
        artifact_id = f"art:E{ids[position]}"
        if kind == "nightly":
            indices = nightly_indices(base, created_ts)
            dataset, actor, location = "ds:customers", "act:etl-nightly", "sys:bi-warehouse"
            columns, style = list(CUSTOMER_COLUMNS), "ETL"
            filter_desc = "state = 'CG' AND created_at >= '2025-01-01'"
            from_loc = "sys:customer-db"
        elif kind == "contractor":
            indices = np.flatnonzero(base.created <= seconds(created_ts))
            dataset, actor, location = "ds:customers", "act:arjun-das", "sys:notebook-server"
            columns, style = list(CUSTOMER_COLUMNS), "CONTRACTOR"
            filter_desc = "all customers at export time"
            from_loc = "sys:customer-db"
        else:
            eligible = np.flatnonzero(base.created <= seconds(created_ts))
            rng_marketing = seeded_rng("marketing", seed)
            indices = np.sort(rng_marketing.choice(eligible, size=round(len(eligible) * 0.2), replace=False))
            dataset, actor, location = "ds:marketing-leads", "act:kavya-rao", "sys:crm"
            columns, style = ["full_name", "email", "city"], "MARKETING"
            filter_desc = "seeded 20 percent marketing sample"
            from_loc = "sys:crm"
        artifact = make_artifact(base, artifact_id, dataset, actor, created_ts, location,
                                 indices, columns, style, filter_desc)
        artifacts.append(artifact)
        export_event = new_event(created_ts, actor, "export", dataset, from_loc, location,
                                 artifact["row_count"], {"artifact_id": artifact_id,
                                                         "filter": filter_desc, "columns": columns})
        events.append(export_event)
        if position == 0:
            origin_indices, origin_event, origin_id = indices, export_event, artifact_id

    if fixed:
        insider = "act:ravi-menon"
        download_ts = "2026-10-09T21:40:00Z"
        upload_ts = "2026-10-10T22:00:00Z"
    else:
        eligible = [actor["id"] for actor in company["actors"]
                    if actor["role"] in ("analyst", "bi-admin", "engineer")]
        insider = eligible[int(rng.integers(len(eligible)))]
        download_ts = timestamp(seconds(nightly_times[0]) // 86400 * 86400 +
                                int(rng.integers(17, 24)) * 3600 + int(rng.integers(0, 3600)))
        upload_ts = timestamp(seconds(download_ts) + int(rng.integers(12, 31)) * 3600)
    endpoint = "ep:" + insider[4:]
    critical = new_event(download_ts, insider, "download", origin_id,
                         "sys:bi-warehouse", endpoint, len(origin_indices))
    events.append(critical)
    if fixed:
        miss_times = ("2026-10-09T09:15:00Z", "2026-10-09T10:30:00Z")
    else:
        morning = seconds(nightly_times[0]) // 86400 * 86400
        miss_times = (timestamp(morning + 9 * 3600 + 15 * 60),
                      timestamp(morning + 10 * 3600 + 30 * 60))
    innocent_admin = "act:meena-iyer" if insider != "act:meena-iyer" else next(
        actor["id"] for actor in company["actors"] if actor["role"] == "bi-admin" and actor["id"] != insider)
    events.append(new_event(miss_times[0], innocent_admin, "read", origin_id,
                            "sys:bi-warehouse", None, 50))
    events.append(new_event(miss_times[1], "act:partner-api-key-7", "api_call", origin_id,
                            "sys:bi-warehouse", "ext:unknown-host", 0,
                            {"client_ip": "198.51.100.10", "note": "list only"}))
    return {"artifacts": artifacts, "events": events, "origin_indices": origin_indices,
            "origin_id": origin_id, "origin_event": origin_event, "critical": critical,
            "insider": insider, "endpoint": endpoint, "upload_ts": upload_ts}
