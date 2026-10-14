from app.sim.lossy import assign_and_drop, new_event


def test_loss_preserves_sequence_gaps_and_seed():
    def events():
        return [new_event(f"2026-10-01T{i // 60:02d}:{i % 60:02d}:00Z", "act:a", "query",
                          "ds:customers", "sys:bi-warehouse", None, 10) for i in range(100)]

    intact, dropped = assign_and_drop(events(), 7, 0.0)
    assert len(intact) == 100 and not dropped
    assert [event["seq"] for event in intact] == list(range(1, 101))

    first, missing = assign_and_drop(events(), 7, 0.4)
    again, missing_again = assign_and_drop(events(), 7, 0.4)
    assert first == again and missing == missing_again
    assert 25 <= len(missing) <= 55
    assert max(event["seq"] for event in first) > len(first)


def test_critical_override():
    critical = new_event("2026-10-09T21:40:00Z", "act:ravi-menon", "download", "art:E1",
                         "sys:bi-warehouse", "ep:ravi-menon", 48_900)
    kept, dropped = assign_and_drop([critical], 42, 0.4, critical, preserve_critical=True)
    assert kept == [critical] and dropped == []
    kept, dropped = assign_and_drop([critical], 42, 0.6, critical, preserve_critical=False)
    assert kept == [] and dropped == [critical["id"]]


def test_loss_distribution_over_200_seeds():
    lost = 0
    critical_lost = 0
    for seed in range(200):
        events = [new_event(f"2026-10-01T{i // 60:02d}:{i % 60:02d}:00Z", "act:a", "query",
                            "ds:customers", "sys:bi-warehouse", None, 10) for i in range(100)]
        _, missing = assign_and_drop(events, seed, 0.4)
        lost += len(missing)

        critical = new_event("2026-10-09T21:40:00Z", "act:a", "download", "art:E1",
                             "sys:bi-warehouse", "ep:a", 10)
        _, missing = assign_and_drop([critical], seed, 0.01, critical)
        critical_lost += critical["id"] in missing
    assert abs(lost / 20_000 - 0.4) < 0.05
    assert 0.4 <= critical_lost / 200 <= 0.6
