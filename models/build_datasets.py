#!/usr/bin/env python3
"""build_datasets.py — FL3 data pipeline (2026 NFL season).

Every value below was transcribed from the official/trusted source cited in the
row (NFL.com scores/standings/injuries pages, ESPN API/depth charts, etc.).
This script emits the JSON datasets consumed by the site AND self-verifies the
scores against the official NFL.com standings table (W-L-T and PF/PA must
match exactly). Any mismatch is printed as a VERIFICATION FAILURE.

Run: python3 models/build_datasets.py
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

SNAPSHOT = "2026-11-14"

NFL = "https://www.nfl.com"
SCORES = {w: f"{NFL}/scores/2026/week-{w}" for w in range(1, 11)}

# ---------------------------------------------------------------------------
# 1. COMPLETED GAMES (weeks 1-9 + week 10 TNF). Source per week noted in row.
#    (week, date, away, away_score, home, home_score, label, source)
# ---------------------------------------------------------------------------
GAMES = [
    # ---- WEEK 1 (source: https://www.nfl.com/scores/2026/week-1) ----
    (1, "2026-09-09", "NE", 10, "SEA", 13, "SNF", SCORES[1]),
    (1, "2026-09-10", "SF", 27, "LAR", 7, "Intl-EastMelbourne", SCORES[1]),
    (1, "2026-09-13", "CHI", 59, "CAR", 37, "", SCORES[1]),
    (1, "2026-09-13", "TB", 27, "CIN", 33, "", SCORES[1]),
    (1, "2026-09-13", "NO", 30, "DET", 31, "", SCORES[1]),
    (1, "2026-09-13", "BUF", 36, "HOU", 31, "", SCORES[1]),
    (1, "2026-09-13", "BAL", 41, "IND", 23, "", SCORES[1]),
    (1, "2026-09-13", "CLE", 10, "JAX", 34, "", SCORES[1]),
    (1, "2026-09-13", "ATL", 13, "PIT", 20, "", SCORES[1]),
    (1, "2026-09-13", "NYJ", 23, "TEN", 10, "", SCORES[1]),
    (1, "2026-09-13", "ARI", 26, "LAC", 14, "", SCORES[1]),
    (1, "2026-09-13", "MIA", 13, "LV", 27, "", SCORES[1]),
    (1, "2026-09-13", "GB", 22, "MIN", 39, "", SCORES[1]),
    (1, "2026-09-13", "WAS", 22, "PHI", 24, "", SCORES[1]),
    (1, "2026-09-13", "DAL", 20, "NYG", 28, "SNF", SCORES[1]),
    (1, "2026-09-14", "DEN", 10, "KC", 31, "MNF", SCORES[1]),
    # ---- WEEK 2 (source: https://www.nfl.com/scores/2026/week-2) ----
    (2, "2026-09-17", "DET", 31, "BUF", 41, "TNF", SCORES[2]),
    (2, "2026-09-20", "CAR", 34, "ATL", 3, "", SCORES[2]),
    (2, "2026-09-20", "NO", 24, "BAL", 17, "", SCORES[2]),
    (2, "2026-09-20", "MIN", 9, "CHI", 3, "", SCORES[2]),
    (2, "2026-09-20", "CIN", 20, "HOU", 6, "", SCORES[2]),
    (2, "2026-09-20", "PIT", 3, "NE", 20, "", SCORES[2]),
    (2, "2026-09-20", "GB", 20, "NYJ", 17, "", SCORES[2]),
    (2, "2026-09-20", "CLE", 23, "TB", 19, "", SCORES[2]),
    (2, "2026-09-20", "PHI", 24, "TEN", 20, "", SCORES[2]),
    (2, "2026-09-20", "JAX", 13, "DEN", 20, "", SCORES[2]),
    (2, "2026-09-20", "LV", 26, "LAC", 14, "", SCORES[2]),
    (2, "2026-09-20", "SEA", 31, "ARI", 7, "", SCORES[2]),
    (2, "2026-09-20", "WAS", 20, "DAL", 37, "", SCORES[2]),
    (2, "2026-09-20", "MIA", 13, "SF", 35, "", SCORES[2]),
    (2, "2026-09-20", "IND", 30, "KC", 33, "SNF", SCORES[2]),
    (2, "2026-09-21", "NYG", 6, "LAR", 28, "MNF", SCORES[2]),
    # ---- WEEK 3 (source: https://www.nfl.com/scores/2026/week-3) ----
    (3, "2026-09-24", "ATL", 35, "GB", 14, "TNF", SCORES[3]),
    (3, "2026-09-27", "LAC", 16, "BUF", 24, "", SCORES[3]),
    (3, "2026-09-27", "CAR", 18, "CLE", 21, "", SCORES[3]),
    (3, "2026-09-27", "NYJ", 24, "DET", 31, "", SCORES[3]),
    (3, "2026-09-27", "HOU", 17, "IND", 19, "", SCORES[3]),
    (3, "2026-09-27", "NE", 6, "JAX", 35, "", SCORES[3]),
    (3, "2026-09-27", "KC", 24, "MIA", 10, "", SCORES[3]),
    (3, "2026-09-27", "TEN", 7, "NYG", 12, "", SCORES[3]),
    (3, "2026-09-27", "CIN", 27, "PIT", 30, "", SCORES[3]),
    (3, "2026-09-27", "SEA", 31, "WAS", 33, "", SCORES[3]),
    (3, "2026-09-27", "ARI", 30, "SF", 36, "", SCORES[3]),
    (3, "2026-09-27", "MIN", 23, "TB", 16, "", SCORES[3]),
    (3, "2026-09-27", "LV", 35, "NO", 27, "", SCORES[3]),
    (3, "2026-09-27", "BAL", 34, "DAL", 31, "Intl-RioDeJaneiro", SCORES[3]),
    (3, "2026-09-27", "LAR", 26, "DEN", 30, "SNF", SCORES[3]),
    (3, "2026-09-28", "PHI", 7, "CHI", 27, "MNF", SCORES[3]),
    # ---- WEEK 4 (source: https://www.nfl.com/scores/2026/week-4) ----
    (4, "2026-10-01", "PIT", 24, "CLE", 27, "TNF", SCORES[4]),
    (4, "2026-10-04", "IND", 30, "WAS", 13, "Intl-London", SCORES[4]),
    (4, "2026-10-04", "TEN", 18, "BAL", 24, "", SCORES[4]),
    (4, "2026-10-04", "NE", 29, "BUF", 26, "", SCORES[4]),
    (4, "2026-10-04", "NYJ", 12, "CHI", 23, "", SCORES[4]),
    (4, "2026-10-04", "JAX", 22, "CIN", 17, "", SCORES[4]),
    (4, "2026-10-04", "DAL", 34, "HOU", 30, "", SCORES[4]),
    (4, "2026-10-04", "ARI", 24, "NYG", 36, "", SCORES[4]),
    (4, "2026-10-04", "LAR", 24, "PHI", 20, "", SCORES[4]),
    (4, "2026-10-04", "GB", 17, "TB", 14, "", SCORES[4]),
    (4, "2026-10-04", "MIA", 10, "MIN", 15, "", SCORES[4]),
    (4, "2026-10-04", "KC", 30, "LV", 27, "", SCORES[4]),
    (4, "2026-10-04", "LAC", 23, "SEA", 30, "", SCORES[4]),
    (4, "2026-10-04", "DEN", 14, "SF", 24, "", SCORES[4]),
    (4, "2026-10-04", "DET", 26, "CAR", 32, "SNF", SCORES[4]),
    (4, "2026-10-05", "ATL", 45, "NO", 24, "MNF", SCORES[4]),
    # ---- WEEK 5 (source: https://www.nfl.com/scores/2026/week-5; byes CAR KC) ----
    (5, "2026-10-08", "TB", 24, "DAL", 16, "TNF", SCORES[5]),
    (5, "2026-10-11", "PHI", 17, "JAX", 19, "Intl-London", SCORES[5]),
    (5, "2026-10-11", "CIN", 31, "MIA", 24, "", SCORES[5]),
    (5, "2026-10-11", "LV", 17, "NE", 45, "", SCORES[5]),
    (5, "2026-10-11", "MIN", 23, "NO", 13, "", SCORES[5]),
    (5, "2026-10-11", "CLE", 12, "NYJ", 17, "", SCORES[5]),
    (5, "2026-10-11", "IND", 22, "PIT", 34, "", SCORES[5]),
    (5, "2026-10-11", "HOU", 26, "TEN", 3, "", SCORES[5]),
    (5, "2026-10-11", "NYG", 27, "WAS", 27, "TIE", SCORES[5]),
    (5, "2026-10-11", "CHI", 7, "GB", 31, "", SCORES[5]),
    (5, "2026-10-11", "DEN", 23, "LAC", 17, "", SCORES[5]),
    (5, "2026-10-11", "DET", 45, "ARI", 21, "", SCORES[5]),
    (5, "2026-10-11", "SF", 32, "SEA", 29, "", SCORES[5]),
    (5, "2026-10-11", "BAL", 30, "ATL", 23, "SNF", SCORES[5]),
    (5, "2026-10-12", "BUF", 37, "LAR", 34, "MNF", SCORES[5]),
    # ---- WEEK 6 (source: https://www.nfl.com/scores/2026/week-6; byes CIN DET MIA MIN) ----
    (6, "2026-10-15", "SEA", 14, "DEN", 17, "TNF", SCORES[6]),
    (6, "2026-10-18", "HOU", 34, "JAX", 31, "Intl-London", SCORES[6]),
    (6, "2026-10-18", "CHI", 31, "ATL", 23, "", SCORES[6]),
    (6, "2026-10-18", "BAL", 10, "CLE", 13, "", SCORES[6]),
    (6, "2026-10-18", "TEN", 26, "IND", 20, "", SCORES[6]),
    (6, "2026-10-18", "NYJ", 19, "NE", 26, "", SCORES[6]),
    (6, "2026-10-18", "NO", 34, "NYG", 27, "", SCORES[6]),
    (6, "2026-10-18", "CAR", 25, "PHI", 14, "", SCORES[6]),
    (6, "2026-10-18", "PIT", 26, "TB", 19, "", SCORES[6]),
    (6, "2026-10-18", "ARI", 18, "LAR", 16, "", SCORES[6]),
    (6, "2026-10-18", "LAC", 6, "KC", 22, "", SCORES[6]),
    (6, "2026-10-18", "BUF", 33, "LV", 30, "", SCORES[6]),
    (6, "2026-10-18", "DAL", 13, "GB", 23, "SNF", SCORES[6]),
    (6, "2026-10-19", "WAS", 17, "SF", 23, "MNF", SCORES[6]),
    # ---- WEEK 7 (source: https://www.nfl.com/scores/2026/week-7; byes BUF JAX LAC WAS) ----
    (7, "2026-10-22", "NE", 24, "CHI", 30, "TNF", SCORES[7]),
    (7, "2026-10-25", "PIT", 16, "NO", 10, "Intl-SaintDenis", SCORES[7]),
    (7, "2026-10-25", "SF", 20, "ATL", 29, "", SCORES[7]),
    (7, "2026-10-25", "CIN", 35, "BAL", 13, "", SCORES[7]),
    (7, "2026-10-25", "TB", 43, "CAR", 13, "", SCORES[7]),
    (7, "2026-10-25", "NYG", 27, "HOU", 21, "", SCORES[7]),
    (7, "2026-10-25", "IND", 10, "MIN", 16, "", SCORES[7]),
    (7, "2026-10-25", "MIA", 28, "NYJ", 25, "", SCORES[7]),
    (7, "2026-10-25", "CLE", 27, "TEN", 24, "", SCORES[7]),
    (7, "2026-10-25", "DEN", 30, "ARI", 16, "", SCORES[7]),
    (7, "2026-10-25", "GB", 17, "DET", 20, "", SCORES[7]),
    (7, "2026-10-25", "LAR", 35, "LV", 21, "", SCORES[7]),
    (7, "2026-10-25", "KC", 3, "SEA", 20, "SNF", SCORES[7]),
    (7, "2026-10-26", "DAL", 38, "PHI", 21, "MNF", SCORES[7]),
    # ---- WEEK 8 (scores page hid 5 games; those verified on NFL.com game pages;
    #      MNF verified via ESPN + seahawks.com. byes HOU NO NYG SF) ----
    (8, "2026-10-29", "CAR", 19, "GB", 27, "TNF", SCORES[8]),
    (8, "2026-11-01", "BAL", 10, "BUF", 36, "", SCORES[8]),
    (8, "2026-11-01", "TEN", 36, "CIN", 43, "", SCORES[8]),
    (8, "2026-11-01", "ARI", 33, "DAL", 30, "", SCORES[8]),
    (8, "2026-11-01", "MIN", 15, "DET", 19, "", SCORES[8]),
    (8, "2026-11-01", "IND", 7, "JAX", 42, "", SCORES[8]),
    (8, "2026-11-01", "LV", 38, "NYJ", 33, "", SCORES[8]),
    (8, "2026-11-01", "CLE", 6, "PIT", 27, "", SCORES[8]),
    (8, "2026-11-01", "ATL", 0, "TB", 16, "", SCORES[8]),
    (8, "2026-11-01", "LAC", 9, "LAR", 24, "", f"{NFL}/games/chargers-at-rams-2026-reg-8"),
    (8, "2026-11-01", "KC", 24, "DEN", 28, "", f"{NFL}/games/chiefs-at-broncos-2026-reg-8"),
    (8, "2026-11-01", "NE", 24, "MIA", 19, "", f"{NFL}/games/patriots-at-dolphins-2026-reg-8"),
    (8, "2026-11-01", "PHI", 10, "WAS", 27, "SNF", f"{NFL}/games/eagles-at-commanders-2026-reg-8"),
    (8, "2026-11-02", "CHI", 34, "SEA", 17, "MNF", "https://www.espn.com/nfl/game/_/gameId/401873036/bears-seahawks"),
    # ---- WEEK 9 (source: https://www.nfl.com/scores/2026/week-9; byes PIT TEN) ----
    (9, "2026-11-05", "JAX", 33, "BAL", 10, "TNF", SCORES[9]),
    (9, "2026-11-08", "CIN", 34, "ATL", 17, "Intl-Madrid", SCORES[9]),
    (9, "2026-11-08", "DEN", 26, "CAR", 21, "", SCORES[9]),
    (9, "2026-11-08", "DAL", 27, "IND", 23, "", SCORES[9]),
    (9, "2026-11-08", "NYJ", 12, "KC", 35, "", SCORES[9]),
    (9, "2026-11-08", "DET", 19, "MIA", 9, "", SCORES[9]),
    (9, "2026-11-08", "CLE", 22, "NO", 23, "", SCORES[9]),
    (9, "2026-11-08", "NYG", 19, "PHI", 11, "", SCORES[9]),
    (9, "2026-11-08", "LAR", 20, "WAS", 13, "", SCORES[9]),
    (9, "2026-11-08", "HOU", 44, "LAC", 22, "", SCORES[9]),
    (9, "2026-11-08", "LV", 17, "SF", 38, "", SCORES[9]),
    (9, "2026-11-08", "GB", 45, "NE", 27, "", SCORES[9]),
    (9, "2026-11-08", "ARI", 3, "SEA", 17, "", SCORES[9]),
    (9, "2026-11-08", "TB", 24, "CHI", 27, "SNF", SCORES[9]),
    (9, "2026-11-09", "BUF", 23, "MIN", 6, "MNF", SCORES[9]),
    # ---- WEEK 10 (partial — only TNF final as of snapshot) ----
    (10, "2026-11-12", "WAS", 24, "NYG", 21, "TNF",
     "https://www.espn.com/nfl/game/_/gameId/401873052/commanders-giants"),
]

# ---------------------------------------------------------------------------
# 2. OFFICIAL STANDINGS (NFL.com, snapshot after W10 TNF)
#    https://www.nfl.com/standings/league/2026/REG
#    (team, conf, div, W, L, T, PF, PA, home, road, div_rec, conf_rec, streak)
# ---------------------------------------------------------------------------
STANDINGS_SRC = f"{NFL}/standings/league/2026/REG"
STANDINGS = [
    ("BUF", "AFC", "East", 7, 1, 0, 256, 187, "3-1-0", "4-0-0", "0-1-0", "4-1-0", "4W"),
    ("SF",  "NFC", "West", 7, 1, 0, 235, 156, "5-0-0", "2-1-0", "3-0-0", "4-1-0", "1W"),
    ("CHI", "NFC", "North", 7, 2, 0, 241, 184, "4-1-0", "3-1-0", "0-2-0", "5-2-0", "4W"),
    ("DEN", "AFC", "West", 7, 2, 0, 198, 186, "4-0-0", "3-2-0", "2-1-0", "3-1-0", "5W"),
    ("JAX", "AFC", "South", 6, 2, 0, 229, 121, "4-1-0", "2-1-0", "1-1-0", "5-2-0", "2W"),
    ("CIN", "AFC", "North", 6, 2, 0, 240, 175, "2-1-0", "4-1-0", "1-1-0", "4-2-0", "4W"),
    ("DET", "NFC", "North", 6, 2, 0, 222, 189, "4-0-0", "2-2-0", "2-0-0", "4-1-0", "4W"),
    ("KC",  "AFC", "West", 6, 2, 0, 202, 143, "4-0-0", "2-2-0", "3-1-0", "6-1-0", "1W"),
    ("MIN", "NFC", "North", 6, 2, 0, 146, 116, "3-1-0", "3-1-0", "2-1-0", "4-1-0", "2L"),
    ("PIT", "AFC", "North", 6, 2, 0, 180, 144, "4-0-0", "2-2-0", "2-1-0", "3-2-0", "4W"),
    ("GB",  "NFC", "North", 6, 3, 0, 216, 191, "3-1-0", "3-2-0", "1-2-0", "4-3-0", "2W"),
    ("NYG", "NFC", "East", 5, 3, 1, 203, 196, "3-2-0", "2-1-1", "2-1-1", "3-3-1", "1L"),
    ("CLE", "AFC", "North", 5, 4, 0, 161, 196, "3-0-0", "2-4-0", "2-1-0", "3-3-0", "2L"),
    ("LAR", "NFC", "West", 5, 4, 0, 214, 181, "2-3-0", "3-1-0", "0-2-0", "3-2-0", "3W"),
    ("NE",  "AFC", "East", 5, 4, 0, 211, 207, "3-1-0", "2-3-0", "3-0-0", "5-1-0", "1L"),
    ("SEA", "NFC", "West", 5, 4, 0, 202, 162, "4-2-0", "1-2-0", "2-1-0", "2-3-0", "1W"),
    ("BAL", "AFC", "North", 4, 5, 0, 189, 236, "1-3-0", "3-2-0", "0-2-0", "2-4-0", "4L"),
    ("DAL", "NFC", "East", 4, 5, 0, 246, 236, "1-3-0", "3-2-0", "2-1-0", "2-4-0", "1W"),
    ("LV",  "AFC", "West", 4, 5, 0, 238, 268, "1-3-0", "3-2-0", "1-1-0", "3-3-0", "1L"),
    ("CAR", "NFC", "South", 3, 5, 0, 199, 219, "1-3-0", "2-2-0", "1-1-0", "3-3-0", "3L"),
    ("HOU", "AFC", "South", 3, 5, 0, 209, 192, "0-4-0", "3-1-0", "2-1-0", "3-3-0", "1W"),
    ("NO",  "NFC", "South", 3, 5, 0, 185, 216, "1-4-0", "2-1-0", "0-1-0", "1-3-0", "1W"),
    ("WAS", "NFC", "East", 3, 5, 1, 196, 223, "2-2-1", "1-3-0", "2-2-1", "3-4-1", "1W"),
    ("ARI", "NFC", "West", 3, 6, 0, 178, 255, "0-3-0", "3-3-0", "1-3-0", "2-5-0", "1L"),
    ("ATL", "NFC", "South", 3, 6, 0, 188, 223, "1-4-0", "2-2-0", "1-2-0", "3-3-0", "2L"),
    ("TB",  "NFC", "South", 3, 6, 0, 202, 178, "1-4-0", "2-2-0", "2-0-0", "3-3-0", "1L"),
    ("IND", "AFC", "South", 2, 7, 0, 184, 249, "1-3-0", "1-4-0", "1-2-0", "1-5-0", "5L"),
    ("NYJ", "AFC", "East", 2, 7, 0, 182, 223, "1-3-0", "1-4-0", "0-2-0", "2-4-0", "4L"),
    ("PHI", "NFC", "East", 2, 7, 0, 148, 221, "1-4-0", "1-3-0", "1-3-0", "1-6-0", "7L"),
    ("TEN", "AFC", "South", 1, 7, 0, 144, 199, "0-4-0", "1-3-0", "1-1-0", "1-5-0", "2L"),
    ("MIA", "AFC", "East", 1, 7, 0, 126, 200, "0-4-0", "1-3-0", "1-1-0", "1-4-0", "2L"),
    ("LAC", "AFC", "West", 0, 8, 0, 121, 219, "0-4-0", "0-4-0", "0-3-0", "0-5-0", "8L"),
]

def emit(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)
    print(f"wrote data/{name}")

games = [
    {"week": w, "date": d, "away": a, "away_score": asc, "home": h, "home_score": hsc,
     "label": lbl, "source": src}
    for (w, d, a, asc, h, hsc, lbl, src) in GAMES
]
emit("scores_2026.json", {
    "season": 2026, "snapshot": SNAPSHOT,
    "description": "All completed 2026 NFL regular-season games through Week 10 TNF. "
                   "Every score transcribed from the official NFL.com source linked in the row "
                   "(Week 8 hidden-score games verified via official NFL.com game pages; "
                   "W8 MNF via ESPN game summary + seahawks.com game center).",
    "games": games,
})

standings = [
    {"team": t, "conference": c, "division": d, "w": w, "l": l, "tie": tt,
     "pf": pf, "pa": pa, "home": hm, "road": rd, "div": dv, "conf": cf, "streak": st,
     "source": STANDINGS_SRC}
    for (t, c, d, w, l, tt, pf, pa, hm, rd, dv, cf, st) in STANDINGS
]
emit("standings_2026.json", {
    "season": 2026, "snapshot": "after Week 10 TNF (2026-11-12)", "source": STANDINGS_SRC,
    "standings": standings,
})

# ---------------------------------------------------------------------------
# 3. SELF-VERIFICATION: recompute W-L-T / PF / PA from games and compare with
#    the official standings table. Fail the build on any mismatch.
# ---------------------------------------------------------------------------
rec = {t: {"w": 0, "l": 0, "tie": 0, "pf": 0, "pa": 0} for t, *_ in STANDINGS}
for g in games:
    a, h, as_, hs = g["away"], g["home"], g["away_score"], g["home_score"]
    rec[a]["pf"] += as_; rec[a]["pa"] += hs
    rec[h]["pf"] += hs; rec[h]["pa"] += as_
    if as_ > hs:
        rec[a]["w"] += 1; rec[h]["l"] += 1
    elif hs > as_:
        rec[h]["w"] += 1; rec[a]["l"] += 1
    else:
        rec[a]["tie"] += 1; rec[h]["tie"] += 1

failures = []
for (t, *_rest) in STANDINGS:
    # _rest = (conf, div, W, L, T, PF, PA, home, road, div_rec, conf_rec, streak)
    w, l, tt = _rest[2], _rest[3], _rest[4]
    pf, pa = _rest[5], _rest[6]
    r = rec[t]
    if (r["w"], r["l"], r["tie"], r["pf"], r["pa"]) != (w, l, tt, pf, pa):
        failures.append((t, (w, l, tt, pf, pa), (r["w"], r["l"], r["tie"], r["pf"], r["pa"])))

print("=" * 70)
print("VERIFICATION: recomputed records from game rows vs NFL.com standings")
print(f"games transcribed: {len(games)}  teams: {len(STANDINGS)}")
if failures:
    for t, off, mine in failures:
        print(f"  MISMATCH {t}: standings={off} recomputed={mine}")
    print("RESULT: FAIL — fix game rows before publishing")
    sys.exit(1)
print("RESULT: PASS — all 32 team records, PF and PA match official standings exactly")
print("=" * 70)
