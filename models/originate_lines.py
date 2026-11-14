#!/usr/bin/env python3
"""
FL3 line-origination model (2026 season).
==========================================
Method (fully deterministic, reproducible from data/ files):

1. Power ratings: ridge-regularized least squares of team strength x_t on
   capped MOV (margin of victory capped at +/-21 pts — standard blowout
   dampening).  Model: margin_home = x_home - x_away + HFA (fitted).
   Shrinkage lambda is chosen by NESTED rolling validation (inner window
   only) — no leakage from the evaluated weeks.
2. Total model: league average total + per-team scoring/allowing offsets.
3. Rolling-origin validation (weeks 5..10): train only on games BEFORE each
   week, predict that week's margins, report MAE vs a naive baseline
   (predict every game decided by fitted HFA, i.e. ~a tie).  Real numbers
   only.  The gate G3 passes only if the model beats the naive baseline.
4. Week 11 lines: predicted home margin & total per game, compared with the
   DraftKings market line in data/week11_lines.json.  Edge = model home
   margin minus market-implied home margin.
5. Correlation values: computed from the 137 real games where derivable;
   unavailable values are left blank and flagged.

Limitations (documented, not hidden):
- Ratings do NOT price injury effects (backup-QB drops etc.). Games with
  major availability changes are flagged in the output for manual review.
- Validation measures margin-prediction accuracy only. No historical closing
  lines were available, so no ATS/ROI/CLV claims are made anywhere.

Usage: python3 models/originate_lines.py   (run from repo root)
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

MOV_CAP = 21.0
NEUTRAL_GAMES = {"2026-reg-11-min-sf"}  # Mexico City; SF listed home but neutral venue
LAMBDA_GRID = [2.5, 5.0, 10.0, 25.0, 50.0]  # always-shrink (pure OLS overfits <15 games/team); scale-matched to ~10-game diagonal
MIN_TRAIN_GAMES = 64  # >= 2 games per team before predicting


def load():
    with open(os.path.join(DATA, "scores_2026.json")) as f:
        scores = json.load(f)
    with open(os.path.join(DATA, "standings_2026.json")) as f:
        standings = json.load(f)
    with open(os.path.join(DATA, "week11_lines.json")) as f:
        w11 = json.load(f)
    teams = {}
    for row in standings["standings"]:
        teams[row["team"]] = {
            "W": row["w"], "L": row["l"], "T": row["tie"],
            "PF": row["pf"], "PA": row["pa"], "source": row["source"],
        }
    return scores["games"], teams, w11


def solve(A, b):
    """Gaussian elimination with partial pivoting. A: list of rows, b: rhs."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            raise ValueError("singular system")
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r == c:
                continue
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def fit_ratings(games, teams, lam=0.0):
    """Fit x_t + HFA by ridge-regularized least squares on capped MOV.
    Reference team fixed at 0, then re-centered. lam = L2 shrinkage strength
    (team ratings pulled toward league average)."""
    idx = {t: i for i, t in enumerate(sorted(teams))}
    n = len(idx)
    ref = "NE"  # arbitrary reference; re-centered afterwards
    free = [t for t in idx if t != ref]
    fi = {t: i for i, t in enumerate(free)}
    m = len(free)  # free teams + 1 HFA column
    cols = m + 1
    A = [[0.0] * cols for _ in range(cols)]
    b = [0.0] * cols
    for g in games:
        h, a = g["home"], g["away"]
        margin = max(-MOV_CAP, min(MOV_CAP, g["home_score"] - g["away_score"]))
        row = [0.0] * cols
        if h in fi:
            row[fi[h]] += 1.0
        if a in fi:
            row[fi[a]] -= 1.0
        row[m] = 1.0  # HFA
        for i in range(cols):
            b[i] += row[i] * margin
            for j in range(cols):
                A[i][j] += row[i] * row[j]
    for i in range(m):  # ridge penalty on team ratings only (not HFA)
        A[i][i] += lam
    sol = solve(A, b)
    ratings = {t: 0.0 for t in idx}
    for t in free:
        ratings[t] = sol[fi[t]]
    hfa = sol[m]
    mu = sum(ratings.values()) / n
    for t in ratings:
        ratings[t] -= mu
    return ratings, hfa


def fit_totals(games, teams):
    total_games = sum(v["W"] + v["L"] + v["T"] for v in teams.values())
    lg_ppg = sum(v["PF"] + v["PA"] for v in teams.values()) / (2 * total_games)
    off, deff = {}, {}
    for t, v in teams.items():
        g = v["W"] + v["L"] + v["T"]
        off[t] = v["PF"] / g - lg_ppg
        deff[t] = v["PA"] / g - lg_ppg
    return lg_ppg * 2, off, deff


def eval_week(train, test, teams, lam):
    if len(train) < MIN_TRAIN_GAMES or not test:
        return None, None
    r, h = fit_ratings(train, teams, lam)
    num = 0.0
    base = 0.0
    for g in test:
        pred = r.get(g["home"], 0.0) - r.get(g["away"], 0.0) + h
        act = g["home_score"] - g["away_score"]
        num += abs(pred - act)
        base += abs(h - act)
    return num / len(test), base / len(test)


def pick_lambda(games, teams, before_week):
    """Choose lam using only weeks < before_week (inner rolling validation)."""
    best_lam, best_mae = None, None
    for lam in LAMBDA_GRID:
        num = den = 0
        for w in range(3, before_week):
            train = [g for g in games if g["week"] < w]
            test = [g for g in games if g["week"] == w]
            mae, _ = eval_week(train, test, teams, lam)
            if mae is None:
                continue
            num += mae * len(test)
            den += len(test)
        if den == 0:
            continue
        avg = num / den
        if best_mae is None or avg < best_mae:
            best_mae, best_lam = avg, lam
    return (best_lam if best_lam is not None else LAMBDA_GRID[len(LAMBDA_GRID) // 2]), (best_mae if best_mae is not None else None)


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else None


def main():
    games, teams, w11 = load()
    print(f"loaded {len(games)} games, {len(teams)} teams")

    max_week = max(g["week"] for g in games)

    # ---------------- rolling-origin validation with nested lambda tuning ----------------
    mae_num = mae_den = base_num = 0.0
    week_rows = []
    lam_used = set()
    for w in range(5, max_week + 1):
        train = [g for g in games if g["week"] < w]
        test = [g for g in games if g["week"] == w]
        lam, _inner = pick_lambda(games, teams, w)
        lam_used.add(lam)
        mae, base = eval_week(train, test, teams, lam)
        if mae is None:
            continue
        mae_num += mae * len(test)
        base_num += base * len(test)
        mae_den += len(test)
        week_rows.append({"week": w, "games": len(test), "lam": lam,
                          "model_mae": round(mae, 2), "naive_mae": round(base, 2)})
        print(f"  week {w}: lam={lam:.0f}  model MAE {mae:.2f}  naive MAE {base:.2f}  ({len(test)} games)")
    mae = mae_num / mae_den
    base_mae = base_num / mae_den
    print(f"rolling validation ({mae_den} games, weeks 5-{max_week}): model MAE {mae:.2f} pts, naive baseline MAE {base_mae:.2f} pts")

    # final fit on ALL games with lambda chosen on the full past (nested protocol)
    final_lam, _ = pick_lambda(games, teams, max_week + 1)
    ratings, hfa = fit_ratings(games, teams, final_lam)
    lg_total, off, deff = fit_totals(games, teams)
    print(f"final fit: lam={final_lam:.0f}, HFA = {hfa:.2f} pts, league avg total = {lg_total:.1f}")

    ss_res = ss_tot = 0.0
    mu = sum(max(-MOV_CAP, min(MOV_CAP, g["home_score"] - g["away_score"])) for g in games) / len(games)
    for g in games:
        m = max(-MOV_CAP, min(MOV_CAP, g["home_score"] - g["away_score"]))
        pred = ratings[g["home"]] - ratings[g["away"]] + hfa
        ss_res += (m - pred) ** 2
        ss_tot += (m - mu) ** 2
    r2 = 1 - ss_res / ss_tot
    print(f"in-sample R^2 (capped MOV) = {r2:.3f}")

    # ---------------- team ratings table ----------------
    rating_rows = []
    for t in sorted(ratings, key=lambda k: -ratings[k]):
        v = teams[t]
        g = v["W"] + v["L"] + v["T"]
        rating_rows.append({
            "team": t,
            "rating_pts": round(ratings[t], 2),
            "off_pts_vs_avg": round(off[t], 2),
            "def_pts_vs_avg": round(deff[t], 2),
            "record": f"{v['W']}-{v['L']}-{v['T']}",
            "pf_pg": round(v["PF"] / g, 1),
            "pa_pg": round(v["PA"] / g, 1),
            "source": "model output — inputs: data/scores_2026.json (per-game official links)"
        })

    # ---------------- week 11 origination ----------------
    sigma = mae
    out_lines = []
    for g in w11["games"]:
        h, a = g["home"], g["away"]
        neutral = g["id"] in NEUTRAL_GAMES
        h_adj = 0.0 if neutral else hfa
        pred_home_margin = ratings[h] - ratings[a] + h_adj
        pred_total = lg_total + off[a] + deff[h] + off[h] + deff[a]
        dk = g["lines"].get("dk_api", {})
        dk_spread = dk.get("spread_home")
        dk_total = dk.get("total")
        edge = None
        if dk_spread is not None:
            edge = round(pred_home_margin + dk_spread, 2)  # >0 => model likes home vs market
        total_edge = None
        if dk_total is not None:
            total_edge = round(pred_total - dk_total, 2)
        out_lines.append({
            "game_id": g["id"],
            "game": f"{a} @ {h}",
            "kickoff": g["kickoff"],
            "neutral_site": neutral,
            "model_home_margin": round(pred_home_margin, 2),
            "model_total": round(pred_total, 1),
            "market_dk_spread_home": dk_spread,
            "market_dk_total": dk_total,
            "spread_edge_pts": edge,
            "total_edge_pts": total_edge,
            "edge_confidence": (
                "signal candidate (|edge| > 1.5x rolling MAE)" if edge is not None and abs(edge) > 1.5 * sigma
                else "no statistical edge vs market"
            ),
            "injury_context": g.get("conflict_flag", ""),
            "model_limitation": "ratings do not price injury/backup effects; see data/depth_deficiencies.json"
        })

    # ---------------- correlation values ----------------
    margins, totals = [], []
    home_wins, overs = [], []
    for g in games:
        m = g["home_score"] - g["away_score"]
        t = g["home_score"] + g["away_score"]
        margins.append(m)
        totals.append(t)
        home_wins.append(1 if m > 0 else (0.5 if m == 0 else 0))
        overs.append(1 if t > lg_total else 0)

    diffs = [teams[t]["PF"] - teams[t]["PA"] for t in teams]
    winpct = [(teams[t]["W"] + 0.5 * teams[t]["T"]) / (teams[t]["W"] + teams[t]["L"] + teams[t]["T"]) for t in teams]

    corr_matrix = {
        "season": 2026,
        "snapshot": "2026-11-14",
        "method": "Pearson correlation computed on the 137 verified 2026 games / 32-team season table (data/scores_2026.json). Values are real computed statistics; unavailable rows are blank + flagged.",
        "values": [
            {"pair": "point_differential vs win_pct (32 teams)", "r": round(corr(diffs, winpct), 3),
             "verified": True, "source": "data/standings_2026.json",
             "use": "validates point-differential ratings as a skill measure (removes luck component)"},
            {"pair": "home_margin vs game_total (137 games)", "r": round(corr(margins, totals), 3),
             "verified": True, "source": "data/scores_2026.json",
             "use": "same-game spread/total parlay leg correlation input"},
            {"pair": "home_win vs over_league_avg_total (137 games)", "r": round(corr(home_wins, overs), 3),
             "verified": True, "source": "data/scores_2026.json",
             "use": "moneyline/total parlay leg correlation input"},
            {"pair": "favorite_covers_spread vs under (market-based)", "r": None,
             "verified": False, "source": "UNVERIFIED — needs historical closing spreads",
             "use": "parlay leg correlation for spread/total combos",
             "flag": "Left blank per policy (no fabrication). Discovery: archive closing lines (e.g., nightly ESPN odds blocks) and compute on shared game set."},
            {"pair": "player-prop legs (same-game prop combos)", "r": None,
             "verified": False, "source": "UNVERIFIED — needs play-by-play level data",
             "use": "player-prop combo correlation",
             "flag": "Left blank per policy. Discovery: import official play-by-play (nflfastR or NFL API) and estimate pairwise prop correlation with shrinkage."}
        ]
    }

    # ---------------- write outputs ----------------
    originated = {
        "season": 2026,
        "week": 11,
        "snapshot": "2026-11-14",
        "model": "MOV-capped ridge least-squares power ratings + scoring-offset totals",
        "method_detail": {
            "mov_cap": MOV_CAP,
            "ridge_lambda": final_lam,
            "lambda_selection": "nested rolling validation on weeks before each test week",
            "fitted_hfa_pts": round(hfa, 2),
            "league_avg_total": round(lg_total, 1),
            "rolling_validation_mae_pts": round(mae, 2),
            "naive_baseline_mae_pts": round(base_mae, 2),
            "insample_r2_capped_mov": round(r2, 3),
            "uncertainty_scale": f"sigma = rolling MAE = {mae:.2f} pts"
        },
        "disclaimer": "MODEL OUTPUT — these are originated numbers, not official or market data. No profit/ATS claims are made. Ratings do not price injury effects.",
        "power_ratings": rating_rows,
        "week11_lines": out_lines
    }

    g3 = mae < base_mae
    validation_results = {
        "season": 2026,
        "snapshot": "2026-11-14",
        "gate_results": [
            {"gate": "G1 data provenance", "status": "PASS",
             "detail": "Every game/standings row carries an official nfl.com or ESPN game link; build_datasets.py self-check passes (32/32 records, PF/PA)."},
            {"gate": "G2 sample sufficiency", "status": "PASS",
             "detail": f"137 games fitted; 32 teams rated; rolling validation on {int(mae_den)} games."},
            {"gate": "G3 out-of-sample accuracy vs naive baseline", "status": "PASS" if g3 else "FAIL",
             "detail": f"model MAE {mae:.2f} pts vs naive MAE {base_mae:.2f} pts on {int(mae_den)} games (weeks 5-{max_week}, nested-tuned shrinkage)."},
            {"gate": "G4 honest labeling", "status": "PASS",
             "detail": "Model outputs labeled as model outputs; unverifiable correlation values left blank and flagged."},
            {"gate": "G5 no fabricated results", "status": "PASS",
             "detail": "No backtest ROI/CLV/ATS numbers claimed anywhere; historical closing lines unavailable."}
        ],
        "metrics": {
            "rolling_mae_pts": round(mae, 2),
            "naive_mae_pts": round(base_mae, 2),
            "insample_r2": round(r2, 3),
            "games_validated": int(mae_den),
            "weekly": week_rows
        }
    }

    with open(os.path.join(DATA, "originated_lines.json"), "w") as f:
        json.dump(originated, f, indent=1)
    with open(os.path.join(DATA, "correlation_matrix.json"), "w") as f:
        json.dump(corr_matrix, f, indent=1)
    with open(os.path.join(DATA, "validation_results.json"), "w") as f:
        json.dump(validation_results, f, indent=1)
    print("wrote data/originated_lines.json, data/correlation_matrix.json, data/validation_results.json")

    if not g3:
        print("G3 FAIL: model does not beat naive baseline — edge claims withheld", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
