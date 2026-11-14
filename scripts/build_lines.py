"""Generate ORIGINAL lines from verified data only.

Everything here is derived from data/standings_verified.json (S01) plus, optionally, the
lineup-risk exposure score. No sportsbook number is read, stored or copied.

What is deliberately NOT done:
  * no home-field constant is invented - the repo has no split data to calibrate one
  * no injury adjustment is invented - there is no verified relationship in hand
  * no market comparison - there is no verified odds feed in this environment
Each of those omissions is surfaced on the site rather than papered over.
"""
import json
import math

lg = json.load(open("data/standings_verified.json"))
risk = {t["team"]: t for t in json.load(open("data/lineup_risk.json"))["teams"]}
sched = json.load(open("data/schedule_2026_w10.json"))["games"]

games_played = lambda t: t["w"] + t["l"] + t["t"]

def league_baseline(teams):
    """League points per TEAM-GAME, computed from the data itself.

    sum(PF) == sum(PA) == total points scored, and sum(PF)/sum(games) is the mean
    points one team scores in one game - i.e. half of the game total. Using
    (sum PF + sum PA) / sum(games) would double-count and return ~2x the true mean.
    """
    total_points = sum(t["pf"] for t in teams)
    team_games = sum(games_played(t) for t in teams)
    return total_points / team_games

teams = lg["meta"]["teams"]
BASE = league_baseline(teams)
assert 18.0 < BASE < 28.0, "league baseline out of plausible range: %r" % BASE

def shrunken_off_def(team, k=4.0):
    """Regress team scoring/allowance toward the league mean. k = games of prior weight.

    k=4 follows the standard 'regress ~half way at a quarter season' rule of thumb and is
    stated here so it can be challenged. It is a modelling choice, not a sourced fact.
    """
    g = max(games_played(team), 1)
    off_raw = team["pf"] / g
    def_raw = team["pa"] / g
    w = g / (g + k)
    off = w * off_raw + (1 - w) * BASE
    dfn = w * def_raw + (1 - w) * BASE
    return off, dfn

model = {}
for t in teams:
    off, dfn = shrunken_off_def(t)
    model[t["team"]] = {"off": round(off, 2), "def": round(dfn, 2),
                        "off_raw": round(t["pf"] / max(games_played(t), 1), 2),
                        "def_raw": round(t["pa"] / max(games_played(t), 1), 2),
                        "games": games_played(t)}

lines = []
for g in sched:
    if g["status"] == "FINAL":
        continue
    a, h = g["away"], g["home"]
    A, H = model[a], model[h]
    # Expected points, additive form (standard, and it reproduces the league mean exactly):
    #   team_expected = league_mean + (own_off - league_mean) + (opp_def - league_mean)
    # off and def are already on a per-team-game scale centred on BASE, so the
    # deviation form is: exp = BASE + (own_off - BASE) + (opp_def - BASE).
    exp_a = BASE + (A["off"] - BASE) + (H["def"] - BASE)
    exp_h = BASE + (H["off"] - BASE) + (A["def"] - BASE)
    # neutral site (no calibrated HFA available -> no adjustment, and say so)
    hfa_applied = 0.0
    # Round the published components FIRST, then derive the line and total from the
    # published values. Otherwise the displayed numbers do not add up and a reader
    # who checks the arithmetic finds a defect rather than a model.
    exp_a = round(exp_a, 1)
    exp_h = round(exp_h + hfa_applied, 1)
    line_home = round(exp_h - exp_a, 1)          # home team favoured by +x
    total = round(exp_a + exp_h, 1)
    lines.append({
        "away": a, "home": h, "date": g["date"], "kickoff_et": g["kickoff_et"],
        "neutral_site": g["neutral_site"], "designation": g["designation"],
        "model_home_line": -line_home,       # negative = home favoured (standard notation)
        "model_total": total,
        "exp_away_points": exp_a,
        "exp_home_points": exp_h,
        "hfa_applied": hfa_applied,
        "inputs": {
            "away": {"off": A["off"], "def": A["def"], "games": A["games"], "raw_off": A["off_raw"], "raw_def": A["def_raw"]},
            "home": {"off": H["off"], "def": H["def"], "games": H["games"], "raw_off": H["off_raw"], "raw_def": H["def_raw"]},
        },
        "lineup_risk": {"away": risk.get(a, {}).get("replacement_risk_index"),
                        "home": risk.get(h, {}).get("replacement_risk_index")},
        "injury_adjustment_applied": 0.0,
        "src": "S01",
    })

lines.sort(key=lambda x: -abs(x["model_home_line"]))

doc = {
 "meta": {
   "title": "Original model lines - 2026 Week 10 (13 unplayed games)",
   "as_of": "2026-11-14",
   "purpose": "Line ORIGINATION. These numbers are produced from the published 2026 season results and nothing else.",
   "inputs": {
     "league_points_per_team_game": round(BASE, 3),
     "shrinkage_prior_games_k": 4.0,
     "home_field_advantage": 0.0,
     "injury_adjustment": 0.0
   },
   "formula": {
     "off": "w * (PF/G) + (1-w) * league_mean, w = G/(G+k)",
     "def": "w * (PA/G) + (1-w) * league_mean",
     "expected_points": "league_mean + (own_off - league_mean) + (opp_def - league_mean)",
     "model_home_line": "-(exp_home - exp_away)",
     "model_total": "exp_away + exp_home"
   },
   "gaps_that_make_these_not_bettable_yet": [
     "Home-field advantage is set to 0.0 because the repo contains no home/road scoring split to calibrate it. The nfl.com standings page does publish home and road W-L records; it does not publish home and road points. Filling 2.5 points in from memory would be a hallucination, so the field is 0.0 and flagged F-04.",
     "No injury adjustment is applied. The lineup-risk index exists but has never been validated against outcomes, so applying it here would be an unbacked assumption. Flagged F-05.",
     "No bye-week adjustment: the model ignores rest differential.",
     "No HFA means every modelled line is compressed toward pick'em; expect the market to sit closer to the home side on most games.",
     "No quarterback-specific term: the data set identifies starters but carries no per-QB performance data.",
     "Shrinkage k=4.0 is a modelling convention, not a sourced fact. It is a documented parameter so a reviewer can change it and re-run."
   ],
   "sources": ["S01", "S02", "S03", "S04"]
 },
 "games": lines,
 "all_models": model
}
json.dump(doc, open("data/lines.json", "w"), indent=1)
print("league baseline pts/team-game:", round(BASE, 3))
print("games modelled:", len(lines))
for l in lines[:6]:
    print("  %s @ %s  home %+.1f  total %.1f" % (l["away"], l["home"], l["model_home_line"], l["model_total"]))
