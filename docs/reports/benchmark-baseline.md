# Benchmark baseline: seeds 0 to 49, no tuning

Real simulator, real engine, bench scale, canary off. **Nothing was tuned and no config value was changed**; this is the starting point before any tuning. Seeds 0 to 49 are the TUNING set (04 sec 6.2), so these numbers are not held-out and must not be presented as the final result; the held-out run is seeds 50 to 199 and was NOT run.

Synthetic data: numbers measure the engine on our simulator, not real-world accuracy. Relative likelihoods, not calibrated probabilities.

## Setup
- Seeds: 0 to 49 minus seed 42 (the demo story is never benchmarked) = 49 seeds, each at 4 loss levels = 196 scenarios per archetype set.
- Archetype per seed: A1, A2, A3 by `seed % 3` as in 04 sec 6.1 (A1 16 seeds because seed 42 is removed, A2 17, A3 16).
- Origin: rank of the true origin artifact. Leaker: rank of the best-ranked actor in `truth.true_actors`; an actor not in the ranking counts as rank = number of actors.
- Chokepoint hit: the first chokepoint's item (or any of the first 3) names a true actor (`perm:<actor>@...`). A channel item (`ch:...`) is never a hit.
- Baselines: B1 last accessor, B2 biggest exporter (actors); B3 largest export, B4 most recent export (artifacts). Ties keep the scenario's actor order.
- Engine config: unchanged ENGINE dict (version 1.0.0, ACTOR_ALT_MAX 3); main at the A2 variant B rule.
- Cross-check: my per-scenario numbers equal `bench.run.run_benchmark` on the same seeds and losses (identical).
- With n of 16 or 17 per archetype and 49 per level, one scenario moves a figure by 2 to 6 points; read differences below about 10 points as noise.

## Main benchmark: A1, A2, A3

### log_loss 0.0  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) | 0.67 (33/49) / 0.67 (33/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 0.82 (40/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.02 (1/49) | 0.04 (2/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.00 (0/49) | 0.51 (25/49) | n/a |

Runtime: generate 1.8 s + trace 0.5 s = 2.2 s for the level (45 ms per scenario, slowest trace 29 ms). Mean rank of the true origin 1.00, of the best true actor 1.00.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A1 | 16 | 16 / 0 / 0 | 16 / 1 / 0 | 16 / 2 / 9 | 0 of 16 | 16 of 16 |
| A2 | 17 | 17 / 0 / 0 | 17 / 0 / 0 | 17 / 0 / 0 | 0 of 17 | 1 of 17 |
| A3 | 16 | 16 / 0 / 0 | 16 / 0 / 0 | 16 / 0 / 16 | 0 of 16 | 16 of 16 |

### log_loss 0.2  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.67 (33/49) | 0.67 (33/49) | 0.55 (27/49) / 0.55 (27/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 0.82 (40/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.02 (1/49) | 0.04 (2/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.02 (1/49) | 0.57 (28/49) | n/a |

Runtime: generate 1.7 s + trace 0.3 s = 2.1 s for the level (42 ms per scenario, slowest trace 12 ms). Mean rank of the true origin 1.00, of the best true actor 6.67.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A1 | 16 | 16 / 0 / 0 | 10 / 1 / 0 | 10 / 2 / 7 | 0 of 16 | 10 of 16 |
| A2 | 17 | 17 / 0 / 0 | 7 / 0 / 0 | 7 / 0 / 5 | 10 of 17 | 1 of 17 |
| A3 | 16 | 16 / 0 / 0 | 16 / 0 / 1 | 16 / 0 / 16 | 0 of 16 | 16 of 16 |

### log_loss 0.4  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.61 (30/49) | 0.65 (32/49) | 0.53 (26/49) / 0.55 (27/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 0.82 (40/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.02 (1/49) | 0.02 (1/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.06 (3/49) | 0.55 (27/49) | n/a |

Runtime: generate 1.8 s + trace 0.3 s = 2.0 s for the level (42 ms per scenario, slowest trace 11 ms). Mean rank of the true origin 1.00, of the best true actor 7.12.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A1 | 16 | 16 / 0 / 0 | 10 / 1 / 0 | 10 / 1 / 6 | 0 of 16 | 10 of 16 |
| A2 | 17 | 17 / 0 / 0 | 5 / 0 / 0 | 6 / 0 / 6 | 11 of 17 | 1 of 17 |
| A3 | 16 | 16 / 0 / 0 | 15 / 0 / 3 | 16 / 0 / 15 | 0 of 16 | 15 of 16 |

### log_loss 0.6  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.53 (26/49) | 0.59 (29/49) | 0.49 (24/49) / 0.55 (27/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 0.82 (40/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.02 (1/49) | 0.10 (5/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.12 (6/49) | 0.47 (23/49) | n/a |

Runtime: generate 1.7 s + trace 0.2 s = 1.9 s for the level (40 ms per scenario, slowest trace 9 ms). Mean rank of the true origin 1.00, of the best true actor 8.45.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A1 | 16 | 16 / 0 / 0 | 9 / 1 / 0 | 10 / 3 / 9 | 0 of 16 | 9 of 16 |
| A2 | 17 | 17 / 0 / 0 | 3 / 0 / 1 | 3 / 0 / 3 | 14 of 17 | 1 of 17 |
| A3 | 16 | 16 / 0 / 0 | 14 / 0 / 5 | 16 / 2 / 11 | 0 of 16 | 14 of 16 |

## A5 (backup copy), listed separately
A5 is not part of the 04 sec 6.1 benchmark set. `truth.true_actors` here holds the backup service account AND the reader who downloaded it; the leaker is scored as the best-ranked of the two. The service account is hidden from the ranking by the creator-exclusion rule (03 sec 8), so a hit means the human reader.

### log_loss 0.0  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) / 1.00 (49/49) |
| B3 largest export | 1.00 (49/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.12 (6/49) | 0.41 (20/49) | n/a |
| B2 biggest exporter | n/a | n/a | 1.00 (49/49) | 1.00 (49/49) | n/a |

Runtime: generate 3.2 s + trace 0.3 s = 3.5 s for the level (72 ms per scenario, slowest trace 11 ms). Mean rank of the true origin 1.00, of the best true actor 1.00.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A5 | 49 | 49 / 49 / 0 | 49 / 6 / 49 | 49 / 20 / 49 | 0 of 49 | 49 of 49 |

### log_loss 0.2  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.67 (33/49) | 1.00 (49/49) | 0.67 (33/49) / 1.00 (49/49) |
| B3 largest export | 1.00 (49/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.12 (6/49) | 0.33 (16/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.84 (41/49) | 0.84 (41/49) | n/a |

Runtime: generate 3.0 s + trace 0.3 s = 3.2 s for the level (66 ms per scenario, slowest trace 10 ms). Mean rank of the true origin 1.00, of the best true actor 1.33.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A5 | 49 | 49 / 49 / 0 | 33 / 6 / 41 | 49 / 16 / 41 | 0 of 49 | 33 of 49 |

### log_loss 0.4  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.59 (29/49) | 1.00 (49/49) | 0.59 (29/49) / 1.00 (49/49) |
| B3 largest export | 1.00 (49/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.10 (5/49) | 0.35 (17/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.67 (33/49) | 0.84 (41/49) | n/a |

Runtime: generate 3.0 s + trace 0.2 s = 3.3 s for the level (67 ms per scenario, slowest trace 8 ms). Mean rank of the true origin 1.00, of the best true actor 1.41.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A5 | 49 | 49 / 49 / 0 | 29 / 5 / 33 | 49 / 17 / 41 | 0 of 49 | 29 of 49 |

### log_loss 0.6  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.69 (34/49) | 1.00 (49/49) | 0.69 (34/49) / 1.00 (49/49) |
| B3 largest export | 1.00 (49/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.10 (5/49) | 0.29 (14/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.55 (27/49) | 0.80 (39/49) | n/a |

Runtime: generate 3.0 s + trace 0.2 s = 3.3 s for the level (66 ms per scenario, slowest trace 7 ms). Mean rank of the true origin 1.00, of the best true actor 1.31.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A5 | 49 | 49 / 49 / 0 | 34 / 5 / 27 | 49 / 14 / 39 | 0 of 49 | 34 of 49 |

## A4 (public bucket), extra, listed separately
Not requested; included because the simulator generates A4 and it was free to run.

### log_loss 0.0  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) | 1.00 (49/49) / 1.00 (49/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.00 (0/49) | 0.14 (7/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.00 (0/49) | 1.00 (49/49) | n/a |

Runtime: generate 2.3 s + trace 0.7 s = 3.0 s for the level (61 ms per scenario, slowest trace 162 ms). Mean rank of the true origin 1.00, of the best true actor 1.00.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A4 | 49 | 49 / 0 / 0 | 49 / 0 / 0 | 49 / 7 / 49 | 0 of 49 | 49 of 49 |

### log_loss 0.2  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.82 (40/49) | 0.82 (40/49) | 0.82 (40/49) / 0.82 (40/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.00 (0/49) | 0.18 (9/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.02 (1/49) | 0.82 (40/49) | n/a |

Runtime: generate 2.1 s + trace 0.5 s = 2.6 s for the level (53 ms per scenario, slowest trace 18 ms). Mean rank of the true origin 1.00, of the best true actor 2.53.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A4 | 49 | 49 / 0 / 0 | 40 / 0 / 1 | 40 / 9 / 40 | 0 of 49 | 40 of 49 |

### log_loss 0.4  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.57 (28/49) | 0.57 (28/49) | 0.57 (28/49) / 0.57 (28/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.04 (2/49) | 0.18 (9/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.08 (4/49) | 0.63 (31/49) | n/a |

Runtime: generate 2.1 s + trace 0.4 s = 2.6 s for the level (52 ms per scenario, slowest trace 15 ms). Mean rank of the true origin 1.00, of the best true actor 4.41.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A4 | 49 | 49 / 0 / 0 | 28 / 2 / 4 | 28 / 9 / 31 | 0 of 49 | 28 of 49 |

### log_loss 0.6  (n = 49 of 49 scenarios)
| Method | Origin top-1 | Origin top-3 | Leaker top-1 | Leaker top-3 | Chokepoint hit (first / any of 3) |
|---|---|---|---|---|---|
| **PUGMARK** | 1.00 (49/49) | 1.00 (49/49) | 0.31 (15/49) | 0.31 (15/49) | 0.31 (15/49) / 0.31 (15/49) |
| B3 largest export | 0.00 (0/49) | 0.00 (0/49) | n/a | n/a | n/a |
| B4 most recent export | 0.00 (0/49) | 1.00 (49/49) | n/a | n/a | n/a |
| B1 last accessor | n/a | n/a | 0.06 (3/49) | 0.20 (10/49) | n/a |
| B2 biggest exporter | n/a | n/a | 0.12 (6/49) | 0.49 (24/49) | n/a |

Runtime: generate 2.0 s + trace 0.3 s = 2.3 s for the level (47 ms per scenario, slowest trace 10 ms). Mean rank of the true origin 1.00, of the best true actor 6.53.

| Archetype | n | Origin top-1: PUGMARK / B3 / B4 | Leaker top-1: PUGMARK / B1 / B2 | Leaker top-3: PUGMARK / B1 / B2 | Leaker absent from ranking | Chokepoint hit (first) |
|---|---|---|---|---|---|---|
| A4 | 49 | 49 / 0 / 0 | 15 / 3 / 6 | 15 / 10 / 24 | 0 of 49 | 15 of 49 |

## Reading notes (what the tables do and do not say)

1. **Origin is solved on this set, leaker is not, and the gap is log loss.** Origin top-1 is 49/49 at every loss level. Leaker top-1 falls from 49/49
   (loss 0.0) to 33, 30, 26 of 49 (0.2, 0.4, 0.6). B1 last accessor never exceeds 1 of 49 at top-1; B2 biggest exporter reaches 6 of 49 at best.
   B3 largest export is 0 of 49 on A1 to A3; B4 most recent export is 0 of 49 at top-1 and 40 of 49 at top-3.
2. **A2 absences are all lost evidence, not engine misses.** Seeds of A2 (17 per level), leaker's `api_call` event in the public log vs leaker missing from the ranking:

   | log_loss | event survived | leaker absent from ranking | absent because the event was dropped | absent although the event was present |
   |---|---|---|---|---|
   | 0.0 | 17 of 17 | 0 | 0 | 0 |
   | 0.2 | 7 of 17 | 10 | 10 | 0 |
   | 0.4 | 6 of 17 | 11 | 11 | 0 |
   | 0.6 | 3 of 17 | 14 | 14 | 0 |

   When the event survives the key is found (rank 1 in 17/17 at loss 0.0 and in 7/7 at 0.2). When the simulator drops it (the forced drop plus random loss), the key leaves no trace in the logs.
3. **Chokepoint "hit" understates A2.** The metric counts only items that name a true actor. For A2 the engine's first chokepoint is usually the channel
   `ch:ext:unknown-host` (it covers the key's whole path and wins the tie on marginal against the key's own permission by item id). That is a correct
   containment recommendation, counted here as a miss. First chokepoint in the A2 scenarios (17 per level): channel 16 / 6 / 4 / 2 at loss 0.0 / 0.2 / 0.4 / 0.6;
   the key's own permission 1 / 1 / 1 / 1; the remaining scenarios have no chokepoint naming the key (the key's event was dropped). Read the A2 chokepoint
   column as "names the key", not "recommends the right action".
4. **A5 is not informative for the baselines.** `truth.true_actors` includes the backup service account and the reader; the creator-exclusion rule hides the
   service account, so PUGMARK scores on the reader. B3 largest export is 49/49 on A5 origin by construction (the full snapshot is the biggest file) and B2 biggest
   exporter is 49/49 at loss 0.0 (the reader downloads the full snapshot). Do not average A5 into the headline numbers.
5. **Small n.** 49 scenarios per level, 16 or 17 per archetype. A single scenario is 2 to 6 points; differences under about 10 points are noise.
6. **These are tuning-set numbers.** Seeds 0 to 49 are for tuning only. This table is the "before" for any weight change; the "after" and the reported
   result must come from seeds 50 to 199, run once. Seeds 50 to 199 were not run.
7. **Cross-check.** The aggregate figures match `bench.run.run_benchmark` on the same generator and seeds exactly (the repo runner reports no per-archetype
   or chokepoint figures, which is why this report uses its own script, `testing/bench_baseline.py`, kept outside the repo and git-ignored).

## Scenarios that crashed, timed out or were slow
None. All 588 scenarios generated and traced; no crash, no timeout (limit 30 s), no trace over 3 s.

Total wall time for everything above: 43 s.
