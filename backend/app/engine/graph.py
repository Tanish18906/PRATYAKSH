"""TraceResult.graph builder (docs/03_ENGINE.md section 12)."""


def build_graph(idx, hyps: list) -> dict:
    nodes, edges = {}, {}

    def node(ident, kind, label):
        nodes.setdefault(ident, {"id": ident, "kind": kind, "label": label})

    def edge(key, eid, frm, to, kind, ts, event_id, label, path_id):
        e = edges.setdefault(key, {"id": eid, "from": frm, "to": to, "kind": kind, "ts": ts,
                                   "event_id": event_id, "path_ids": [], "label": label})
        if path_id not in e["path_ids"]:
            e["path_ids"].append(path_id)

    def loc_node(loc_id):
        L = idx.loc[loc_id]
        node(loc_id, L["kind"], L["name"])

    for h in hyps:
        art = idx.artifact[h["origin_artifact"]]
        node(art["id"], "artifact", art["id"])
        loc_node(art["location"])
        edge(("origin", art["id"]), f"e:{art['id']}>{art['location']}:observed:origin", art["id"],
             art["location"], "observed", art["created_ts"], None, f"created by {idx.name(art['created_by'])}",
             h["path_id"])
        for hop in h["hops"]:
            loc_node(hop["from_loc"])
            loc_node(hop["to_loc"])
            who = idx.name(hop["actor"])
            if hop["kind"] == "observed":
                label = f"{who}: {hop['action']}, {hop['rows']} rows"
                tag = hop["event_id"]
            else:
                src = idx.loc[hop["from_loc"]]["log_source"]
                if hop["est_loss"] is None or src is None:
                    label = f"{who}: unlogged channel"
                else:
                    label = (f"{who}: log missing (about {round(hop['est_loss'] * 100)}% of "
                             f"{idx.src_name[src]} logs lost)")
                tag = f"hid:{hop['actor']}"
            key = (hop["from_loc"], hop["to_loc"], hop["kind"], tag)
            edge(key, f"e:{hop['from_loc']}>{hop['to_loc']}:{hop['kind']}:{tag}", hop["from_loc"], hop["to_loc"],
                 hop["kind"], hop["ts"], hop["event_id"], label, h["path_id"])
    for e in edges.values():
        e["path_ids"].sort(key=lambda s: int(s.split(":")[1]))
    return {"nodes": list(nodes.values()), "edges": list(edges.values())}
