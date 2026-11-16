#!/usr/bin/env python3
"""
FL3 — pre-registration harness for FL3-SHADOW-1.

Implements exactly the model text in verified/PREREGISTRATION.md §2 and emits a
hash of the forecasts it would have produced for a given deadline. The hash is
the anti-tamper evidence: if the implementation changes, the hash changes, even
if the prose does not.

This script does NOT publish forecasts for future games. A forecast is only
valid once it is committed before kickoff, and there is no licensed price feed or
kickoff clock available offline. What it does is prove, reproducibly, what the
registered model would say given only games that had finished before a stated
deadline — so that when real forecasts are published they can be checked against
a rule that already existed.

Run:  python3 scripts/preregister_model.py
      python3 scripts/preregister_model.py --deadline 2026-11-12 --format json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(DATA, "week_results_2026.csv")
OUT = os.path.join(DATA, "preregistration.json")

MODEL_ID = "FL3-SHADOW-1"
# Every constant below is frozen by verified/PREREGISTRATION.md §2.
K = 4.0
L = 22.0
HFA = 1.9
SIGMA = 8.5
LOGISTIC_SCALE = 0.55


def load_results() -> list[dict]:
    with open(RESULTS, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["week"] = int(r["week"])
        r["away_pts"] = int(r["away_pts"])
        r["home_pts"] = int(r["home_pts"])
    return rows


def fit(history: list[dict]) -> dict:
    agg: dict[str, dict] = {}
    for r in history:
        for t, s, c in ((r["away_abbr"], r["away_pts"], r["home_pts"]),
                        (r["home_abbr"], r["home_pts"], r["away_pts"])):
            a = agg.setdefault(t, dict(g=0, pf=0, pa=0))
            a["g"] += 1
            a["pf"] += s
            a["pa"] += c
    out = {}
    for t, a in agg.items():
        w = a["g"] / (a["g"] + K)
        out[t] = dict(
            games=a["g"],
            off=round(w * (a["pf"] / a["g"]) + (1 - w) * L, 6),
            defense=round(w * (a["pa"] / a["g"]) + (1 - w) * L, 6),
        )
    return out


def forecast(ratings: dict, away: str, home: str) -> dict:
    A, H = ratings[away], ratings[home]
    exp_away = L + (A["off"] - L) + (H["defense"] - L)
    exp_home = L + (H["off"] - L) + (A["defense"] - L) + HFA
    m = exp_home - exp_away
    p_home = 1.0 / (1.0 + math.exp(-m / (SIGMA * LOGISTIC_SCALE)))
    return dict(
        spread_home=round(-m, 4),
        total=round(exp_away + exp_home, 4),
        p_home=round(p_home, 6),
        exp_away=round(exp_away, 4),
        exp_home=round(exp_home, 4),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deadline", default=None,
                    help="use only games dated strictly before this ISO date (default: all committed results)")
    ap.add_argument("--format", default="text", choices=["text", "json"])
    a = ap.parse_args()

    rows = load_results()
    if a.deadline:
        history = [r for r in rows if r["game_date"] < a.deadline]
    else:
        history = rows

    ratings = fit(history)
    payload = dict(
        model_id=MODEL_ID,
        registration="verified/PREREGISTRATION.md",
        constants=dict(k=K, league_points=L, hfa=HFA, sigma=SIGMA, logistic_scale=LOGISTIC_SCALE),
        deadline=a.deadline,
        games_used=len(history),
        clubs=len(ratings),
        ratings=dict(sorted(ratings.items())),
    )
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["sha256"] = hashlib.sha256(blob).hexdigest()

    if a.deadline:
        # forecast every club pairing that has a rating, in a stable order
        teams = sorted(ratings)
        fc = {}
        for i, aw in enumerate(teams):
            for h in teams[i + 1:]:
                fc[f"{aw}@{h}"] = forecast(ratings, aw, h)
        payload["example_forecasts"] = fc

    if a.format == "json":
        print(json.dumps(payload, indent=1, sort_keys=True))
        return 0

    print(f"{MODEL_ID}  constants k={K} L={L} HFA={HFA} sigma={SIGMA}")
    print(f"fitted on {len(history)} games, {len(ratings)} clubs"
          + (f", deadline {a.deadline}" if a.deadline else " (all committed results)"))
    print(f"implementation hash sha256 {payload['sha256'][:32]}...")
    print()
    for t, r in sorted(ratings.items(), key=lambda kv: -kv[1]["off"])[:8]:
        print(f"  {t}  g={r['games']:>2}  off={r['off']:>6.2f}  def={r['defense']:>6.2f}")
    if not a.deadline:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
        print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
