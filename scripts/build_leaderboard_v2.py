#!/usr/bin/env python3
"""
FL3 — strategy leaderboard v2.

WHAT CHANGED FROM v1, AND WHY
-----------------------------
v1 ranked strategies by season-long ROI. The brief rejects that: ROI is noisy,
needs a price the project does not hold, and rewards luck. v2 ranks by a proper
score (Brier skill against a declared benchmark), reports a game-cluster lower
bound, applies a multiplicity adjustment across the strategies compared, and
prints ROI as UNAVAILABLE rather than as a number.

Each strategy is scored on the SAME 85 walk-forward games (Weeks 5-10), so the
comparison is paired. Four baselines are included by requirement: a 0.5 coin,
always-home, always-away and always-favourite (the favourite is the club with
the better record through the cut — the only definition that needs no price).

Statistics:
  Brier skill    1 - Brier_model / Brier_benchmark, benchmark = 0.5 coin
  cluster CI     game-cluster bootstrap (resampling games, paired)
  lower bound    the 2.5% bootstrap quantile of skill, which is what a claim
                 must survive
  multiplicity   Holm adjustment over the p-values of "skill > 0", each computed
                 from the bootstrap distribution of the paired skill difference
  verdict        DEMOTED_TO_PAPER unless the adjusted lower bound clears 0

Output: data/lab/leaderboard_v2.csv, data/lab/leaderboard_v2.json
"""
from __future__ import annotations

import csv
import json
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

SEED = 20261117
N_BOOT = 4000
LEAGUE_POINTS, HFA, SIGMA, LOGIT, K_SHRINK = 22.0, 1.9, 8.5, 0.55, 4.0
DEMOTION_LOWER_BOUND = 0.0

# R010 (governance): every row this script writes is a RETROSPECTIVE backtest over games that were
# already played when the ranking was computed. It is never a prospective record, so it may never
# be copied into the prospective leaderboard (data/leaderboard.csv, board/data/leaderboard.csv,
# data/dashboard/leaderboard.json). scripts/check_leaderboard_governance.py enforces this.
DATASET_TYPE = "RETROSPECTIVE_BACKTEST"
PROSPECTIVE = False


def read_csv(rel):
    with open(os.path.join(DATA, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load(rel):
    with open(os.path.join(DATA, rel), encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(rel, header, rows):
    path = os.path.join(DATA, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {rel}: {len(rows)} rows")


def fit_ratings(games, cut):
    agg = {}
    rec = {}
    for g in games:
        if g["week"] > cut:
            continue
        for tm, pts, opp in ((g["away"], g["away_pts"], g["home_pts"]),
                             (g["home"], g["home_pts"], g["away_pts"])):
            s = agg.setdefault(tm, {"g": 0, "pf": 0, "pa": 0})
            s["g"] += 1
            s["pf"] += pts
            s["pa"] += opp
            r = rec.setdefault(tm, {"w": 0, "l": 0, "t": 0})
            if pts > opp:
                r["w"] += 1
            elif pts < opp:
                r["l"] += 1
            else:
                r["t"] += 1
    ratings = {}
    for tm, s in agg.items():
        sh = s["g"] / (s["g"] + K_SHRINK)
        ratings[tm] = {"off": LEAGUE_POINTS + (s["pf"] / s["g"] - LEAGUE_POINTS) * sh,
                       "defense": LEAGUE_POINTS + (s["pa"] / s["g"] - LEAGUE_POINTS) * sh,
                       "pct": (rec[tm]["w"] + 0.5 * rec[tm]["t"]) / max(1, s["g"])}
    return ratings


def p_from_margin(m):
    return 1.0 / (1.0 + math.exp(-m / (SIGMA * LOGIT)))


def strategies(ratings, g):
    """Every strategy is a probability of the HOME club winning. No price."""
    ra, rh = ratings.get(g["away"]), ratings.get(g["home"])
    out = {}
    if ra and rh:
        margin = (rh["off"] + ra["defense"]) - (ra["off"] + rh["defense"])
        margin += 0.0 if g["neutral"] else HFA
        out["FL3-SHADOW-1 (ratings)"] = p_from_margin(margin)
        out["FL3 ratings, no home edge"] = p_from_margin(margin - (0.0 if g["neutral"] else HFA))
        out["Rating differential, overconfident"] = p_from_margin(margin * 1.5)
        out["Rating differential, cautious"] = p_from_margin(margin * 0.5)
        out["Record-only (no points)"] = 0.5 + 0.5 * (rh["pct"] - ra["pct"])
    else:
        for k in ("FL3-SHADOW-1 (ratings)", "FL3 ratings, no home edge",
                  "Rating differential, overconfident", "Rating differential, cautious",
                  "Record-only (no points)"):
            out[k] = 0.5
    # baselines
    out["BASELINE coin 0.5"] = 0.5
    out["BASELINE always home"] = 1.0
    out["BASELINE always away"] = 0.0
    fav_home = 1.0 if (rh and ra and rh["pct"] >= ra["pct"]) else 0.0
    out["BASELINE always favourite"] = fav_home
    return out


def brier(p, y):
    return (p - y) ** 2


def holm(pvals):
    """Holm step-down adjusted p-values, order preserved."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


def build_strategy_payload(results):
    payload = []
    for i, r in enumerate(results, 1):
        baseline = r["name"].startswith("BASELINE")
        payload.append({
            "rank": i,
            "strategy": r["name"],
            "brier": round(r["brier"], 5),
            "brier_skill_vs_coin": round(r["skill"], 4),
            "boot_lo95": round(r["lo"], 4),
            "boot_hi95": round(r["hi"], 4),
            "cluster_lower_bound": round(r["lower_bound"], 4),
            "p_skill_gt_0": r["p_skill_gt_0"],
            "p_holm_adjusted": r["p_holm"],
            "roi": None,
            "roi_status": "UNAVAILABLE — PD-01",
            "verdict": r["verdict"],
            "what_would_change_our_mind": (
                ["Nothing — this row exists to be beaten by the others."] if baseline else
                ["A cluster lower bound that stays above zero on games the strategy did "
                 "not see when it was fitted (a second season).",
                 "The same sign of skill on a different scoring rule (log loss), so the "
                 "result is not an artefact of Brier."]),
            "what_would_falsify_it": (
                ["A model that fails to beat it."] if baseline else
                ["A bootstrap interval that includes zero once a second season is added.",
                 "Skill that flips sign between Weeks 5-7 and Weeks 8-10."]),
        })
    return payload


def main():
    feed = read_csv("official/results_feed.csv")
    games = []
    for r in feed:
        games.append({"week": int(r["week"]), "date": r["date"],
                      "away": r["away"], "away_pts": int(r["away_pts"]),
                      "home": r["home"], "home_pts": int(r["home_pts"]),
                      "neutral": "Munich" in r["neutral_note"] or "Mexico" in r["neutral_note"]})
    games.sort(key=lambda g: (g["week"], g["date"]))

    names = None
    per_game = []
    for cut in range(4, 10):
        test = [g for g in games if g["week"] == cut + 1]
        if not test:
            continue
        ratings = fit_ratings(games, cut)
        for g in test:
            y = 1.0 if g["home_pts"] > g["away_pts"] else 0.0
            s = strategies(ratings, g)
            names = names or list(s)
            per_game.append({"week": g["week"], "y": y, "s": s})

    n = len(per_game)
    print(f"scored {n} games x {len(names)} strategies, paired")

    results = []
    for name in names:
        ps = [r["s"][name] for r in per_game]
        ys = [r["y"] for r in per_game]
        b = sum(brier(p, y) for p, y in zip(ps, ys)) / n
        b_pickem = sum(brier(0.5, y) for y in ys) / n
        skill = 1 - b / b_pickem if b_pickem else 0.0
        results.append({"name": name, "brier": b, "skill": skill,
                        "p": ps, "y": ys})

    # paired game-cluster bootstrap for skill
    rng = random.Random(SEED)
    idxs = list(range(n))
    for _ in range(N_BOOT):
        sample = [idxs[rng.randrange(n)] for _ in range(n)]
        bp = sum(brier(0.5, per_game[i]["y"]) for i in sample) / n
        for r in results:
            bm = sum(brier(r["p"][i], per_game[i]["y"]) for i in sample) / n
            r.setdefault("boot_skill", []).append(1 - bm / bp if bp else 0.0)

    for r in results:
        r["boot_skill"].sort()
        r["lo"] = r["boot_skill"][int(0.025 * N_BOOT)]
        r["hi"] = r["boot_skill"][int(0.975 * N_BOOT) - 1]
        # one-sided p for skill > 0 from the bootstrap distribution
        below = sum(1 for v in r["boot_skill"] if v <= 0)
        r["p_skill_gt_0"] = below / N_BOOT

    # multiplicity: only the genuinely proposed strategies are tested; the
    # baselines are the reference, not claims.
    testable = [r for r in results if not r["name"].startswith("BASELINE")]
    adj = holm([r["p_skill_gt_0"] for r in testable])
    for r, a in zip(testable, adj):
        r["p_holm"] = a
    for r in results:
        r.setdefault("p_holm", "")

    for r in results:
        r["lower_bound"] = min(r["lo"], r["skill"])
        if r["name"].startswith("BASELINE"):
            r["verdict"] = "BASELINE (reference, not a claim)"
        elif r["p_holm"] != "" and r["p_holm"] < 0.05 and r["lower_bound"] > DEMOTION_LOWER_BOUND:
            r["verdict"] = "SKILL_ESTABLISHED"
        else:
            r["verdict"] = "DEMOTED_TO_PAPER"

    results.sort(key=lambda r: -r["skill"])
    rows = []
    for i, r in enumerate(results, 1):
        rows.append([
            i, r["name"], "PROBABILITY_OF_HOME_WIN", n,
            round(r["brier"], 5), round(r["brier"], 5),
            round(r["skill"], 4), round(r["lo"], 4), round(r["hi"], 4),
            round(r["lower_bound"], 4),
            round(r["p_skill_gt_0"], 5),
            "" if r["p_holm"] == "" else round(r["p_holm"], 5),
            "UNAVAILABLE (PD-01: no licensed price)" if not r["name"].startswith("BASELINE") else "n/a baseline",
            r["verdict"],
            DATASET_TYPE, "false",
        ])
    write_csv("lab/leaderboard_v2.csv",
              ["rank", "strategy", "scored_field", "n_games",
               "brier", "brier_benchmark", "brier_skill_vs_coin",
               "boot_lo95", "boot_hi95", "cluster_lower_bound",
               "p_skill_gt_0", "p_holm_adjusted", "roi", "verdict",
               "dataset_type", "prospective"], rows)

    # JSON with the full detail the page renders
    out = {
        "_meta": {
            "title": "FL3 strategy leaderboard v2 — proper-score ranking (RETROSPECTIVE, not prospective)",
            "dataset_type": DATASET_TYPE,
            "prospective": PROSPECTIVE,
            "eligible_for_prospective_leaderboard": False,
            "governance": "R010: backtest-origin numbers may not appear on the prospective leaderboard. Games scored here were all played before this ranking was computed.",
            "generated_utc": "2026-11-17T02:47Z",
            "n_games": n,
            "seasons": ["2026"],
            "weeks_tested": sorted({g["week"] for g in per_game}),
            "benchmark": "coin flip p=0.5 for the home club",
            "score": "Brier, lower is better; skill = 1 - Brier/Brier(coin)",
            "uncertainty": f"game-cluster bootstrap, {N_BOOT} resamples, seed {SEED}",
            "multiplicity": "Holm over the non-baseline strategies",
            "demotion_rule": f"DEMOTED_TO_PAPER unless Holm-adjusted p < 0.05 and the "
                             f"2.5% cluster lower bound is > {DEMOTION_LOWER_BOUND}",
            "roi_policy": "PD-01 — no licensed price is held, so ROI is UNAVAILABLE for "
                          "every strategy. It is never reported as zero.",
            "why_not_win_rate": "Win rate ignores confidence and drops ties; a strategy "
                                "that says 0.51 every week and one that says 0.99 are "
                                "indistinguishable to it.",
        },
        "benchmark_brier": round(sum(brier(0.5, r["y"]) for r in per_game) / n, 5),
        "strategies": build_strategy_payload(results),
    }
    for row in out["strategies"]:
        row["dataset_type"] = DATASET_TYPE
        row["prospective"] = PROSPECTIVE
    path = os.path.join(DATA, "lab", "leaderboard_v2.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(f"wrote lab/leaderboard_v2.json")

    print()
    for r in results:
        print(f"  {r['name']:38s} skill={r['skill']:+.4f} "
              f"[{r['lo']:+.4f},{r['hi']:+.4f}] holm={r['p_holm']} {r['verdict']}")


if __name__ == "__main__":
    main()
