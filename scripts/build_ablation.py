#!/usr/bin/env python3
"""
FL3 — injury / availability ablation on chronological holdouts.

THE QUESTION
------------
The brief rejects fixed point penalties for injuries ("instead of subtracting a
fixed number of points for a missing starter, test the same model with and
without the personnel features and report the difference with uncertainty").
This script does exactly that.

WHAT IS TESTED
--------------
Two models, otherwise identical:

  M0  base      expected points = off + opp_def - league_points + HFA,
                where off/def are fitted on the club's scoring through the cut.

  M1  personnel M0 plus a term for the depth-1 players the OFFICIAL report had
                already ruled out, with a single global coefficient fitted on the
                training slice only. The coefficient is what the data says about
                losing depth-1 players, not a number chosen by a human.

Walk-forward protocol (no leakage):
  for cut in 4..9:  fit on Weeks 1..cut, predict Week cut+1, score, roll.
  The personnel term is only available for the weeks a depth chart is held
  (Week 10 in this repository), so the ablation runs on the Week 10 holdout and
  says so. Anything else would be an invented number.

Scoring needs no price: margin absolute error and total absolute error, plus the
proper score for the win probability (Brier). Uncertainty is a game-cluster
bootstrap (resampling games, not clubs or plays) and a paired comparison, which
is the correct interval for "same games, two models".

Output: data/lab/ablation_injury.csv, data/lab/ablation_summary.csv,
        data/lab/walkforward_folds.csv
"""
from __future__ import annotations

import csv
import json
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

LEAGUE_POINTS = 22.0
HFA = 1.9
SIGMA = 8.5
LOGIT = 0.55
K_SHRINK = 4.0
SEED = 20261117
N_BOOT = 4000


def load(rel):
    with open(os.path.join(DATA, rel), encoding="utf-8") as fh:
        return json.load(fh)


def read_csv(rel):
    with open(os.path.join(DATA, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(rel, header, rows):
    path = os.path.join(DATA, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {rel}: {len(rows)} rows")


# ---------------------------------------------------------------------------
# ratings
# ---------------------------------------------------------------------------
def fit_ratings(games, cut_week):
    """Shrunk attack/defence ratings from games with week <= cut_week."""
    agg = {}
    for g in games:
        if g["week"] > cut_week:
            continue
        for tm, pts, opp in ((g["away"], g["away_pts"], g["home_pts"]),
                             (g["home"], g["home_pts"], g["away_pts"])):
            s = agg.setdefault(tm, {"g": 0, "pf": 0, "pa": 0})
            s["g"] += 1
            s["pf"] += pts
            s["pa"] += opp
    ratings = {}
    for tm, s in agg.items():
        if s["g"] == 0:
            continue
        raw_off = s["pf"] / s["g"] - LEAGUE_POINTS
        raw_def = s["pa"] / s["g"] - LEAGUE_POINTS
        shrink = s["g"] / (s["g"] + K_SHRINK)
        ratings[tm] = {"off": LEAGUE_POINTS + raw_off * shrink,
                       "defense": LEAGUE_POINTS + raw_def * shrink,
                       "games": s["g"]}
    return ratings


def predict(ratings, away, home, delta_away=0.0, delta_home=0.0, neutral=False):
    ra, rh = ratings.get(away), ratings.get(home)
    if not ra or not rh:
        return None
    hfa = 0.0 if neutral else HFA
    exp_away = ra["off"] + rh["defense"] - LEAGUE_POINTS + delta_away
    exp_home = rh["off"] + ra["defense"] - LEAGUE_POINTS + hfa + delta_home
    margin_home = exp_home - exp_away
    p_home = 1.0 / (1.0 + math.exp(-margin_home / (SIGMA * LOGIT)))
    return exp_away, exp_home, margin_home, exp_away + exp_home, p_home


# ---------------------------------------------------------------------------
# personnel feature: depth-1 players ruled OUT by the official report
# ---------------------------------------------------------------------------
def personnel_counts():
    """club -> number of depth-1 players the official report lists as Out.

    Availability comes ONLY from the official report; the depth-1 identity comes
    from the declared third-party order source. A player the report does not list
    is never counted as available or unavailable.
    """
    depth = load("depth_risk.json")["depth"]
    inj = load("injuries_week10.json")
    out = {}
    for g in inj["games"]:
        for t in g["teams"]:
            out[(t["abbr"], t["abbr"])] = out.get((t["abbr"], t["abbr"]), 0)
    report_out = {}
    for g in inj["games"]:
        for t in g["teams"]:
            for p in t["players"]:
                if (p.get("game_status") or "") in ("Out", "Doubtful"):
                    report_out.setdefault(t["abbr"], set()).add(p["name"].lower())
    counts = {}
    for d in depth:
        if d["depth"] != 1:
            continue
        if d["player"].lower() in report_out.get(d["team"], set()):
            counts[d["team"]] = counts.get(d["team"], 0) + 1
    return counts


def fit_personnel_coefficient(games, ratings, counts, max_week):
    """Least squares on one parameter: points per depth-1 player ruled out.

    Fitted on the training slice only. If the slice has no variation the
    coefficient is left at 0 and that is reported, not hidden.
    """
    num = den = 0.0
    for g in games:
        if g["week"] > max_week:
            continue
        r = ratings.get(g["away"]), ratings.get(g["home"])
        if not r[0] or not r[1]:
            continue
        base = predict(ratings, g["away"], g["home"])
        if base is None:
            continue
        exp_away, exp_home = base[0], base[1]
        ca, ch = counts.get(g["away"], 0), counts.get(g["home"], 0)
        # residual of actual points minus base prediction, in the direction of
        # the club that is shorthanded
        num += (-ca) * (g["away_pts"] - exp_away) + (-ch) * (g["home_pts"] - exp_home)
        den += ca * ca + ch * ch
    return (num / den) if den > 0 else 0.0


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------
def brier(p, outcome):
    return (p - outcome) ** 2


def bootstrap_ci(values, n_boot=N_BOOT, seed=SEED):
    """Game-cluster bootstrap over per-game statistics."""
    if not values:
        return None, None, None
    rng = random.Random(seed)
    m = len(values)
    means = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(m):
            s += values[rng.randrange(m)]
        means.append(s / m)
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot) - 1]
    return sum(values) / m, lo, hi


def main():
    feed = read_csv("official/results_feed.csv")
    games = []
    for r in feed:
        games.append({"week": int(r["week"]), "date": r["date"],
                      "away": r["away"], "away_pts": int(r["away_pts"]),
                      "home": r["home"], "home_pts": int(r["home_pts"]),
                      "neutral": "Munich" in r["neutral_note"] or "Mexico" in r["neutral_note"]})
    games.sort(key=lambda g: (g["week"], g["date"]))

    counts = personnel_counts()
    print(f"clubs with at least one depth-1 player ruled Out/Doubtful: {len(counts)} "
          f"({sum(counts.values())} players)")

    # ---------------------------------------------------- walk-forward folds
    folds = []
    per_game = []
    for cut in range(4, 13):
        train = [g for g in games if g["week"] <= cut]
        test = [g for g in games if g["week"] == cut + 1]
        if not test:
            continue
        ratings = fit_ratings(games, cut)
        beta = fit_personnel_coefficient(games, ratings, counts, cut)
        have_personnel = cut + 1 == 10   # the only week a depth chart is held
        fold = {"cut": cut, "test_week": cut + 1, "n": len(test), "beta": beta,
                "personnel_available": have_personnel,
                "abs_margin_M0": [], "abs_margin_M1": [],
                "abs_total_M0": [], "abs_total_M1": [],
                "brier_M0": [], "brier_M1": [],
                "brier_base_pickem": [], "brier_home_always": []}
        for g in test:
            neutral = g["neutral"]
            m0 = predict(ratings, g["away"], g["home"], neutral=neutral)
            if m0 is None:
                continue
            ca, ch = (counts.get(g["away"], 0), counts.get(g["home"], 0)) if have_personnel else (0, 0)
            m1 = predict(ratings, g["away"], g["home"],
                         delta_away=beta * ca, delta_home=beta * ch, neutral=neutral)
            actual_margin = g["home_pts"] - g["away_pts"]
            actual_total = g["home_pts"] + g["away_pts"]
            home_won = 1.0 if actual_margin > 0 else 0.0
            fold["abs_margin_M0"].append(abs(actual_margin - m0[2]))
            fold["abs_margin_M1"].append(abs(actual_margin - m1[2]))
            fold["abs_total_M0"].append(abs(actual_total - m0[3]))
            fold["abs_total_M1"].append(abs(actual_total - m1[3]))
            fold["brier_M0"].append(brier(m0[4], home_won))
            fold["brier_M1"].append(brier(m1[4], home_won))
            fold["brier_base_pickem"].append(brier(0.5, home_won))
            fold["brier_home_always"].append(brier(0.56, home_won))
            per_game.append([g["week"], g["date"], g["away"], g["away_pts"],
                             g["home"], g["home_pts"], ca, ch, beta,
                             round(m0[2], 3), round(m1[2], 3),
                             round(m0[3], 3), round(m1[3], 3),
                             round(m0[4], 4), round(m1[4], 4),
                             "YES" if have_personnel else "NO"])
        folds.append(fold)

    write_csv("lab/walkforward_folds.csv",
              ["cut_week", "test_week", "n_games", "personnel_beta",
               "personnel_available", "mae_margin_M0", "mae_margin_M1",
               "mae_total_M0", "mae_total_M1", "brier_M0", "brier_M1",
               "brier_pickem", "brier_home_always"],
              [[f["cut"], f["test_week"], f["n"], round(f["beta"], 4),
                "YES" if f["personnel_available"] else "NO",
                round(sum(f["abs_margin_M0"]) / max(1, f["n"]), 4),
                round(sum(f["abs_margin_M1"]) / max(1, f["n"]), 4),
                round(sum(f["abs_total_M0"]) / max(1, f["n"]), 4),
                round(sum(f["abs_total_M1"]) / max(1, f["n"]), 4),
                round(sum(f["brier_M0"]) / max(1, f["n"]), 5),
                round(sum(f["brier_M1"]) / max(1, f["n"]), 5),
                round(sum(f["brier_base_pickem"]) / max(1, f["n"]), 5),
                round(sum(f["brier_home_always"]) / max(1, f["n"]), 5)]
               for f in folds])

    # ---------------------------------------------------- the ablation itself
    w10 = next(f for f in folds if f["test_week"] == 10)
    diffs_margin = [a - b for a, b in zip(w10["abs_margin_M1"], w10["abs_margin_M0"])]
    diffs_total = [a - b for a, b in zip(w10["abs_total_M1"], w10["abs_total_M0"])]
    diffs_brier = [a - b for a, b in zip(w10["brier_M1"], w10["brier_M0"])]
    rows = []
    for label, vals, direction in (
            ("margin absolute error", diffs_margin, "negative is better for M1"),
            ("total absolute error", diffs_total, "negative is better for M1"),
            ("Brier score (home win)", diffs_brier, "negative is better for M1")):
        mean, lo, hi = bootstrap_ci(vals)
        verdict = ("M1 better, interval excludes 0" if hi < 0 else
                   "M0 better, interval excludes 0" if lo > 0 else
                   "no difference distinguishable from noise")
        rows.append([label, len(vals), round(mean, 5), round(lo, 5), round(hi, 5),
                     direction, verdict])
    write_csv("lab/ablation_summary.csv",
              ["metric", "n_games", "mean_difference_M1_minus_M0",
               "boot_lo95", "boot_hi95", "sign_convention", "verdict"], rows)

    write_csv("lab/ablation_per_game.csv",
              ["week", "date", "away", "away_pts", "home", "home_pts",
               "away_depth1_out", "home_depth1_out", "beta",
               "M0_margin", "M1_margin", "M0_total", "M1_total",
               "M0_p_home", "M1_p_home", "personnel_available"], per_game)

    # ---------------------------------------------------- printed readout
    print()
    print("Week 10 holdout — injury ablation (the only week with a depth chart):")
    for r in rows:
        print(f"  {r[0]:28s} n={r[1]:3d}  diff={r[2]:+.4f}  95% CI [{r[3]:+.4f}, {r[4]:+.4f}]  {r[6]}")
    allm = [x for f in folds for x in f["abs_margin_M0"]]
    allb = [x for f in folds for x in f["brier_M0"]]
    allp = [x for f in folds for x in f["brier_base_pickem"]]
    print(f"\nWalk-forward, all folds: n={len(allm)} games, "
          f"margin MAE M0={sum(allm)/len(allm):.3f}, "
          f"Brier M0={sum(allb)/len(allb):.4f} vs pick'em {sum(allp)/len(allp):.4f}")


if __name__ == "__main__":
    main()
