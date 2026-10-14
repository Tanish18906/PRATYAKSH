"""Plant incident paths alongside the company's standing exports."""

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


def standing_exports(base: BaseTable, seed: int, found_ts: str, rng,
                     nights_back: int, fixed: bool = False, extra: bool = False) -> dict:
    found_day = seconds(found_ts) // 86400 * 86400
    origin_day = found_day - nights_back * 86400
    nightly_times = [timestamp(day + 2 * 3600 + 10 * 60)
                     for day in range(origin_day, found_day + 1, 86400)]
    contractor_ts = "2026-10-02T11:00:00Z" if fixed else timestamp(found_day - 10 * 86400 + 11 * 3600)
    marketing_ts = "2026-10-06T09:30:00Z" if fixed else timestamp(found_day - 6 * 86400 + 9 * 3600 + 30 * 60)

    recipes = [("nightly", ts) for ts in nightly_times]
    recipes.insert(1, ("contractor", contractor_ts))
    recipes.insert(2, ("marketing", marketing_ts))
    ids = list(range(1, len(recipes) + 1)) if fixed else list(
        seeded_rng("ids", seed).permutation(np.arange(1, len(recipes) + 1 + int(extra))))

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

    return {"artifacts": artifacts, "events": events, "origin_indices": origin_indices,
            "origin_id": origin_id, "origin_event": origin_event,
            "extra_id": f"art:E{ids[-1]}" if extra else None, "origin_day": origin_day}


def plant_a1(base: BaseTable, company: dict, seed: int, scale: str,
             found_ts: str, rng, forced_actor: str | None = None) -> dict:
    fixed = seed == 42 and scale == "demo" and forced_actor is None
    nights_back = 3 if fixed else int(rng.choice((2, 3)))
    planted = standing_exports(base, seed, found_ts, rng, nights_back, fixed)
    artifacts, events = planted["artifacts"], planted["events"]
    origin_indices = planted["origin_indices"]
    origin_event, origin_id = planted["origin_event"], planted["origin_id"]
    origin_day = planted["origin_day"]
    if fixed:
        insider = "act:ravi-menon"
        download_ts = "2026-10-09T21:40:00Z"
        upload_ts = "2026-10-10T22:00:00Z"
    else:
        eligible = [actor["id"] for actor in company["actors"]
                    if actor["role"] in ("analyst", "bi-admin", "engineer")]
        insider = forced_actor or eligible[int(rng.integers(len(eligible)))]
        download_ts = timestamp(origin_day +
                                int(rng.integers(17, 24)) * 3600 + int(rng.integers(0, 3600)))
        upload_ts = timestamp(seconds(download_ts) + int(rng.integers(12, 31)) * 3600)
    endpoint = "ep:" + insider[4:]
    critical = new_event(download_ts, insider, "download", origin_id,
                         "sys:bi-warehouse", endpoint, len(origin_indices))
    events.append(critical)
    if forced_actor and "sys:bi-warehouse" not in next(
            actor["access"] for actor in company["actors"] if actor["id"] == forced_actor):
        grant_ts = timestamp(origin_day - int(rng.integers(1, 4)) * 86400 + 12 * 3600)
        events.append(new_event(grant_ts, "act:meena-iyer", "permission_change", None,
                                None, None, 0, {"grantee": forced_actor,
                                               "scope": "sys:bi-warehouse", "change": "grant"},
                                "src:bi-warehouse"))
    if fixed:
        miss_times = ("2026-10-09T09:15:00Z", "2026-10-09T10:30:00Z")
    else:
        morning = origin_day
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
            "insider": insider, "endpoint": endpoint, "upload_ts": upload_ts,
            "path": [("sys:customer-db", "sys:bi-warehouse", "act:etl-nightly", origin_event),
                     ("sys:bi-warehouse", endpoint, insider, critical),
                     (endpoint, "ext:telegram-leak-channel", insider, None)]}


def plant_a2(base: BaseTable, company: dict, seed: int, found_ts: str, rng,
             forced_actor: str | None = None) -> dict:
    planted = standing_exports(base, seed, found_ts, rng, int(rng.choice((1, 2))))
    origin_event, origin_id = planted["origin_event"], planted["origin_id"]
    actor = forced_actor or "act:partner-api-key-7"
    api_ts = timestamp(planted["origin_day"] + int(rng.integers(3, 6)) * 3600)
    critical = new_event(api_ts, actor, "api_call", origin_id, "sys:bi-warehouse",
                         "ext:unknown-host", len(planted["origin_indices"]),
                         {"client_ip": f"203.0.113.{int(rng.integers(1, 255))}"})
    planted["events"].append(critical)
    planted["events"].append(new_event(timestamp(planted["origin_day"] + 9 * 3600),
                                       "act:meena-iyer", "read", origin_id,
                                       "sys:bi-warehouse", None, 50))
    planted.update(critical=critical, insider=actor,
                   upload_ts=timestamp(seconds(api_ts) + int(rng.integers(12, 21)) * 3600),
                   path=[("sys:customer-db", "sys:bi-warehouse", "act:etl-nightly", origin_event),
                         ("sys:bi-warehouse", "ext:unknown-host", actor, critical),
                         ("ext:unknown-host", "ext:telegram-leak-channel", actor, None)])
    return planted


def plant_a3(base: BaseTable, company: dict, seed: int, found_ts: str, rng,
             forced_actor: str | None = None) -> dict:
    planted = standing_exports(base, seed, found_ts, rng, 2, extra=True)
    found_day = seconds(found_ts) // 86400 * 86400
    actor = forced_actor or "act:kavya-rao"
    export_ts = timestamp(found_day - 86400 + 11 * 3600)
    grant_ts = timestamp(seconds(export_ts) - 3 * 86400)
    indices = nightly_indices(base, export_ts)
    columns = ["full_name", "email", "phone", "city", "created_at"]
    artifact = make_artifact(base, planted["extra_id"], "ds:customers", actor,
                             export_ts, "sys:partner-sftp", indices, columns,
                             "MARKETING", "state = 'CG' AND created_at >= '2025-01-01'")
    planted["artifacts"].append(artifact)
    grant = new_event(grant_ts, "act:meena-iyer", "permission_change", None,
                      None, None, 0, {"grantee": actor, "scope": "sys:customer-db",
                                     "change": "grant"}, "src:customer-db")
    export = new_event(export_ts, actor, "export", "ds:customers", "sys:customer-db",
                       "sys:partner-sftp", len(indices), {"artifact_id": artifact["id"],
                                                          "columns": columns})
    send_ts = timestamp(seconds(export_ts) + 6 * 3600)
    critical = new_event(send_ts, actor, "send", artifact["id"], "sys:partner-sftp",
                         "ext:vendor-nimbus", len(indices))
    other_marketer = next(user["id"] for user in company["actors"]
                          if user["role"] == "marketing" and user["id"] != actor)
    near_miss = new_event(timestamp(seconds(export_ts) + 3600), other_marketer, "read",
                          artifact["id"], "sys:partner-sftp", None, 50)
    planted["events"].extend((grant, export, near_miss, critical))
    planted.update(origin_indices=indices, origin_id=artifact["id"], origin_event=export,
                   critical=critical, insider=actor,
                   upload_ts=timestamp(seconds(send_ts) + 12 * 3600),
                   path=[("sys:customer-db", "sys:partner-sftp", actor, export),
                         ("sys:partner-sftp", "ext:vendor-nimbus", actor, critical),
                         ("ext:vendor-nimbus", "ext:telegram-leak-channel", actor, None)])
    return planted


def plant_a4(base: BaseTable, company: dict, seed: int, found_ts: str, rng) -> dict:
    planted = standing_exports(base, seed, found_ts, rng, 2)
    origin_event, origin_id = planted["origin_event"], planted["origin_id"]
    engineer_ids = [actor["id"] for actor in company["actors"] if actor["role"] == "engineer"]
    actor = engineer_ids[int(rng.integers(len(engineer_ids)))]
    copy_ts = timestamp(planted["origin_day"] + 86400 + 10 * 3600)
    copy = new_event(copy_ts, actor, "copy", origin_id, "sys:bi-warehouse",
                     "sys:object-store", len(planted["origin_indices"]))
    grant_ts = timestamp(seconds(copy_ts) + 3600)
    critical = new_event(grant_ts, actor, "permission_change", None, None, None, 0,
                         {"grantee": "act:anonymous", "scope": "sys:object-store",
                          "change": "grant"}, "src:object-store")
    near_miss = new_event(timestamp(planted["origin_day"] + 9 * 3600),
                          "act:meena-iyer", "read", origin_id,
                          "sys:bi-warehouse", None, 50)
    planted["events"].extend((copy, critical, near_miss))
    planted.update(critical=critical, insider=actor,
                   upload_ts=timestamp(seconds(grant_ts) + 12 * 3600),
                   path=[("sys:customer-db", "sys:bi-warehouse", "act:etl-nightly", origin_event),
                         ("sys:bi-warehouse", "sys:object-store", actor, copy),
                         ("sys:object-store", "ext:telegram-leak-channel", actor, None)])
    return planted


def plant_a5(base: BaseTable, company: dict, seed: int, found_ts: str, rng) -> dict:
    planted = standing_exports(base, seed, found_ts, rng, 2, extra=True)
    found_day = seconds(found_ts) // 86400 * 86400
    copy_ts = timestamp(found_day - 86400 + 3 * 3600 + 10 * 60)
    indices = np.flatnonzero(base.created <= seconds(copy_ts))
    artifact = make_artifact(base, planted["extra_id"], "ds:customers", "act:backup-svc",
                             copy_ts, "sys:object-store", indices,
                             list(CUSTOMER_COLUMNS), "ETL", "full backup snapshot")
    planted["artifacts"].append(artifact)
    copy = new_event(copy_ts, "act:backup-svc", "copy", "ds:customers",
                     "sys:customer-db", "sys:object-store", len(indices),
                     {"artifact_id": artifact["id"]})
    readers = [actor["id"] for actor in company["actors"] if actor["role"] == "engineer"][:2]
    reader, other_reader = readers
    read_ts = seconds(copy_ts) + 2 * 3600
    reads = [new_event(timestamp(read_ts), actor, "read", artifact["id"],
                       "sys:object-store", None, 50) for actor in (reader, other_reader)]
    download_ts = timestamp(read_ts + 3600)
    endpoint = "ep:" + reader[4:]
    critical = new_event(download_ts, reader, "download", artifact["id"],
                         "sys:object-store", endpoint, len(indices))
    planted["events"].extend((copy, *reads, critical))
    planted.update(origin_indices=indices, origin_id=artifact["id"], origin_event=copy,
                   critical=critical, insider=reader,
                   true_actors=["act:backup-svc", reader],
                   upload_ts=timestamp(seconds(download_ts) + 12 * 3600),
                   path=[("sys:customer-db", "sys:object-store", "act:backup-svc", copy),
                         ("sys:object-store", endpoint, reader, critical),
                         (endpoint, "ext:telegram-leak-channel", reader, None)])
    return planted
