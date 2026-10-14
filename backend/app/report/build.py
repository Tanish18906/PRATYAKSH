"""HTML incident report (docs/FEATURES.md F-04, contract GET /api/report/{trace_id}).

Built only from the masked scenario summary and the trace result, so it holds counts, timestamps, names and masked
examples. No wall clock: the same trace gives the same report. Every dynamic string is HTML-escaped.
"""
from html import escape as e
from pathlib import Path
from string import Template

TEMPLATE = Template((Path(__file__).with_name("template.html")).read_text())
LEGAL = "Verify current legal timelines with counsel."
KIND = {"observed": "Observed", "inferred": "Inferred", "anomaly": "Anomaly", "fingerprint": "Fingerprint"}


def _pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _num(x) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def _table(head: list, rows: list) -> str:
    th = "".join(f"<th>{e(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{tr}</table>"


def _vendor_boundary(summary: dict, hyps: list) -> bool:
    """True when a leading path hands the file to an outside party, where custody evidence stops."""
    kind = {x["id"]: x["kind"] for x in summary["locations"]}
    for h in hyps[:3]:
        for hop in h["hops"]:
            if hop["action"] == "send" and kind.get(hop["to_loc"]) == "external":
                return True
            if "sftp" in hop["from_loc"] or "sftp" in hop["to_loc"]:
                return True
    return False


def build_report(summary: dict, trace: dict) -> str:
    name = {x["id"]: x["name"] for x in summary["actors"] + summary["locations"]}
    leak, hyps = summary["leak_sample"], trace["hypotheses"]
    out = [f"<h1>PUGMARK incident report</h1>",
           f"<p><span class=\"badge\">SIMULATED</span> <span class=\"muted\">All data in this report is synthetic. "
           f"Trace {e(trace['trace_id'])} for scenario {e(summary['id'])}.</span></p>",
           "<h2>1. What was found</h2>",
           _table(["Item", "Value"], [
               ["Company (simulated)", summary["company"]],
               ["Found at", f"{name.get(leak['found_at'], leak['found_at'])} ({leak['found_at']})"],
               ["Found (UTC)", leak["found_ts"]], ["File", leak["file_name"]], ["Rows", leak["row_count"]],
               ["Columns", ", ".join(leak["columns"])], ["Newest record in file (UTC)", leak["newest_record_ts"]],
               ["Systems / actors / events / exports", " / ".join(str(summary["counts"][k]) for k in (
                   "locations", "actors", "events", "artifacts"))]])]
    if leak["masked_preview"]:
        cols = list(leak["masked_preview"][0])
        out.append("<p class=\"muted\">Masked preview (first rows):</p>")
        out.append(_table(cols, [[r.get(c, "") for c in cols] for r in leak["masked_preview"]]))

    out.append("<h2>2. Which export it most likely came from</h2>")
    if trace["origin_pinned"]:
        out.append("<p class=\"note\">The origin was pinned by a canary record found in the leaked file.</p>")
    out.append(_table(["Export", "Verdict", "Overlap with leak", "Format match", "Watermark term", "Fit", "Why"], [
        [c["artifact_id"], c["verdict"] + (f" ({c['exclusion_rule']})" if c["exclusion_rule"] else ""),
         _pct(c["containment"]), _pct(c["format_sim"]), _num(c["watermark_term"]), _num(c["origin_fit"]),
         " ".join(c["notes"])] for c in trace["origin_candidates"]]))

    out.append("<h2>3. Most likely custody paths</h2>")
    if not hyps:
        out.append("<p>No custody path could be proposed. See the notes below.</p>")
    for h in hyps[:3]:
        out.append(f"<h3>Hypothesis {h['rank']}: relative likelihood {_pct(h['probability'])}</h3>")
        out.append(f"<p>{e(h['summary_text'])}</p>")
        ordered = sorted(h["evidence"], key=lambda x: list(KIND).index(x["kind"]))
        out.append("<ul>" + "".join(
            f"<li><strong>{e(KIND[x['kind']])}</strong>: {e(x['text'])}</li>" for x in ordered) + "</ul>")
    if _vendor_boundary(summary, hyps):
        out.append("<p class=\"note\">The chain of custody ends at the vendor boundary: transfers to an outside "
                   "party are visible, but what happened after the hand-over is outside the company's logs.</p>")

    out.append("<h2>4. Who is most exposed on these paths</h2>")
    out.append(_table(["Actor", "Share of path likelihood"], [
        [name.get(a["actor"], a["actor"]), _pct(a["marginal"])] for a in trace["actor_ranking"][:5]]))

    out.append("<h2>5. Containment recommendations</h2>")
    if trace["chokepoints"]:
        out.append(_table(["Action", "Paths covered", "Cumulative coverage"], [
            [c["action_text"], _pct(c["marginal"]), _pct(c["cumulative_coverage"])] for c in trace["chokepoints"]]))
    else:
        out.append("<p>No containment item could be derived.</p>")

    out.append("<h2>6. Evidence that would narrow this down</h2>")
    if trace["recommended_evidence"]:
        out.append("<ul>" + "".join(f"<li>{e(r['request_text'])} (on {_pct(r['mass'])} of path likelihood)</li>"
                                    for r in trace["recommended_evidence"]) + "</ul>")
    else:
        out.append("<p>No specific log request was derived.</p>")

    if trace["notes"]:
        out.append("<h2>7. Notes</h2><ul>" + "".join(f"<li>{e(n)}</li>" for n in trace["notes"]) + "</ul>")
    out.append("<h2>Limits of this report</h2><ul>"
               "<li>Figures are relative likelihoods between the hypotheses listed, not a probability that "
               "any person is responsible.</li>"
               "<li>Loss of log events is estimated from sequence gaps; missing hops are inferences, not facts.</li>"
               "<li>The output is a ranked set of hypotheses for a human investigator, never a finding of guilt.</li>"
               "</ul>")
    out.append(f"<p class=\"note\">{e(LEGAL)}</p>")
    return TEMPLATE.substitute(title=e(f"Incident report {trace['trace_id']}"), body="\n".join(out))
