"""Stage 4: event and actor anomaly (docs/03_ENGINE.md section 8)."""
import math
from collections import defaultdict
from statistics import mean, pstdev

from app.config import ENGINE as CFG
from app.engine.normalize import parse_ts, shift_days


class Anomaly:
    def __init__(self, idx):
        self.idx = idx
        self._cache = {}
        self._by_role = defaultdict(list)
        for e in idx.events:
            if e["rows"] > 0:
                self._by_role[self._role(e["actor"])].append(e)
        self._grants = [e for e in idx.events
                        if e["action"] == "permission_change" and e["meta"].get("change") == "grant"]

    def _role(self, actor):
        return self.idx.actor.get(actor, {}).get("role")

    def event(self, e: dict) -> dict:
        """Anomaly of one observed event: {score, z, off, first, priv, mu, sigma, n_baseline}."""
        if e["id"] in self._cache:
            return self._cache[e["id"]]
        lo = shift_days(e["ts"], -CFG["BASELINE_DAYS"])

        def window(events, same_actor):
            return [x for x in events if x["rows"] > 0 and lo <= x["ts"] < e["ts"] and x["id"] != e["id"]
                    and (x["actor"] == e["actor"]) == same_actor]

        base = window(self.idx.events_by_actor[e["actor"]], True)
        if len(base) < CFG["BASELINE_MIN_EVENTS"]:
            base = window(self._by_role[self._role(e["actor"])], False)
        if len(base) < CFG["BASELINE_MIN_EVENTS"]:
            mu, sigma, n = CFG["DEFAULT_MU"], CFG["DEFAULT_SIGMA"], 0
        else:
            xs = [math.log(1 + x["rows"]) for x in base]
            mu, sigma, n = mean(xs), max(pstdev(xs), CFG["SIGMA_FLOOR"]), len(xs)
        z = min(max((math.log(1 + e["rows"]) - mu) / sigma, 0.0), CFG["Z_CAP"])
        t = parse_ts(e["ts"])
        is_user = self.idx.actor.get(e["actor"], {}).get("kind") == "user"
        off = int(is_user and (t.hour >= 22 or t.hour < 5 or t.weekday() >= 5))
        first = int(not any(x["id"] != e["id"] and x["action"] == e["action"] and x["from_loc"] == e["from_loc"]
                            and lo <= x["ts"] < e["ts"] for x in self.idx.events_by_actor[e["actor"]]))
        glo = shift_days(e["ts"], -CFG["PRIV_WINDOW_DAYS"])
        priv = int(any(g["meta"].get("grantee") == e["actor"] and glo <= g["ts"] < e["ts"]
                       and g["meta"].get("scope") in (e["from_loc"], None) for g in self._grants))
        out = {"score": z + CFG["OFF_HOURS_W"] * off + CFG["FIRST_TIME_W"] * first + CFG["PRIV_W"] * priv,
               "z": z, "off": off, "first": first, "priv": priv, "mu": mu, "sigma": sigma, "n_baseline": n}
        self._cache[e["id"]] = out
        return out

    def actor_on_path(self, actor: str, art: dict, found_ts: str, locs: set):
        """Highest-scoring event (event, info) by `actor` touching the path's locations, or None."""
        best = None
        for e in self.idx.events_by_actor[actor]:
            if (e["rows"] > 0 and art["created_ts"] <= e["ts"] <= found_ts
                    and (e["from_loc"] in locs or e["to_loc"] in locs)):
                info = self.event(e)
                if best is None or info["score"] > best[1]["score"]:
                    best = (e, info)
        return best
