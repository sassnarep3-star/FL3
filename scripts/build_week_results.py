#!/usr/bin/env python3
"""
Build the verified 2026 regular-season results corpus from official NFL.com pages.

Every row is transcribed from https://www.nfl.com/schedules/2026/by-week/week-N.
The point-by-point provenance (URL + read clock time) is stored per row, and the
whole file is hashed.

Why this file exists
--------------------
The board's own verification log reports 33 verified game rows against 137 through
its stated period, which means ROI, calibration and any proper-score leaderboard
cannot be computed at all. This module supplies the missing rows.

The check that makes it trustworthy
-----------------------------------
The standings page publishes, per club, wins, losses, ties, points-for and
points-against. If the game rows are transcribed correctly, then for every club:

    wins  = regular-season games won      (from the rows)
    pf    = sum of points scored          (from the rows)
    pa    = sum of points allowed         (from the rows)

Two independent official pages must agree exactly, club by club, with no fudge
factor. `verify_results()` enforces that identity and refuses to publish on a
mismatch. That is a much stronger test than counting rows: a single transposed
score breaks it.

Run:  python3 scripts/build_week_results.py
      python3 scripts/build_week_results.py --check
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RESULTS_CSV = os.path.join(DATA, "week_results_2026.csv")
STANDINGS_CSV = os.path.join(DATA, "standings_2026_wk10_verified.csv")
OUT_JSON = os.path.join(DATA, "week_results_2026.json")

SCHED = "https://www.nfl.com/schedules/2026/by-week/week-{w}"
STANDINGS = "https://www.nfl.com/standings/league/2026/reg"

# Read clock times (UTC) of each official page capture, per week.
READ_AT = {w: "2026-11-16T01:35Z" for w in range(1, 11)}
STANDINGS_READ_AT = "2026-11-16T01:36Z"

# ---------------------------------------------------------------------------
# Raw transcription. (week, date, weekday-as-published, away, away_pts, home,
# home_pts, note).  Away/home order and the weekday string are exactly as the
# official page renders them; where the page is internally inconsistent the
# note says so and the contradiction is published rather than "corrected".
# ---------------------------------------------------------------------------
GAMES: list[tuple] = [
    # ---- Week 1 -- https://www.nfl.com/schedules/2026/by-week/week-1
    (1, "2026-09-09", "Wednesday", "NE", 10, "SEA", 13,
     "Section header reads 'Sunday Night Football, September 9th'; the game line reads Wednesday, September 9th"),
    (1, "2026-09-10", "Thursday", "SF", 27, "LA", 7, "International Game, East Melbourne"),
    (1, "2026-09-13", "Sunday", "CHI", 59, "CAR", 37, ""),
    (1, "2026-09-13", "Sunday", "TB", 27, "CIN", 33, ""),
    (1, "2026-09-13", "Sunday", "NO", 30, "DET", 31, ""),
    (1, "2026-09-13", "Sunday", "BUF", 36, "HOU", 31, ""),
    (1, "2026-09-13", "Sunday", "BAL", 41, "IND", 23, ""),
    (1, "2026-09-13", "Sunday", "CLE", 10, "JAX", 34, ""),
    (1, "2026-09-13", "Sunday", "ATL", 13, "PIT", 20, ""),
    (1, "2026-09-13", "Sunday", "NYJ", 23, "TEN", 10, ""),
    (1, "2026-09-13", "Sunday", "AZ", 26, "LAC", 14, ""),
    (1, "2026-09-13", "Sunday", "MIA", 13, "LV", 27, ""),
    (1, "2026-09-13", "Sunday", "GB", 22, "MIN", 39, ""),
    (1, "2026-09-13", "Sunday", "WAS", 22, "PHI", 24, ""),
    (1, "2026-09-13", "Sunday", "DAL", 20, "NYG", 28, "Sunday Night Football"),
    (1, "2026-09-14", "Monday", "DEN", 10, "KC", 31, "Monday Night Football"),
    # ---- Week 2
    (2, "2026-09-17", "Thursday", "DET", 31, "BUF", 41, "Thursday Night Football"),
    (2, "2026-09-20", "Sunday", "CAR", 34, "ATL", 3, ""),
    (2, "2026-09-20", "Sunday", "NO", 24, "BAL", 17, ""),
    (2, "2026-09-20", "Sunday", "MIN", 9, "CHI", 3, ""),
    (2, "2026-09-20", "Sunday", "CIN", 20, "HOU", 6, ""),
    (2, "2026-09-20", "Sunday", "PIT", 3, "NE", 20, ""),
    (2, "2026-09-20", "Sunday", "GB", 20, "NYJ", 17, ""),
    (2, "2026-09-20", "Sunday", "CLE", 23, "TB", 19, ""),
    (2, "2026-09-20", "Sunday", "PHI", 24, "TEN", 20, ""),
    (2, "2026-09-20", "Sunday", "JAX", 13, "DEN", 20, ""),
    (2, "2026-09-20", "Sunday", "LV", 26, "LAC", 14, ""),
    (2, "2026-09-20", "Sunday", "SEA", 31, "AZ", 7, ""),
    (2, "2026-09-20", "Sunday", "WAS", 20, "DAL", 37, ""),
    (2, "2026-09-20", "Sunday", "MIA", 13, "SF", 35, ""),
    (2, "2026-09-20", "Sunday", "IND", 30, "KC", 33, "Sunday Night Football"),
    (2, "2026-09-21", "Monday", "NYG", 6, "LA", 28, "Monday Night Football"),
    # ---- Week 3
    (3, "2026-09-24", "Thursday", "ATL", 35, "GB", 14, "Thursday Night Football"),
    (3, "2026-09-27", "Sunday", "LAC", 16, "BUF", 24, ""),
    (3, "2026-09-27", "Sunday", "CAR", 18, "CLE", 21, ""),
    (3, "2026-09-27", "Sunday", "NYJ", 24, "DET", 31, ""),
    (3, "2026-09-27", "Sunday", "HOU", 17, "IND", 19, ""),
    (3, "2026-09-27", "Sunday", "NE", 6, "JAX", 35, ""),
    (3, "2026-09-27", "Sunday", "KC", 24, "MIA", 10, ""),
    (3, "2026-09-27", "Sunday", "TEN", 7, "NYG", 12, ""),
    (3, "2026-09-27", "Sunday", "CIN", 27, "PIT", 30, ""),
    (3, "2026-09-27", "Sunday", "SEA", 31, "WAS", 33, ""),
    (3, "2026-09-27", "Sunday", "AZ", 30, "SF", 36, ""),
    (3, "2026-09-27", "Sunday", "MIN", 23, "TB", 16, ""),
    (3, "2026-09-27", "Sunday", "LV", 35, "NO", 27, ""),
    (3, "2026-09-27", "Sunday", "BAL", 34, "DAL", 31, "International Game, Rio de Janeiro"),
    (3, "2026-09-27", "Sunday", "LA", 26, "DEN", 30, "Sunday Night Football"),
    (3, "2026-09-28", "Monday", "PHI", 7, "CHI", 27, "Monday Night Football"),
    # ---- Week 4
    (4, "2026-10-01", "Thursday", "PIT", 24, "CLE", 27, "Thursday Night Football"),
    (4, "2026-10-04", "Sunday", "IND", 30, "WAS", 13, "International Game, London"),
    (4, "2026-10-04", "Sunday", "TEN", 18, "BAL", 24, ""),
    (4, "2026-10-04", "Sunday", "NE", 29, "BUF", 26, ""),
    (4, "2026-10-04", "Sunday", "NYJ", 12, "CHI", 23, ""),
    (4, "2026-10-04", "Sunday", "JAX", 22, "CIN", 17, ""),
    (4, "2026-10-04", "Sunday", "DAL", 34, "HOU", 30, ""),
    (4, "2026-10-04", "Sunday", "AZ", 24, "NYG", 36, ""),
    (4, "2026-10-04", "Sunday", "LA", 24, "PHI", 20, ""),
    (4, "2026-10-04", "Sunday", "GB", 17, "TB", 14, ""),
    (4, "2026-10-04", "Sunday", "MIA", 10, "MIN", 15, ""),
    (4, "2026-10-04", "Sunday", "KC", 30, "LV", 27, ""),
    (4, "2026-10-04", "Sunday", "LAC", 23, "SEA", 30, ""),
    (4, "2026-10-04", "Sunday", "DEN", 14, "SF", 24, ""),
    (4, "2026-10-04", "Sunday", "DET", 26, "CAR", 32, "Sunday Night Football"),
    (4, "2026-10-05", "Monday", "ATL", 45, "NO", 24, "Monday Night Football"),
    # ---- Week 5
    (5, "2026-10-08", "Thursday", "TB", 24, "DAL", 16, "Thursday Night Football"),
    (5, "2026-10-11", "Sunday", "PHI", 17, "JAX", 19, "International Game, London"),
    (5, "2026-10-11", "Sunday", "CIN", 31, "MIA", 24, ""),
    (5, "2026-10-11", "Sunday", "LV", 17, "NE", 45, ""),
    (5, "2026-10-11", "Sunday", "MIN", 23, "NO", 13, ""),
    (5, "2026-10-11", "Sunday", "CLE", 12, "NYJ", 17, ""),
    (5, "2026-10-11", "Sunday", "IND", 22, "PIT", 34, ""),
    (5, "2026-10-11", "Sunday", "HOU", 26, "TEN", 3, ""),
    (5, "2026-10-11", "Sunday", "NYG", 27, "WAS", 27, "TIE"),
    (5, "2026-10-11", "Sunday", "CHI", 7, "GB", 31, ""),
    (5, "2026-10-11", "Sunday", "DEN", 23, "LAC", 17, ""),
    (5, "2026-10-11", "Sunday", "DET", 45, "AZ", 21, ""),
    (5, "2026-10-11", "Sunday", "SF", 32, "SEA", 29, ""),
    (5, "2026-10-11", "Sunday", "BAL", 30, "ATL", 23, "Sunday Night Football"),
    (5, "2026-10-12", "Monday", "BUF", 37, "LA", 34, "Monday Night Football"),
    # ---- Week 6
    (6, "2026-10-15", "Thursday", "SEA", 14, "DEN", 17, "Thursday Night Football"),
    (6, "2026-10-18", "Sunday", "HOU", 34, "JAX", 31, "International Game, London"),
    (6, "2026-10-18", "Sunday", "CHI", 31, "ATL", 23, ""),
    (6, "2026-10-18", "Sunday", "BAL", 10, "CLE", 13, ""),
    (6, "2026-10-18", "Sunday", "TEN", 26, "IND", 20, ""),
    (6, "2026-10-18", "Sunday", "NYJ", 19, "NE", 26, ""),
    (6, "2026-10-18", "Sunday", "NO", 34, "NYG", 27, ""),
    (6, "2026-10-18", "Sunday", "CAR", 25, "PHI", 14, ""),
    (6, "2026-10-18", "Sunday", "PIT", 26, "TB", 19, ""),
    (6, "2026-10-18", "Sunday", "AZ", 18, "LA", 16, ""),
    (6, "2026-10-18", "Sunday", "LAC", 6, "KC", 22, ""),
    (6, "2026-10-18", "Sunday", "BUF", 33, "LV", 30, ""),
    (6, "2026-10-18", "Sunday", "DAL", 13, "GB", 23, "Sunday Night Football"),
    (6, "2026-10-19", "Monday", "WAS", 17, "SF", 23, "Monday Night Football"),
    # ---- Week 7
    (7, "2026-10-22", "Thursday", "NE", 24, "CHI", 30, "Thursday Night Football"),
    (7, "2026-10-25", "Sunday", "PIT", 16, "NO", 10, "International Game, Saint-Denis"),
    (7, "2026-10-25", "Sunday", "SF", 20, "ATL", 29, ""),
    (7, "2026-10-25", "Sunday", "CIN", 35, "BAL", 13, ""),
    (7, "2026-10-25", "Sunday", "TB", 43, "CAR", 13, ""),
    (7, "2026-10-25", "Sunday", "NYG", 27, "HOU", 21, ""),
    (7, "2026-10-25", "Sunday", "IND", 10, "MIN", 16, ""),
    (7, "2026-10-25", "Sunday", "MIA", 28, "NYJ", 25, ""),
    (7, "2026-10-25", "Sunday", "CLE", 27, "TEN", 24, ""),
    (7, "2026-10-25", "Sunday", "DEN", 30, "AZ", 16, ""),
    (7, "2026-10-25", "Sunday", "GB", 17, "DET", 20, ""),
    (7, "2026-10-25", "Sunday", "LA", 35, "LV", 21, ""),
    (7, "2026-10-25", "Sunday", "KC", 3, "SEA", 20, "Sunday Night Football"),
    (7, "2026-10-26", "Monday", "DAL", 38, "PHI", 21, "Monday Night Football"),
    # ---- Week 8
    (8, "2026-10-29", "Thursday", "CAR", 19, "GB", 27, "Thursday Night Football"),
    (8, "2026-11-01", "Sunday", "BAL", 10, "BUF", 36, ""),
    (8, "2026-11-01", "Sunday", "TEN", 36, "CIN", 43, ""),
    (8, "2026-11-01", "Sunday", "AZ", 33, "DAL", 30, ""),
    (8, "2026-11-01", "Sunday", "MIN", 15, "DET", 19, ""),
    (8, "2026-11-01", "Sunday", "IND", 7, "JAX", 42, ""),
    (8, "2026-11-01", "Sunday", "LV", 38, "NYJ", 33, ""),
    (8, "2026-11-01", "Sunday", "CLE", 6, "PIT", 27, ""),
    (8, "2026-11-01", "Sunday", "ATL", 0, "TB", 16, ""),
    (8, "2026-11-01", "Sunday", "LAC", 9, "LA", 24, ""),
    (8, "2026-11-01", "Sunday", "KC", 24, "DEN", 28, ""),
    (8, "2026-11-01", "Sunday", "NE", 24, "MIA", 19, ""),
    (8, "2026-11-01", "Sunday", "PHI", 10, "WAS", 27, "Sunday Night Football"),
    (8, "2026-11-02", "Monday", "CHI", 34, "SEA", 17, "Monday Night Football"),
    # ---- Week 9
    (9, "2026-11-05", "Thursday", "JAX", 33, "BAL", 10, "Thursday Night Football"),
    (9, "2026-11-08", "Sunday", "CIN", 34, "ATL", 17, "International Game, Madrid"),
    (9, "2026-11-08", "Sunday", "DEN", 26, "CAR", 21, ""),
    (9, "2026-11-08", "Sunday", "DAL", 27, "IND", 23, ""),
    (9, "2026-11-08", "Sunday", "NYJ", 12, "KC", 35, ""),
    (9, "2026-11-08", "Sunday", "DET", 19, "MIA", 9, ""),
    (9, "2026-11-08", "Sunday", "CLE", 22, "NO", 23, ""),
    (9, "2026-11-08", "Sunday", "NYG", 19, "PHI", 11, ""),
    (9, "2026-11-08", "Sunday", "LA", 20, "WAS", 13, ""),
    (9, "2026-11-08", "Sunday", "HOU", 44, "LAC", 22, ""),
    (9, "2026-11-08", "Sunday", "LV", 17, "SF", 38, ""),
    (9, "2026-11-08", "Sunday", "GB", 45, "NE", 27, ""),
    (9, "2026-11-08", "Sunday", "AZ", 3, "SEA", 17, ""),
    (9, "2026-11-08", "Sunday", "TB", 24, "CHI", 27, "Sunday Night Football"),
    (9, "2026-11-09", "Monday", "BUF", 23, "MIN", 6, "Monday Night Football"),
    # ---- Week 10 -- 12 of 14 FINAL at read time. Two are deliberately NOT in the
    # corpus: PIT at CIN was rendering as "Live Q1 0-0" and LAC at BAL had not
    # kicked off (Mon Nov 16, 8:15 PM ET). A live or unplayed game is not a result.
    (10, "2026-11-12", "Thursday", "WAS", 24, "NYG", 21, "Thursday Night Football"),
    (10, "2026-11-15", "Sunday", "NE", 10, "DET", 35, "International Game, Munich"),
    (10, "2026-11-15", "Sunday", "KC", 35, "ATL", 13, ""),
    (10, "2026-11-15", "Sunday", "HOU", 24, "CLE", 27, ""),
    (10, "2026-11-15", "Sunday", "MIN", 30, "GB", 10, ""),
    (10, "2026-11-15", "Sunday", "MIA", 22, "IND", 24, ""),
    (10, "2026-11-15", "Sunday", "CAR", 20, "NO", 17, ""),
    (10, "2026-11-15", "Sunday", "BUF", 31, "NYJ", 12, ""),
    (10, "2026-11-15", "Sunday", "JAX", 40, "TEN", 23, ""),
    (10, "2026-11-15", "Sunday", "LA", 34, "AZ", 6, ""),
    (10, "2026-11-15", "Sunday", "SEA", 21, "LV", 13, ""),
    (10, "2026-11-15", "Sunday", "SF", 46, "DAL", 40, ""),
]


def load_games() -> list[dict]:
    """Return GAMES with seed identity fields, plus any rows stored in the CSV."""
    out = []
    for w, d, wd, away, ap, home, hp, note in GAMES:
        out.append(dict(
            week=w, game_date=d, weekday_as_published=wd,
            away_abbr=away, away_pts=ap, home_abbr=home, home_pts=hp,
            neutral_site_note=note, source_url=SCHED.format(w=w),
            accessed_utc=READ_AT[w],
        ))
    return out


def load_standings() -> dict[str, dict]:
    with open(STANDINGS_CSV, encoding="utf-8") as fh:
        return {r["team"]: r for r in csv.DictReader(fh)}


def verify_results(rows: list[dict], standings: dict[str, dict]) -> list[str]:
    """The strong cross-check: two official pages must agree club by club."""
    errors = []
    agg: dict[str, dict] = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "gp": 0})
    for r in rows:
        a, h = r["away_abbr"], r["home_abbr"]
        ap, hp = int(r["away_pts"]), int(r["home_pts"])
        for t, pf, pa in ((a, ap, hp), (h, hp, ap)):
            agg[t]["pf"] += pf
            agg[t]["pa"] += pa
            agg[t]["gp"] += 1
        if ap > hp:
            agg[a]["w"] += 1
            agg[h]["l"] += 1
        elif hp > ap:
            agg[h]["w"] += 1
            agg[a]["l"] += 1
        else:
            agg[a]["t"] += 1
            agg[h]["t"] += 1

    if set(agg) != set(standings):
        errors.append(f"club sets differ: only-in-results {sorted(set(agg) - set(standings))}, "
                      f"only-in-standings {sorted(set(standings) - set(agg))}")
        return errors

    for t in sorted(standings):
        s, o = standings[t], agg[t]
        for field, key in (("w", "w"), ("l", "l"), ("t", "t"), ("pf", "pf"), ("pa", "pa")):
            sv, ov = int(s[field]), o[key]
            if sv != ov:
                errors.append(f"{t}: standings {field}={sv} but results sum to {ov}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, do not write")
    args = ap.parse_args()

    rows = load_games()
    standings = load_standings()
    errors = verify_results(rows, standings)

    weeks = sorted({r["week"] for r in rows})
    teams = sorted({r["away_abbr"] for r in rows} | {r["home_abbr"] for r in rows})
    print(f"games={len(rows)} team-games={2*len(rows)} weeks={weeks} clubs={len(teams)}")

    if errors:
        print(f"\nIDENTITY CHECK FAILED — {len(errors)} mismatch(es):", file=sys.stderr)
        for e in errors[:40]:
            print("  " + e, file=sys.stderr)
        return 1
    print("IDENTITY CHECK PASSED — every club's W/L/T, PF and PA match the standings page exactly")

    if args.check:
        return 0

    if not args.check:
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        raw = open(RESULTS_CSV, "rb").read()
        payload = {
            "meta": {
                "title": "2026 NFL regular-season results corpus, verified",
                "games": len(rows),
                "weeks": weeks,
                "clubs": len(teams),
                "source_primary": STANDINGS,
                "source_rows": SCHED.format(w="N"),
                "standings_read_utc": STANDINGS_READ_AT,
                "identity_check": "passed: per-club W/L/T, PF and PA agree exactly with the standings page",
                "csv_sha256": hashlib.sha256(raw).hexdigest(),
                "policy": "A result row is only included when the official schedule page renders it as FINAL. "
                          "No score is inferred, and no row is added from memory.",
            },
            "games": rows,
        }
        with open(OUT_JSON, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
        print(f"wrote {RESULTS_CSV}")
        print(f"wrote {OUT_JSON}  (sha256 {payload['meta']['csv_sha256'][:16]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
