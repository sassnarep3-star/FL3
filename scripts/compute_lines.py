#!/usr/bin/env python3
"""
FL3 — line origination engine (v0)

Purpose
-------
Originate our own NFL lines from data we have actually verified against
official NFL.com sources, instead of importing somebody else's number.

Hard rules baked into this file
-------------------------------
1. Every input is either (a) a figure captured from an official NFL.com page and
   stored in data/*.json with its `src`, or (b) a *transparent* model constant
   declared below. Nothing is copied from a sportsbook and nothing is invented
   per-team.
2. Uncertainty is part of the output. Every line ships with a sigma, a 50% band
   and a 90% band. A point estimate without a band is a bug.
3. The injury/availability adjustment is capped and expressed as a *loss of
   team quality per unavailable projected contributor*, not as a guess about a
   specific replacement player. This is a deliberate limitation (see flag F05):
   we cannot verify depth-chart ordinal from an official source.
4. The script is deterministic (fixed seed). Re-running it must reproduce
   data/lines_week10.json byte-for-byte (modulo the generated timestamp).

Outputs
-------
data/lines_week10.json  — our originated spread / total / win probability per game
data/team_power.json    — the iterative power ratings the lines are built on
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------------------
# Model constants — declared, not tuned to any market. Changing one requires a
# new version string and a re-run of the validation gates.
# ---------------------------------------------------------------------------
MODEL = {
    "version": "v0.1.0",
    "seed": 20261114,
    # Expected points per game across the league. Used only as the centre of the
    # total, never to override team-level offence/defence.
    "league_points_per_team": 22.0,
    # Home-field advantage in points, applied on the spread only.
    "hfa_points": 1.9,
    # Prior strength (games of evidence) pulling a club toward .500 before the
    # season data speaks. With 8-9 games played this is intentionally small.
    "prior_games": 2.0,
    # Points of team quality removed per unavailable player, by projected role.
    # These are conservative and are NOT depth-chart facts (see flag F05).
    "availability_penalty": {
        "QB": 2.60,
        "WR": 0.55,
        "RB": 0.45,
        "TE": 0.35,
        "T": 0.45,
        "G": 0.35,
        "C": 0.40,
        "DE": 0.45,
        "DT": 0.40,
        "LB": 0.40,
        "CB": 0.50,
        "S": 0.45,
        "K": 0.80,
        "P": 0.35,
        "LS": 0.15,
        "FB": 0.10,
    },
    # Which side of the ball a position sits on. This matters: a missing
    # offensive player LOWERS that club's expected points, while a missing
    # defensive player RAISES the opponent's expected points. Getting this
    # wrong would push every total in the same direction as the injury list.
    "off_positions": ["QB", "WR", "RB", "TE", "T", "G", "C", "FB"],
    "def_positions": ["DE", "DT", "LB", "CB", "S"],
    "st_positions": ["K", "P", "LS"],
    # Separate caps so one very long injury list cannot swamp the ratings.
    "cap_off": 3.5,
    "cap_def": 3.0,
    "cap_st": 1.0,
    # Share of the penalty actually applied. "Out" is full, "Doubtful" is a
    # fraction (the player usually does not play), "Questionable" a smaller
    # fraction. This is the only place where probability-of-absence enters.
    "status_weight": {"Out": 1.00, "Doubtful": 0.60, "Questionable": 0.25, "": 0.0},
    # Game-to-game noise in a single team's score (points). This is the floor of
    # the uncertainty; estimation error grows on top of it when few games exist.
    "single_game_sigma": 8.5,
    # Estimation-error constant: sigma grows as sqrt(1 + k/games_played).
    # With k=8 a club at 8-9 games carries ~37% extra width from estimation.
    "sigma_k": 8.0,
    # Total sigma: pace and turnovers swing totals somewhat independently of the
    # margin, but both are built from the same two scoring distributions, so the
    # total band is narrower than 2x the single-game sigma.
    "total_sigma": 11.5,
    # Weight of special-teams/one-score luck. The engine reports it so the
    # leaderboard can strip it out (see strategies: LUCK-FILTER).
    "one_score_margin": 8,
}

SRC_STAND = "https://www.nfl.com/standings/division/2026/REG"
SRC_INJ = "https://www.nfl.com/injuries/"
SRC_SCHED = "https://www.nfl.com/schedules/2026/REG/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def norm_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def band(center: float, sigma: float, pct: float) -> tuple[float, float]:
    """Symmetric probability band around a point estimate."""
    z = {0.50: 0.6745, 0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600}[pct]
    return round(center - z * sigma, 1), round(center + z * sigma, 1)


def load(name: str) -> dict:
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 1. Power ratings from verified season aggregates
# ---------------------------------------------------------------------------
def build_power(standings: dict) -> dict:
    """Iterative opponent-adjusted rating on points scored / allowed per game.

    We only have league-wide PF/PA (not per-opponent splits), so this is a
    *schedule-strength-free* rating: offence and defence per game, centred on
    the league mean, shrunk toward .500-quality by `prior_games`.
    The rating is in points: expected margin vs. an average team on a neutral
    field.
    """
    teams = standings["teams"]
    gp = {t["abbr"]: t["w"] + t["l"] + t["t"] for t in teams}
    off = {t["abbr"]: t["pf"] / max(gp[t["abbr"]], 1) for t in teams}
    dfn = {t["abbr"]: t["pa"] / max(gp[t["abbr"]], 1) for t in teams}
    league_off = sum(off.values()) / len(off)
    league_dfn = sum(dfn.values()) / len(dfn)

    power = {}
    for t in teams:
        a = t["abbr"]
        g = max(gp[a], 1)
        # shrink toward league average with a prior worth `prior_games` games
        w = g / (g + MODEL["prior_games"])
        o = w * off[a] + (1 - w) * league_off
        d = w * dfn[a] + (1 - w) * league_dfn
        rating = (o - league_off) - (d - league_dfn)
        power[a] = {
            "gp": g,
            "off_ppg": round(off[a], 2),
            "def_ppg": round(dfn[a], 2),
            "off_shrunk": round(o, 2),
            "def_shrunk": round(d, 2),
            "rating": round(rating, 2),
            "win_pct": t["pct"],
            "pf": t["pf"],
            "pa": t["pa"],
            "src": SRC_STAND,
        }
    return {
        "model_version": MODEL["version"],
        "league_off_ppg": round(league_off, 2),
        "league_def_ppg": round(league_dfn, 2),
        "note": "Rating = (shrunk offence − league offence) − (shrunk defence − league defence), in points per game. No opponent adjustment is possible from league aggregates; that is a stated limitation.",
        "teams": dict(sorted(power.items())),
        "src": SRC_STAND,
    }


# ---------------------------------------------------------------------------
# 2. Availability adjustment from the official injury report
# ---------------------------------------------------------------------------
def unit_side(pos: str) -> str:
    if pos in MODEL["off_positions"]:
        return "off"
    if pos in MODEL["def_positions"]:
        return "def"
    if pos in MODEL["st_positions"]:
        return "st"
    return "off"  # unknown positions are treated as offensive depth and logged


def availability(injuries: dict) -> dict:
    """Per-club availability split into offence / defence / special teams.

    Only players with a game status (Out / Doubtful / Questionable) count.
    Practice-only listings are deliberately excluded: NFL.com prints them with
    a blank game status, so we cannot say whether the player will play.
    """
    out = {}
    for game in injuries["games"]:
        for team in game["teams"]:
            abbr = team["abbr"]
            buckets = {"off": 0.0, "def": 0.0, "st": 0.0}
            drivers = []
            unknown_pos = set()
            for p in team["players"]:
                pos = p["pos"]
                status = p["game_status"]
                sw = MODEL["status_weight"].get(status, 0.0)
                if sw == 0.0:
                    continue
                if pos not in MODEL["availability_penalty"]:
                    unknown_pos.add(pos)
                unit = MODEL["availability_penalty"].get(pos, 0.30)
                side = unit_side(pos)
                contrib = unit * sw
                buckets[side] += contrib
                drivers.append(
                    {
                        "name": p["name"],
                        "pos": pos,
                        "side": side,
                        "injury": p["injury"],
                        "status": status,
                        "penalty": round(contrib, 2),
                    }
                )
            capped = {
                "off": round(min(buckets["off"], MODEL["cap_off"]), 2),
                "def": round(min(buckets["def"], MODEL["cap_def"]), 2),
                "st": round(min(buckets["st"], MODEL["cap_st"]), 2),
            }
            out[abbr] = {
                "abbr": abbr,
                "raw": {k: round(v, 2) for k, v in buckets.items()},
                "capped": capped,
                "any_capped": any(
                    buckets[k] > capped[k] for k in ("off", "def", "st")
                ),
                "unknown_positions": sorted(unknown_pos),
                "n_out": sum(1 for d in drivers if d["status"] == "Out"),
                "n_doubtful": sum(1 for d in drivers if d["status"] == "Doubtful"),
                "n_questionable": sum(1 for d in drivers if d["status"] == "Questionable"),
                "drivers": sorted(drivers, key=lambda d: -d["penalty"]),
                "src": SRC_INJ,
            }
    return out


# ---------------------------------------------------------------------------
# 3. Lines per game
# ---------------------------------------------------------------------------
def build_lines(standings: dict, injuries: dict, power: dict) -> dict:
    avail = availability(injuries)
    games_out = []

    for game in injuries["games"]:
        a, h = game["away"], game["home"]
        pa_ = power["teams"].get(a)
        ph_ = power["teams"].get(h)
        av_a = avail.get(a, {"capped": {"off": 0.0, "def": 0.0, "st": 0.0}, "drivers": [], "src": SRC_INJ})
        av_h = avail.get(h, {"capped": {"off": 0.0, "def": 0.0, "st": 0.0}, "drivers": [], "src": SRC_INJ})

        if not pa_ or not ph_:
            games_out.append(
                {
                    "game_id": game["game_id"],
                    "away": a,
                    "home": h,
                    "status": "NO LINE — missing verified rating input",
                    "src": SRC_STAND,
                }
            )
            continue

        # ---- Expected scoring for each club, from the same shrunk stats ----
        # Away club:    its offence vs the home club's defence
        # Home club:    its offence vs the away club's defence
        exp_away = (pa_["off_shrunk"] + ph_["def_shrunk"]) / 2.0
        exp_home = (ph_["off_shrunk"] + pa_["def_shrunk"]) / 2.0
        # Availability, applied to the correct side of the ball:
        #   missed offensive players lower the club's own expected points;
        #   missed defensive players raise the opponent's expected points;
        #   missed specialists move both club's totals slightly.
        exp_away -= av_a["capped"]["off"]
        exp_away += av_h["capped"]["def"]
        exp_home -= av_h["capped"]["off"]
        exp_home += av_a["capped"]["def"]
        exp_away -= av_a["capped"]["st"] / 2.0
        exp_home -= av_h["capped"]["st"] / 2.0
        # Home-field advantage is applied as points to the home club's score.
        exp_home += MODEL["hfa_points"]

        total = exp_away + exp_home
        margin = exp_home - exp_away  # positive => home club favoured

        # Uncertainty: floor from single-game variance, widened when a club has
        # played few games (less evidence about its true quality).
        est = math.sqrt(1.0 + MODEL["sigma_k"] / max(min(pa_["gp"], ph_["gp"]), 1))
        sigma_spread = MODEL["single_game_sigma"] * est
        sigma_total = MODEL["total_sigma"] * est

        home_wp = norm_cdf(margin, 0.0, sigma_spread)
        s50 = band(margin, sigma_spread, 0.50)
        s90 = band(margin, sigma_spread, 0.90)
        t50 = band(total, sigma_total, 0.50)
        t90 = band(total, sigma_total, 0.90)

        games_out.append(
            {
                "game_id": game["game_id"],
                "away": a,
                "home": h,
                "kickoff": game["status_line"],
                "status": "LINE ORIGINATED",
                "inputs": {
                    "away_rating": pa_["rating"],
                    "home_rating": ph_["rating"],
                    "away_gp": pa_["gp"],
                    "home_gp": ph_["gp"],
                    "hfa": MODEL["hfa_points"],
                    "away_availability": av_a["capped"],
                    "home_availability": av_h["capped"],
                    "exp_away_points": round(exp_away, 1),
                    "exp_home_points": round(exp_home, 1),
                    "away_src": pa_["src"],
                    "home_src": ph_["src"],
                    "injury_src": av_a["src"],
                },
                "line": {
                    "home_spread": round(-margin, 1),
                    "away_spread": round(margin, 1),
                    "spread_point_estimate_home": round(margin, 2),
                    "spread_sigma": round(sigma_spread, 2),
                    "spread_band_50": s50,
                    "spread_band_90": s90,
                    "total_point_estimate": round(total, 1),
                    "total_sigma": round(sigma_total, 2),
                    "total_band_50": t50,
                    "total_band_90": t90,
                    "home_win_prob": round(home_wp, 4),
                    "away_win_prob": round(1 - home_wp, 4),
                    "pick_confidence": round(abs(home_wp - 0.5) * 2, 4),
                },
                "publication_state": {
                    "line_source": "originated by this model",
                    "market_comparison": "unavailable — no licensed official odds feed (flag F07)",
                    "bet_recommendation": "none — this is an input to the scoring gates, not a tip",
                },
                "src": SRC_STAND,
                "src_injuries": SRC_INJ,
                "src_schedule": SRC_SCHED,
            }
        )

    return {
        "meta": {
            "title": "Week 10, 2026 — originated lines (model v0)",
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model": MODEL,
            "inputs": {
                "standings": {"src": SRC_STAND, "captured": standings["meta"]["captured_utc"]},
                "injuries": {"src": SRC_INJ, "captured": injuries["meta"]["captured_utc"]},
                "schedule": {"src": SRC_SCHED, "captured": "2026-11-14"},
            },
            "what_this_is": "Our own point estimates with explicit uncertainty. Not a sportsbook quote and not betting advice.",
            "what_this_is_not": [
                "not compared to a market price (no licensed feed)",
                "not backtested yet (no historical week snapshots captured)",
                "not adjusted for depth-chart ordinal (unverifiable officially)",
            ],
        },
        "games": games_out,
    }


def main() -> None:
    standings = load("standings.json")
    injuries = load("injuries_week10.json")
    power = build_power(standings)
    lines = build_lines(standings, injuries, power)

    with open(os.path.join(DATA, "team_power.json"), "w", encoding="utf-8") as fh:
        json.dump(power, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(DATA, "lines_week10.json"), "w", encoding="utf-8") as fh:
        json.dump(lines, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"power ratings: {len(power['teams'])} clubs")
    print(f"lines: {len(lines['games'])} games")
    for g in lines["games"][:3]:
        ln = g["line"]
        print(
            f"  {g['away']} @ {g['home']}: {g['home']} {ln['home_spread']:+.1f}"
            f" | total {ln['total_point_estimate']} | home WP {ln['home_win_prob']:.1%}"
        )


if __name__ == "__main__":
    main()
