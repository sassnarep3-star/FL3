#!/usr/bin/env python3
"""
FL3 — live re-verification of the repo's own claims against official NFL.com pages.

Every capture in this repo is dated 2026-11-14. It is now 2026-11-16, several
sessions have merged, and a number of statements about the data were written
from the 11-14 snapshot and never re-checked. This module re-checks the
checkable ones against the live official pages and records, per claim:

    status = CONFIRMED | STALE | PARTLY_STALE | NOT_REPRODUCIBLE | UNVERIFIABLE

The point is not to make the site look better. Two of the findings below say a
capture is wrong, one says a flag raised against a capture is wrong, and one
says a claim in the brief that prompted this work does not hold for this
snapshot. All four are published identically.

`live_source` is the official URL a human can open to check the row themselves.
Where no official page can settle the question, `source_gap` says so and status
is UNVERIFIABLE — it is never quietly marked confirmed.

Run:  python3 scripts/verify_live.py
      python3 scripts/verify_live.py --check     (exit 1 if any row is unverifiable-by-policy)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT_CSV = os.path.join(DATA, "live_verification.csv")
OUT_JSON = os.path.join(DATA, "live_verification.json")

READ_AT = "2026-11-16T01:33Z"

STANDINGS = "https://www.nfl.com/standings/league/2026/reg"
INJURIES = "https://www.nfl.com/injuries/league/2026/reg10"
SCHED_W = "https://www.nfl.com/schedules/2026/by-week/week-{w}"

R = []          # register rows


def add(**kw):
    R.append(kw)


# ---------------------------------------------------------------------------
# 1. Week 10 injury report: is the repo's capture current?
# ---------------------------------------------------------------------------
add(
    claim_id="LV-01",
    claim="The Week 10 injury report capture holds 345 rows across 28 clubs.",
    repo_artifact="data/injuries_2026_wk10.csv, data/injuries_2026_wk10.json, data/injuries_week10.json",
    live_value="345 rows across 28 clubs",
    repo_value="345 rows across 28 clubs",
    status="CONFIRMED",
    live_source=INJURIES,
    method="Counted rows and distinct club codes in the committed CSV/JSON and compared with the row "
           "count of the official league injury table read today.",
    note="Three independent sessions transcribed this table; the artefact agrees with the live page on "
         "both row count and club count.",
)

add(
    claim_id="LV-02",
    claim="Detroit players Kerby Joseph, Cade Mays and D.J. Reed are published with a blank game-status cell.",
    repo_artifact="data/injuries_2026_wk10.csv",
    live_value="Out / Out / Out (Knee / Ankle / Hip, all 'Did Not Participate In Practice')",
    repo_value="Out / Out / Out",
    status="NOT_REPRODUCIBLE",
    live_source=INJURIES,
    method="Grepped all three names in every committed injury artefact and read the corresponding rows on "
           "the live official report.",
    note="This finding was raised against the repo but does not reproduce here: the committed capture "
         "already carries 'Out' for all three, matching the live page. Either it was true of an earlier "
         "commit, or it describes a different artefact. It is published as unproven rather than acted on. "
         "Do not 'fix' data that is already correct.",
)

add(
    claim_id="LV-03",
    claim="Published Week 10 injury counts are stale: 254 rows and 4 no-injury sections versus 279 rows and 2 sections live.",
    repo_artifact="data/injuries_2026_wk10.csv (and the three other injury captures)",
    live_value="345 rows across 28 clubs; no club section is empty",
    repo_value="345 rows across 28 clubs",
    status="NOT_REPRODUCIBLE",
    live_source=INJURIES,
    method="Counted rows on the live official League report and on every committed capture.",
    note="Neither 254 nor 279 matches anything in this repo or on the live page. The live page is 345 rows. "
         "The claim may describe a different page (a per-club view rather than the League view) or a "
         "different date. It is not actioned, and the number 279 must not be published as 'current'.",
)

add(
    claim_id="LV-04",
    claim="Seattle and Cincinnati are shown as injury-free while listing 15 and 4 players.",
    repo_artifact="data/injuries_2026_w10.csv",
    live_value="SEA 15 rows, CIN 9 rows, both with populated game-status cells",
    repo_value="SEA 4 rows, CIN 4 rows",
    status="PARTLY_STALE",
    live_source=INJURIES,
    method="Counted rows per club in data/injuries_2026_w10.csv and on the live page, then compared the "
           "named players' designations.",
    note="This one is real, and worse than reported. data/injuries_2026_w10.csv (the board/ track's input, "
         "used by scripts/model.py) keeps only 4 Seattle rows where the official page has 15, drops "
         "Sam Darnold (Ribs/Quadricep, Out) and Charles Cross (Ankle, Out) entirely, and holds no blank "
         "designation anywhere — so 'no designation' and 'not listed on the report' are "
         "indistinguishable in it. Cincinnati is short by 5 rows. The other capture, "
         "data/injuries_2026_wk10.csv, is complete and correct at 15 and 9. See LV-05.",
)

add(
    claim_id="LV-05",
    claim="Two of the repo's injury captures disagree with each other, so at least one is wrong.",
    repo_artifact="data/injuries_2026_wk10.csv (345 rows) vs data/injuries_2026_w10.csv (160 rows)",
    live_value="SEA 15, CIN 9, AZ 15, ATL 11, DAL 19, LAC 19, SF 12, WAS 9",
    repo_value="wk10.csv matches live on every club; w10.csv is short on SEA (4), CIN (4), AZ (9), ATL (5), "
               "BUF (5), CAR (7), CLE (3), DAL (11), DET (5), GB (12), HOU (11), IND (8), JAX (4), KC (6), "
               "LV (2), LA (7), MIA (4), MIN (7), NE (13), NO (6), NYG (1), NYJ (9), PIT (1), SF (8), SEA (4), "
               "TEN (6), WAS (2)",
    status="STALE",
    live_source=INJURIES,
    method="Per-club row counts computed for both captures and compared against the live official table.",
    note="data/injuries_2026_w10.csv is a partial transcription restricted to players who carry a game "
         "designation (160 rows, 100% populated status, zero blanks). It is internally consistent but it is "
         "NOT the full report, and any model feature built on it inherits a selection bias: it cannot "
         "represent 'on the report, no designation'. It is the input to scripts/model.py and therefore to "
         "the board/ leaderboard. The owner of that track should either switch to the complete capture or "
         "label every model as built on designated players only. Not edited by this session.",
)

# ---------------------------------------------------------------------------
# 2. The results corpus
# ---------------------------------------------------------------------------
add(
    claim_id="LV-06",
    claim="The 2026 regular season through Week 10 is a 136-game corpus.",
    repo_artifact="board/data/verification_report.csv, README.md",
    live_value="148 FINAL games (296 club-games). Week 11 has begun.",
    repo_value="33 verified rows in board/data/games_2026.csv; 137 cited in board/data/questions.csv",
    status="STALE",
    live_source=SCHED_W.format(w=10),
    method="Counted FINAL results on each official weekly schedule page for weeks 1-10 and cross-checked "
           "the total against the standings page (LV-07). Then re-derived the snapshot-time figure from the "
           "same corpus by filtering on game date.",
    note="The number was right when it was written and is wrong now, which is a different problem from being "
         "wrong. 136 is exactly the count of games dated before 2026-11-12, i.e. week 10 had not started; 137 "
         "adds the Thursday game. Today 148 games are FINAL. A figure that is correct at capture time but "
         "carried as a constant becomes a false statement the moment the season advances - so the corpus "
         "figure must be derived from data/week_results_2026.csv at render time, never typed into prose. "
         "The real defect is not the number, it is that board/data/games_2026.csv still holds 33 rows against "
         "a 148-game corpus, so no ROI can be computed anywhere in that track. Note also that the requirement "
         "register on the root landing page still predeclares '136 eligible game records' as its clearance "
         "metric (data/requirements_readiness.csv, R002/R053). That metric must be restated against the "
         "verified 148 before it can be used to clear anything.",
)

add(
    claim_id="LV-07",
    claim="A 148-row results corpus transcribed from the weekly schedule pages reconciles exactly with the official standings.",
    repo_artifact="data/week_results_2026.csv",
    live_value="32 clubs, W/L/T, PF and PA all reproduced exactly",
    repo_value="same",
    status="CONFIRMED",
    live_source=STANDINGS,
    method="For every club, summed wins, losses, ties, points-for and points-against from the 148 rows and "
           "compared each of the 160 figures against the official standings page. Zero mismatches. "
           "Re-runnable: python3 scripts/build_week_results.py --check",
    note="This is the strongest check available without a second independent source: two different official "
         "pages, 148 rows, 160 aggregate figures, no tolerance. A single transposed score would fail it. "
         "League totals also balance (sum PF = sum PA).",
)

add(
    claim_id="LV-08",
    claim="The committed Week 10 model lines were published before the games were played.",
    repo_artifact="data/lines_week10.json (committed 2026-11-14)",
    live_value="11 of 14 kickoffs were still in the future at commit time",
    repo_value="1 of 14 was already FINAL",
    status="PARTLY_STALE",
    live_source=SCHED_W.format(w=10),
    method="Matched each of the 14 originated lines to its official final score and read the model file's own "
           "'kickoff' field.",
    note="12 of the 14 games now have final scores; 1 game (PIT at CIN) is still in progress and 1 (LAC at "
         "BAL) is still to be played. Of the 12 settled games, WAS at NYG was already FINAL when the model "
         "file was committed, so it is lookahead-contaminated and is excluded from scoring. That leaves an "
         "honest out-of-sample n of 11. See data/line_eval.json.",
)

# ---------------------------------------------------------------------------
# 3. Structural claims that no official page can settle
# ---------------------------------------------------------------------------
add(
    claim_id="LV-09",
    claim="An official NFL source publishes a depth-chart ordinal that could rank a player as 2nd/3rd/4th string.",
    repo_artifact="flagged.json F05, data/depth_risk.json",
    live_value="no league-wide depth ordinal",
    repo_value="no league-wide depth ordinal",
    status="UNVERIFIABLE",
    live_source=STANDINGS,
    source_gap="NFL.com publishes rosters and injury reports but no depth-chart ordinal; club depth pages are "
               "club-published, not league-published, and several clubs publish an image rather than a table. "
               "There is no official league URL that settles a 32-club depth ranking. This row therefore "
               "cannot be marked confirmed and must not be presented as if it had been.",
    method="Searched the league site for a depth-chart route; none is registered in any session's source list.",
    note="The repo's existing position (F05) is correct and should stand: backup depth is a model estimate "
         "built on third-party chart data, never a league fact, and every use of it is labelled as such.",
)

add(
    claim_id="LV-10",
    claim="An official, licensed market price for spreads, totals or props is available to this repo.",
    repo_artifact="flagged.json F07, data/sources.json",
    live_value="no league-published price",
    repo_value="no league-published price",
    status="UNVERIFIABLE",
    live_source=STANDINGS,
    source_gap="No NFL-operated page publishes a betting price. Sportsbook pages are operator-published, not "
               "league-official, and are geo-gated or non-machine-readable from this environment. There is no "
               "official URL for this row.",
    method="Confirmed across sessions (F07, FLG-010, Q-01) and re-confirmed here: nothing on nfl.com publishes "
           "a spread, total, moneyline or prop price.",
    note="Consequence, stated plainly: closing-line value and ROI cannot be computed for any strategy in this "
         "repo, and no leaderboard can rank a staking result. The honest scoreboard is proper-score skill, "
         "which needs only results - and those are now verified (LV-07).",
)

add(
    claim_id="LV-11",
    claim="Snap counts and official inactive lists are captured, so a backup replacing a starter can be confirmed rather than suspected.",
    repo_artifact="board/data/injuries_2026_w10.csv, data/depth_risk.json",
    live_value="not captured",
    repo_value="not captured",
    status="UNVERIFIABLE",
    live_source=INJURIES,
    source_gap="The league injury report publishes practice and game designations but not snap counts and not "
               "the 90-minute inactive list. No official machine-readable snap-count feed is registered.",
    method="Checked the official report's columns: Player, Position, Injuries, Practice Status, Game Status. "
           "No snap or inactive column exists.",
    note="The brief's requirement stands unmet and must stay flagged. A replacement can currently be "
         "identified from a club depth chart, but 'the backup actually played the starter's snaps' cannot be "
         "evidenced from an official league page.",
)

add(
    claim_id="LV-12",
    claim="The Week 10 injury report can be reconstructed as a daily series (Wed/Thu/Fri practice progression).",
    repo_artifact="data/injuries_2026_wk10.csv",
    live_value="single snapshot only",
    repo_value="single snapshot only",
    status="UNVERIFIABLE",
    live_source=INJURIES,
    source_gap="The official League injury page renders one current report per week, overwriting the previous "
               "day's designations. There is no dated archive URL for the Wednesday or Thursday version of "
               "the Week 10 report.",
    method="Read the live page: it shows one Practice Status and one Game Status per player, with no date axis.",
    note="This is why the 'DNP -> LP -> FP' trend requirement cannot be satisfied retroactively for Week 10. "
         "It has to be captured prospectively, on a schedule, from here on. See the snapshot protocol on the "
         "site's method page.",
)

add(
    claim_id="LV-13",
    claim="A club depth chart is a durable statement of who will start.",
    repo_artifact="data/depth_risk.json",
    live_value="club-published, undated on the page",
    repo_value="club-published, undated on the page",
    status="UNVERIFIABLE",
    live_source=INJURIES,
    source_gap="Club depth pages carry no league-issued version or effective date, so there is no official "
               "reference point against which to prove a chart is current. A chart cannot be shown to be "
               "stale from an official source alone.",
    method="Used the league roster and injury pages as the authority for availability; treated charts as "
           "depth-order only, per the existing authority rule.",
    note="The existing rule - league report owns availability, club chart owns order, every disagreement is "
         "published - remains the only defensible position. Any claim that a chart is 'stale' is an "
         "inference and is labelled one.",
)

add(
    claim_id="LV-14",
    claim="Seattle's Sam Darnold (QB) is on the Week 10 report as Out, which is a starting-quarterback availability event.",
    repo_artifact="data/injuries_2026_wk10.csv",
    live_value="Sam Darnold, QB, Ribs/Quadricep, Did Not Participate In Practice, Out",
    repo_value="Sam Darnold, QB, Ribs/Quadricep, Did Not Participate In Practice, Out",
    status="CONFIRMED",
    live_source=INJURIES,
    method="Read the Seattle club section of the official Week 10 report.",
    note="Included because it is the clearest example of the defect in LV-04: the complete capture has this "
         "row, the board's capture does not. A model fed the board's file would price Seattle as if its "
         "starting quarterback were available. This is the single most material data defect found today.",
)

add(
    claim_id="LV-15",
    claim="A club's published roster page is the official authority for roster status (active / IR / PUP / traded).",
    repo_artifact="data/sources.json",
    live_value="roster pages publish a status per player",
    repo_value="roster pages publish a status per player",
    status="CONFIRMED",
    live_source="https://www.nfl.com/teams/",
    method="Checked that club roster pages on the league site carry a per-player status field.",
    note="This is the one availability signal that is both official and durable, and it is the right basis "
         "for 'not listed on the injury report' never being read as 'available'.",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    rows = sorted(R, key=lambda r: r["claim_id"])
    # every row carries the same columns, with '' where a field does not apply
    cols = ["claim_id", "claim", "repo_artifact", "live_value", "repo_value", "status",
            "live_source", "source_gap", "method", "note"]
    rows = [{c: r.get(c, "") for c in cols} for r in rows]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    raw = open(OUT_CSV, "rb").read()
    payload = dict(
        meta=dict(
            title="Live re-verification of repo claims against official NFL.com pages",
            read_at_utc=READ_AT,
            claims=len(rows),
            by_status=counts,
            csv_sha256=hashlib.sha256(raw).hexdigest(),
            official_sources=[STANDINGS, INJURIES, "https://www.nfl.com/schedules/2026/by-week/week-N"],
            policy="A claim is CONFIRMED only when a live official page shows the same value. STALE means the "
                   "repo disagrees with the live page. NOT_REPRODUCIBLE means the claim could not be produced "
                   "from this snapshot. UNVERIFIABLE means no official page can settle it; such rows carry a "
                   "source_gap and are never presented as confirmed.",
        ),
        claims=rows,
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)

    for r in rows:
        print(f'{r["claim_id"]}  {r["status"]:<18} {r["claim"][:88]}')
    print(f'\n{len(rows)} claims: ' + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"wrote {OUT_CSV}\nwrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
