"""All tunable engine numbers live here and nowhere else (docs/03_ENGINE.md section 3).

Change only on benchmark seeds 0 to 49 and log before/after numbers in docs/DECISIONS.md.
"""

ENGINE = {
    # origin
    "W_CONTAINMENT": 5.0, "W_SPECIFICITY": 1.0, "W_FORMAT": 2.0,
    "WM_RATIO_MIN": 0.9,        # watermark term only if |L|/|E| >= this
    "WM_CAP": 8.0,              # max magnitude of the watermark penalty
    "WM_TOLERANCE_MIN": 5,      # minutes of slack on the watermark hard rule
    "NO_MATCH_CONTAINMENT": 0.2,  # below this a candidate is not used for paths
    "ORIGIN_MARGIN": 12.0,      # keep candidates within this origin_fit of the best
    "MAX_CANDIDATES": 8,
    # path costs
    "OBS_COST": 0.10, "H_ENDPOINT": 0.50, "H_BASE": 1.0,
    "ACTOR_SWITCH": 1.0, "UNKNOWN_CHANNEL": 2.0,
    "LOSS_DEFAULT": 0.40, "LOSS_FLOOR": 0.05, "LOSS_CEIL": 0.90, "LOSS_MIN_EVENTS": 20,
    "MAX_HIDDEN": 2, "MAX_DEPTH": 6, "MAX_PATHS_PER_ORIGIN": 2000, "COST_MARGIN": 8.0,
    "ACTOR_ALT_MAX": 3, "ACTOR_ALT_WINDOW_DAYS": 7,
    # scoring
    "W_ORIGIN": 1.0, "W_PATH": 1.0, "W_ANOMALY": 0.6, "TEMPERATURE": 1.0,
    # anomaly
    "BASELINE_DAYS": 30, "BASELINE_MIN_EVENTS": 3, "SIGMA_FLOOR": 0.5,
    "DEFAULT_MU": 3.93, "DEFAULT_SIGMA": 1.0,     # ln(51)
    "Z_CAP": 4.0, "OFF_HOURS_W": 0.5, "FIRST_TIME_W": 0.7, "PRIV_W": 0.7, "PRIV_WINDOW_DAYS": 7,
    # outputs
    "TOP_K": 5, "CHOKE_MAX": 3, "EVIDENCE_MAX": 3,
    "ENGINE_VERSION": "1.0.0",
}
