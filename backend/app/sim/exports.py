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
