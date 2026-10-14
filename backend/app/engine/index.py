"""Lookup tables built once from the public scenario (docs/03_ENGINE.md section 4)."""
from collections import defaultdict

MOVE_ACTIONS = {"copy", "download", "upload", "send", "api_call"}


class Index:
    def __init__(self, sc: dict):
        self.loc = {x["id"]: x for x in sc["locations"]}
        self.actor = {x["id"]: x for x in sc["actors"]}
        self.artifact = {x["id"]: x for x in sc["artifacts"]}
        self.dataset = {x["id"]: x for x in sc["datasets"]}
        self.src_to_loc = {x["id"]: x["location"] for x in sc["log_sources"]}
        self.events = sorted(sc["events"], key=lambda e: (e["ts"], e["seq"], e["id"]))
        self.events_by_actor = defaultdict(list)
        self.events_by_object = defaultdict(list)
        self.moves_by_artifact = defaultdict(list)
        for e in self.events:
            self.events_by_actor[e["actor"]].append(e)
            self.events_by_object[e["object"]].append(e)
            if e["action"] in MOVE_ACTIONS and e["to_loc"] is not None:
                self.moves_by_artifact[e["object"]].append(e)
        self.owner_endpoint = {
            x["owner_actor"]: x["id"] for x in sc["locations"]
            if x["kind"] == "endpoint" and x["owner_actor"]
        }

    def name(self, ident: str) -> str:
        """Display name for an actor or location id."""
        return (self.actor.get(ident) or self.loc.get(ident) or {}).get("name", ident)
