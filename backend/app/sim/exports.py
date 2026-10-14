"""Export artifacts built from the cached synthetic base table."""

import numpy as np

from .base_table import BaseTable, seconds, timestamp
from .styles import format_profile


def nightly_indices(base: BaseTable, created_ts: str) -> np.ndarray:
    return np.flatnonzero((base.created <= seconds(created_ts)) &
                           (base.created >= seconds("2025-01-01T00:00:00Z")) &
                           (base.states == 0))


def make_artifact(base: BaseTable, artifact_id: str, dataset: str, created_by: str,
                  created_ts: str, location: str, indices: np.ndarray, columns: list[str],
                  style: str, filter_desc: str) -> dict:
    if len(indices) == 0:
        raise ValueError("an export must contain at least one row")
    since = seconds(created_ts) - 30 * 86400
    recent = np.count_nonzero(base.created[indices] > since)
    identifiers = ("customer_id", "email", "phone", "policy_no")
    return {
        "id": artifact_id, "dataset": dataset, "created_by": created_by,
        "created_ts": created_ts, "location": location, "columns": list(columns),
        "row_count": int(len(indices)), "filter_desc": filter_desc,
        "format_profile": format_profile(style, columns),
        "sketches": {column: base.sketch(column, indices) for column in identifiers if column in columns},
        "newest_record_ts": timestamp(int(base.created[indices[-1]])),
        "arrivals_per_hour": round(int(recent) / 720, 4), "canary_ids": [],
    }


def plant_canaries(artifacts: list[dict], key: bytes) -> tuple[list[dict], dict[str, list[dict]]]:
    """Add three synthetic records per artifact and return private row data by artifact."""
    from app.common.sketch import h64, normalize

    registry = []
    rows_by_artifact = {}
    for artifact in artifacts:
        slug = artifact["id"].removeprefix("art:")
        number = int(slug.removeprefix("E"))
        rows = []
        for n in range(1, 4):
            canary_id = f"can:{slug}-{n}"
            row = {"customer_id": f"CAN{slug}{n}", "full_name": "Canary Record",
                   "email": f"canary.{slug.lower()}.{n}@example.net",
                   "phone": f"500{number:03d}{n:04d}", "policy_no": f"CAN-{slug}-{n}",
                   "dob": "1990-01-01", "city": "Raipur", "state": "CG",
                   "signup_date": artifact["newest_record_ts"][:10],
                   "created_at": artifact["newest_record_ts"], "premium_tier": "basic"}
            hashes = {column: f"{h64(key, normalize(column, row[column])):016x}"
                      for column in ("customer_id", "email", "phone", "policy_no")
                      if column in artifact["columns"]}
            registry.append({"id": canary_id, "export_id": artifact["id"], "hashes": hashes})
            artifact["canary_ids"].append(canary_id)
            rows.append({"id": canary_id, "values": row, "hashes": hashes})
        artifact["row_count"] += 3
        for column, sketch in artifact["sketches"].items():
            sketch["distinct"] += 3
            sketch["hashes"] = sorted(set(sketch["hashes"]) |
                                      {row["hashes"][column] for row in rows})[:sketch["k"]]
        rows_by_artifact[artifact["id"]] = rows
    return registry, rows_by_artifact
