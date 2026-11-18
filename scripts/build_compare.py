#!/usr/bin/env python3
"""FL3 — origination comparison lab.

WHAT THIS ANSWERS
-----------------
The repo can originate a line (five different ways, in five different subsessions) and it can no
longer tell which way is better, because nobody ever compared them on the same games with the same
clock. This module does exactly that, and nothing else:

  * four rival scoring strategies, one shared evaluation harness;
  * every forecast for week w is built only from weeks < w  (walk-forward, no leakage);
  * inputs are the 148 verified game rows in data/week_results_2026.csv, which reproduce the
    league's own standings figure for figure (W/L/T/PF/PA for all 32 clubs);
  * no price exists in this repository, so ROI and CLV are NOT computed anywhere. The comparison is
    on proper scores (Brier, log loss) and pricing error (MAE, RMSE, bias, dispersion), none of
    which need a price;
  * every interval is a game-cluster bootstrap: a resample draws whole games, so the two clubs in a
    game move together;
  * the number of comparisons is published and used to widen the significance threshold, because
    "best of N on one sample" is itself a source of apparent skill;
  * a strategy is only called *skillful* if its interval against the best control excludes zero
    **after** that adjustment. With n = 148 and this much noise the honest answer is very likely
    "not established" — and the page is allowed to say so.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
No backtest number from this file may appear on the prospective leaderboard (readiness R010). The
output carries `dataset="retrospective"` on every row and the renderer prints it. Week 11 forecasts
are produced by the same frozen code and *are* prospective — they are written to a separate file
with a separate label, and committed before the first Week 11 kickoff (2026-11-19T20:15 ET).

Run:  python3 scripts/build_compare.py
      python3 scripts/build_compare.py --check     (exit 1 if the committed output is stale)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics as st
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "compare")

RESULTS = os.path.join(DATA, "week_results_2026.csv")
SLATE = os.path.join(DATA, "week11_slate_2026.csv")

SEED = 20261117
BOOT = 4000
PRIOR_GAMES = 2.0          # shrink each club rate toward the league mean by this many games
HFA_PRIOR_GAMES = 8.0      # same idea for the home-field estimate

RESULTS_URL = "https://www.nfl.com/schedules/2026/by-week/week-{w}"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/reg"
SLATE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"


# ---------------------------------------------------------------------------
# tiny stats toolkit (stdlib only, deterministic)
# ---------------------------------------------------------------------------
def mean(xs):
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    return st.pstdev(xs) if len(xs) > 1 else None


def erf_inv_ok():
    return True


def phi(z):
    """Standard normal CDF via erf — no scipy, no approximation error to argue about."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def boot_z(games, stat_fn, seed=SEED, B=BOOT):
    """(estimate, bootstrap SD, z) for a statistic. z is estimate / its own resample SD.

    The Bonferroni verdict is made on this z against the adjusted critical value, not on whether a
    95% interval happens to clear zero — those are different tests and only the first one accounts
    for how many arms were tried.
    """
    est = stat_fn(games)
    rng = random.Random(seed)
    n = len(games)
    vals = []
    for _ in range(B):
        sample = [games[rng.randrange(n)] for _ in range(n)]
        v = stat_fn(sample)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if len(vals) < 50:
        return est, None, None
    d = sd(vals)
    z = (est / d) if d else None
    return est, d, z


def _z_for_two_sided(alpha):
    """Inverse normal for a two-sided alpha, by bisection on erf — no table, no scipy."""
    target = 1.0 - alpha / 2.0
    lo, hi = 0.0, 12.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if phi(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def pct(xs, q):
    """Percentile with linear interpolation; q in [0,1]."""
    if not xs:
        return None
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def cluster_bootstrap(games, stat_fn, seed=SEED, B=BOOT):
    """Resample whole games (a game carries both clubs, so clusters stay intact)."""
    rng = random.Random(seed)
    n = len(games)
    vals = []
    for _ in range(B):
        sample = [games[rng.randrange(n)] for _ in range(n)]
        v = stat_fn(sample)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if len(vals) < 50:
        return None, None
    return pct(vals, 0.025), pct(vals, 0.975)


def cluster_bootstrap_paired(games, stat_fn, seed=SEED, B=BOOT):
    """Same resample used for both arms — the correct way to interval a *difference*."""
    rng = random.Random(seed)
    n = len(games)
    vals = []
    for _ in range(B):
        sample = [games[rng.randrange(n)] for _ in range(n)]
        v = stat_fn(sample)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if len(vals) < 50:
        return None, None
    return pct(vals, 0.025), pct(vals, 0.975)


# ---------------------------------------------------------------------------
# input
# ---------------------------------------------------------------------------
def load_games():
    rows = []
    with open(RESULTS, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "week": int(r["week"]),
                "date": r["game_date"],
                "away": r["away_abbr"],
                "home": r["home_abbr"],
                "away_pts": int(r["away_pts"]),
                "home_pts": int(r["home_pts"]),
                "source_url": r["source_url"],
                "accessed_utc": r["accessed_utc"],
            })
    rows.sort(key=lambda g: (g["week"], g["date"], g["away"], g["home"]))
    return rows


def load_slate():
    out = []
    with open(SLATE, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# rolling club state — the only place a number is allowed to see the past
# ---------------------------------------------------------------------------
class History:
    """Everything a forecast may know before a given week.

    `add()` is called only after the week's forecasts have been produced, so the object is
    physically incapable of leaking a same-week result into a same-week forecast.
    """

    def __init__(self):
        self.pf = {}
        self.pa = {}
        self.gp = {}
        self.opp = {}          # club -> list of opponents faced
        self.margins = []      # home margin, league-wide
        self.totals = []
        self.team_totals = {}  # club -> list of game totals it played in

    def add(self, g):
        for club, scored, allowed in ((g["home"], g["home_pts"], g["away_pts"]),
                                      (g["away"], g["away_pts"], g["home_pts"])):
            self.pf[club] = self.pf.get(club, 0) + scored
            self.pa[club] = self.pa.get(club, 0) + allowed
            self.gp[club] = self.gp.get(club, 0) + 1
        self.opp.setdefault(g["home"], []).append(g["away"])
        self.opp.setdefault(g["away"], []).append(g["home"])
        self.margins.append(g["home_pts"] - g["away_pts"])
        tot = g["home_pts"] + g["away_pts"]
        self.totals.append(tot)
        self.team_totals.setdefault(g["home"], []).append(tot)
        self.team_totals.setdefault(g["away"], []).append(tot)

    # --- league context -----------------------------------------------------
    def league_ppg(self):
        n = sum(self.gp.values())
        return (sum(self.pf.values()) / n) if n else 22.0

    def league_total(self):
        return mean(self.totals) if self.totals else 44.0

    def hfa(self):
        """Home margin shrunk toward 0 — with 8 prior games of pseudo-evidence."""
        if not self.margins:
            return 1.9
        n = len(self.margins)
        return (sum(self.margins) / (n + HFA_PRIOR_GAMES)) * (n / (n + HFA_PRIOR_GAMES)) if n else 0.0

    def pace_total(self, home, away):
        """Expected total from both clubs' own game totals — the S2/S4 total estimator."""
        if not self.totals:
            return self.league_total()
        L = self.league_total()
        gp = self.gp
        g_h, g_a = gp.get(home, 0), gp.get(away, 0)
        t_h = self.team_totals.get(home, []); t_a = self.team_totals.get(away, [])
        if not t_h or not t_a:
            return L
        m_h = mean(t_h); m_a = mean(t_a)
        w_h = g_h / (g_h + PRIOR_GAMES); w_a = g_a / (g_a + PRIOR_GAMES)
        e_h = w_h * m_h + (1 - w_h) * L
        e_a = w_a * m_a + (1 - w_a) * L
        return (e_h + e_a) / 2.0

    def margin_sigma(self):
        """Trailing SD of actual margins — the scale used to turn a margin into a probability."""
        return sd(self.margins) if len(self.margins) >= 12 else 13.0

    def scale(self):
        L = self.league_ppg()
        return L if L > 0 else 22.0

    def def_rate(self, club):
        """Points this club allows per game, shrunk toward the league mean.

        Deliberately NOT h.pa[club]/g. With a single `pa` table the expression
        (own PF + opponent PA)/2 collapses algebraically to a plain net-points rating, which would
        silently make two of the four arms the same model. This is the honest separate quantity.
        """
        return self.rate(self.pa, club)

    # --- per-club rates, shrunk toward the league mean ----------------------
    def rate(self, table, club, prior=None):
        g = self.gp.get(club, 0)
        raw = table.get(club)
        base = prior if prior is not None else self.league_ppg()
        if raw is None or g == 0:
            return base
        w = g / (g + PRIOR_GAMES)
        return w * (raw / g) + (1.0 - w) * base


# ---------------------------------------------------------------------------
# the four strategies. Each returns (pred_margin, pred_total) for a fixture,
# where pred_margin is HOME minus AWAY.
# ---------------------------------------------------------------------------
def s_net(h, home, away):
    """Net points per game: one number per club, the simplest rating that works."""
    L = h.scale()
    hn = h.rate(h.pf, home, L) - h.rate(h.pa, home, L)
    an = h.rate(h.pf, away, L) - h.rate(h.pa, away, L)
    return (hn - an) + h.hfa(), h.pace_total(home, away)


def s_pfpa(h, home, away):
    """Offence meets defence, with an offence-only total.

    The margin is the matchup version: own scoring rate against the opponent's concession rate.
    The total is deliberately a *different family* — league total plus each club's own scoring
    deviation — so that "pace" and "expected scores" are genuinely two estimators and the head-to-
    head on the page is not the same quantity written twice.
    """
    L = h.scale()
    exp_home = (h.rate(h.pf, home, L) + h.def_rate(away)) / 2.0 + h.hfa() / 2.0
    exp_away = (h.rate(h.pf, away, L) + h.def_rate(home)) / 2.0 - h.hfa() / 2.0
    tot = h.league_total() + (h.rate(h.pf, home, L) - L) + (h.rate(h.pf, away, L) - L)
    return exp_home - exp_away, tot


def _z_for_p(p):
    """Inverse standard normal by bisection on erf."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    lo, hi = -12.0, 12.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


PYTH_EXP = 2.37   # the standard Pythagorean exponent for the NFL; a modelling choice, not a fact


def pyth_share(pf, pa):
    if not pf or not pa:
        return None
    return (pf ** PYTH_EXP) / (pf ** PYTH_EXP + pa ** PYTH_EXP)


def s_pyth(h, home, away):
    """Luck-stripped rating: convert each club's Pythagorean win share into an expected margin.

    A club that has won on a +90 point differential has the same record as one that has won on
    +5, and a rating built on points *already* regresses that. Converting through the normal
    quantile keeps the output in the same margin units as the other arms, so they can be scored
    against the same benchmark.
    """
    L = h.scale()
    sigma = h.margin_sigma()

    def club_margin(club):
        g = h.gp.get(club, 0)
        share = pyth_share(h.pf.get(club), h.pa.get(club))
        if share is None or not g:
            return 0.0
        w = g / (g + PRIOR_GAMES)
        share = w * share + (1.0 - w) * 0.5
        return sigma * _z_for_p(share)

    m_home = club_margin(home)
    m_away = club_margin(away)
    # total: the pace estimator plus the whole home-field term, which is the open question about
    # home field — does it raise the total or only shift the margin? Published as a third column.
    return (m_home - m_away) + h.hfa(), h.pace_total(home, away) + h.hfa()


def _solve(a, b):
    """Gaussian elimination with partial pivoting; small dense systems only."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        ssum = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = ssum / m[r][r]
    return x


def massey_ratings(games, clubs):
    """Opponent-aware least squares (Massey).

    Minimises the squared error of (rating_home - rating_away - margin). The home-field term is
    netted out by centring, so it is added back once when the fixture is priced. A small ridge
    penalty keeps the system solvable in week 2, when the game graph is still disconnected.
    """
    idx = {c: i for i, c in enumerate(clubs)}
    n = len(clubs)
    A = [[0.0] * n for _ in range(n)]
    y = [0.0] * n
    ridge = 1.0
    for g in games:
        i, j = idx[g["home"]], idx[g["away"]]
        m = g["home_pts"] - g["away_pts"]
        A[i][i] += 1.0
        A[j][j] += 1.0
        A[i][j] -= 1.0
        A[j][i] -= 1.0
        y[i] += m
        y[j] -= m
    for i in range(n):
        A[i][i] += ridge
    x = _solve(A, y)
    if x is None:
        return None
    mu = sum(x) / n
    return {c: x[i] - mu for c, i in idx.items()}


class MasseyState:
    """The solver needs the game list, not just running sums. Kept here so the leak rule holds:
    `add()` is only called after a week's forecasts have been produced."""

    def __init__(self):
        self.games = []

    def add(self, g):
        self.games.append(g)


def s_massey(h, ms, home, away, clubs):
    r = massey_ratings(ms.games, clubs) if ms.games else None
    if r is None:
        return None, None
    hm = r.get(home, 0.0) - r.get(away, 0.0) + h.hfa()
    return hm, h.pace_total(home, away)


STRATEGIES = [
    ("S1", "net", "Net points per game", s_net,
     "one rating per club: (PF-PA)/G shrunk to the league mean; total from both clubs' own pace"),
    ("S2", "pfpa", "Offence meets defence", s_pfpa,
     "own scoring rate against the opponent's concession rate; total is the two expected scores"),
    ("S3", "massey", "Opponent-aware least squares", None,
     "Massey ratings solved from the game graph, so a club is rated against whom it actually played"),
    ("S4", "pyth", "Pythagorean, luck-stripped", s_pyth,
     "Pythagorean win share mapped to a margin; tests whether home field also raises the total"),
]

CONTROLS = [
    ("C1", "coin", "Coin flip", "win probability 0.50 fixed"),
    ("C2", "home_always", "Home always wins", "win probability 1.00 for the home club"),
    ("C3", "pickem", "Pick'em margin", "predicted margin 0 for every game"),
    ("C4", "trailing_total", "Trailing league mean total", "predicted total = mean total of all games already played"),
]


# ---------------------------------------------------------------------------
# walk-forward run
# ---------------------------------------------------------------------------
def forecast_all(games, strategies):
    """One pass over the season in week order. Returns per-game forecast rows."""
    clubs = sorted({g["home"] for g in games} | {g["away"] for g in games})
    h = History()
    ms = MasseyState()
    by_week = {}
    for g in games:
        by_week.setdefault(g["week"], []).append(g)
    out = []
    weeks = sorted(by_week)
    for w in weeks:
        # ---- forecast every game in week w using state built from weeks < w ----
        sigma = h.margin_sigma()
        for g in by_week[w]:
            row = {
                "week": w,
                "date": g["date"],
                "away": g["away"],
                "home": g["home"],
                "away_pts": g["away_pts"],
                "home_pts": g["home_pts"],
                "actual_margin": g["home_pts"] - g["away_pts"],
                "actual_total": g["home_pts"] + g["away_pts"],
                "home_won": 1 if g["home_pts"] > g["away_pts"] else 0,
                "source_url": g["source_url"],
                "burn_in": 1 if w == weeks[0] else 0,
                "clubs_seen_home": h.gp.get(g["home"], 0),
                "clubs_seen_away": h.gp.get(g["away"], 0),
                "sigma_used": round(sigma, 4),
            }
            for sid, key, _label, fn, _desc in strategies:
                m, t = (None, None)
                if key == "massey":
                    m, t = s_massey(h, ms, g["home"], g["away"], clubs)
                else:
                    m, t = fn(h, g["home"], g["away"])
                row[f"{sid}_margin"] = None if m is None else round(m, 4)
                row[f"{sid}_total"] = None if t is None else round(t, 4)
                row[f"{sid}_p_home"] = None if m is None else round(phi(m / sigma), 6)
            # controls
            row["C3_margin"] = 0.0
            row["C4_total"] = round(h.league_total(), 4)
            row["C1_p_home"] = 0.5
            row["C2_p_home"] = 1.0
            out.append(row)
        # ---- only now is the week's result allowed into the state ----
        for g in by_week[w]:
            h.add(g)
            ms.add(g)
    return out, weeks


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------
def brier(rows, key):
    return mean([(r[key] - r["home_won"]) ** 2 for r in rows])


def logloss(rows, key, eps=1e-6):
    total = 0.0
    for r in rows:
        p = min(max(r[key], eps), 1 - eps)
        total += -(math.log(p) if r["home_won"] == 1 else math.log(1 - p))
    return total / len(rows)


def mae(rows, pred_key):
    return mean([abs(r[pred_key] - r["actual_margin"]) for r in rows])


def rmse(rows, pred_key, actual_key="actual_margin"):
    return math.sqrt(mean([(r[pred_key] - r[actual_key]) ** 2 for r in rows]))


def bias(rows, pred_key, actual_key="actual_margin"):
    return mean([r[pred_key] - r[actual_key] for r in rows])


def dispersion(rows, pred_key, actual_key="actual_margin"):
    p = sd([r[pred_key] for r in rows])
    a = sd([r[actual_key] for r in rows])
    return (p / a) if (p is not None and a) else None


def evaluate(rows, sid, key, base_rate=None):
    """All metrics for one (strategy, market) cell, with clustered intervals."""
    mrows = [r for r in rows if r[f"{sid}_margin"] is not None]
    trows = [r for r in rows if r[f"{sid}_total"] is not None]
    prows = [r for r in rows if r[f"{sid}_p_home"] is not None]
    res = {
        "strategy": sid, "key": key, "base_rate": base_rate,
        "n_margin": len(mrows), "n_total": len(trows), "n_win": len(prows),
    }
    if mrows:
        res["margin_mae"] = mae(mrows, f"{sid}_margin")
        res["margin_rmse"] = rmse(mrows, f"{sid}_margin")
        res["margin_bias"] = bias(mrows, f"{sid}_margin")
        res["margin_dispersion"] = dispersion(mrows, f"{sid}_margin")
        res["margin_mae_ci"] = cluster_bootstrap(mrows, lambda s: mae(s, f"{sid}_margin"))
        res["margin_rmse_ci"] = cluster_bootstrap(mrows, lambda s: rmse(s, f"{sid}_margin"))
        res["dir_acc"] = mean([1.0 if (r[f"{sid}_margin"] > 0) == (r["actual_margin"] > 0)
                               and r["actual_margin"] != 0 else 0.0 for r in mrows])
    if trows:
        res["total_mae"] = mae(trows, f"{sid}_total") if False else mean(
            [abs(r[f"{sid}_total"] - r["actual_total"]) for r in trows])
        res["total_rmse"] = math.sqrt(mean([(r[f"{sid}_total"] - r["actual_total"]) ** 2 for r in trows]))
        res["total_bias"] = mean([r[f"{sid}_total"] - r["actual_total"] for r in trows])
        res["total_mae_ci"] = cluster_bootstrap(
            trows, lambda s: mean([abs(r[f"{sid}_total"] - r["actual_total"]) for r in s]))
        res["total_rmse_ci"] = cluster_bootstrap(
            trows, lambda s: math.sqrt(mean([(r[f"{sid}_total"] - r["actual_total"]) ** 2 for r in s])))
    if prows:
        res["brier"] = brier(prows, f"{sid}_p_home")
        res["logloss"] = logloss(prows, f"{sid}_p_home")
        res["brier_ci"] = cluster_bootstrap(prows, lambda s: brier(s, f"{sid}_p_home"))
        res["brier_skill_vs_coin"] = 1.0 - res["brier"] / 0.25
        res["brier_skill_vs_base"] = 1.0 - res["brier"] / (res["base_rate"] * (1 - res["base_rate"]))
        # paired difference against the coin, same resample draw
        def _d(s):
            return brier(s, f"{sid}_p_home") - 0.25
        res["brier_diff_vs_coin_ci"] = cluster_bootstrap_paired(prows, _d)
    return res


# ---------------------------------------------------------------------------
# main computation
# ---------------------------------------------------------------------------
def calibration(rows, key, bins=(0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0001)):
    """Reliability: for each predicted-probability band, what actually happened."""
    out = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        band = [r for r in rows if lo <= r[key] < hi]
        if not band:
            out.append({"lo": lo, "hi": min(hi, 1.0), "n": 0, "pred": None, "actual": None})
            continue
        out.append({
            "lo": lo, "hi": min(hi, 1.0), "n": len(band),
            "pred": mean([r[key] for r in band]),
            "actual": mean([r["home_won"] for r in band]),
        })
    return out


def luck_panel(rows, key):
    """Score of the model's own implied picks, split into what it earned and what it was given.

    `expected_wins` accumulates the model's own probability on the side it favours; that is what a
    perfectly calibrated version of this model would win on the same games. `won` is what happened.
    The difference is luck. It is reported per strategy and never ranked on.
    """
    exp_w = 0.0
    won = 0
    n = 0
    for r in rows:
        p = r[key]
        if p is None:
            continue
        side_home = p >= 0.5
        p_pick = p if side_home else 1 - p
        exp_w += p_pick
        act = r["home_won"] if side_home else 1 - r["home_won"]
        won += act
        n += 1
    if not n:
        return None
    return {"n": n, "expected_wins": exp_w, "won": won, "luck": won - exp_w,
            "win_rate": won / n, "expected_rate": exp_w / n}


def regime_split(forecasts, sid, cuts=((2, 6), (7, 10))):
    out = []
    for lo, hi in cuts:
        band = [f for f in forecasts if lo <= f["week"] <= hi and f[f"{sid}_margin"] is not None]
        if not band:
            continue
        out.append({
            "weeks": f"{lo}-{hi}", "n": len(band),
            "margin_mae": mae(band, f"{sid}_margin"),
            "margin_mae_ci": cluster_bootstrap(band, lambda s: mae(s, f"{sid}_margin")),
            "brier": brier(band, f"{sid}_p_home"),
        })
    return out


def build():
    games = load_games()
    for g in games:
        g["home_won"] = 1 if g["home_pts"] > g["away_pts"] else 0
    forecasts, weeks = forecast_all(games, STRATEGIES)
    headline = [f for f in forecasts if f["burn_in"] == 0]

    # attach outcome + base-rate context used by the scorers
    base_rate = mean([f["home_won"] for f in forecasts])

    eval_rows = []
    for sid, key, label, fn, desc in STRATEGIES:
        r = evaluate(headline, sid, key, base_rate)
        r["label"] = label
        r["description"] = desc
        r["kind"] = "strategy"
        r["base_rate"] = base_rate
        eval_rows.append(r)
    for sid, key, label, desc in CONTROLS:
        if key in ("coin", "home_always"):
            res = {
                "strategy": sid, "key": key, "label": label, "description": desc,
                "kind": "control", "n_win": len(headline), "base_rate": base_rate,
            }
            res["brier"] = brier(headline, f"{sid}_p_home")
            res["logloss"] = logloss(headline, f"{sid}_p_home")
            res["brier_ci"] = cluster_bootstrap(headline, lambda s: brier(s, f"{sid}_p_home"))
            res["brier_skill_vs_coin"] = 1.0 - res["brier"] / 0.25
            res["brier_skill_vs_base"] = 1.0 - res["brier"] / (base_rate * (1 - base_rate))
            eval_rows.append(res)
        elif key == "pickem":
            res = {"strategy": sid, "key": key, "label": label, "description": desc,
                   "kind": "control", "n_margin": len(headline)}
            res["margin_mae"] = mae(headline, "C3_margin")
            res["margin_rmse"] = rmse(headline, "C3_margin")
            res["margin_bias"] = bias(headline, "C3_margin")
            res["margin_dispersion"] = 0.0
            res["margin_mae_ci"] = cluster_bootstrap(headline, lambda s: mae(s, "C3_margin"))
            res["margin_rmse_ci"] = cluster_bootstrap(headline, lambda s: rmse(s, "C3_margin"))
            res["base_rate"] = base_rate
            eval_rows.append(res)
        else:
            res = {"strategy": sid, "key": key, "label": label, "description": desc,
                   "kind": "control", "n_total": len(headline)}
            res["total_mae"] = mean([abs(r["C4_total"] - r["actual_total"]) for r in headline])
            res["total_rmse"] = math.sqrt(mean([(r["C4_total"] - r["actual_total"]) ** 2
                                                for r in headline]))
            res["total_bias"] = mean([r["C4_total"] - r["actual_total"] for r in headline])
            res["total_mae_ci"] = cluster_bootstrap(
                headline, lambda s: mean([abs(r["C4_total"] - r["actual_total"]) for r in s]))
            res["total_rmse_ci"] = cluster_bootstrap(
                headline, lambda s: math.sqrt(mean([(r["C4_total"] - r["actual_total"]) ** 2 for r in s])))
            res["base_rate"] = base_rate
            eval_rows.append(res)

    # ---- multiplicity ledger ----------------------------------------------
    n_tests = len(STRATEGIES) * 3          # 4 strategies x (side, total, moneyline)
    alpha = 0.05
    z_crit = 1.96                      # two-sided 95%
    adj = alpha / n_tests
    z_bonf = _z_for_two_sided(adj)

    eval_summary = {
        "games": len(games),
        "z_crit_95": z_crit,
        "z_crit_bonferroni": round(z_bonf, 4),
        "weeks": weeks,
        "strategies": len(STRATEGIES),
        "controls": len(CONTROLS),
        "comparisons": n_tests,
        "alpha": alpha,
        "bonferroni_alpha": alpha / n_tests,
        "zero_inside_interval_rule": "materially-zero: a 95% interval that contains 0 cannot "
                                     "establish skill, and this page will not call it skill",
        "bootstrap": f"{BOOT} game-cluster resamples, seed {SEED}",
        "price_policy": "No licensed price is held, so ROI and CLV are not computed and not implied",
        "dataset": "retrospective",
        "estimator_families": "A = pace (mean of both clubs' game totals). "
                              "B = offence only (league total plus each club's scoring deviation). "
                              "C = pace plus the whole home-field term. Three different quantities, "
                              "published side by side until one wins walk-forward (R051).",
        "regime_split": "every strategy is also evaluated on two disjoint slices — weeks 2-6, where "
                        "every club has seen fewer than six games, and weeks 7-10, where it has "
                        "seen more. A strategy whose edge only exists in one regime has not been "
                        "shown to generalise.",
        # NO build timestamp: CI requires this file to be byte-identical on a re-run, and a
        # clock read would make every run dirty. Provenance is the input SHA-256 below.
        "method_version": "compare-1.1",
    }

    # ---- honest verdict per (strategy, market) -----------------------------
    verdicts = []
    ctrl_mae = next(r["margin_mae"] for r in eval_rows if r["strategy"] == "C3")
    ctrl_brier = min(r["brier"] for r in eval_rows if r["kind"] == "control" and "brier" in r)
    for r in eval_rows:
        if r["kind"] != "strategy":
            continue
        v = {"strategy": r["strategy"], "label": r["label"]}
        if "margin_mae" in r:
            lo, hi = r["margin_mae_ci"] or (None, None)
            diff = r["margin_mae"] - ctrl_mae
            v["margin_gain_vs_pickem"] = diff
            v["margin_gain_material"] = (lo is not None and hi < ctrl_mae)
            # paired difference interval vs pick'em
            mrows = [f for f in forecasts if f[f"{r['strategy']}_margin"] is not None]
            def _d(s, sid=r["strategy"]):
                return (mean([abs(x[f"{sid}_margin"] - x["actual_margin"]) for x in s])
                        - mean([abs(0.0 - x["actual_margin"]) for x in s]))
            v["margin_gain_ci"] = cluster_bootstrap_paired(mrows, _d)
        if "brier" in r:
            lo, hi = r["brier_ci"] or (None, None)
            pr = [f for f in forecasts if f[f"{r['strategy']}_p_home"] is not None]
            def _db(s, sid=r["strategy"]):
                return brier(s, f"{sid}_p_home") - 0.25
            v["brier_diff_vs_coin"] = r["brier"] - 0.25
            v["brier_diff_ci"] = cluster_bootstrap_paired(pr, _db)
            v["brier_material"] = (lo is not None and hi < 0.25)
        # proper Bonferroni verdict: estimate / bootstrap SE against the adjusted critical value
        if "margin_mae" in r:
            mrows = [f for f in forecasts if f[f"{r['strategy']}_margin"] is not None]
            def _dg(s, sid=r["strategy"]):
                return (mean([abs(x[f"{sid}_margin"] - x["actual_margin"]) for x in s])
                        - mean([abs(0.0 - x["actual_margin"]) for x in s]))
            est, d, z = boot_z(mrows, _dg)
            v["margin_gain"] = est
            v["margin_gain_boot_sd"] = d
            v["margin_gain_z"] = z
            v["margin_survives_bonferroni"] = bool(z is not None and abs(z) >= z_bonf)
        if "brier" in r:
            pr = [f for f in forecasts if f[f"{r['strategy']}_p_home"] is not None]
            def _dz(s, sid=r["strategy"]):
                return brier(s, f"{sid}_p_home") - 0.25
            est, d, z = boot_z(pr, _dz)
            v["brier_diff"] = est
            v["brier_diff_boot_sd"] = d
            v["brier_diff_z"] = z
            v["brier_survives_bonferroni"] = bool(z is not None and abs(z) >= z_bonf)
        v["called_skillful"] = bool(v.get("margin_survives_bonferroni") or
                                   v.get("brier_survives_bonferroni"))
        v["bonferroni_alpha"] = alpha / n_tests
        verdicts.append(v)

    # ---- correlations that need no price ----------------------------------
    corr = []
    def add_corr(name, xs, ys, note):
        n = len(xs)
        if n < 4:
            corr.append({"name": name, "r": None, "n": n, "note": note})
            return
        mx, my = mean(xs), mean(ys)
        sx = math.sqrt(sum((a - mx) ** 2 for a in xs))
        sy = math.sqrt(sum((b - my) ** 2 for b in ys))
        if sx == 0 or sy == 0:
            corr.append({"name": name, "r": None, "n": n, "note": note})
            return
        rr = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (sx * sy)
        corr.append({"name": name, "r": rr, "n": n, "note": note,
                     "ci": cluster_bootstrap(list(zip(xs, ys)),
                                             lambda s: _pearson([p[0] for p in s], [p[1] for p in s]))})
    add_corr("home margin vs game total (row-level, same game)",
             [f["actual_margin"] for f in forecasts],
             [f["actual_total"] for f in forecasts],
             "the dependence a same-game parlay would have to model")
    add_corr("predicted margin (S2) vs actual margin",
             [f["S2_margin"] for f in forecasts],
             [f["actual_margin"] for f in forecasts],
             "the model's own discrimination, n = all forecast games")
    add_corr("predicted total (S2) vs actual total",
             [f["S2_total"] for f in forecasts],
             [f["actual_total"] for f in forecasts],
             "totals are much harder than sides and the number should be lower")
    add_corr("club points for vs points against (32 clubs, all games to date)",
             [sum(r["home_pts"] if r["home"] == c else r["away_pts"]
                  for r in games if c in (r["home"], r["away"])) for c in sorted({g["home"] for g in games})],
             [sum(r["away_pts"] if r["home"] == c else r["home_pts"]
                  for r in games if c in (r["home"], r["away"])) for c in sorted({g["home"] for g in games})],
             "positive r means good offences also concede more — pace, not collapse")

    # ---- week 11 prospective slate ---------------------------------------
    slate = load_slate()
    h = History()
    ms = MasseyState()
    clubs = sorted({g["home"] for g in games} | {g["away"] for g in games})
    for g in games:
        h.add(g)
        ms.add(g)
    sigma = h.margin_sigma()
    slate_rows = []
    for r in slate:
        away, home = r["away_abbr"], r["home_abbr"]
        out = {
            "game_date": r["game_date"], "kickoff_et": r["kickoff_et"],
            "away": away, "home": home, "neutral": r["neutral_site"],
            "source_url": r["source_url"], "accessed_utc": r["accessed_utc"],
            "label": "prospective", "market_spread": "", "market_total": "", "market_ml": "",
            "residual_spread": "", "residual_total": "",
        }
        for sid, key, _l, fn, _d in STRATEGIES:
            m, t = (s_massey(h, ms, home, away, clubs) if key == "massey"
                    else fn(h, home, away))
            out[f"{sid}_margin"] = "" if m is None else f"{m:.2f}"
            out[f"{sid}_total"] = "" if t is None else f"{t:.2f}"
            out[f"{sid}_p_home"] = "" if m is None else f"{phi(m / sigma):.4f}"
        slate_rows.append(out)
    # side first, total second, moneyline third — the published origination order (R003)
    slate_header = ["game_date", "kickoff_et", "away", "home", "neutral",
                    "S2_margin", "S2_total", "S2_p_home",
                    "S1_margin", "S1_total", "S1_p_home",
                    "S3_margin", "S3_total", "S3_p_home",
                    "S4_margin", "S4_total", "S4_p_home",
                    "market_spread", "market_total", "market_ml",
                    "residual_spread", "residual_total",
                    "sigma_used", "label", "source_url", "accessed_utc"]

    # ---- calibration and luck, per strategy ------------------------------
    calibr = {}
    luck = {}
    for sid, key, _l, _fn, _d in STRATEGIES:
        rows = [f for f in headline if f[f"{sid}_p_home"] is not None]
        calibr[sid] = calibration(rows, f"{sid}_p_home")
        luck[sid] = luck_panel(rows, f"{sid}_p_home")

    # ---- the same strategy in two regimes --------------------------------
    regimes = {sid: regime_split(headline, sid) for sid, *_ in STRATEGIES}

    # ---- two total estimators, published side by side (readiness R051) ---
    # A: own pace (S1/S3).  B: the two expected scores (S2/S4).  Neither is retired until one
    # beats the other out of sample, and the gap column is published with its interval.
    total_cmp = []
    for lo, hi, name in ((2, 10, "weeks 2-10, all games"), (2, 6, "weeks 2-6"), (7, 10, "weeks 7-10")):
        band = [f for f in headline if lo <= f["week"] <= hi]
        if not band:
            continue
        a = mean([abs(f["S1_total"] - f["actual_total"]) for f in band])
        b = mean([abs(f["S2_total"] - f["actual_total"]) for f in band])
        c = mean([abs(f["S4_total"] - f["actual_total"]) for f in band])
        def _pair(x, y):
            est, d, z = boot_z(band, lambda s: (mean([abs(f[y] - f["actual_total"]) for f in s])
                                                - mean([abs(f[x] - f["actual_total"]) for f in s])))
            return {"est": est, "boot_sd": d, "z": z,
                    "survives_bonferroni": bool(z is not None and abs(z) >= z_bonf)}
        total_cmp.append({
            "window": name, "n": len(band),
            "mae_a_pace": a, "mae_b_offence_only": b, "mae_c_pace_plus_hfa": c,
            "b_minus_a": _pair("S1_total", "S2_total"),
            "c_minus_a": _pair("S1_total", "S4_total"),
            "best": min((a, "A"), (b, "B"), (c, "C"))[1],
            "established": False,
        })

    out = {
        "meta": eval_summary,
        "calibration": calibr,
        "luck": luck,
        "regimes": regimes,
        "total_estimator_comparison": total_cmp,
        "strategies": [{"id": s[0], "key": s[1], "label": s[2], "description": s[4]} for s in STRATEGIES],
        "controls": [{"id": c[0], "key": c[1], "label": c[2], "description": c[3]} for c in CONTROLS],
        "evaluation": eval_rows,
        "verdicts": verdicts,
        "correlations": corr,
        "forecast_games": len(forecasts),
        "slate_week11": {k: v for k, v in zip(slate_header, [[r.get(c, "") for c in slate_header]
                                                             for r in slate_rows])} if False else slate_rows,
        "slate_header": slate_header,
        "sigma_week11": sigma,
        "forecast_sha256_of_inputs": hashlib.sha256(
            open(RESULTS, "rb").read()).hexdigest(),
    }
    return out, forecasts


def _pearson(xs, ys):
    mx, my = mean(xs), mean(ys)
    sx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    sy = math.sqrt(sum((b - my) ** 2 for b in ys))
    if not sx or not sy:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (sx * sy)


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------
def write(out, forecasts):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "evaluation.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=False, default=str)
        fh.write("\n")

    # per-game forecast ledger — the thing anyone can re-score without trusting this file
    keys = ["week", "date", "away", "home", "away_pts", "home_pts", "actual_margin",
            "actual_total", "burn_in", "sigma_used",
            "S1_margin", "S1_total", "S1_p_home",
            "S2_margin", "S2_total", "S2_p_home",
            "S3_margin", "S3_total", "S3_p_home",
            "S4_margin", "S4_total", "S4_p_home",
            "C1_p_home", "C2_p_home", "C3_margin", "C4_total", "source_url"]
    with open(os.path.join(OUT, "forecast_ledger.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for f in forecasts:
            w.writerow({k: f.get(k, "") for k in keys})

    # the week 11 slate: side, then total, then moneyline
    hdr = out["slate_header"]
    with open(os.path.join(OUT, "slate_week11_forecasts.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=hdr)
        w.writeheader()
        for r in out["slate_week11"]:
            r = dict(r)
            r["sigma_used"] = f"{out['sigma_week11']:.3f}"
            w.writerow({k: r.get(k, "") for k in hdr})

    # evaluation table
    cols = ["strategy", "kind", "label", "n_margin", "margin_mae", "margin_mae_ci",
            "margin_rmse", "margin_bias", "margin_dispersion", "dir_acc",
            "n_total", "total_mae", "total_mae_ci", "total_rmse", "total_bias",
            "n_win", "brier", "brier_ci", "logloss", "brier_skill_vs_coin"]
    with open(os.path.join(OUT, "evaluation.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols + ["dataset"])
        for r in out["evaluation"]:
            row = []
            for c in cols:
                v = r.get(c)
                if isinstance(v, tuple):
                    v = f"{v[0]:.4f} .. {v[1]:.4f}" if v[0] is not None else ""
                elif isinstance(v, float):
                    v = f"{v:.4f}"
                row.append("" if v is None else v)
            w.writerow(row + ["retrospective"])
    return OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if committed output differs")
    args = ap.parse_args()
    out, forecasts = build()
    if args.check:
        path = os.path.join(OUT, "evaluation.json")
        if not os.path.exists(path):
            print("compare: no committed evaluation.json", file=sys.stderr)
            return 1
        with open(path, encoding="utf-8") as fh:
            old = json.load(fh)
        # No clock value is written, so this is an exact comparison. JSON round-trip both sides
        # first so a tuple in memory and a list on disk compare equal.
        a = json.loads(json.dumps(old, default=str))
        b = json.loads(json.dumps(out, default=str))
        a["meta"].pop("built_utc", None); b["meta"].pop("built_utc", None)
        if a != b:
            print("compare: committed evaluation is stale — re-run scripts/build_compare.py",
                  file=sys.stderr)
            return 1
        print("compare: --check OK (evaluation reproduces)")
        return 0
    write(out, forecasts)
    print(f"compare: {out['meta']['games']} games, {out['meta']['comparisons']} comparisons, "
          f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
