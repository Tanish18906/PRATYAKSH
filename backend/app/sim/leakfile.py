"""Leak sample derivation and on-demand private row rendering."""

from dataclasses import dataclass, field

import numpy as np

from .base_table import BaseTable, case_key, seeded_rng, timestamp
from .styles import format_profile, render_value


@dataclass(slots=True)
class PrivateStore:
    base: BaseTable
    indices: np.ndarray
    columns: list[str]
    style: str
    case_key: bytes
    canary_rows: list[dict] = field(default_factory=list)


def mask_value(column: str, value: str) -> str:
    if not value:
        return value
    if column == "email":
        local, _, domain = value.partition("@")
        return f"{local[:1]}***@{domain}" if local and domain else "*" * len(value)
    if column == "phone":
        return value[:6] + "*" * (len(value) - 8) + value[-2:] if len(value) > 8 else "*" * len(value)
    if column == "full_name":
        return " ".join(f"{part[0]}." for part in value.split())
    if column == "policy_no":
        return value[:2] + "*" * (len(value) - 4) + value[-2:] if len(value) > 4 else "*" * len(value)
    if column == "customer_id":
        return "*" * (len(value) - 3) + value[-3:] if len(value) > 3 else "*" * len(value)
    if column == "dob":
        return value[:4] + "-**-**" if len(value) >= 4 else "*" * len(value)
    if column == "created_at":
        return value
    return "***"


def render_leak_row(private: PrivateStore, row_index: int) -> dict:
    if not 0 <= row_index < len(private.indices) + len(private.canary_rows):
        raise IndexError("leak row index out of range")
    row = (private.base.row(int(private.indices[row_index])) if row_index < len(private.indices)
           else private.canary_rows[row_index - len(private.indices)])
    return {column: render_value(column, row[column], private.style, row_index)
            for column in private.columns}


def make_leak(base: BaseTable, origin_indices: np.ndarray, seed: int, scale: str,
              found_ts: str, archetype: str = "A1",
              origin_canaries: list[dict] | None = None,
              origin_style: str = "ETL",
              origin_columns: list[str] | None = None) -> tuple[dict, PrivateStore]:
    rng = seeded_rng("leak", seed)
    fixed = archetype == "A1" and seed == 42 and scale == "demo"
    ratio = 0.986 if fixed else float(rng.choice((1.0, 0.98, 0.5, 0.1), p=(0.6, 0.15, 0.15, 0.1)))
    count = max(5, round(len(origin_indices) * ratio))
    if count >= len(origin_indices):
        indices = origin_indices.copy()
    else:
        indices = np.sort(np.concatenate((rng.choice(origin_indices[:-5], size=count - 5,
                                                     replace=False), origin_indices[-5:])))
    if fixed:
        columns = ["full_name", "phone", "policy_no", "created_at"]
        style = "ETL"
        file_name = "nova_customers_cg.csv"
    else:
        possibilities = [column for column in
                         ("customer_id", "full_name", "email", "phone", "policy_no", "city", "created_at")
                         if origin_columns is None or column in origin_columns]
        chosen = set(rng.choice(possibilities[:-1],
                                size=int(rng.integers(2, min(6, len(possibilities)))),
                                replace=False))
        if not chosen.intersection(("customer_id", "email", "phone", "policy_no")):
            chosen.add(next(column for column in ("customer_id", "email", "phone", "policy_no")
                            if column in possibilities))
        chosen.add("created_at")
        columns = [column for column in possibilities if column in chosen]
        style = "NOTEBOOK" if rng.random() < 0.25 else origin_style
        file_name = f"nova_customers_{seed}.csv"
    selected_canaries = [canary for canary in origin_canaries or []
                         if ratio == 1.0 or rng.random() < 0.9]
    private = PrivateStore(base, indices, columns, style, case_key(scale),
                           [canary["values"] for canary in selected_canaries])
    preview = [{column: mask_value(column, value) for column, value in render_leak_row(private, i).items()}
               for i in range(min(5, len(indices)))]
    sketches = {column: base.sketch(column, indices) for column in
                ("customer_id", "email", "phone", "policy_no") if column in columns}
    for column, sketch in sketches.items():
        sketch["distinct"] += len(selected_canaries)
        sketch["hashes"] = sorted(set(sketch["hashes"]) |
                                  {canary["hashes"][column] for canary in selected_canaries})[:sketch["k"]]
    hits = []
    if selected_canaries:
        from app.common.sketch import h64, normalize
        for canary in selected_canaries:
            if any(f"{h64(private.case_key, normalize(column, canary['values'][column])):016x}" ==
                   canary["hashes"][column] for column in sketches):
                hits.append(canary["id"])
    leak = {
        "id": f"leak:{archetype}-{seed}", "found_at": "ext:telegram-leak-channel",
        "found_ts": found_ts, "file_name": file_name, "columns": columns,
        "row_count": int(len(indices) + len(selected_canaries)),
        "format_profile": format_profile(style, columns), "sketches": sketches,
        "newest_record_ts": timestamp(int(base.created[indices[-1]])),
        "masked_preview": preview, "canary_hits": hits,
    }
    return leak, private
