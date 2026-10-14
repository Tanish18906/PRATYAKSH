"""Validate public scenario and trace JSON against the PUGMARK contract."""

import argparse
import json
import re
from pathlib import Path


HEX64 = re.compile(r"[0-9a-f]{16}\Z")
UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
RAW_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RAW_PHONE = re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)")
RAW_POLICY = re.compile(r"\bNH-\d{4}-\d{6}\b")
RAW_CUSTOMER = re.compile(r"\bC\d{7}\b")
IDENTIFIERS = {"customer_id", "email", "phone", "policy_no"}
FORBIDDEN = {"truth", "raw", "case_key", "true_path", "dropped"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(obj, names, label):
    require(isinstance(obj, dict), f"{label} must be an object")
    require(set(names) <= obj.keys(), f"{label} missing {sorted(set(names) - obj.keys())}")


def references(items, label):
    require(isinstance(items, list), f"{label} must be a list")
    ids = [item.get("id") for item in items]
    require(all(isinstance(item_id, str) for item_id in ids), f"{label} needs string ids")
    require(len(ids) == len(set(ids)), f"duplicate {label} id")
    return set(ids)


def check_sketch(sketch, label):
    fields(sketch, ("k", "distinct", "hashes"), label)
    require(isinstance(sketch["k"], int) and sketch["k"] > 0, f"{label}.k invalid")
    require(isinstance(sketch["distinct"], int) and sketch["distinct"] >= 0,
            f"{label}.distinct invalid")
    hashes = sketch["hashes"]
    require(isinstance(hashes, list) and len(hashes) <= sketch["k"], f"{label}.hashes invalid")
    require(sketch["distinct"] >= len(hashes), f"{label}.distinct too small")
    require(all(isinstance(value, str) and HEX64.fullmatch(value) for value in hashes),
            f"{label}.hashes must be 16 lowercase hex chars")
    require(hashes == sorted(set(hashes)), f"{label}.hashes not sorted and unique")


def check_profile(profile, columns, label):
    fields(profile, ("delimiter", "quoting", "header_case", "line_ending", "encoding",
                     "null_token", "columns"), label)
    require(profile["delimiter"] in (",", ";", "\t", "|"), f"{label}.delimiter invalid")
    require(profile["quoting"] in ("minimal", "all", "none"), f"{label}.quoting invalid")
    require(profile["header_case"] in ("snake", "title", "upper", "camel"),
            f"{label}.header_case invalid")
    require(profile["line_ending"] in ("LF", "CRLF"), f"{label}.line_ending invalid")
    require(profile["encoding"] in ("utf-8", "utf-8-bom", "latin-1"), f"{label}.encoding invalid")
    require(profile["null_token"] in ("", "NULL", "N/A"), f"{label}.null_token invalid")
    require(isinstance(profile["columns"], dict) and set(profile["columns"]) <= set(columns),
            f"{label}.columns invalid")
    for column, entry in profile["columns"].items():
        require(isinstance(entry, dict) and set(entry) <= {"style", "case"},
                f"{label}.{column} invalid")
        if "style" in entry:
            require(entry["style"] in ("e164_dash", "digits10", "intl_spaced", "iso",
                                       "dmy_slash", "mdy_dash_yy"), f"{label}.{column}.style invalid")
        if "case" in entry:
            require(entry["case"] in ("lower", "mixed", "upper", "title"),
                    f"{label}.{column}.case invalid")


def check_forbidden(obj, path="public"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            require(key not in FORBIDDEN, f"forbidden key {path}.{key}")
            # Event.rows is an aggregate count; a raw row collection is forbidden.
            if key == "rows":
                require(path.startswith("public.events[") and isinstance(value, int),
                        f"raw rows forbidden at {path}")
            check_forbidden(value, f"{path}.{key}")
    elif isinstance(obj, list):
        if len(obj) > 20:
            require(not any(isinstance(item, dict) and
                            set(item).intersection(("email", "phone", "full_name", "policy_no",
                                                    "customer_id")) for item in obj),
                    f"raw personal rows forbidden at {path}")
        for index, item in enumerate(obj):
            check_forbidden(item, f"{path}[{index}]")


def check_masked(value, label):
    serialized = json.dumps(value)
    require(not any(pattern.search(serialized) for pattern in
                    (RAW_EMAIL, RAW_PHONE, RAW_POLICY, RAW_CUSTOMER)),
            f"unmasked personal value in {label}")


def validate_public_scenario(obj):
    fields(obj, ("contract_version", "id", "archetype", "seed", "params", "company",
                 "now_ts", "locations", "log_sources", "actors", "datasets", "events",
                 "artifacts", "canary_registry", "leak_sample", "discovery"), "scenario")
    require(obj["contract_version"] == "1.0", "contract version must be 1.0")
    require(isinstance(obj["id"], str) and obj["id"].startswith("scn:"), "scenario id invalid")
    require(obj["archetype"] in ("A1", "A2", "A3", "A4", "A5"), "archetype invalid")
    require(isinstance(obj["seed"], int), "seed invalid")
    require(obj["company"] == "Nova Health", "company invalid")
    fields(obj["params"], ("log_loss", "canary_mode", "scale"), "params")
    require(0 <= obj["params"]["log_loss"] <= 0.8, "log_loss invalid")
    require(isinstance(obj["params"]["canary_mode"], bool), "canary_mode invalid")
    require(obj["params"]["scale"] in ("demo", "bench"), "scale invalid")
    require(isinstance(obj["now_ts"], str) and UTC.fullmatch(obj["now_ts"]), "now_ts invalid")
    check_forbidden(obj)

    locations = references(obj["locations"], "location")
    sources = references(obj["log_sources"], "log source")
    actors = references(obj["actors"], "actor")
    datasets = references(obj["datasets"], "dataset")
    artifacts = references(obj["artifacts"], "artifact")
    events = references(obj["events"], "event")
    canaries = references(obj["canary_registry"], "canary")
    for location in obj["locations"]:
        fields(location, ("id", "kind", "name", "owner_actor", "monitored", "log_source",
                          "egress_capable"), "location")
        require(location["id"].startswith(("sys:", "ep:", "ext:")), "location id invalid")
        require(location["kind"] in ("system", "endpoint", "external"), "location kind invalid")
        require(location["owner_actor"] is None or location["owner_actor"] in actors,
                "location owner unknown")
        require(location["log_source"] is None or location["log_source"] in sources,
                "location log source unknown")
    for source in obj["log_sources"]:
        fields(source, ("id", "name", "location"), "log source")
        require(source["location"] in locations, "log source location unknown")
    for actor in obj["actors"]:
        fields(actor, ("id", "kind", "name", "role", "team", "access"), "actor")
        require(actor["id"].startswith("act:"), "actor id invalid")
        require(actor["kind"] in ("user", "service"), "actor kind invalid")
        require(isinstance(actor["access"], list) and set(actor["access"]) <= locations,
                "actor access references unknown location")
    for dataset in obj["datasets"]:
        fields(dataset, ("id", "name", "system", "columns", "identifier_columns",
                         "row_count", "sensitivity", "arrivals_per_hour"), "dataset")
        require(dataset["id"].startswith("ds:") and dataset["system"] in locations,
                "dataset reference invalid")
        require(set(dataset["identifier_columns"]) <= set(dataset["columns"]),
                "identifier column absent")
        require(dataset["row_count"] >= 0 and dataset["arrivals_per_hour"] >= 0,
                "dataset counts invalid")
        require(dataset["sensitivity"] in ("high", "medium", "low"),
                "dataset sensitivity invalid")

    for artifact in obj["artifacts"]:
        fields(artifact, ("id", "dataset", "created_by", "created_ts", "location",
                          "columns", "row_count", "filter_desc", "format_profile", "sketches",
                          "newest_record_ts", "arrivals_per_hour", "canary_ids"), "artifact")
        require(artifact["id"].startswith("art:") and artifact["dataset"] in datasets and
                artifact["created_by"] in actors and artifact["location"] in locations,
                "artifact reference invalid")
        require(UTC.fullmatch(artifact["created_ts"]) and UTC.fullmatch(artifact["newest_record_ts"]),
                "artifact timestamp invalid")
        require(artifact["newest_record_ts"] <= artifact["created_ts"], "artifact watermark after export")
        require(artifact["row_count"] > 0 and artifact["arrivals_per_hour"] >= 0,
                "artifact counts invalid")
        check_profile(artifact["format_profile"], artifact["columns"], "artifact profile")
        require(set(artifact["sketches"]) <= set(artifact["columns"]) & IDENTIFIERS,
                "artifact sketch column invalid")
        for column, sketch in artifact["sketches"].items():
            check_sketch(sketch, f"artifact {artifact['id']} {column}")
        require(set(artifact["canary_ids"]) <= canaries, "artifact canary unknown")

    last_by_source = {}
    for event in obj["events"]:
        fields(event, ("id", "ts", "seq", "source", "actor", "action", "object",
                       "from_loc", "to_loc", "rows", "meta"), "event")
        require(event["id"].startswith("evt:") and UTC.fullmatch(event["ts"]), "event id/time invalid")
        require(event["source"] in sources and event["actor"] in actors, "event actor/source unknown")
        require(event["action"] in ("read", "query", "export", "copy", "send", "upload", "download",
                                    "api_call", "permission_change"), "event action invalid")
        require(event["object"] is None or event["object"] in datasets | artifacts,
                "event object unknown")
        require(event["from_loc"] is None or event["from_loc"] in locations,
                "event from_loc unknown")
        require(event["to_loc"] is None or event["to_loc"] in locations, "event to_loc unknown")
        require(isinstance(event["rows"], int) and event["rows"] >= 0, "event rows invalid")
        require(isinstance(event["meta"], dict), "event meta invalid")
        if "artifact_id" in event["meta"]:
            require(event["meta"]["artifact_id"] in artifacts, "event artifact unknown")
        if "grantee" in event["meta"]:
            require(event["meta"]["grantee"] in actors, "event grantee unknown")
        if "scope" in event["meta"]:
            require(event["meta"]["scope"] in locations, "event scope unknown")
        if "change" in event["meta"]:
            require(event["meta"]["change"] in ("grant", "revoke"), "event change invalid")
        previous = last_by_source.get(event["source"])
        require(isinstance(event["seq"], int) and event["seq"] > 0, "event seq invalid")
        require(previous is None or (event["seq"] > previous[0] and event["ts"] >= previous[1]),
                "event sequence/time not increasing per source")
        last_by_source[event["source"]] = (event["seq"], event["ts"])
    require(obj["events"] == sorted(obj["events"], key=lambda event: (event["ts"], event["seq"])),
            "events not sorted by timestamp then sequence")

    for canary in obj["canary_registry"]:
        fields(canary, ("id", "export_id", "hashes"), "canary")
        require(canary["export_id"] in artifacts, "canary export unknown")
        require(all(column in IDENTIFIERS and HEX64.fullmatch(value)
                    for column, value in canary["hashes"].items()), "canary hash invalid")
    leak = obj["leak_sample"]
    fields(leak, ("id", "found_at", "found_ts", "file_name", "columns", "row_count",
                  "format_profile", "sketches", "newest_record_ts", "masked_preview",
                  "canary_hits"), "leak sample")
    require(leak["found_at"] in locations and leak["found_ts"] == obj["now_ts"],
            "leak location/time invalid")
    require(UTC.fullmatch(leak["newest_record_ts"]) and leak["newest_record_ts"] <= leak["found_ts"],
            "leak watermark invalid")
    require(isinstance(leak["columns"], list) and len(leak["columns"]) > 0, "leak columns empty")
    require(leak["row_count"] > 0 and isinstance(leak["masked_preview"], list) and
            len(leak["masked_preview"]) <= 5, "leak count/preview invalid")
    require(all(isinstance(row, dict) and set(row) <= set(leak["columns"]) and
                all(isinstance(value, str) for value in row.values())
                for row in leak["masked_preview"]), "leak preview shape invalid")
    check_profile(leak["format_profile"], leak["columns"], "leak profile")
    require(set(leak["sketches"]) <= set(leak["columns"]) & IDENTIFIERS,
            "leak sketch column invalid")
    for column, sketch in leak["sketches"].items():
        check_sketch(sketch, f"leak {column}")
    require(set(leak["canary_hits"]) <= canaries, "leak canary unknown")
    check_masked(leak["masked_preview"], "preview")
    discovery = obj["discovery"]
    fields(discovery, ("platform", "channel", "messages", "leak_message_id"), "discovery")
    require(discovery["platform"] == "telegram-mock", "discovery platform invalid")
    fields(discovery["channel"], ("name", "handle", "members"), "discovery channel")
    require(isinstance(discovery["messages"], list), "discovery messages invalid")
    for message in discovery["messages"]:
        fields(message, ("id", "ts", "sender", "text", "attachment"), "message")
        require(isinstance(message["id"], int) and UTC.fullmatch(message["ts"]),
                "message id/time invalid")
        if message["attachment"] is not None:
            fields(message["attachment"], ("file_name", "size_bytes", "rows_hint"),
                   "message attachment")
    require(any(message.get("id") == discovery["leak_message_id"] and message.get("attachment")
                for message in discovery["messages"]), "discovery attachment message missing")
    return None


def validate_trace(obj, scenario):
    validate_public_scenario(scenario)
    fields(obj, ("contract_version", "trace_id", "scenario_id", "engine_version", "origin_pinned",
                 "origin_candidates", "hypotheses", "actor_ranking", "location_ranking",
                 "chokepoints", "recommended_evidence", "loss_estimates", "graph", "notes"), "trace")
    require(obj["contract_version"] == "1.0" and obj["scenario_id"] == scenario["id"],
            "trace version/scenario mismatch")
    artifact_ids = {artifact["id"] for artifact in scenario["artifacts"]}
    actor_ids = {actor["id"] for actor in scenario["actors"]}
    location_ids = {location["id"] for location in scenario["locations"]}
    source_ids = {source["id"] for source in scenario["log_sources"]}
    candidate_ids = [candidate["artifact_id"] for candidate in obj["origin_candidates"]]
    require(len(candidate_ids) == len(artifact_ids) and set(candidate_ids) == artifact_ids,
            "origin candidates must contain every artifact exactly once")
    for candidate in obj["origin_candidates"]:
        fields(candidate, ("artifact_id", "verdict", "exclusion_rule", "containment",
                           "specificity", "format_sim", "watermark_term", "origin_fit",
                           "notes"), "origin candidate")
        require(candidate["verdict"] in ("candidate", "excluded"), "candidate verdict invalid")
        require(candidate["exclusion_rule"] is None or
                candidate["exclusion_rule"] in ("schema", "watermark_before", "after_found"),
                "candidate exclusion rule invalid")
    probabilities = [hypothesis["probability"] for hypothesis in obj["hypotheses"]]
    require(all(0 <= value <= 1 for value in probabilities) and
            probabilities == sorted(probabilities, reverse=True) and sum(probabilities) <= 1.0005,
            "hypothesis probabilities invalid")
    event_ids = {event["id"] for event in scenario["events"]}
    pinned = {entry["export_id"] for entry in scenario["canary_registry"]
              if entry["id"] in scenario["leak_sample"]["canary_hits"]}
    for hypothesis in obj["hypotheses"]:
        fields(hypothesis, ("rank", "path_id", "origin_artifact", "probability", "score",
                            "score_parts", "hops", "actors", "summary_text", "evidence"),
               "hypothesis")
        require(hypothesis["origin_artifact"] in artifact_ids, "hypothesis origin unknown")
        require(set(hypothesis["actors"]) <= actor_ids, "hypothesis actor unknown")
        fields(hypothesis["score_parts"], ("origin_fit", "path_cost", "anomaly"), "score parts")
        if obj["origin_pinned"]:
            require(hypothesis["origin_artifact"] in pinned, "hypothesis violates canary pin")
        previous = None
        for hop in hypothesis["hops"]:
            fields(hop, ("from_loc", "to_loc", "actor", "ts", "kind", "event_id",
                         "action", "rows", "est_loss", "note"), "hop")
            require(hop["from_loc"] in location_ids and hop["to_loc"] in location_ids and
                    hop["actor"] in actor_ids, "hop reference unknown")
            require(hop["kind"] in ("observed", "inferred"), "hop kind invalid")
            require(hop["event_id"] is None or hop["event_id"] in event_ids,
                    "hop event unknown")
            if previous is not None:
                require(previous["to_loc"] == hop["from_loc"], "hops not contiguous")
                if previous["ts"] is not None and hop["ts"] is not None:
                    require(previous["ts"] <= hop["ts"], "hop timestamps decrease")
            previous = hop
        for evidence in hypothesis["evidence"]:
            fields(evidence, ("kind", "text", "ts", "event_id"), "evidence")
            require(evidence["kind"] in ("observed", "inferred", "anomaly", "fingerprint"),
                    "evidence kind invalid")
    require(all(entry["actor"] in actor_ids for entry in obj["actor_ranking"]),
            "actor ranking reference unknown")
    require(all(entry["location"] in location_ids for entry in obj["location_ranking"]),
            "location ranking reference unknown")
    require(set(obj["loss_estimates"]) <= source_ids and
            all(0 <= value <= 1 for value in obj["loss_estimates"].values()),
            "loss estimate invalid")
    graph = obj["graph"]
    fields(graph, ("nodes", "edges"), "graph")
    node_ids = {node["id"] for node in graph["nodes"]}
    require(len(node_ids) == len(graph["nodes"]), "duplicate graph node id")
    for edge in graph["edges"]:
        fields(edge, ("id", "from", "to", "kind", "ts", "event_id", "path_ids", "label"),
               "graph edge")
        require(edge["from"] in node_ids and edge["to"] in node_ids,
                "graph edge references unknown node")
        require(edge["event_id"] is None or edge["event_id"] in event_ids,
                "graph edge event unknown")
    def check_all_event_ids(value):
        if isinstance(value, dict):
            if "event_id" in value:
                require(value["event_id"] is None or value["event_id"] in event_ids,
                        "trace event reference unknown")
            for nested in value.values():
                check_all_event_ids(nested)
        elif isinstance(value, list):
            for nested in value:
                check_all_event_ids(nested)

    check_all_event_ids(obj)
    check_masked(obj, "trace")
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("scenario", "trace"))
    parser.add_argument("path", type=Path)
    parser.add_argument("scenario_path", type=Path, nargs="?")
    args = parser.parse_args()
    obj = json.loads(args.path.read_text())
    if args.kind == "scenario":
        validate_public_scenario(obj)
    else:
        if args.scenario_path is None:
            parser.error("trace requires scenario path")
        validate_trace(obj, json.loads(args.scenario_path.read_text()))
    print("VALID")


if __name__ == "__main__":
    main()
