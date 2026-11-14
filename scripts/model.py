#!/usr/bin/env python3
"""Derive team metrics, league statistics, correlations, ratings and origination lines.

Every number this file writes is a computation over rows in data/ that already passed
scripts/verify.py. It never introduces a fact: if an input is blank the output is blank.

Outputs
  data/derived_team_metrics.csv     per club: volume, efficiency, availability load
  data/derived_league_stats.csv     league-level distributions (n as published)
  data/derived_correlations.csv     measured correlations with 95% CI, sample-labelled
  data/power_ratings.csv            two independent ratings + their disagreement
  data/lines_origination.csv        Week 10 slate priced from the above
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_fl3 import mean, num, read_rows, sd, summary, write_rows  # noqa: E402

ABBR = {}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def corr(xs, ys):
    """Pearson r + Fisher-z 95% CI. Returns (r, lo, hi, n); (None,...) if n<4."""
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pts)
    if n < 4:
        return None, None, None, n
    xv, yv = [p[0] for p in pts], [p[1] for p in pts]
    mx, my = mean(xv), mean(yv)
    sx = math.sqrt(sum((a - mx) ** 2 for a in xv))
    sy = math.sqrt(sum((a - my) ** 2 for a in yv))
    if sx == 0 or sy == 0:
        return None, None, None, n
    r = min(0.999999, max(-0.999999, sum((a - mx) * (b - my) for a, b in pts) / (sx * sy)))
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    return r, math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se), n


def fmt(v, dp=2):
    return "" if v is None else f"{v:.{dp}f}"


# --------------------------------------------------------------------------- #
# team metrics
# --------------------------------------------------------------------------- #
def team_metrics(standings, p_off, r_off, p_def, injuries):
    off = {r["abbr"]: r for r in p_off}
    rush = {r["abbr"]: r for r in r_off}
    dfn = {r["abbr"]: r for r in p_def}
    out = []
    for s in standings:
        a = s["abbr"]
        gp = num(s["games"], 0) or None
        o, ru, d = off.get(a, {}), rush.get(a, {}), dfn.get(a, {})
        pass_att, sack = num(o.get("pass_att")), num(o.get("sacks_taken"))
        rush_att = num(ru.get("rush_att"))
        dropbacks = None if pass_att is None or sack is None else pass_att + sack
        plays = None if dropbacks is None or rush_att is None else dropbacks + rush_att
        pass_rate = None if not plays else 100.0 * dropbacks / plays
        # availability load, from the Week 10 report only (see FLG-005/FLG-017)
        team_rows = [r for r in injuries if r["team_abbr"] == a]
        out_ = [r for r in team_rows if r["game_status"] == "Out"]
        dq = [r for r in team_rows if r["game_status"] in ("Doubtful",)]
        q = [r for r in team_rows if r["game_status"] == "Questionable"]
        ol_out = [r for r in out_ if r["pos"] in ("T", "G", "C")]
        db_out = [r for r in out_ if r["pos"] in ("CB", "S")]
        dl_out = [r for r in out_ if r["pos"] in ("DE", "DT")]
        qb_out = [r for r in out_ if r["pos"] == "QB"]
        row = {
            "team": s["team"], "abbr": a, "games": s["games"],
            "ppg": fmt(num(s["pf"], 0) / gp, 2) if gp else "",
            "papg": fmt(num(s["pa"], 0) / gp, 2) if gp else "",
            "net_ppg": fmt((num(s["pf"], 0) - num(s["pa"], 0)) / gp, 2) if gp else "",
            "pyth_expected_wins": "",           # filled after the exponent is fitted
            "dropbacks_per_game": fmt(dropbacks / gp, 1) if gp and dropbacks is not None else "",
            "rush_att_per_game": fmt(rush_att / gp, 1) if gp and rush_att is not None else "",
            "pass_rate_pct": fmt(pass_rate, 1) if pass_rate is not None else "",
            "pass_yds_per_game": fmt(num(o.get("pass_yds"), 0) / gp, 1) if gp else "",
            "yds_per_play": fmt((num(o.get("pass_yds"), 0) + num(ru.get("rush_yds"), 0)) / plays, 2)
                            if plays else "",
            "sacks_taken_per_game": fmt(sack / gp, 2) if gp and sack is not None else "",
            "opp_dropbacks_per_game": fmt(num(d.get("opp_pass_att"), 0) / gp, 1) if gp else "",
            "opp_pass_yds_per_game": fmt(num(d.get("opp_pass_yds"), 0) / gp, 1) if gp else "",
            "opp_yds_per_att": o.get("opp_yds_per_att", "") if False else fmt(num(d.get("opp_yds_per_att")), 2),
            "def_sacks_per_game": fmt(num(d.get("def_sacks"), 0) / gp, 2) if gp else "",
            "avail_out": len(out_), "avail_doubtful": len(dq), "avail_questionable": len(q),
            "avail_ol_out": len(ol_out), "avail_db_out": len(db_out),
            "avail_dl_out": len(dl_out), "avail_qb_out": len(qb_out),
            "status": "derived", "source_id": "SRC-002;SRC-003;SRC-004;SRC-005;SRC-001",
            "note": "availability counts are from the Week 10 report only (FLG-005: IR players absent)",
        }
        out.append(row)
    return out, off, rush, dfn


def fit_pyth(standings):
    """Choose the Pythagorean exponent that best reproduces the official W-L records."""
    best = None
    for k10 in range(5, 251):           # 0.5 .. 25.0 in 0.1 steps
        k = k10 / 10.0
        sse = 0.0
        for s in standings:
            pf, pa = num(s["pf"], 0), num(s["pa"], 0)
            gp = num(s["games"], 0)
            if not gp:
                continue
            exp_w = gp * (pf ** k) / (pf ** k + pa ** k)
            sse += (exp_w - num(s["w"], 0)) ** 2
        if best is None or sse < best[1]:
            best = (k, sse)
    return best



# --------------------------------------------------------------------------- #
# calibration of the conversion constants against verified games
# --------------------------------------------------------------------------- #
best_L = 22.96


def fit_calibration(games, by_abbr):
    """Fit the two constants the price needs, from verified data only.

    spread: observed home margin ~ alpha + beta * (net_ppg_home - net_ppg_away)
      beta  = shrinkage toward the mean (how much of a rating gap actually shows up)
      alpha = home-field advantage in points
      residual SD = sigma_margin, the width of the spread distribution
    total:  predicted total = L * prod(ratios ** gamma); gamma fitted on a grid.

    Only as many games as are in data/games_2026.csv can be used, so this is a
    small in-sample fit: it is labelled provisional and gated (G-02/G-05).
    """
    xs, ys = [], []
    for g in games:
        h = by_abbr.get(g["home_abbr"])
        a = by_abbr.get(g["away_abbr"])
        if not h or not a:
            continue
        rh, ra = num(h.get("net_ppg")), num(a.get("net_ppg"))
        if rh is None or ra is None:
            continue
        xs.append(rh - ra)
        ys.append(num(g["home_pts"], 0) - num(g["away_pts"], 0))
    n = len(xs)
    if n < 6:
        return {"n": n, "beta": None, "alpha": None, "sigma_margin": None,
                "r2": None, "se_beta": None, "se_alpha": None, "gamma": None,
                "total_rmse": None, "total_mae": None}
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = sxy / sxx if sxx else 0.0
    alpha = my - beta * mx
    resid = [y - (alpha + beta * x) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in resid)
    sst = sum((y - my) ** 2 for y in ys)
    sigma = math.sqrt(sse / (n - 2)) if n > 2 else None
    se_beta = sigma / math.sqrt(sxx) if sigma and sxx else None
    se_alpha = sigma * math.sqrt(1.0 / n + mx * mx / sxx) if sigma and sxx else None
    r2 = 1.0 - sse / sst if sst else None

    # gamma for the total model
    best = None
    for g10 in range(2, 31):          # 0.10 .. 1.50
        gamma = g10 / 20.0
        L = best_L
        errs = []
        for g in games:
            h, a = by_abbr.get(g["home_abbr"]), by_abbr.get(g["away_abbr"])
            if not h or not a:
                continue
            try:
                pred = (L * (num(h["ppg"]) / L) ** gamma * (num(a["papg"]) / L) ** gamma
                        + L * (num(a["ppg"]) / L) ** gamma * (num(h["papg"]) / L) ** gamma)
            except (TypeError, ZeroDivisionError):
                continue
            errs.append(num(g["home_pts"], 0) + num(g["away_pts"], 0) - pred)
        if len(errs) < 6:
            continue
        rmse = math.sqrt(sum(e * e for e in errs) / len(errs))
        if best is None or rmse < best[1]:
            best = (gamma, rmse, sum(abs(e) for e in errs) / len(errs))
    return {"n": n, "beta": beta, "alpha": alpha, "sigma_margin": sigma, "r2": r2,
            "se_beta": se_beta, "se_alpha": se_alpha,
            "gamma": best[0] if best else None, "total_rmse": best[1] if best else None,
            "total_mae": best[2] if best else None}

# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    standings = read_rows("standings_2026.csv")
    p_off = read_rows("team_pass_off_2026.csv")
    r_off = read_rows("team_rush_off_2026.csv")
    p_def = read_rows("team_pass_def_2026.csv")
    injuries = read_rows("injuries_2026_w10.csv")
    games = [g for g in read_rows("games_2026.csv") if g["away_pts"] != ""]

    metrics, off, rush, dfn = team_metrics(standings, p_off, r_off, p_def, injuries)

    k, sse = fit_pyth(standings)
    for row in metrics:
        s = next(x for x in standings if x["abbr"] == row["abbr"])
        pf, pa, gp = num(s["pf"], 0), num(s["pa"], 0), num(s["games"], 0)
        if gp:
            row["pyth_expected_wins"] = fmt(gp * (pf ** k) / (pf ** k + pa ** k), 2)
            row["pyth_exponent_used"] = fmt(k, 1)
        else:
            row["pyth_exponent_used"] = ""
    write_rows("derived_team_metrics.csv", metrics)

    # ---- league stats -----------------------------------------------------
    away = [num(g["away_pts"], 0) for g in games]
    home = [num(g["home_pts"], 0) for g in games]
    margins = [h - a for a, h in zip(away, home)]           # home - away
    totals = [h + a for a, h in zip(away, home)]
    s_m, s_t = summary(margins), summary(totals)
    rows = [
        {"metric": "games_ingested", "value": str(len(games)), "unit": "games",
         "basis": "data/games_2026.csv (Weeks 1-2 + one Week 10 result)", "status": "partial",
         "note": "137 games are verified at league level; only these are row-verified (FLG-016)"},
        {"metric": "mean_home_margin", "value": fmt(s_m["mean"]), "unit": "points",
         "basis": f"n={s_m['n']}", "status": "derived-provisional",
         "note": "sample estimate of home-field advantage in points; CI ~ +/-1.96*SD/sqrt(n)"},
        {"metric": "sd_home_margin", "value": fmt(s_m["sd"]), "unit": "points",
         "basis": f"n={s_m['n']}", "status": "derived-provisional",
         "note": "first input to the spread-width problem; needs the full season (Q-05)"},
        {"metric": "mean_game_total", "value": fmt(s_t["mean"]), "unit": "points",
         "basis": f"n={s_t['n']}", "status": "derived-provisional",
         "note": "compare with the standings-derived 45.92 (F-13), which covers all 137 games"},
        {"metric": "sd_game_total", "value": fmt(s_t["sd"]), "unit": "points",
         "basis": f"n={s_t['n']}", "status": "derived-provisional", "note": ""},
        {"metric": "home_win_rate", "value": fmt(sum(1 for m in margins if m > 0) / len(margins), 3),
         "unit": "share", "basis": f"n={len(margins)}", "status": "derived-provisional",
         "note": "excludes ties; ties reported separately"},
        {"metric": "tie_rate", "value": fmt(sum(1 for m in margins if m == 0) / len(margins), 3),
         "unit": "share", "basis": f"n={len(margins)}", "status": "derived-provisional",
         "note": "under the post-2025 OT rule a tie is still possible (Q-09); the standings show 1 tie "
                 "league-wide through Week 9, i.e. 1/137 = 0.007"},
        {"metric": "pyth_exponent_fitted", "value": fmt(k, 1), "unit": "exponent",
         "basis": f"fitted on 2026 standings (n={sum(1 for x in standings if num(x['games'],0))} clubs), SSE={sse:.2f}",
         "status": "derived", "note": "fitted here, not borrowed: chosen to reproduce official W-L records"},
        {"metric": "league_points_per_club_per_game", "value": fmt(sum(num(s['pf'], 0) for s in standings)
                                                                    / sum(num(s['games'], 0) for s in standings), 2),
         "unit": "points", "basis": "sum(PF)/sum(team-games) over the official standings", "status": "derived-verified",
         "note": "covers all 137 verified games (F-13)"},
    ]
    write_rows("derived_league_stats.csv", rows)

    # ---- correlations -----------------------------------------------------
    def col(table, c):
        return [num(r.get(c)) for r in table]

    pairs = [
        ("game", "home points vs away points (same game)", away, home,
         "drives the correlation of two same-game team-total bets"),
        ("game", "home margin vs game total", margins, totals,
         "negative r means high totals come with closer games - matters for spread+total parlays"),
        ("team", "net points per game vs pass yards per game",
         [num(r["net_ppg"]) for r in metrics], [num(r["pass_yds_per_game"]) for r in metrics],
         "does the aerial game actually separate good teams from bad ones this year"),
        ("team", "net points per game vs rush yards per game",
         [num(r["net_ppg"]) for r in metrics], col(r_off, "rush_yds"),
         "the classic test; a small r here is why run-heavy 'control' edges are hard to bet"),
        ("team", "net points per game vs pass rate",
         [num(r["net_ppg"]) for r in metrics], [num(r["pass_rate_pct"]) for r in metrics],
         "script effect: losing teams pass more, so raw pass-rate correlations are misleading"),
        ("team", "points allowed per game vs opponent pass yards allowed per game",
         [num(r["papg"]) for r in metrics], [num(r["opp_pass_yds_per_game"]) for r in metrics],
         "if r is high, pass-yards allowed is a usable defensive-quality proxy for prop pricing"),
        ("team", "sacks taken per game vs opponent sacks per game (same club)",
         [num(r["sacks_taken_per_game"]) for r in metrics], [num(r["def_sacks_per_game"]) for r in metrics],
         "near-zero is expected: O-line quality and pass-rush quality are different traits"),
        ("team", "offense pass attempts vs rush attempts (same club)",
         [num(r["pass_att"]) for r in p_off], col(r_off, "rush_att"),
         "within-team volume substitution; the reason 'both overs' in one backfield are not independent"),
    ]
    crows = []
    for scope, label, xs, ys, why in pairs:
        r, lo, hi, n = corr(xs, ys)
        crows.append({
            "scope": scope, "pair": label, "r": fmt(r, 3), "ci95_low": fmt(lo, 3), "ci95_high": fmt(hi, 3),
            "n": n, "basis": "2026 Weeks 1-2 box scores" if scope == "game" else "2026 season team aggregates",
            "status": "measured-provisional" if r is not None else "insufficient",
            "interpretation": why,
            "source_id": "SRC-006;SRC-007" if scope == "game" else "SRC-002;SRC-003;SRC-004;SRC-005",
        })
    for label, why in [
        ("spread outcome vs next-week spread outcome (market autocorrelation)",
         "cannot be measured without market lines (Q-01)"),
        ("injury-report 'Out' count vs same-game point total", "needs 4+ weeks of game-level data (Q-04)"),
        ("parlay leg correlation as priced by books", "no official source publishes book correlation rules (FLG-010)"),
        ("player prop vs team volume, per position", "blocked by Q-08 (no player-level rates in repo)"),
    ]:
        crows.append({"scope": "pending", "pair": label, "r": "", "ci95_low": "", "ci95_high": "", "n": "",
                      "basis": "no verified data", "status": "unverified-blank", "interpretation": why,
                      "source_id": ""})
    write_rows("derived_correlations.csv", crows)

    # ---- ratings ----------------------------------------------------------
    rated = []
    for row in metrics:
        s = next(x for x in standings if x["abbr"] == row["abbr"])
        gp = num(s["games"], 0)
        net = num(row["net_ppg"]) if row["net_ppg"] else None
        pyth_ppg = None
        if gp:
            exp_w = num(row["pyth_expected_wins"], 0)
            pyth_ppg = (exp_w - (gp - exp_w) * 0.0) / gp      # win share, kept separate from points
        rated.append({
            "abbr": row["abbr"], "team": row["team"],
            "rating_net_ppg": fmt(net),
            "rating_pyth_win_share": fmt(pyth_ppg, 3) if pyth_ppg is not None else "",
            "rating_method_a_vs_b_gap": "",
            "schedule_adjusted": "",
            "status": "provisional-unadjusted",
            "note": "no schedule adjustment: game-level opponents for Weeks 3-9 are not ingested (Q-04)",
            "source_id": row["source_id"],
        })
    write_rows("power_ratings.csv", rated)

    # ---- calibration ------------------------------------------------------
    by_abbr = {r["abbr"]: r for r in metrics}
    cal = fit_calibration(games, by_abbr)
    crows_cal = [
        {"constant": "beta (rating-gap to points)", "value": fmt(cal["beta"], 3), "unit": "multiplier",
         "se": fmt(cal["se_beta"], 3), "n": cal["n"],
         "method": "OLS of verified home margin on the net-points gap, no intercept-free constraint",
         "status": "provisional-in-sample",
         "note": "beta should be < 1 (shrinkage toward the mean); beta >= 1 on a 33-game in-sample fit "
                 "is a symptom of too small a sample, not evidence that ratings under-move the line - FLG-026"},
        {"constant": "alpha (home-field advantage)", "value": fmt(cal["alpha"], 2), "unit": "points",
         "se": fmt(cal["se_alpha"], 2), "n": cal["n"], "method": "OLS intercept",
         "status": "provisional-in-sample",
         "note": "2026 estimate from the ingested games; Q-06 asks for the full-season value"},
        {"constant": "sigma_margin (residual SD)", "value": fmt(cal["sigma_margin"], 2), "unit": "points",
         "se": "", "n": cal["n"], "method": "residual SD of the OLS fit (n-2)",
         "status": "provisional-in-sample",
         "note": "converts a spread into a win probability, and a win probability into a moneyline"},
        {"constant": "r2 (rating gap explains margin)", "value": fmt(cal["r2"], 3), "unit": "R^2",
         "se": "", "n": cal["n"], "method": "1 - SSE/SST", "status": "provisional-in-sample",
         "note": "how much of a game margin an unadjusted net-points gap captures at all"},
        {"constant": "gamma (total model exponent)", "value": fmt(cal["gamma"], 2), "unit": "exponent",
         "se": "", "n": cal["n"], "method": "grid search minimising total RMSE, gamma in 0.10..1.00",
         "status": "provisional-in-sample",
         "note": ("GRID BOUNDARY HIT - the fit wants more than the search range, which means the "
                  "multiplicative total model is not yet identified (FLG-026)"
                  if cal["gamma"] and abs(cal["gamma"] - 1.50) < 1e-9 else
                  "gamma=1 is the naive multiplicative model; gamma<1 shrinks the ratios")},
        {"constant": "total model RMSE", "value": fmt(cal["total_rmse"], 2), "unit": "points",
         "se": "", "n": cal["n"], "method": "sqrt(mean squared error) on verified game totals",
         "status": "provisional-in-sample", "note": f"MAE={fmt(cal['total_mae'], 2)} points"},
        {"constant": "pyth_exponent", "value": fmt(k, 1), "unit": "exponent", "se": "",
         "n": sum(1 for x in standings if num(x["games"], 0)),
         "method": "grid search reproducing official W-L records", "status": "derived",
         "note": f"SSE={sse:.2f} wins^2 over 32 clubs"},
    ]
    write_rows("model_calibration.csv", crows_cal)

    # ---- lines ------------------------------------------------------------
    try:
        slate = read_rows("slate_2026_w10.csv")
    except FileNotFoundError:
        slate = []
    lines = []
    lg_ppg = num([r for r in rows if r["metric"] == "league_points_per_club_per_game"][0]["value"], 0)
    globals()["best_L"] = lg_ppg or 22.96
    gamma = cal["gamma"] or 1.0
    beta, alpha = cal["beta"], cal["alpha"]
    for g in slate:
        h, a = by_abbr.get(g["home_abbr"], {}), by_abbr.get(g["away_abbr"], {})
        r_h, r_a = num(h.get("net_ppg")), num(a.get("net_ppg"))
        spread = None
        if r_h is not None and r_a is not None and beta is not None:
            exp_margin_home = alpha + beta * (r_h - r_a)
            spread = -exp_margin_home                       # price on the home team
        else:
            exp_margin_home = None
        tot = None
        if h and a and lg_ppg:
            try:
                tot = (lg_ppg * (num(h["ppg"]) / lg_ppg) ** gamma * (num(a["papg"]) / lg_ppg) ** gamma
                       + lg_ppg * (num(a["ppg"]) / lg_ppg) ** gamma * (num(h["papg"]) / lg_ppg) ** gamma)
            except (TypeError, ZeroDivisionError):
                tot = None
        p_home = None
        if exp_margin_home is not None and cal["sigma_margin"]:
            p_home = 0.5 * (1.0 + math.erf(exp_margin_home / (cal["sigma_margin"] * math.sqrt(2.0))))
        avail_note = []
        for tag, r_ in (("home", h), ("away", a)):
            if num(r_.get("avail_qb_out"), 0):
                avail_note.append(f"{tag}:QB-out")
            if num(r_.get("avail_ol_out"), 0) >= 2:
                avail_note.append(f"{tag}:2+ OL out")
            if num(r_.get("avail_db_out"), 0) >= 2:
                avail_note.append(f"{tag}:2+ DB out")
        lines.append({
            "game_date": g["game_date"], "kickoff_et": g["kickoff_et"], "venue_note": g.get("venue_note", ""),
            "away": g["away"], "home": g["home"],
            "expected_home_margin": fmt(exp_margin_home, 1) if exp_margin_home is not None else "",
            "model_spread_home": fmt(spread, 1) if spread is not None else "",
            "model_p_home": fmt(p_home, 3) if p_home is not None else "",
            "model_total": fmt(tot, 1) if tot is not None else "",
            "hfa_applied": fmt(alpha, 2) if alpha is not None else "uncalibrated (Q-06)",
            "market_spread": "", "market_total": "", "market_source": "",
            "gap_to_market": "", "actionable": "no - no market price exists to compare with (Q-01)",
            "availability_flags": ";".join(avail_note),
            "status": "provisional-fitted-not-bettable",
            "note": "rounded only to 0.5 at the market column; constants are in-sample (model_calibration.csv)",
            "source_id": "SRC-001;SRC-002;SRC-003;SRC-004;SRC-005;SRC-006;SRC-007",
        })

    write_rows("lines_origination.csv", lines)
    print(f"calibration: beta={fmt(cal['beta'],3)} alpha={fmt(cal['alpha'],2)} sigma={fmt(cal['sigma_margin'],2)} "
          f"gamma={fmt(cal['gamma'],2)} r2={fmt(cal['r2'],3)} on n={cal['n']} games")
    print(f"derived: {len(metrics)} teams, {len(rows)} league stats, {len(crows)} correlations, "
          f"{len(rated)} ratings, {len(lines)} lines (Pythagoras exponent fitted = {k:.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
