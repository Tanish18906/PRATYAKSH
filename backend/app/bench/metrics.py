"""Rank metrics and sanity gates (docs/04_TEST_PLAN.md sections 6.3 and 6.4)."""


def rank_of(item, order: list, worst: int) -> int:
    return order.index(item) + 1 if item in order else worst


def best_rank(items: list, order: list, worst: int) -> int:
    return min((rank_of(i, order, worst) for i in items), default=worst)


def stats(ranks: list) -> dict:
    n = len(ranks)
    if n == 0:
        return {"top1": 0.0, "top3": 0.0, "mean_rank": None, "n": 0}
    return {"top1": sum(r == 1 for r in ranks) / n, "top3": sum(r <= 3 for r in ranks) / n,
            "mean_rank": sum(ranks) / n, "n": n}


def sanity_gates(result: dict) -> list:
    """Messages for gates that fail; empty list when the numbers may be shown. Spot checks stay manual."""
    out = []
    p = result["origin"].get("pugmark", {}).get("0.0")
    if p is not None and p["top3"] < 0.9:
        out.append(f"At loss 0.0 pugmark origin top3 is {p['top3']:.2f}, below 0.9: this is a bug, not a result.")
    for kind in ("origin", "actor"):
        mine = result[kind].get("pugmark")
        for name, theirs in result[kind].items():
            if name != "pugmark" and mine and theirs == mine:
                out.append(f"Baseline {name} is identical to pugmark for {kind}: the benchmark is trivial.")
    return out
