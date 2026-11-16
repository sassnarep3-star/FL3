#!/usr/bin/env python3
"""
FL3 — honest evaluation of the repo's own originated lines.

Two evaluations, both out of sample, both against explicit baselines, both with
uncertainty. Nothing here is a betting result: the repo holds no licensed price,
so CLV and ROI are not computable and are reported as such.

Evaluation 1 — the committed Week 10 forecasts (the accidental pre-registration)
------------------------------------------------------------------------------
`data/lines_week10.json` was committed on 2026-11-14 with 14 originated lines,
before 12 of those games had been played. The commit is the registration: the
numbers could not have been chosen after seeing the results. Today the official
schedule page publishes final scores for 12 of the 14.

One of the 14 is contaminated and is excluded:
  WAS @ NYG kicked off Thu 2026-11-12 8:15 PM ET and was FINAL before the model
  file was committed on 2026-11-14. The file's own `kickoff` field says
  "FINAL — Commanders 24, Giants 21". Scoring it as a forecast would be
  lookahead leakage, so it is dropped and counted here.

That leaves n = 11 genuinely out-of-sample games. n = 11 is far too small to
rank anything; it is reported with its uncertainty and no conclusion is drawn
from it beyond consistency.

Evaluation 2 — walk-forward over the verified corpus
---------------------------------------------------
Fit the same rating structure on weeks < k, forecast week k, for every k with
enough history. Chronological, no shuffling, no leakage. This gives ~100
out-of-sample games, which is enough to say something weakly.

Baselines, because "we beat nothing" is the default state of any model:
  * spread: predict 0 (i.e. a pick'em line)
  * total:  predict the trailing league mean total
  * win prob: 0.5 (coin flip) and home-always (the trailing home win rate)

Uncertainty: bootstrap resampling **by game** (a game's margin and total move
together, so resampling rows would understate the interval).

Run: python3 scripts/score_lines.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(DATA, "week_results_2026.csv")
NEW_LINES = os.path.join(DATA, "lines_week10.json")
OUT_JSON = os.path.join(DATA, "line_eval.json")
OUT_CSV = os.path.join(DATA, "line_eval.csv")

BOOT = 4000
SEED = 20261116

HOME_FIELD = 1.9      # points, the value already used by data/lines_week10.json
PRIOR_GAMES = 4.0     # shrinkage strength, as data/lines.json documents
LEAGUE_PPG = 22.0     # points per team per game, as data/lines_week10.json


def load_results() -> list[dict]:
    with open(RESULTS, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["week"] = int(r["week"])
        r["away_pts"] = int(r["away_pts"])
        r["home_pts"] = int(r["home_pts"])
        r["margin"] = r["away_pts"] - r["home_pts"]      # away minus home
        r["total"] = r["away_pts"] + r["home_pts"]
    return rows


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
def rmse(errs: list[float]) -> float:
    return math.sqrt(sum(e * e for e in errs) / len(errs)) if errs else float("nan")


def mae(errs: list[float]) -> float:
    return sum(abs(e) for e in errs) / len(errs) if errs else float("nan")


def brier(probs: list[float], outcomes: list[int]) -> float:
    """outcome 1 = home win, 0 = home loss, 0.5 counted as 0.5 (a tie is not a win)."""
    if not probs:
        return float("nan")
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


def cluster_bootstrap(games: list[dict], fn, n: int = BOOT, seed: int = SEED) -> tuple[float, float, float]:
    """Percentile CI of fn(sample) resampling whole games."""
    rng = random.Random(seed)
    stats = []
    for _ in range(n):
        sample = [games[rng.randrange(len(games))] for _ in games]
        stats.append(fn(sample))
    stats.sort()
    lo = stats[int(0.025 * len(stats))]
    hi = stats[int(0.975 * len(stats)) - 1]
    return lo, statistics.median(stats), hi


# ---------------------------------------------------------------------------
# Evaluation 1 — committed Week 10 forecasts
# ---------------------------------------------------------------------------
def eval_committed(rows: list[dict]) -> dict:
    d = json.load(open(NEW_LINES, encoding="utf-8"))
    by_pair = {(r["away_abbr"], r["home_abbr"]): r for r in rows if r["week"] == 10}
    games, excluded = [], []
    for g in d["games"]:
        key = (g["away"], g["home"])
        res = by_pair.get(key)
        kick = g.get("kickoff", "")
        if res is None:
            excluded.append(dict(game=g["game_id"], reason="not FINAL on the official schedule page at read time"))
            continue
        if "FINAL" in kick:
            excluded.append(dict(game=g["game_id"], reason="already FINAL when the model file was committed — lookahead leakage, excluded"))
            continue
        games.append(dict(
            game=g["game_id"],
            pred_margin=-g["line"]["home_spread"],             # convention: model margin = home - away
            actual_margin=-(res["margin"]),                    # home - away
            pred_total=g["line"]["total_point_estimate"],
            actual_total=res["total"],
            p_home=g["line"]["home_win_prob"],
            home_won=int(res["home_pts"] > res["away_pts"]),
            tie=int(res["home_pts"] == res["away_pts"]),
        ))

    def pack(sample):
        sp = [x["pred_margin"] - x["actual_margin"] for x in sample]
        to = [x["pred_total"] - x["actual_total"] for x in sample]
        return dict(
            n=len(sample),
            spread_rmse=rmse(sp), spread_mae=mae(sp), spread_bias=statistics.fmean(sp),
            total_rmse=rmse(to), total_mae=mae(to), total_bias=statistics.fmean(to),
            brier_model=brier([x["p_home"] for x in sample], [x["home_won"] for x in sample]),
            brier_coin=brier([0.5] * len(sample), [x["home_won"] for x in sample]),
            spread_dir_acc=sum(1 for x in sample if (x["pred_margin"] > 0) == (x["actual_margin"] > 0)) / len(sample),
        )

    point = pack(games)

    def brier_skill(sample):
        p = [x["p_home"] for x in sample]
        o = [x["home_won"] for x in sample]
        bc = brier([0.5] * len(sample), o)
        return 1.0 - brier(p, o) / bc if bc else float("nan")

    def spread_rmse_fn(sample):
        return rmse([x["pred_margin"] - x["actual_margin"] for x in sample])

    lo_b, med_b, hi_b = cluster_bootstrap(games, brier_skill)
    lo_s, med_s, hi_s = cluster_bootstrap(games, spread_rmse_fn)

    return dict(
        evaluation="committed Week 10 forecasts (pre-registered by commit, 2026-11-14)",
        source_model_file="data/lines_week10.json",
        excluded=excluded,
        point=point,
        brier_skill_vs_coin=dict(estimate=1.0 - point["brier_model"] / point["brier_coin"],
                                 ci95=[lo_b, hi_b], median_boot=med_b),
        spread_rmse_ci95=[lo_s, hi_s],
        interpretation=(
            "n is too small to rank or to claim skill. Directional accuracy on 11 games has a "
            "standard error of roughly 0.15, so any value between about 0.20 and 0.80 is "
            "indistinguishable from a coin at this sample size."
        ),
        per_game=games,
    )


# ---------------------------------------------------------------------------
# Evaluation 2 — walk-forward over the verified corpus
# ---------------------------------------------------------------------------
def fit_ratings(history: list[dict]) -> dict:
    """Offence/defence ratings shrunk toward the league mean, exactly as documented."""
    pf = defaultdict(float)
    pa = defaultdict(float)
    gp = defaultdict(int)
    for r in history:
        for t, s, c in ((r["away_abbr"], r["away_pts"], r["home_pts"]),
                        (r["home_abbr"], r["home_pts"], r["away_pts"])):
            pf[t] += s
            pa[t] += c
            gp[t] += 1
    ratings = {}
    for t in set(list(pf) + list(pa)):
        g = gp[t]
        w = g / (g + PRIOR_GAMES)
        off = w * (pf[t] / g) + (1 - w) * LEAGUE_PPG
        dfn = w * (pa[t] / g) + (1 - w) * LEAGUE_PPG
        ratings[t] = dict(off=off, defense=dfn, games=g)
    home_wins = sum(1 for r in history if r["home_pts"] > r["away_pts"])
    home_rate = home_wins / len(history) if history else 0.5
    return dict(ratings=ratings, home_rate=home_rate,
                games=len(history), mean_total=statistics.fmean(r["total"] for r in history))


def forecast(model: dict, away: str, home: str) -> dict | None:
    r = model["ratings"]
    if away not in r or home not in r:
        return None
    A, H = r[away], r[home]
    exp_away = LEAGUE_PPG + (A["off"] - LEAGUE_PPG) + (H["defense"] - LEAGUE_PPG)
    exp_home = LEAGUE_PPG + (H["off"] - LEAGUE_PPG) + (A["defense"] - LEAGUE_PPG) + HOME_FIELD
    margin_home = exp_home - exp_away
    # Logistic map from expected margin to a win probability. sigma is the
    # league-typical single-game margin sd (8.5, as used in lines_week10.json);
    # this is a scale choice, not a fitted parameter, and it is declared, not tuned.
    sigma = 8.5
    p_home = 1.0 / (1.0 + math.exp(-margin_home / (sigma * 0.55)))
    return dict(exp_away=exp_away, exp_home=exp_home, margin_home=margin_home,
                total=exp_away + exp_home, p_home=p_home)


def eval_walkforward(rows: list[dict], min_week: int = 4) -> dict:
    out, per_week = [], {}
    for wk in sorted({r["week"] for r in rows}):
        if wk < min_week:
            continue
        history = [r for r in rows if r["week"] < wk]
        model = fit_ratings(history)
        week_rows = []
        for r in rows:
            if r["week"] != wk:
                continue
            f = forecast(model, r["away_abbr"], r["home_abbr"])
            if f is None:
                continue
            week_rows.append(dict(
                week=wk, game=f'{r["away_abbr"]}@{r["home_abbr"]}',
                pred_margin=f["margin_home"], actual_margin=-r["margin"],
                pred_total=f["total"], actual_total=r["total"],
                p_home=f["p_home"], home_won=int(r["home_pts"] > r["away_pts"]),
                base_total=model["mean_total"], base_p_home=model["home_rate"],
            ))
        per_week[wk] = dict(n=len(week_rows))
        out.extend(week_rows)

    def pack(sample):
        sm = [x["pred_margin"] - x["actual_margin"] for x in sample]
        st = [x["pred_total"] - x["actual_total"] for x in sample]
        st_base = [x["base_total"] - x["actual_total"] for x in sample]
        return dict(
            n=len(sample),
            spread_rmse=rmse(sm), spread_bias=statistics.fmean(sm),
            spread_rmse_vs_zero=rmse([x["actual_margin"] for x in sample]),
            total_rmse=rmse(st), total_bias=statistics.fmean(st),
            total_rmse_vs_mean=rmse(st_base),
            brier=brier([x["p_home"] for x in sample], [x["home_won"] for x in sample]),
            brier_coin=brier([0.5] * len(sample), [x["home_won"] for x in sample]),
            brier_home_always=brier([x["base_p_home"] for x in sample], [x["home_won"] for x in sample]),
            dir_acc=sum(1 for x in sample if (x["pred_margin"] > 0) == (x["actual_margin"] > 0)) / len(sample),
        )

    point = pack(out)

    def skill(sample):
        o = [x["home_won"] for x in sample]
        bc = brier([0.5] * len(sample), o)
        return 1.0 - brier([x["p_home"] for x in sample], o) / bc if bc else float("nan")

    def rmse_gain(sample):
        a = rmse([x["pred_margin"] - x["actual_margin"] for x in sample])
        b = rmse([x["actual_margin"] for x in sample])
        return 1.0 - a / b if b else float("nan")

    def total_gain(sample):
        a = rmse([x["pred_total"] - x["actual_total"] for x in sample])
        b = rmse([x["base_total"] - x["actual_total"] for x in sample])
        return 1.0 - a / b if b else float("nan")

    bs = cluster_bootstrap(out, skill)
    sg = cluster_bootstrap(out, rmse_gain)
    tg = cluster_bootstrap(out, total_gain)
    dirci = cluster_bootstrap(out, lambda s: sum(1 for x in s if (x["pred_margin"] > 0) == (x["actual_margin"] > 0)) / len(s))

    return dict(
        evaluation=f"walk-forward, fit on all weeks < k, forecast week k, k >= {min_week}",
        point=point,
        by_week=per_week,
        brier_skill_vs_coin=dict(estimate=1.0 - point["brier"] / point["brier_coin"], ci95=[bs[0], bs[2]]),
        spread_rmse_gain_vs_pickem=dict(estimate=1.0 - point["spread_rmse"] / point["spread_rmse_vs_zero"], ci95=[sg[0], sg[2]]),
        total_rmse_gain_vs_league_mean=dict(estimate=1.0 - point["total_rmse"] / point["total_rmse_vs_mean"], ci95=[tg[0], tg[2]]),
        directional_accuracy=dict(estimate=point["dir_acc"], ci95=[dirci[0], dirci[2]]),
        per_game=out,
    )


def verdict(d: dict) -> str:
    """Say plainly whether the evidence supports skill. No hedging beyond the CI."""
    g = d["spread_rmse_gain_vs_pickem"]
    if g["ci95"][0] > 0:
        s = (f"The rating model beats a pick'em baseline on spread error: gain "
             f"{g['estimate']:.3f}, 95% CI [{g['ci95'][0]:.3f}, {g['ci95'][1]:.3f}] excludes zero.")
    elif g["ci95"][1] < 0:
        s = (f"The rating model is WORSE than a pick'em baseline on spread error: gain "
             f"{g['estimate']:.3f}, 95% CI [{g['ci95'][0]:.3f}, {g['ci95'][1]:.3f}] is entirely negative.")
    else:
        s = (f"No demonstrated spread skill: gain over pick'em {g['estimate']:.3f}, "
             f"95% CI [{g['ci95'][0]:.3f}, {g['ci95'][1]:.3f}] spans zero at n={d['point']['n']}.")
    b = d["brier_skill_vs_coin"]
    if b["ci95"][0] > 0:
        s += f" Win probability is better than a coin consistently (Brier skill {b['estimate']:.3f}, CI excludes zero)."
    elif b["ci95"][1] < 0:
        s += f" Win probability is WORSE than a coin (Brier skill {b['estimate']:.3f}, CI entirely negative)."
    else:
        s += f" Win probability is not distinguishable from a coin (Brier skill {b['estimate']:.3f}, CI spans zero)."
    return s


def main() -> None:
    rows = load_results()
    e1 = eval_committed(rows)
    e2 = eval_walkforward(rows)
    e2["verdict"] = verdict(e2)
    payload = dict(
        meta=dict(
            title="Out-of-sample evaluation of the repo's originated lines",
            results_corpus="data/week_results_2026.csv (148 games, identity-checked against official standings)",
            prices="No licensed price is held anywhere in this repo. CLV and ROI are therefore NOT computed and are not implied by anything on this page.",
            bootstrap=f"{BOOT} game-cluster resamples, seed {SEED}",
            baselines="pick'em for spread, trailing league mean for total, coin flip and home-always for the win probability",
            policy="Model output is labelled as model output everywhere. Nothing here is a pick or a bet.",
        ),
        committed_week10=e1,
        walkforward=e2,
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["evaluation", "n", "metric", "estimate", "ci95_low", "ci95_high", "baseline"])
        def row(ev, n, m, est, lo, hi, base):
            w.writerow([ev, n, m, f"{est:.4f}", f"{lo:.4f}" if lo is not None else "",
                        f"{hi:.4f}" if hi is not None else "", base])
        p = e1["point"]
        row("committed_w10", p["n"], "spread_rmse", p["spread_rmse"], *e1["spread_rmse_ci95"], "pick'em")
        row("committed_w10", p["n"], "total_rmse", p["total_rmse"], None, None, "trailing league mean")
        row("committed_w10", p["n"], "brier_skill_vs_coin",
            e1["brier_skill_vs_coin"]["estimate"], *e1["brier_skill_vs_coin"]["ci95"], "coin flip")
        row("committed_w10", p["n"], "spread_directional_accuracy", p["spread_dir_acc"], None, None, "0.5")
        q = e2["point"]
        row("walkforward", q["n"], "spread_rmse", q["spread_rmse"], *e2["spread_rmse_gain_vs_pickem"]["ci95"], "pick'em")
        row("walkforward", q["n"], "spread_rmse_gain_vs_pickem",
            e2["spread_rmse_gain_vs_pickem"]["estimate"], *e2["spread_rmse_gain_vs_pickem"]["ci95"], "0")
        row("walkforward", q["n"], "total_rmse", q["total_rmse"], None, None, "trailing league mean")
        row("walkforward", q["n"], "total_rmse_gain_vs_mean",
            e2["total_rmse_gain_vs_league_mean"]["estimate"], *e2["total_rmse_gain_vs_league_mean"]["ci95"], "0")
        row("walkforward", q["n"], "brier_skill_vs_coin",
            e2["brier_skill_vs_coin"]["estimate"], *e2["brier_skill_vs_coin"]["ci95"], "coin flip")
        row("walkforward", q["n"], "directional_accuracy",
            e2["directional_accuracy"]["estimate"], *e2["directional_accuracy"]["ci95"], "0.5")

    print("=== Committed Week 10 forecasts (as committed 2026-11-14) ===")
    print(f"  scored n={e1['point']['n']}, excluded {len(e1['excluded'])}: "
          f"{[x['game'] for x in e1['excluded']]}")
    print(f"  spread  RMSE {e1['point']['spread_rmse']:.2f} pts   bias {e1['point']['spread_bias']:+.2f}")
    print(f"  total   RMSE {e1['point']['total_rmse']:.2f} pts   bias {e1['point']['total_bias']:+.2f}")
    print(f"  Brier   model {e1['point']['brier_model']:.4f} vs coin {e1['point']['brier_coin']:.4f}"
          f"  -> skill {e1['brier_skill_vs_coin']['estimate']:+.4f}"
          f"  CI [{e1['brier_skill_vs_coin']['ci95'][0]:+.3f}, {e1['brier_skill_vs_coin']['ci95'][1]:+.3f}]")
    print(f"  spread pick direction correct on {e1['point']['spread_dir_acc']:.0%} of {e1['point']['n']}")
    print()
    print(f"=== Walk-forward over the verified corpus (n={e2['point']['n']}) ===")
    print(f"  spread RMSE {e2['point']['spread_rmse']:.2f} vs pick'em {e2['point']['spread_rmse_vs_zero']:.2f}"
          f"  gain {e2['spread_rmse_gain_vs_pickem']['estimate']:+.3f}"
          f"  CI [{e2['spread_rmse_gain_vs_pickem']['ci95'][0]:+.3f}, {e2['spread_rmse_gain_vs_pickem']['ci95'][1]:+.3f}]")
    print(f"  total  RMSE {e2['point']['total_rmse']:.2f} vs league mean {e2['point']['total_rmse_vs_mean']:.2f}"
          f"  gain {e2['total_rmse_gain_vs_league_mean']['estimate']:+.3f}"
          f"  CI [{e2['total_rmse_gain_vs_league_mean']['ci95'][0]:+.3f}, {e2['total_rmse_gain_vs_league_mean']['ci95'][1]:+.3f}]")
    print(f"  Brier  model {e2['point']['brier']:.4f} coin {e2['point']['brier_coin']:.4f}"
          f" home-always {e2['point']['brier_home_always']:.4f}"
          f"  skill vs coin {e2['brier_skill_vs_coin']['estimate']:+.4f}"
          f"  CI [{e2['brier_skill_vs_coin']['ci95'][0]:+.3f}, {e2['brier_skill_vs_coin']['ci95'][1]:+.3f}]")
    print(f"  direction correct {e2['directional_accuracy']['estimate']:.1%}"
          f"  CI [{e2['directional_accuracy']['ci95'][0]:.1%}, {e2['directional_accuracy']['ci95'][1]:.1%}]")
    print()
    print("VERDICT:", e2["verdict"])
    print(f"\nwrote {OUT_JSON}\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
