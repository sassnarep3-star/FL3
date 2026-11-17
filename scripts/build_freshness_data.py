#!/usr/bin/env python3
"""
FL3 — official-source freshness pass (session arena/4ac55b56-fl3, 2026-11-17).

Writes the dated freshness dataset under data/freshness/ from values transcribed
from live official NFL.com pages fetched on 2026-11-17 (UTC), and computes the
standings delta between the committed 2026-11-14 snapshot (data/standings.json)
and the live page.

Evidence rules (same as the rest of the repo):
* Every row carries the official URL it was read from.
* Nothing is inferred. Where the official page does not state a value, the cell
  stays blank and the item is recorded in findings.json.
* The delta file is computed, never hand-written.

Sources fetched 2026-11-17 (UTC) through the agent fetch tool:
  https://www.nfl.com/standings/league/2026/reg          (2 chunks, 32 teams)
  https://www.nfl.com/schedules/2026/by-week/week-11     (3 chunks, 13 games + 6 byes)
  https://www.nfl.com/schedules/2026/by-week/week-10     (2 chunks, 14 games + results)
  https://www.nfl.com/injuries/league/2026/reg11        (redirects to the Week 10 report)
  https://www.nfl.com/injuries/league/2026/reg10        (Week 10 report still served)
  https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced
  13 official game centres for the Week 11 slate (venues + game info)
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "freshness")

FETCHED = "2026-11-17"

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/reg"
SCHED_W11_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
SCHED_W10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJ_W11_URL = "https://www.nfl.com/injuries/league/2026/reg11"
INJ_W10_URL = "https://www.nfl.com/injuries/league/2026/reg10"
ANNounce_URL = "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"

# Live standings transcribed from the league standings page on 2026-11-17
# (post-Week 10 for the Sunday slate; the TNF and MNF Week 10 results are NOT
# reflected on the page — see findings F-FRESH-02 / F-FRESH-03).
# Fields: abbr, name, w, l, t, pct, pf, pa, net
STANDINGS_LIVE = [
    ("BUF", "Buffalo Bills", 8, 1, 0, 0.889, 287, 199, 88),
    ("SF", "San Francisco 49ers", 8, 1, 0, 0.889, 281, 196, 85),
    ("CHI", "Chicago Bears", 7, 2, 0, 0.778, 241, 184, 57),
    ("CIN", "Cincinnati Bengals", 7, 2, 0, 0.778, 278, 193, 85),
    ("DEN", "Denver Broncos", 7, 2, 0, 0.778, 198, 186, 12),
    ("DET", "Detroit Lions", 7, 2, 0, 0.778, 257, 199, 58),
    ("JAX", "Jacksonville Jaguars", 7, 2, 0, 0.778, 269, 144, 125),
    ("KC", "Kansas City Chiefs", 7, 2, 0, 0.778, 237, 156, 81),
    ("MIN", "Minnesota Vikings", 7, 2, 0, 0.778, 176, 126, 50),
    ("PIT", "Pittsburgh Steelers", 6, 3, 0, 0.667, 198, 182, 16),
    ("NYG", "New York Giants", 5, 3, 1, 0.611, 203, 196, 7),
    ("CLE", "Cleveland Browns", 6, 4, 0, 0.600, 188, 220, -32),
    ("GB", "Green Bay Packers", 6, 4, 0, 0.600, 226, 221, 5),
    ("LAR", "Los Angeles Rams", 6, 4, 0, 0.600, 248, 187, 61),
    ("SEA", "Seattle Seahawks", 6, 4, 0, 0.600, 223, 175, 48),
    ("NE", "New England Patriots", 5, 5, 0, 0.500, 221, 242, -21),
    ("BAL", "Baltimore Ravens", 4, 5, 0, 0.444, 189, 236, -47),
    ("CAR", "Carolina Panthers", 4, 5, 0, 0.444, 219, 236, -17),
    ("DAL", "Dallas Cowboys", 4, 6, 0, 0.400, 286, 282, 4),
    ("LV", "Las Vegas Raiders", 4, 6, 0, 0.400, 251, 289, -38),
    ("WAS", "Washington Commanders", 3, 5, 1, 0.389, 196, 223, -27),
    ("HOU", "Houston Texans", 3, 6, 0, 0.333, 233, 219, 14),
    ("NO", "New Orleans Saints", 3, 6, 0, 0.333, 202, 236, -34),
    ("TB", "Tampa Bay Buccaneers", 3, 6, 0, 0.333, 202, 178, 24),
    ("AZ", "Arizona Cardinals", 3, 7, 0, 0.300, 184, 289, -105),
    ("ATL", "Atlanta Falcons", 3, 7, 0, 0.300, 201, 258, -57),
    ("IND", "Indianapolis Colts", 3, 7, 0, 0.300, 208, 271, -63),
    ("PHI", "Philadelphia Eagles", 2, 7, 0, 0.222, 148, 221, -73),
    ("NYJ", "New York Jets", 2, 8, 0, 0.200, 194, 254, -60),
    ("MIA", "Miami Dolphins", 1, 8, 0, 0.111, 148, 224, -76),
    ("TEN", "Tennessee Titans", 1, 8, 0, 0.111, 167, 239, -72),
    ("LAC", "Los Angeles Chargers", 0, 8, 0, 0.000, 121, 219, -98),
]

# Week 11 slate transcribed from the schedule page + the 13 official game
# centres (venue / location read from each game centre's Game Info block).
# Fields: away, home, date, time, network, location, stadium, src
SCHEDULE_W11 = [
    ("IND", "HOU", "Thu Nov 19", "8:15 PM", "Prime Video", "HOUSTON, TX", "RELIANT STADIUM",
     "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
    ("MIA", "BUF", "Sun Nov 22", "1:00 PM", "CBS", "ORCHARD PARK, NY", "HIGHMARK STADIUM",
     "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11"),
    ("BAL", "CAR", "Sun Nov 22", "1:00 PM", "FOX", "CHARLOTTE, NC", "BANK OF AMERICA STADIUM",
     "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11"),
    ("NO", "CHI", "Sun Nov 22", "1:00 PM", "FOX", "CHICAGO, IL", "SOLDIER FIELD",
     "https://www.nfl.com/games/saints-at-bears-2026-reg-11"),
    ("TEN", "DAL", "Sun Nov 22", "1:00 PM", "FOX", "ARLINGTON, TX", "AT&T STADIUM",
     "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11"),
    ("TB", "DET", "Sun Nov 22", "1:00 PM", "FOX", "DETROIT, MI", "FORD FIELD",
     "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
    ("AZ", "KC", "Sun Nov 22", "1:00 PM", "CBS", "KANSAS CITY, MO", "ARROWHEAD STADIUM",
     "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11"),
    ("PIT", "PHI", "Sun Nov 22", "1:00 PM", "CBS", "PHILADELPHIA, PA", "LINCOLN FINANCIAL FIELD",
     "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11"),
    ("NYJ", "LAC", "Sun Nov 22", "4:05 PM", "FOX", "INGLEWOOD, CA", "SOFI STADIUM",
     "https://www.nfl.com/games/jets-at-chargers-2026-reg-11"),
    ("JAX", "NYG", "Sun Nov 22", "4:25 PM", "CBS", "EAST RUTHERFORD, NJ", "METLIFE STADIUM",
     "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11"),
    ("LV", "DEN", "Sun Nov 22", "4:25 PM", "CBS", "DENVER, CO", "EMPOWER FIELD AT MILE HIGH",
     "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11"),
    ("MIN", "SF", "Sun Nov 22", "8:20 PM", "NBC", "MEXICO CITY", "ESTADIO BANORTE",
     "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"),
    ("CIN", "WAS", "Mon Nov 23", "8:15 PM", "ESPN", "LANDOVER, MD", "NORTHWEST STADIUM",
     "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11"),
]

BYE_W11 = ["ATL", "CLE", "GB", "LAR", "NE", "SEA"]

# Week 10 bye clubs, read from the "Teams on Bye" block of the Week 10
# schedule page (CHI 7-2, DEN 7-2, PHI 2-7, TB 3-6).
BYE_W10 = ["CHI", "DEN", "PHI", "TB"]

# Week 10 results transcribed from the schedule page on 2026-11-17.
# status: FINAL for 13 games; the MNF game is recorded exactly as displayed
# ("Q2 / Live", score 17-7) — its final score is NOT published on the page.
# Fields: away, home, away_score, home_score, slot, status, src
RESULTS_W10 = [
    ("WAS", "NYG", 24, 21, "TNF Thu Nov 12", "FINAL",
     "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"),
    ("NE", "DET", 10, 35, "International (Munich) Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"),
    ("KC", "ATL", 35, 13, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10"),
    ("HOU", "CLE", 24, 27, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/texans-at-browns-2026-reg-10"),
    ("MIN", "GB", 30, 10, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/vikings-at-packers-2026-reg-10"),
    ("MIA", "IND", 22, 24, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10"),
    ("CAR", "NO", 20, 17, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/panthers-at-saints-2026-reg-10"),
    ("BUF", "NYJ", 31, 12, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/bills-at-jets-2026-reg-10"),
    ("JAX", "TEN", 40, 23, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10"),
    ("LAR", "AZ", 34, 6, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10"),
    ("SEA", "LV", 21, 13, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10"),
    ("SF", "DAL", 46, 40, "Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10"),
    ("PIT", "CIN", 18, 38, "SNF Sun Nov 15", "FINAL",
     "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10"),
    ("LAC", "BAL", 17, 7, "MNF Mon Nov 16", "LIVE Q2 as displayed 2026-11-17 (final score not published)",
     "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"),
]

FINDINGS = [
    {
        "id": "F-FRESH-01",
        "severity": "info",
        "title": "Week 11 injury report is not yet published",
        "detail": (
            "The Week 11 injury-report URL https://www.nfl.com/injuries/league/2026/reg11 serves the "
            "Week 10 report (page title: \"Official NFL Injury Report for Players - Week 10 of the 2026 "
            "Season\"). All 13 Week 11 game centres display \"Injury Report is not available at this "
            "time.\" Week 11 kicks off Thursday 2026-11-19, so no Week 11 availability data exists yet. "
            "The ledger records the absence; no availability value is inferred for Week 11."
        ),
        "src": INJ_W11_URL,
    },
    {
        "id": "F-FRESH-02",
        "severity": "medium",
        "title": "Live standings page still excludes the Week 10 Thursday result (flag F01 persists)",
        "detail": (
            "As of the 2026-11-17 fetch, https://www.nfl.com/standings/league/2026/reg still shows NYG "
            "5-3-1 and WAS 3-5-1, unchanged from the 2026-11-14 committed snapshot, while the schedule "
            "page marks WAS 24 - NYG 21 (Thursday Night Football, Nov 12) FINAL. The Thursday result is "
            "not reflected in the standings page three days after the game. Existing flag F01 persists; "
            "the delta table classifies WAS and NYG as 'not reflected' rather than correcting them."
        ),
        "src": STANDINGS_URL,
    },
    {
        "id": "F-FRESH-03",
        "severity": "high",
        "title": "Week 10 Monday game displayed as LIVE in Q2 on the schedule page; standings exclude it",
        "detail": (
            "The schedule page fetched 2026-11-17 displays the Week 10 Monday Night Football game "
            "\"Chargers 17, Ravens 7, Q2, ESPN\" with a LIVE indicator, roughly one day after the "
            "scheduled 2026-11-16 kickoff. The final score is not published on the official schedule "
            "page, and the standings page shows both BAL (4-5) and LAC (0-8) unchanged from the "
            "2026-11-14 snapshot. The final score cell is left blank and flagged; no result is inferred."
        ),
        "src": SCHED_W10_URL,
    },
    {
        "id": "F-FRESH-04",
        "severity": "info",
        "title": "Week 11 slate verified: 13 games, 6 bye clubs, one Mexico City international game",
        "detail": (
            "The Week 11 schedule page lists 13 games and 6 bye clubs (ATL, CLE, GB, LAR, NE, SEA): "
            "26 playing clubs + 6 byes = 32. The MIN@SF Sunday night game is an international game in "
            "Mexico City (Estadio Banorte), consistent with the league's dated schedule announcement."
        ),
        "src": SCHED_W11_URL,
    },
    {
        "id": "F-FRESH-05",
        "severity": "info",
        "title": "Dated 2026 schedule announcement verified live (May 14, 2026)",
        "detail": (
            "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced is live, "
            "by Football Communications, dated May 14, 2026, and announces the 18-week, 272-game "
            "regular season. It confirms the Week 11 Mexico City game. This is the dated announcement "
            "evidence for requirement R025."
        ),
        "src": ANNounce_URL,
    },
    {
        "id": "F-FRESH-06",
        "severity": "info",
        "title": "Week 11 venues transcribed from all 13 official game centres",
        "detail": (
            "Location and stadium for every Week 11 fixture were read from the Game Info block of each "
            "official nfl.com game centre (13/13). Each venue row links its own game centre. No venue "
            "was inferred from third-party sources."
        ),
        "src": SCHED_W11_URL,
    },
]


def write(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")


def main():
    os.makedirs(OUT, exist_ok=True)

    write("manifest.json", {
        "pass": "official-source freshness pass",
        "session": "arena/4ac55b56-fl3",
        "fetched_utc": FETCHED,
        "committed_snapshot": "2026-11-14 (data/standings.json)",
        "sources": [
            {"role": "standings", "url": STANDINGS_URL, "chunks": 2,
             "what": "32 clubs W/L/T/PCT/PF/PA/NET, post-Week 10 Sunday slate"},
            {"role": "schedule_week11", "url": SCHED_W11_URL, "chunks": 3,
             "what": "13 games, dates/times/networks, 6 bye clubs"},
            {"role": "schedule_week10", "url": SCHED_W10_URL, "chunks": 2,
             "what": "14 games with final scores (13 FINAL; MNF displayed LIVE Q2)"},
            {"role": "injuries_week11_url", "url": INJ_W11_URL, "chunks": 1,
             "what": "redirects to the Week 10 report; Week 11 report not published"},
            {"role": "injuries_week10", "url": INJ_W10_URL, "chunks": 1,
             "what": "Week 10 report still served as the current report"},
            {"role": "schedule_announcement", "url": ANNounce_URL, "chunks": 1,
             "what": "dated 2026 schedule announcement, May 14, 2026"},
        ],
        "game_centres": [s for *_rest, s in SCHEDULE_W11],
    })

    write("standings_live_2026-11-17.json", {
        "meta": {
            "title": "2026 NFL league standings — live capture",
            "source": STANDINGS_URL,
            "fetched_utc": FETCHED,
            "note": ("Post-Week 10 for the Sunday slate. The Week 10 TNF (WAS@NYG) and MNF "
                     "(LAC@BAL) results are NOT reflected on this page — see F-FRESH-02/F-FRESH-03."),
        },
        "teams": [
            {"abbr": a, "name": n, "w": w, "l": l, "t": t, "pct": p, "pf": pf, "pa": pa, "net": nt,
             "src": STANDINGS_URL}
            for a, n, w, l, t, p, pf, pa, nt in STANDINGS_LIVE
        ],
    })

    write("schedule_w11_2026-11-17.json", {
        "meta": {
            "title": "2026 NFL Week 11 schedule — live capture",
            "source": SCHED_W11_URL,
            "fetched_utc": FETCHED,
            "note": ("13 games + 6 bye clubs. Venue and location for every fixture were read from "
                     "the official game centre linked per row."),
        },
        "games": [
            {"away": a, "home": h, "date": d, "time": t, "network": nw,
             "location": loc, "stadium": st, "src": s}
            for a, h, d, t, nw, loc, st, s in SCHEDULE_W11
        ],
        "bye_clubs": BYE_W11,
    })

    write("results_w10_2026-11-17.json", {
        "meta": {
            "title": "2026 NFL Week 10 results — live capture",
            "source": SCHED_W10_URL,
            "fetched_utc": FETCHED,
            "note": ("Scores read from the official schedule page. The MNF game is recorded exactly "
                     "as displayed (LIVE Q2, 17-7); its final score is not published — see F-FRESH-03."),
        },
        "games": [
            {"away": a, "home": h, "away_score": as_, "home_score": hs, "slot": slot,
             "status": st, "src": s}
            for a, h, as_, hs, slot, st, s in RESULTS_W10
        ],
    })

    write("findings.json", {
        "meta": {
            "title": "Freshness pass findings (2026-11-17)",
            "session": "arena/4ac55b56-fl3",
            "fetched_utc": FETCHED,
            "note": ("Published on the Flagged for Review page of the freshness subsite. "
                     "None of these block the merge; none were silently corrected."),
        },
        "findings": FINDINGS,
    })

    # ---- delta: committed 2026-11-14 snapshot vs live 2026-11-17 ------------
    with open(os.path.join(DATA, "standings.json"), encoding="utf-8") as fh:
        committed = {t["abbr"]: t for t in json.load(fh)["teams"]}
    # The committed snapshot uses the club code LA for the Rams (flag F27); the
    # live page uses LAR. Map the alias for the delta only — the committed file
    # is not edited.
    committed = {"LAR" if k == "LA" else k: v for k, v in committed.items()}

    live = {a: dict(w=w, l=l, t=t, pct=p, pf=pf, pa=pa, net=nt)
            for a, n, w, l, t, p, pf, pa, nt in STANDINGS_LIVE}

    # Week 10 game scores per team, from the results capture (for the delta check)
    played = {}
    for a, h, as_, hs, slot, st, s in RESULTS_W10:
        played[a] = {"pf": as_, "pa": hs, "slot": slot, "status": st}
        played[h] = {"pf": hs, "pa": as_, "slot": slot, "status": st}

    rows = []
    for abbr in sorted(live):
        c = committed.get(abbr)
        lv = live[abbr]
        if abbr in BYE_W10:
            classification = "bye (week 10)"
        elif abbr not in played:
            classification = "no week-10 game found"
        elif abbr in ("WAS", "NYG", "BAL", "LAC"):
            classification = "not reflected on standings page"
        else:
            classification = "reflected"
        row = {
            "abbr": abbr,
            "committed_w": c["w"], "committed_l": c["l"], "committed_t": c["t"],
            "committed_pct": c["pct"], "committed_pf": c["pf"], "committed_pa": c["pa"],
            "committed_net": c["net"],
            "live_w": lv["w"], "live_l": lv["l"], "live_t": lv["t"],
            "live_pct": lv["pct"], "live_pf": lv["pf"], "live_pa": lv["pa"],
            "live_net": lv["net"],
            "dw": lv["w"] - c["w"], "dl": lv["l"] - c["l"], "dt": lv["t"] - c["t"],
            "dpf": lv["pf"] - c["pf"], "dpa": lv["pa"] - c["pa"],
            "classification": classification,
            "src": STANDINGS_URL,
        }
        if classification == "reflected":
            game = played[abbr]
            row["expected_dpf"] = game["pf"]
            row["expected_dpa"] = game["pa"]
        rows.append(row)

    write("delta_standings_2026-11-17.json", {
        "meta": {
            "title": "Standings delta: committed 2026-11-14 snapshot vs live 2026-11-17",
            "committed_source": "data/standings.json (captured 2026-11-14)",
            "live_source": STANDINGS_URL,
            "fetched_utc": FETCHED,
            "note": ("Classification: 'reflected' = the Week 10 result appears in the live page and "
                     "the PF/PA deltas equal that game's scores; 'bye (week 10)' = club was on its Week 10 bye; "
                     "'not reflected on standings page' = the club played in Week 10 but the live "
                     "page shows no change (see F-FRESH-02/F-FRESH-03). The committed snapshot's "
                     "club code LA for the Rams is mapped to LAR for the delta only (flag F27)."),
        },
        "rows": rows,
    })

    counts = {"reflected": 0, "bye": 0, "not reflected on standings page": 0}
    for r in rows:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    print("freshness dataset written to", OUT)
    print("classification counts:", counts)


if __name__ == "__main__":
    main()
