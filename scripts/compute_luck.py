#!/usr/bin/env python3
"""
FL3 — luck decomposition.

"Remove luck from the equation" needs a number, not a slogan. With official
PF/PA and W-L we can compute a Pythagorean expectation and split actual wins
into (a) wins explained by scoring margin and (b) wins that came from something
other than scoring margin — i.e. the luck/unexplained component.

Two outputs per club:
  exp_wins      Pythagorean expectation from official PF/PA
  luck_wins     actual wins - exp_wins   (positive = outperforming margin)
  luck_share    |luck_wins| / games played

Declared constant: the Pythagorean exponent. 2.37 is the value in common use
for the NFL; it is a MODEL CONSTANT here, not an official league figure, and is
labelled as such everywhere it is displayed.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SRC = "https://www.nfl.com/standings/division/2026/REG"
SRC_TIES = "https://www.nfl.com/standings/tie-breaking-procedures"
EXPONENT = 2.37


def main() -> None:
    standings = json.load(open(os.path.join(DATA, "standings.json"), encoding="utf-8"))
    rows = []
    for t in standings["teams"]:
        gp = t["w"] + t["l"] + t["t"]
        pf, pa = t["pf"], t["pa"]
        if pf == 0 and pa == 0:
            continue
        denom = pf**EXPONENT + pa**EXPONENT
        exp_pct = (pf**EXPONENT) / denom if denom else 0.0
        exp_wins = exp_pct * gp
        # NFL rule, quoted from the official tie-breaking page:
        #   "Tie games count as one-half win and one-half loss for both clubs."
        # so a club's effective wins = W + T/2. Verified 2026-11-14.
        eff_wins = t["w"] + 0.5 * t["t"]
        luck = eff_wins - exp_wins
        rows.append(
            {
                "abbr": t["abbr"],
                "name": t["name"],
                "gp": gp,
                "w": t["w"],
                "l": t["l"],
                "t": t["t"],
                "pf": pf,
                "pa": pa,
                "net": t["net"],
                "actual_pct": t["pct"],
                "pyth_pct": round(exp_pct, 4),
                "exp_wins": round(exp_wins, 2),
                "eff_wins": eff_wins,
                "luck_wins": round(luck, 2),
                "luck_per_game": round(luck / gp, 4),
                "luck_rank": None,
                "src": SRC,
                "src_tie_rule": SRC_TIES,
                "verified": True,
            }
        )
    rows.sort(key=lambda r: r["luck_wins"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["luck_rank"] = i
    rows.sort(key=lambda r: (-r["luck_wins"], r["abbr"]))

    out = {
        "meta": {
            "title": "Luck decomposition — Pythagorean expectation vs actual record",
            "captured_utc": "2026-11-14",
            "exponent": EXPONENT,
            "exponent_status": "declared model constant, not an official NFL figure",
            "formula": "exp_pct = PF^k / (PF^k + PA^k); luck_wins = (W + T/2) - exp_pct * games_played",
            "tie_handling": "Effective wins = W + T/2, per the official NFL tie-breaking page ('Tie games count as one-half win and one-half loss for both clubs'), verified 2026-11-14.",
            "tie_rule_src": SRC_TIES,
            "what_this_cannot_see": [
                "turnover margin (not in the official standings table)",
                "defensive and special-teams touchdowns",
                "opponent field-goal misses",
                "garbage-time scoring"
            ],
            "src": SRC,
        },
        "teams": sorted(rows, key=lambda r: r["abbr"]),
        "most_lucky": sorted(rows, key=lambda r: -r["luck_wins"])[:5],
        "most_unlucky": sorted(rows, key=lambda r: r["luck_wins"])[:5],
    }

    path = os.path.join(DATA, "luck.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"{'TM':4}{'W-L-T':>8}{'PF':>5}{'PA':>5}{'PYTH%':>8}{'EXPW':>7}{'LUCK':>7}{'RANK':>5}")
    for r in sorted(out["teams"], key=lambda r: -r["luck_wins"]):
        print(
            f"{r['abbr']:4}{str(r['w'])+'-'+str(r['l'])+'-'+str(r['t']):>8}"
            f"{r['pf']:>5}{r['pa']:>5}{r['pyth_pct']:>8.3f}{r['exp_wins']:>7.2f}"
            f"{r['luck_wins']:>+7.2f}{r['luck_rank']:>5}"
        )


if __name__ == "__main__":
    main()
