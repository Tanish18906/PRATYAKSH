"""Simulated Telegram discovery messages; no network access."""

from .base_table import seconds, seeded_rng, timestamp


HANDLES = ("@fr3sh_dumps", "@admin_dz", "@buyer_0xA", "@quiet_reader", "@check_demo")
CHAT = ("any updates?", "checking", "legit?", "demo only", "looks like a csv",
        "thanks", "still here", "noted", "sample attached?")


def make_discovery(seed: int, leak: dict, upload_ts: str) -> dict:
    rng = seeded_rng("telegram", seed)
    post_time = seconds(upload_ts) + 30 * 60
    count = int(rng.integers(7, 11))
    other_times = sorted(post_time + int(rng.integers(-3 * 3600, 3 * 3600 + 1))
                         for _ in range(count - 1))
    entries = [(when, False) for when in other_times] + [(post_time, True)]
    entries.sort(key=lambda item: (item[0], item[1]))
    messages = []
    leak_message_id = None
    for number, (when, is_leak) in enumerate(entries, 1):
        if is_leak:
            leak_message_id = number
            rows_k = round(leak["row_count"] / 1000)
            text = f"fresh insurance customers, CG region, ~{rows_k}k rows. csv attached. dm for the rest"
            attachment = {"file_name": leak["file_name"],
                          "size_bytes": leak["row_count"] * 62, "rows_hint": leak["row_count"]}
        else:
            text = CHAT[int(rng.integers(len(CHAT)))]
            attachment = None
        messages.append({"id": number, "ts": timestamp(when),
                         "sender": HANDLES[int(rng.integers(len(HANDLES)))],
                         "text": text, "attachment": attachment})
    return {"platform": "telegram-mock",
            "channel": {"name": "Dump Zone India (demo)", "handle": "@dumpzone_demo",
                        "members": int(rng.integers(1200, 9001))},
            "messages": messages, "leak_message_id": leak_message_id}
