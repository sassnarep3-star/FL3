#!/usr/bin/env python3
"""
FL3 — injury / availability ablation (readiness R028, R029)

The brief asks to replace fixed injury penalties with *measured* ablations:

    "Add injury/depth ablations, not fixed penalties. Compare identical models
     with and without verified availability features using chronological holdouts."

This harness does exactly that, deterministically, over data that has already
passed scripts/verify.py:

  * It runs the SAME originated-line model twice on the SAME holdout games.
      - Variant A "availability ON": the model as published, applying the capped
        availability adjustment built from the official Week 10 injury report.
      - Variant B "availability OFF": the identical model with the availability
        adjustment zeroed (no availability features).
  * The split is CHRONOLOGICAL: ratings are calibrated on Weeks 1-9 and every
    forecast is scored against the verified Week 10 results that were played
    after those ratings were fixed.
  * Scores are MAE / RMSE for the spread and the total, and Brier for the home
    win probability, each with a bootstrap 95% CI and an explicit n.
  * The paired difference (A - B) is bootstrapped the same way. If a CI spans
    zero, the harness says so: it never reports a difference as skill.

Only *verified availability features* are used (injury-report game statuses).
Depth-tier features are deliberately excluded: the depth-tier source is
unverified for most clubs (R042 is BLOCKED), so the brief's own gate forbids
building that feature until a route is verified for all 32 clubs.

This is a model-evaluation study. Its numbers are NOT placed on the leaderboard
(the brief forbids backtest numbers on the leaderboard); they are published on
the dedicated Ablations page, badged as model output.

Outputs
  data/ablations_week10.json   full result (summary + per-game rows + meta)
  data/ablations_week10.csv    flat per-game + summary tables for the site
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compute_lines import (  # noqa: E402
    MODEL,
    SRC_INJ,
    availability,
    build_power,
    norm_cdf,
)
from lib_fl3 import write_rows  # noqa: E402

SRC_STAND = "https://www.nfl.com/standings/division/2026/REG"
SRC_RESULTS = "https://www.nfl.com/schedules/2026/REG10"

BOOTSTRAP = 20000
SEED = 20261117
CAL_WEEK_MAX = 9          # calibration window: Weeks 1-9
HOLD_WEEK = 10            # chronological holdout: Week 10


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #
def load_results() -> list[dict]:
    with open(os.path.join(DATA, "week_results_2026.csv"), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_injuries() -> dict:
    with open(os.path.join(DATA, "injuries_week10.json"), encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# chronological split + cumulative standings reconstructed from verified scores
# --------------------------------------------------------------------------- #
def cumulative_standings(rows: list[dict]) -> dict:
    """Build a standings dict (the shape build_power expects) from per-game scores.

    Every figure is a sum of verified game scores; nothing is inferred.
    """
    teams: dict[str, dict] = {}
    for r in rows:
        wa, ha = r["away_abbr"], r["home_abbr"]
        ap, hp = int(r["away_pts"]), int(r["home_pts"])
        for abbr, pf, pa in ((wa, ap, hp), (ha, hp, ap)):
            t = teams.setdefault(abbr, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            t["pf"] += pf
            t["pa"] += pa
            if pf > pa:
                t["w"] += 1
            elif pf < pa:
                t["l"] += 1
            else:
                t["t"] += 1
    out = []
    for abbr, t in teams.items():
        gp = t["w"] + t["l"] + t["t"]
        out.append(
            {
                "abbr": abbr,
                "w": t["w"],
                "l": t["l"],
                "t": t["t"],
                "pf": t["pf"],
                "pa": t["pa"],
                "pct": round(t["w"] / gp, 3) if gp else 0.0,
            }
        )
    return {
        "meta": {
            "title": "Cumulative standings reconstructed from verified per-game scores",
            "source": SRC_RESULTS,
            "note": "W/L/T and PF/PA are sums of verified Week 1-9 game scores; no standings page is assumed.",
        },
        "teams": out,
    }


# --------------------------------------------------------------------------- #
# forecasting (identical model; only the availability adjustment differs)
# --------------------------------------------------------------------------- #
def sigma_spread(gp_a: int, gp_h: int) -> float:
    est = math.sqrt(1.0 + MODEL["sigma_k"] / max(min(gp_a, gp_h), 1))
    return MODEL["single_game_sigma"] * est


def forecast(power, avail, a, h, use_availability: bool) -> dict:
    """Forecast one game. Variant differs ONLY in the availability adjustment."""
    pa_, ph_ = power["teams"][a], power["teams"][h]
    zero = {"off": 0.0, "def": 0.0, "st": 0.0}
    av_a = avail.get(a, {"capped": zero})["capped"]
    av_h = avail.get(h, {"capped": zero})["capped"]
    if not use_availability:
        av_a, av_h = zero, zero

    exp_away = (pa_["off_shrunk"] + ph_["def_shrunk"]) / 2.0
    exp_home = (ph_["off_shrunk"] + pa_["def_shrunk"]) / 2.0
    exp_away -= av_a["off"]
    exp_away += av_h["def"]
    exp_home -= av_h["off"]
    exp_home += av_a["def"]
    exp_away -= av_a["st"] / 2.0
    exp_home -= av_h["st"] / 2.0
    exp_home += MODEL["hfa_points"]

    total = exp_away + exp_home
    margin = exp_home - exp_away
    sig = sigma_spread(pa_["gp"], ph_["gp"])
    home_wp = norm_cdf(margin, 0.0, sig)
    return {
        "margin": margin,
        "total": total,
        "home_wp": home_wp,
        "sigma_spread": sig,
        "away_availability": av_a,
        "home_availability": av_h,
    }


def err(pred: float, actual: float) -> float:
    return abs(pred - actual)


# --------------------------------------------------------------------------- #
# bootstrap uncertainty
# --------------------------------------------------------------------------- #
def boot_ci(values: list[float], rng: random.Random, reps: int = BOOTSTRAP) -> tuple[float, float]:
    if not values:
        return (None, None)
    arr = sorted(values)
    cis = []
    n = len(arr)
    for _ in range(reps):
        s = sum(rng.choice(arr) for _ in range(n)) / n
        cis.append(s)
    cis.sort()
    lo = cis[int(0.025 * reps)]
    hi = cis[int(0.975 * reps)]
    return (lo, hi)


def mean_rmse(values: list[float]) -> tuple[float, float]:
    if not values:
        return (None, None)
    m = sum(values) / len(values)
    rmse = math.sqrt(sum(v * v for v in values) / len(values))
    return (m, rmse)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    rows = load_results()
    injuries = load_injuries()

    calib = [r for r in rows if int(r["week"]) <= CAL_WEEK_MAX]
    holdout = [r for r in rows if int(r["week"]) == HOLD_WEEK]
    holdout.sort(key=lambda r: (r["game_date"], r["away_abbr"], r["home_abbr"]))

    # ratings fixed on Weeks 1-9 only -> chronological holdout on Week 10
    standings9 = cumulative_standings(calib)
    power = build_power(standings9)
    avail = availability(injuries)

    per_game = []
    a_spread, a_total, a_brier = [], [], []
    b_spread, b_total, b_brier = [], [], []
    diff_spread, diff_total, diff_brier = [], [], []

    for r in holdout:
        a, h = r["away_abbr"], r["home_abbr"]
        ap, hp = int(r["away_pts"]), int(r["home_pts"])
        actual_margin = hp - ap
        actual_total = ap + hp
        actual_home_win = 1.0 if hp > ap else (0.5 if hp == ap else 0.0)

        fa = forecast(power, avail, a, h, use_availability=True)
        fb = forecast(power, avail, a, h, use_availability=False)

        se_a, se_b = err(fa["margin"], actual_margin), err(fb["margin"], actual_margin)
        te_a, te_b = err(fa["total"], actual_total), err(fb["total"], actual_total)
        br_a = (fa["home_wp"] - actual_home_win) ** 2
        br_b = (fb["home_wp"] - actual_home_win) ** 2

        a_spread.append(se_a); a_total.append(te_a); a_brier.append(br_a)
        b_spread.append(se_b); b_total.append(te_b); b_brier.append(br_b)
        diff_spread.append(se_a - se_b)
        diff_total.append(te_a - te_b)
        diff_brier.append(br_a - br_b)

        per_game.append(
            {
                "week": r["week"],
                "game_date": r["game_date"],
                "away": a,
                "home": h,
                "actual_away_pts": ap,
                "actual_home_pts": hp,
                "actual_margin": actual_margin,
                "actual_total": actual_total,
                "pred_margin_avail_on": round(fa["margin"], 2),
                "pred_margin_avail_off": round(fb["margin"], 2),
                "pred_total_avail_on": round(fa["total"], 2),
                "pred_total_avail_off": round(fb["total"], 2),
                "pred_home_wp_on": round(fa["home_wp"], 4),
                "pred_home_wp_off": round(fb["home_wp"], 4),
                "away_avail_on": fa["away_availability"],
                "home_avail_on": fa["home_availability"],
                "spread_err_on": round(se_a, 2),
                "spread_err_off": round(se_b, 2),
                "total_err_on": round(te_a, 2),
                "total_err_off": round(te_b, 2),
                "brier_on": round(br_a, 4),
                "brier_off": round(br_b, 4),
                "results_source_url": r["source_url"],
                "injury_source": SRC_INJ,
            }
        )

    rng = random.Random(SEED)

    def summarize(label, errs, briers):
        m, rmse = mean_rmse(errs)
        ci = boot_ci(errs, rng)
        bmean = sum(briers) / len(briers) if briers else None
        bci = boot_ci(briers, rng)
        return {
            "variant": label,
            "n": len(errs),
            "spread_mae": round(m, 3) if m is not None else None,
            "spread_mae_ci95": [round(ci[0], 3), round(ci[1], 3)] if ci[0] is not None else None,
            "spread_rmse": round(rmse, 3) if rmse is not None else None,
            "total_mae": None,
            "total_mae_ci95": None,
            "total_rmse": None,
            "brier": round(bmean, 4) if bmean is not None else None,
            "brier_ci95": [round(bci[0], 4), round(bci[1], 4)] if bci[0] is not None else None,
        }

    def summarize_total(label, errs):
        m, rmse = mean_rmse(errs)
        ci = boot_ci(errs, rng)
        return {
            "variant": label,
            "total_mae": round(m, 3) if m is not None else None,
            "total_mae_ci95": [round(ci[0], 3), round(ci[1], 3)] if ci[0] is not None else None,
            "total_rmse": round(rmse, 3) if rmse is not None else None,
        }

    sa = summarize("availability ON", a_spread, a_brier)
    sb = summarize("availability OFF", b_spread, b_brier)
    ta = summarize_total("availability ON", a_total)
    tb = summarize_total("availability OFF", b_total)

    d_m, d_rmse = mean_rmse(diff_spread)
    d_ci = boot_ci(diff_spread, rng)
    t_m = sum(diff_total) / len(diff_total) if diff_total else None
    t_ci = boot_ci(diff_total, rng)
    b_m = sum(diff_brier) / len(diff_brier) if diff_brier else None
    b_ci = boot_ci(diff_brier, rng)

    def verdict(mean, ci, metric, lower_is_better=True):
        if ci[0] is None:
            return "insufficient games"
        lo, hi = ci
        if lo <= 0 <= hi:
            return (
                "The 95%% CI on the paired %s difference includes zero: the availability features do "
                "not demonstrate a measurable change on this holdout. No %s advantage is claimed."
                % (metric, "skill" if lower_is_better else "skill")
            )
        improved = mean < 0 if lower_is_better else mean < 0
        if improved:
            return (
                "The availability features reduce %s on this holdout and the paired 95%% CI excludes "
                "zero. Promising, but n is small; treat as a single-window result." % metric
            )
        return (
            "The availability features increase %s on this holdout and the paired 95%% CI excludes "
            "zero. The adjustment is not helping in this window." % metric
        )

    diff = {
        "n": len(diff_spread),
        "spread_mae": {
            "diff_on_minus_off": round(d_m, 3) if d_m is not None else None,
            "diff_ci95": [round(d_ci[0], 3), round(d_ci[1], 3)] if d_ci[0] is not None else None,
            "rmse_diff_on_minus_off": round(d_rmse, 3) if d_rmse is not None else None,
            "verdict": verdict(d_m, d_ci, "spread MAE"),
        },
        "total_mae": {
            "diff_on_minus_off": round(t_m, 3) if t_m is not None else None,
            "diff_ci95": [round(t_ci[0], 3), round(t_ci[1], 3)] if t_ci[0] is not None else None,
            "verdict": verdict(t_m, t_ci, "total MAE"),
        },
        "brier": {
            "diff_on_minus_off": round(b_m, 4) if b_m is not None else None,
            "diff_ci95": [round(b_ci[0], 4), round(b_ci[1], 4)] if b_ci[0] is not None else None,
            "verdict": verdict(b_m, b_ci, "Brier", lower_is_better=False),
        },
    }

    # merge total rows into the summary dicts (overwrite the placeholder Nones)
    for k, v in ta.items():
        sa[k] = v
    for k, v in tb.items():
        sb[k] = v

    out = {
        "meta": {
            "title": "Injury / availability ablation — chronological holdout (Week 10, 2026)",
            "brief_requirements": "R028, R029",
            "method": (
                "Identical originated-line model run twice on the same Week 10 holdout. Ratings are "
                "calibrated on verified Weeks 1-9 only (chronological). Variant A applies the capped "
                "availability adjustment from the official Week 10 injury report; Variant B zeroes it. "
                "The two variants differ ONLY in the availability adjustment. Scored against verified "
                "Week 10 results. MAE/RMSE for spread and total; Brier for home win probability. "
                "95% CIs are non-parametric bootstraps over the holdout games (seed "
                + str(SEED) + ", " + str(BOOTSTRAP) + " reps)."
            ),
            "inputs": {
                "results": {"src": SRC_RESULTS, "file": "data/week_results_2026.csv",
                            "calibration_window": "Weeks 1-%d" % CAL_WEEK_MAX,
                            "holdout_window": "Week %d" % HOLD_WEEK},
                "availability": {"src": SRC_INJ, "file": "data/injuries_week10.json",
                                 "features": "injury-report game status (Out/Doubtful/Questionable) only"},
                "ratings": {"src": SRC_STAND, "note": "power ratings built from Weeks 1-9 cumulative standings"},
            },
            "exclusions": [
                "Depth-tier features are NOT modelled: the depth-tier source is unverified for most "
                "clubs (R042 BLOCKED), so the brief's gate forbids building that feature.",
                "No market price is used; no bet is recommended. Model output only.",
                "These are model-evaluation numbers, NOT leaderboard entries (the brief forbids "
                "backtest numbers on the leaderboard).",
            ],
            "limitations": [
                "Availability is captured for Week 10 only, so the head-to-head comparison is on the "
                "Week 10 holdout (n=%d). The CIs are correspondingly wide." % len(holdout),
                "The holdout has %d scored Week 10 games; the full 14-game slate is not yet fully "
                "scored in the results corpus." % len(holdout),
            ],
        },
        "summary": {
            "availability_on": sa,
            "availability_off": sb,
            "paired_difference": diff,
        },
        "games": per_game,
    }

    with open(os.path.join(DATA, "ablations_week10.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # flat CSV: per-game rows + a summary block
    summary_rows = []
    for key, label in (("availability_on", "availability ON"), ("availability_off", "availability OFF")):
        s = out["summary"][key]
        summary_rows.append(
            {
                "table": "summary",
                "variant": label,
                "n": s["n"],
                "spread_mae": s["spread_mae"],
                "spread_mae_ci95_lo": (s["spread_mae_ci95"] or [None, None])[0],
                "spread_mae_ci95_hi": (s["spread_mae_ci95"] or [None, None])[1],
                "spread_rmse": s["spread_rmse"],
                "total_mae": s["total_mae"],
                "total_mae_ci95_lo": (s["total_mae_ci95"] or [None, None])[0],
                "total_mae_ci95_hi": (s["total_mae_ci95"] or [None, None])[1],
                "total_rmse": s["total_rmse"],
                "brier": s["brier"],
                "brier_ci95_lo": (s["brier_ci95"] or [None, None])[0],
                "brier_ci95_hi": (s["brier_ci95"] or [None, None])[1],
            }
        )
    d = out["summary"]["paired_difference"]
    for metric, label, ci_key, val_key, dp in (
        ("spread_mae", "paired difference (ON - OFF), spread MAE", "diff_ci95", "diff_on_minus_off", 3),
        ("total_mae", "paired difference (ON - OFF), total MAE", "diff_ci95", "diff_on_minus_off", 3),
        ("brier", "paired difference (ON - OFF), Brier", "diff_ci95", "diff_on_minus_off", 4),
    ):
        m = d[metric]
        ci = m.get("diff_ci95") or [None, None]
        row = {
            "table": "summary",
            "variant": label,
            "n": d["n"],
            "spread_mae": "", "spread_mae_ci95_lo": "", "spread_mae_ci95_hi": "", "spread_rmse": "",
            "total_mae": "", "total_mae_ci95_lo": "", "total_mae_ci95_hi": "", "total_rmse": "",
            "brier": "", "brier_ci95_lo": "", "brier_ci95_hi": "",
        }
        row[val_key] = m["diff_on_minus_off"]
        if metric == "spread_mae":
            row["spread_mae"] = m["diff_on_minus_off"]
            row["spread_mae_ci95_lo"], row["spread_mae_ci95_hi"] = ci
            row["spread_rmse"] = m.get("rmse_diff_on_minus_off")
        elif metric == "total_mae":
            row["total_mae"] = m["diff_on_minus_off"]
            row["total_mae_ci95_lo"], row["total_mae_ci95_hi"] = ci
        else:
            row["brier"] = m["diff_on_minus_off"]
            row["brier_ci95_lo"], row["brier_ci95_hi"] = ci
        summary_rows.append(row)
    fieldnames = [
        "table", "variant", "n", "spread_mae", "spread_mae_ci95_lo", "spread_mae_ci95_hi",
        "spread_rmse", "total_mae", "total_mae_ci95_lo", "total_mae_ci95_hi", "total_rmse",
        "brier", "brier_ci95_lo", "brier_ci95_hi",
    ]
    write_rows("ablations_summary.csv", summary_rows, fieldnames=fieldnames)
    write_rows("ablations_week10.csv", per_game)

    print("ablations: %d holdout games, %d calibration games" % (len(holdout), len(calib)))
    print("  availability ON  : spread MAE %s  total MAE %s  Brier %s"
          % (sa["spread_mae"], sa["total_mae"], sa["brier"]))
    print("  availability OFF : spread MAE %s  total MAE %s  Brier %s"
          % (sb["spread_mae"], sb["total_mae"], sb["brier"]))
    for metric in ("spread_mae", "total_mae", "brier"):
        m = diff[metric]
        print("  paired diff (ON-OFF) %-10s: %s  95%% CI %s"
              % (metric, m["diff_on_minus_off"], m["diff_ci95"]))
        print("    ->", m["verdict"])


if __name__ == "__main__":
    main()
