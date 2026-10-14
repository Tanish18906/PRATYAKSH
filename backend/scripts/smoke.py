"""Smoke test against a running API: health, generate seed 42, trace. Prints PASS or FAIL, exit code 0 or 1.

    cd backend && uvicorn app.main:app --port 8000        # in one terminal
    python backend/scripts/smoke.py [http://127.0.0.1:8000]
"""
import json
import sys
import time
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")


def call(path, body=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def main() -> int:
    problems = []
    try:
        health = call("/api/health")
        if health.get("status") != "ok":
            problems.append(f"health: {health}")
        t = time.time()
        summary = call("/api/scenario/generate", {"archetype": "A1", "seed": 42, "log_loss": 0.4,
                                                  "canary_mode": False, "scale": "demo"})
        gen_s = time.time() - t
        t = time.time()
        trace = call("/api/trace", {"scenario_id": summary["id"]})
        trace_s = time.time() - t
        text = json.dumps(summary) + json.dumps(trace)
        if trace["origin_ranking"][0]["artifact_id"] != "art:E1":
            problems.append(f"origin is {trace['origin_ranking'][0]['artifact_id']}, expected art:E1")
        top = trace["hypotheses"][0]
        if "act:ravi-menon" not in top["actors"]:
            problems.append(f"top hypothesis actors {top['actors']} do not include act:ravi-menon")
        last = top["hops"][-1]
        if last["kind"] != "inferred":
            problems.append("final hop of the top hypothesis is not inferred")
        if trace_s >= 3.0:
            problems.append(f"trace took {trace_s:.2f}s (limit 3s)")
        if '"truth"' in text or "case_key" in text:
            problems.append("response contains truth or case_key")
        print(f"scenario {summary['id']}: generate {gen_s:.2f}s, trace {trace_s:.3f}s, origin "
              f"{trace['origin_ranking'][0]['artifact_id']} {trace['origin_ranking'][0]['probability']}, "
              f"top hypothesis {top['actors']} {top['probability']}")
    except Exception as exc:  # connection refused, HTTP error, missing key
        problems.append(f"{type(exc).__name__}: {exc}")
    for p in problems:
        print("  -", p)
    print("PASS" if not problems else "FAIL")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
