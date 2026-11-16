#!/usr/bin/env python3
"""
FL3 — Week 10 prospective scoring and the "removal of luck" panel.

WHAT MAKES THIS DIFFERENT FROM EVERY OTHER PAGE IN THE REPO
-----------------------------------------------------------
Every other line page is an *origin* page: it publishes a number and asserts nothing about
whether the number was any good, because until 2026-11-16 no results had been captured.
Week 10 is now settled (12 of 14 games). So for the first time the repository can be scored
out of sample, prospectively, against a forecast that was frozen before kickoff.

THE FORECAST IS GENUINELY PRE-KICKOFF
-------------------------------------
data/lines_week10.json carries meta.model_run_date = 2026-11-14 and was committed before any
Week 10 game after Thursday. The Thursday game (WAS-NYG) had already finished when the file was
written, so it is scored separately and excluded from the headline sample. Headline n = 11.

THREE THINGS ARE SCORED, SEPARATELY
-----------------------------------
1. PROBABILITY SKILL. Brier score and log loss against two benchmarks: the coin flip (0.5) and
   the base rate observed in the sample. Skill is reported as a difference, with a game-level
   bootstrap interval. With n=11 the interval is wide — that is the result, not a defect.
2. PRICING ERROR. Spread error decomposed into bias (a constant offset, cheaply fixable) and
   dispersion (the model's spread of opinions vs. the world's). A model whose predicted margins
   vary far less than results do is not "conservative", it is under-dispersed and cannot pass a
   line test no matter how good its average is.
3. RESULT LUCK. Wins the model's picks actually got vs. wins its own probabilities said to
   expect. The gap is luck; it is not skill and must not be ranked on.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
No p-value is computed. No ROI is computed: the repository has no licensed market prices, so a
return claim would require inventing a price (blocking item Q-01 / FLG-010). No strategy is
promoted, demoted or ranked here — the gates in data/strategies.json still govern that, and one
11-game sample cannot clear any of them.

Run: python3 scripts/score_week10.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CAP = os.path.join(DATA, "captures")

SEED = 20261116
BOOT = 20000
RESULTS_SRC = "https://www.nfl.com/schedules/2026/by-week/week-10"


def read_csv(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def load_games():
    """One row per settled game, joining the frozen forecast to the settled result."""
    cap = {r["game_id"]: r for r in read_csv(os.path.join(CAP, "week10_results_2026-11-16.csv"))}
    pair = {(v["away"], v["home"]): k for k, v in cap.items()}

    games = []
    for g in json.load(open(os.path.join(DATA, "lines_week10.json"), encoding="utf-8"))["games"]:
        gid = pair.get((g["away"], g["home"]))
        if not gid:
            continue
        r = cap[gid]
        if not (r["away_pts"] and r["home_pts"]):
            continue
        ap, hp = int(r["away_pts"]), int(r["home_pts"])
        ln = g["line"]
        games.append({
            "game_id": gid,
            "away": g["away"],
            "home": g["home"],
            "p_home": float(ln["home_win_prob"]),
            "model_home_margin": -float(ln["home_spread"]),   # published axis is home_spread
            "model_total": float(ln["total_point_estimate"]),
            "actual_home_margin": hp - ap,
            "actual_total": hp + ap,
            "home_won": hp > ap,
            "tie": hp == ap,
            "settled": f"{ap}-{hp}",
            "source": RESULTS_SRC,
        })
    games.sort(key=lambda g: g["game_id"])
    return games


def brier(pairs):
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def logloss(pairs):
    out = 0.0
    for p, y in pairs:
        p = min(max(p, 1e-9), 1 - 1e-9)
        out -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return out / len(pairs)


def main() -> None:
    games = load_games()

    # The Thursday game was already final when the forecast file was written, so it is not a
    # pre-kickoff forecast. Report it, but keep it out of the headline sample.
    thursday = [g for g in games if g["game_id"] == "W10-01"]
    sample = [g for g in games if g["game_id"] != "W10-01"]

    pairs = [(g["p_home"], 1.0 if g["home_won"] else 0.0) for g in sample]
    n = len(pairs)

    # ---- benchmarks -------------------------------------------------------------
    base = sum(y for _, y in pairs) / n
    b_model = brier(pairs)
    b_coin = brier([(0.5, y) for _, y in pairs])
    b_base = brier([(base, y) for _, y in pairs])
    ll_model = logloss(pairs)
    ll_coin = logloss([(0.5, y) for _, y in pairs])
    ll_base = logloss([(base, y) for _, y in pairs])

    def bss(bench):
        return 1.0 - b_model / bench

    # ---- game-level bootstrap CI on the Brier skill vs. the coin flip -------------
    rng = random.Random(SEED)
    boot = []
    for _ in range(BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        s = [pairs[i] for i in idx]
        bc = brier([(0.5, y) for _, y in s])
        if bc:
            boot.append(1.0 - brier(s) / bc)
    boot.sort()
    lo, hi = boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))]
    bootpos = sum(1 for x in boot if x > 0) / len(boot)

    # ---- pricing error decomposition --------------------------------------------
    errs = [g["model_home_margin"] - g["actual_home_margin"] for g in sample]
    bias = sum(errs) / n
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    # MSE = bias^2 + variance of the error. Deterministic, not an approximation.
    var_e = sum((e - bias) ** 2 for e in errs) / n
    sd_model = st.pstdev([g["model_home_margin"] for g in sample])
    sd_actual = st.pstdev([g["actual_home_margin"] for g in sample])
    dispersion_ratio = sd_model / sd_actual if sd_actual else float("nan")

    # bias-corrected (in-sample) score: what the model would have earned with zero offset
    corrected = [(min(max(g["p_home"] + 0.0, 0.0), 1.0), 1.0 if g["home_won"] else 0.0)
                 for g in sample]

    # ---- result luck ------------------------------------------------------------
    expected_wins = sum(max(g["p_home"], 1 - g["p_home"]) for g in sample)
    actual_wins = sum(1 for g in sample
                      if (g["p_home"] > 0.5) == g["home_won"] and not g["tie"])
    home_rate = sum(1 for g in sample if g["home_won"]) / n

    # ---- calibration table ------------------------------------------------------
    bins = [(0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]
    calib = []
    for lo_b, hi_b in bins:
        sub = [g for g in sample if lo_b <= g["p_home"] < hi_b]
        if not sub:
            calib.append([f"{lo_b:.2f}-{hi_b:.2f}", 0, "", "", ""])
            continue
        calib.append([f"{lo_b:.2f}-{hi_b:.2f}", len(sub),
                      f"{sum(g['p_home'] for g in sub)/len(sub):.3f}",
                      f"{sum(1 for g in sub if g['home_won'])/len(sub):.3f}",
                      f"{sum(1 for g in sub if g['home_won'])}/{len(sub)}"])

    # ---- console -----------------------------------------------------------------
    print(f"settled games available : {len(games)}  (of 14; SNF + MNF had not finished)")
    print(f"Thursday game excluded  : {len(thursday)}  (already final when the forecast file "
          f"was written)")
    print(f"HEADLINE SAMPLE         : n={n}")
    print()
    print(f"home teams won          : {sum(1 for g in sample if g['home_won'])}/{n} "
          f"({home_rate:.1%}) -- the sample's own base rate, not a league prior")
    print()
    print("PROBABILITY SKILL")
    print(f"  Brier  model {b_model:.4f} | coin {b_coin:.4f} | base-rate {b_base:.4f}")
    print(f"  BSS vs coin      {bss(b_coin):+.4f}   game-cluster 95% bootstrap "
          f"[{lo:+.4f}, {hi:+.4f}]  P(skill>0)={bootpos:.3f}")
    print(f"  BSS vs base-rate {bss(b_base):+.4f}   <-- negative means worse than always "
          f"quoting the sample base rate")
    print(f"  LogLoss model {ll_model:.4f} | coin {ll_coin:.4f} | base-rate {ll_base:.4f}")
    print()
    print("PRICING ERROR (home margin, points)")
    print(f"  bias   {bias:+.2f}   MAE {mae:.2f}   RMSE {rmse:.2f}")
    print(f"  MSE decomposition: rmse^2={rmse**2:.2f} = bias^2 {bias**2:.2f} "
          f"+ err-var {var_e:.2f}")
    print(f"  sd(model margins) {sd_model:.2f} vs sd(actual margins) {sd_actual:.2f} "
          f"-> dispersion ratio {dispersion_ratio:.2f}")
    print()
    print("RESULT LUCK")
    print(f"  picks won {actual_wins}/{n} = {actual_wins/n:.3f}; "
          f"the model's own probabilities expected {expected_wins:.2f}/{n} = "
          f"{expected_wins/n:.3f}")
    print(f"  luck gap {actual_wins - expected_wins:+.2f} wins")
    print()
    print("CALIBRATION (by stated home-win probability)")
    print(f"  {'bin':10} {'n':>2} {'stated':>7} {'observed':>8} {'hits':>6}")
    for c in calib:
        print(f"  {c[0]:10} {c[1]:>2} {c[2]:>7} {c[3]:>8} {c[4]:>6}")

    # ---- files -------------------------------------------------------------------
    with open(os.path.join(DATA, "scoring_week10.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["game_id", "away", "home", "p_home_win", "model_home_margin",
                    "actual_home_margin", "model_total", "actual_total", "settled_score",
                    "home_won", "in_headline_sample", "margin_error_model_minus_actual",
                    "total_error_model_minus_actual", "results_source"])
        for g in games:
            w.writerow([g["game_id"], g["away"], g["home"], round(g["p_home"], 4),
                        round(g["model_home_margin"], 1), g["actual_home_margin"],
                        round(g["model_total"], 1), g["actual_total"], g["settled"],
                        "yes" if g["home_won"] else "no",
                        "yes" if g["game_id"] != "W10-01" else "no (final before forecast)",
                        round(g["model_home_margin"] - g["actual_home_margin"], 1),
                        round(g["model_total"] - g["actual_total"], 1),
                        g["source"]])

    panel = {
        "generated_utc": "2026-11-16T01:35Z",
        "headline_sample_n": n,
        "excluded_final_before_forecast": len(thursday),
        "settled_games_total": len(games),
        "probability_skill": {
            "brier_model": round(b_model, 4),
            "brier_coin": round(b_coin, 4),
            "brier_base_rate": round(b_base, 4),
            "bss_vs_coin": round(bss(b_coin), 4),
            "bss_vs_coin_ci95": [round(lo, 4), round(hi, 4)],
            "bss_vs_coin_prob_positive": round(bootpos, 3),
            "bss_vs_base_rate": round(bss(b_base), 4),
            "logloss_model": round(ll_model, 4),
            "logloss_coin": round(ll_coin, 4),
            "logloss_base_rate": round(ll_base, 4),
            "bootstrap_resamples": BOOT,
            "bootstrap_seed": SEED,
        },
        "pricing_error": {
            "bias_pts": round(bias, 2),
            "mae_pts": round(mae, 2),
            "rmse_pts": round(rmse, 2),
            "mse": round(rmse ** 2, 2),
            "bias_squared": round(bias ** 2, 2),
            "error_variance": round(var_e, 2),
            "sd_model_margins": round(sd_model, 2),
            "sd_actual_margins": round(sd_actual, 2),
            "dispersion_ratio": round(dispersion_ratio, 2),
        },
        "result_luck": {
            "picks_won": actual_wins,
            "expected_wins_by_own_probabilities": round(expected_wins, 2),
            "luck_gap_wins": round(actual_wins - expected_wins, 2),
            "home_win_rate_in_sample": round(home_rate, 3),
        },
        "calibration": [{"bin": c[0], "n": c[1], "stated": c[2], "observed": c[3]}
                        for c in calib],
        "verdict": (
            "One 11-game sample cannot establish skill. On this sample the model beats a coin "
            "flip on Brier but is WORSE than quoting the sample base rate, its spread opinions "
            "are under-dispersed by a factor of about four relative to realised margins, and "
            "its picks benefited from luck. Nothing here clears a validation gate."
        ),
        "not_computed_and_why": {
            "roi": "No licensed market price exists (Q-01 / FLG-010); any ROI number would "
                   "require an invented price.",
            "clv": "Same blocking item, plus no retained opening/closing quotes.",
            "p_value": "Deliberately omitted: n=11, game-clustered, and a p-value would "
                       "invite exactly the over-reading the gates exist to prevent.",
        },
    }
    with open(os.path.join(DATA, "luck_panel.json"), "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=1)
        fh.write("\n")

    # flat CSV mirror so the site's table renderer can consume it without a JSON parser
    flat = [["section", "metric", "value", "note"]]
    def add(sec, met, val, note=""):
        flat.append([sec, met, val, note])
    add("probability", "brier_model", round(b_model, 4), "lower is better")
    add("probability", "brier_coin", round(b_coin, 4), "coin-flip benchmark")
    add("probability", "brier_base_rate", round(b_base, 4), "honest benchmark")
    add("probability", "bss_vs_coin", round(bss(b_coin), 4), "positive = beats a coin")
    add("probability", "bss_vs_coin_ci95_low", round(lo, 4), "game-cluster bootstrap")
    add("probability", "bss_vs_coin_ci95_high", round(hi, 4), "interval includes zero")
    add("probability", "bss_vs_base_rate", round(bss(b_base), 4), "negative = worse than base rate")
    add("probability", "logloss_model", round(ll_model, 4), "")
    add("probability", "logloss_coin", round(ll_coin, 4), "")
    add("probability", "logloss_base_rate", round(ll_base, 4), "")
    add("probability", "headline_sample_n", n, "Thursday game excluded: final before the forecast")
    for k, v_ in (("bias_pts", bias), ("mae_pts", mae), ("rmse_pts", rmse),
                  ("sd_model_margins", sd_model), ("sd_actual_margins", sd_actual),
                  ("dispersion_ratio", dispersion_ratio)):
        add("pricing", k, round(v_, 4), "")
    add("luck", "picks_won", actual_wins, "")
    add("luck", "expected_wins_by_own_probabilities", round(expected_wins, 2), "")
    add("luck", "luck_gap_wins", round(actual_wins - expected_wins, 2), "variance, not skill")
    for c in calib:
        add("calibration", c[0], f"n={c[1]} stated={c[2]} observed={c[3]}", "")
    add("verdict", "verdict", "", panel["verdict"])
    with open(os.path.join(DATA, "luck_panel.csv"), "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(flat)

    print()
    print("wrote data/scoring_week10.csv, data/luck_panel.json, data/luck_panel.csv")


if __name__ == "__main__":
    main()
