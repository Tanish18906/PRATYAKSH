"""Hand-written mini scenarios H1 to H8 (docs/04_TEST_PLAN.md sections 2 and 3).

Independent of the simulator: imports only app.common.sketch. `build(name)` returns a
PublicScenario dict; `python -m tests.fixtures.mini` (from backend/) writes H1.json to H8.json.
"""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.common.sketch import IDENTIFIER_COLUMNS, h64, make_sketch

NAMES = [f"H{i}" for i in range(1, 9)]
KEY = b"mini-test-key"
K = 512
BASE = datetime(2026, 9, 1, tzinfo=timezone.utc)
FOUND_TS = "2026-10-12T08:00:00Z"
LEAK_AT = "ext:telegram-leak-channel"
ART_COLUMNS = ["customer_id", "full_name", "email", "phone", "policy_no", "created_at"]
LEAK_COLUMNS = ["full_name", "phone", "policy_no", "created_at"]

STYLES = {
    "ETL": dict(delimiter=",", quoting="minimal", header_case="snake", line_ending="LF", encoding="utf-8",
                null_token="", phone="e164_dash", name="title"),
    "OTHER": dict(delimiter=";", quoting="all", header_case="title", line_ending="CRLF", encoding="utf-8-bom",
                  null_token="NULL", phone="digits10", name="upper"),
    "NOTEBOOK": dict(delimiter=",", quoting="minimal", header_case="camel", line_ending="LF", encoding="utf-8",
                     null_token="", phone="digits10", name="lower"),
}

# per-actor rows of the 12 background queries (the 6 values cycle twice)
BG_ROWS = {
    "ann": [150, 220, 310, 180, 260, 200],
    "bob": [90, 140, 120, 160, 110, 130],
    "cat": [60, 80, 50, 70, 90, 40],
}

LOCATIONS = [  # id, log_source, egress_capable, owner
    ("sys:db", "src:db", False, None), ("sys:wh", "src:wh", False, None),
    ("sys:sftp", "src:sftp", True, None), ("sys:bucket", "src:bucket", True, None),
    ("ep:ann", None, True, "act:ann"), ("ep:bob", None, True, "act:bob"), ("ep:cat", None, True, "act:cat"),
    (LEAK_AT, None, False, None), ("ext:vendor-x", None, False, None),
]
ACTORS = [  # id, kind, role, team, access
    ("act:ann", "user", "analyst", "analytics", ["sys:wh", "ep:ann"]),
    ("act:bob", "user", "analyst", "analytics", ["sys:wh", "sys:bucket", "ep:bob"]),
    ("act:cat", "user", "bi-admin", "bi", ["sys:wh", "sys:bucket", "ep:cat"]),
    ("act:etl", "service", "service", "platform", ["sys:db", "sys:wh", "sys:bucket"]),
    ("act:key1", "service", "service", "platform", ["sys:wh", "sys:sftp"]),
]


def fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def created_at(i):
    return fmt(BASE + timedelta(minutes=30 * i))


def ident(column, i):
    return {"customer_id": f"C{i:06d}", "email": f"u{i}@mini.test", "phone": f"9{i:09d}",
            "policy_no": f"MN-{i:06d}"}[column]


def format_profile(style):
    s = STYLES[style]
    return {
        "delimiter": s["delimiter"], "quoting": s["quoting"], "header_case": s["header_case"],
        "line_ending": s["line_ending"], "encoding": s["encoding"], "null_token": s["null_token"],
        "columns": {"phone": {"style": s["phone"]}, "full_name": {"case": s["name"]},
                    "created_at": {"style": "iso"}},
    }


def sketches(indices, columns):
    return {c: make_sketch(c, [ident(c, i) for i in indices], KEY, K)
            for c in IDENTIFIER_COLUMNS if c in columns}


def artifact(aid, by, ts, location, rows, style, canary_ids=()):
    idx = list(range(1, rows + 1)) if isinstance(rows, int) else list(rows)
    return {
        "id": aid, "dataset": "ds:cust", "created_by": by, "created_ts": ts, "location": location,
        "columns": list(ART_COLUMNS), "row_count": len(idx), "filter_desc": "all rows",
        "format_profile": format_profile(style), "sketches": sketches(idx, ART_COLUMNS),
        "newest_record_ts": created_at(max(idx)), "arrivals_per_hour": 2.0,
        "canary_ids": list(canary_ids),
    }


def leak(indices, style, canary_hits=(), newest=None):
    idx = list(indices)
    return {
        "id": "", "found_at": LEAK_AT, "found_ts": FOUND_TS, "file_name": "mini_leak.csv",
        "columns": list(LEAK_COLUMNS), "row_count": len(idx), "format_profile": format_profile(style),
        "sketches": sketches(idx, LEAK_COLUMNS), "newest_record_ts": newest or created_at(max(idx)),
        "masked_preview": [], "canary_hits": list(canary_hits),
    }


def export_event(a):
    return dict(action="export", actor=a["created_by"], ts=a["created_ts"], object="ds:cust",
                from_loc="sys:db", to_loc=a["location"], rows=a["row_count"], artifact=a["id"])


def move(action, actor, ts, art, frm, to, rows):
    return dict(action=action, actor=actor, ts=ts, object=art, from_loc=frm, to_loc=to, rows=rows, artifact=art)


def query(actor, ts, rows):
    return dict(action="query", actor=actor, ts=ts, object="ds:cust", from_loc="sys:wh", to_loc=None, rows=rows)


def background():
    out = []
    for n in range(12):
        t = fmt(datetime(2026, 9, 14, 10, tzinfo=timezone.utc) + timedelta(days=2 * n))
        for who in ("ann", "bob", "cat"):
            out.append(query(f"act:{who}", t, BG_ROWS[who][n % 6]))
    return out


def assemble(name, artifacts, extra_events, lk, canaries=()):
    log_src = {loc: src for loc, src, _, _ in LOCATIONS}
    events, seq = [], {}
    for e in sorted(background() + extra_events, key=lambda e: e["ts"]):  # stable: ties keep insertion order
        src = log_src[e["from_loc"]]
        seq[src] = seq.get(src, 0) + 1
        meta = {"artifact_id": e["artifact"]} if "artifact" in e else {}
        events.append({
            "id": f"evt:{len(events) + 1:06d}", "ts": e["ts"], "seq": seq[src], "source": src,
            "actor": e["actor"], "action": e["action"], "object": e["object"], "from_loc": e["from_loc"],
            "to_loc": e["to_loc"], "rows": e["rows"], "meta": meta,
        })
    registry = [{"id": cid, "export_id": a["id"],
                 "hashes": {c: f"{h64(KEY, f'canary:{cid}:{c}'):016x}" for c in IDENTIFIER_COLUMNS}}
                for a in artifacts for cid in a["canary_ids"]] if canaries else []
    lk["id"] = f"leak:{name}"
    return {
        "contract_version": "1.0", "id": f"scn:{name}", "archetype": "A1", "seed": 0,
        "params": {"log_loss": 0.0, "canary_mode": bool(canaries), "scale": "demo"},
        "company": "Mini Co", "now_ts": FOUND_TS,
        "locations": [{"id": i, "kind": {"sys": "system", "ep:": "endpoint", "ext": "external"}[i[:3]],
                       "name": i.split(":")[1],
                       "owner_actor": own, "monitored": src is not None, "log_source": src,
                       "egress_capable": eg} for i, src, eg, own in LOCATIONS],
        "log_sources": [{"id": src, "name": f"{loc.split(':')[1]}-audit", "location": loc}
                        for loc, src, _, _ in LOCATIONS if src],
        "actors": [{"id": i, "kind": k, "name": i.split(":")[1].capitalize(), "role": r, "team": t,
                    "access": acc} for i, k, r, t, acc in ACTORS],
        "datasets": [{"id": "ds:cust", "name": "customers", "system": "sys:db", "columns": list(ART_COLUMNS),
                      "identifier_columns": list(IDENTIFIER_COLUMNS), "row_count": 2000,
                      "sensitivity": "high", "arrivals_per_hour": 2.0}],
        "events": events, "artifacts": artifacts, "canary_registry": registry, "leak_sample": lk,
        "discovery": {
            "platform": "telegram-mock",
            "channel": {"name": "Mini Leak Channel", "handle": "@mini_leaks", "members": 1200},
            "messages": [{"id": 1, "ts": FOUND_TS, "sender": "@mini_dump", "text": "fresh dump",
                          "attachment": {"file_name": lk["file_name"], "size_bytes": lk["row_count"] * 60,
                                         "rows_hint": lk["row_count"]}}],
            "leak_message_id": 1,
        },
    }


E1_TS, E2_TS = "2026-10-09T02:10:00Z", "2026-10-09T02:40:00Z"
ANN_DL = "2026-10-09T09:00:00Z"


def _exports(*arts):
    return [export_event(a) for a in arts]


def _h1():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL")
    e2 = artifact("art:E2", "act:cat", E2_TS, "sys:wh", 1829, "OTHER")
    ev = _exports(e1, e2) + [move("download", "act:ann", ANN_DL, "art:E1", "sys:wh", "ep:ann", 1828)]
    return assemble("H1", [e1, e2], ev, leak(range(1, 1829), "ETL"))


def _h2():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL")
    ev = _exports(e1) + [
        move("copy", "act:etl", "2026-10-09T02:20:00Z", "art:E1", "sys:wh", "sys:bucket", 1828),
        move("download", "act:bob", "2026-10-09T10:00:00Z", "art:E1", "sys:bucket", "ep:bob", 1828),
        move("download", "act:cat", "2026-10-09T10:05:00Z", "art:E1", "sys:bucket", "ep:cat", 1828),
    ]
    return assemble("H2", [e1], ev, leak(range(1, 1829), "ETL"))


def _h3():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL")
    e2 = artifact("art:E2", "act:cat", "2026-09-22T02:10:00Z", "sys:wh", 1012, "ETL")
    ev = _exports(e1, e2) + [move("download", "act:ann", ANN_DL, "art:E1", "sys:wh", "ep:ann", 1828)]
    return assemble("H3", [e1, e2], ev, leak(range(1, 1829), "NOTEBOOK"))


def _h4():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL")
    e5 = artifact("art:E5", "act:etl", "2026-10-10T02:10:00Z", "sys:wh", 1876, "ETL")
    ev = _exports(e1, e5) + [move("download", "act:ann", ANN_DL, "art:E1", "sys:wh", "ep:ann", 1828)]
    return assemble("H4", [e1, e5], ev, leak(range(10, 1821, 10), "ETL"))


def _h5():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL")
    ev = _exports(e1) + [query("act:ann", "2026-10-09T09:00:00Z", 20000),
                         query("act:bob", "2026-10-09T09:10:00Z", 20000)]
    return assemble("H5", [e1], ev, leak(range(1, 1829), "ETL"))


def _h6():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL", ["can:E1-1"])
    e2 = artifact("art:E2", "act:cat", E2_TS, "sys:wh", 1829, "ETL", ["can:E2-1"])
    ev = _exports(e1, e2) + [
        move("download", "act:ann", ANN_DL, "art:E1", "sys:wh", "ep:ann", 1828),
        move("download", "act:bob", "2026-10-09T09:05:00Z", "art:E2", "sys:wh", "ep:bob", 1829),
    ]
    return assemble("H6", [e1, e2], ev, leak(range(1, 1829), "ETL", ["can:E2-1"]), canaries=True)


def _h7():
    e1 = artifact("art:E1", "act:etl", E1_TS, "sys:wh", 1828, "ETL")
    e2 = artifact("art:E2", "act:cat", "2026-09-22T02:10:00Z", "sys:wh", 1012, "ETL")
    lk = leak(range(5001, 5401), "ETL", newest="2026-10-01T00:00:00Z")
    return assemble("H7", [e1, e2], _exports(e1, e2), lk)


def _h8():
    ren = {"art:E1": "art:E7", "art:E2": "art:E3"}

    def sub(o):
        if isinstance(o, dict):
            return {k: sub(v) for k, v in o.items()}
        if isinstance(o, list):
            return [sub(v) for v in o]
        return ren.get(o, o) if isinstance(o, str) else o

    sc = sub(copy.deepcopy(_h1()))
    sc["id"], sc["leak_sample"]["id"] = "scn:H8", "leak:H8"
    return sc


_BUILDERS = {"H1": _h1, "H2": _h2, "H3": _h3, "H4": _h4, "H5": _h5, "H6": _h6, "H7": _h7, "H8": _h8}


def build(name: str) -> dict:
    return _BUILDERS[name]()


def write_all(outdir=None):
    out = Path(outdir) if outdir else Path(__file__).resolve().parent
    for n in NAMES:
        (out / f"{n}.json").write_text(json.dumps(build(n), indent=2) + "\n")


if __name__ == "__main__":
    write_all()
