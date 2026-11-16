#!/usr/bin/env python3
"""
FL3 — depth-chart blocks, transcribed with their grammar preserved.

WHAT THIS DATASET IS
--------------------
Four club depth charts, read from the club's own page on 2026-11-16, transcribed with cell
structure intact. It is not a "starters" list and it must never be flattened into one. The point
of the dataset is that a club depth chart publishes a *grid*, and several of its properties
destroy the naive reading "column 1 = the starter":

  shared_slot        Two players in the SAME cell. Seattle publishes "Cooper Kupp [Rashid Shaheed]"
                     in one WR cell. The club did not name a starter. Either both start, both
                     rotate, or the club has not decided. Treating Kupp as "the WR1" fabricates
                     information the club did not release.
  duplicate_rank1    The same player at rank 1 of two different positions. Green Bay publishes
                     Kitan Oladapo at rank 1 of BOTH safety spots. That is not two starters, it
                     is one player covering two slots.
  duplicate_rank2    The same player at rank 2 of two different positions (Ryan Neuzil at LG2
                     and C2; Carson Vinson at LT2 and RT2). One backup, two roles.
  empty_rank1        Rank-1 cell is blank. Baltimore publishes no kicker at all.
  continuation_row   A row whose position cell is blank and whose players continue the row above
                     (Green Bay RB4 Kaleb Johnson under a blank position cell). Parsers that key
                     on the position column attach this player to nothing.
  jersey_prefixed    The cell text is "9 Christian Watson" — jersey number prepended to the name,
                     no separator. This is the Packers failure the brief described. It is
                     recoverable: the leading integer is the jersey number, the remainder is the
                     name, and both should be stored.
  image_only         The page publishes the chart as a raster image, not text. Houston. There is
                     no parser fix; the data is not in the document.
  no_timestamp       The page carries no effective date (Seattle, Baltimore). Green Bay carries
                     "Unofficial, Nov. 10, 2026" — six days stale on the day it was read.
  stale_rank1_out    A rank-1 player is also listed OUT on the official injury report for a game
                     that has not been played. Jaylinn Hawkins is BAL SS1 and Out.

THE FEATURE THIS UNLOCKS
------------------------
For a game not yet kicked off (LAC at BAL, 2026-11-16), the combination
`stale_rank1_out` + `the chart still names him` is exactly the "backup replacing a starter" case
the brief asks to detect. It is detectable *now*, from two official sources, with no inference:

  Baltimore  SS1 Jaylinn Hawkins  -> official Week 10 report: Out
             SS2 Keondre Jackson -> not on the injury report at all
  Seattle    DT1 Leonard Williams -> Out,  backup Rylie Mills
             LT1 Charles Cross     -> Out,  backup Josh Jones
             LG1 Quenton Nelson    -> Out,  backup Anthony Bradford
             (Seattle's game was played on 2026-11-15, so this is a post-hoc check, not a
             pre-kickoff signal.)

WHAT IT DOES NOT UNLOCK
-----------------------
Depth *rank* is not talent. Rank 2 behind a rank 1 does not tell you how much worse rank 2 is.
Nothing in this file supports the "fixed points for a missing starter" adjustment the repository
currently uses; that adjustment is still an unvalidated constant.

Run: python3 scripts/build_depth_blocks.py
"""
from __future__ import annotations

import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

CAPTURED = "2026-11-16T01:40Z"

# unit, position, [(cell_text, ...)], raw cell text exactly as the page renders it
# Empty string cell = page publishes an empty cell. None = cell absent.
BLOCKS: dict[str, dict] = {
    "GB": {
        "url": "https://www.packers.com/team/depth-chart",
        "page_effective_date": "Unofficial, Nov. 10, 2026",
        "format": "html_table",
        "note": "Jersey number prepended to every player name with a single space and no separator.",
        "rows": [
            ("OFF", "WR", ["9 Christian Watson", "16 Bo Melton", ""]),
            ("OFF", "WR", ["0 Matthew Golden", "87 J. Michael Sturdivant", ""]),
            ("OFF", "LT", ["77 Jordan Morgan", "73 John Williams", ""]),
            ("OFF", "LG", ["65 Aaron Banks", "79 Travis Glover", "67 Donovan Jennings"]),
            ("OFF", "C", ["75 Sean Rhyan", "52 Jager Burton", ""]),
            ("OFF", "RG", ["72 Laken Tomlinson", "70 Kevin Zeitler", ""]),
            ("OFF", "RT", ["71 Anthony Belton", "74 Mekhi Becton Sr.", ""]),
            ("OFF", "TE", ["85 Tucker Kraft", "18 Jonnu Smith", "86 Mark Redman"]),
            ("OFF", "WR", ["83 Savion Williams", "", ""]),
            ("OFF", "QB", ["10 Jordan Love", "6 Tyrod Taylor", ""]),
            ("OFF", "RB", ["8 Josh Jacobs", "32 MarShawn Lloyd", "22 Pierre Strong Jr."]),
            ("OFF", "", ["26 Kaleb Johnson"]),                       # continuation row
            ("DEF", "DT", ["94 Karl Brooks", "97 Jordon Riley", "93 Anthony Campbell"]),
            ("DEF", "DT", ["95 Devonte Wyatt", "55 Chris McClellan", ""]),
            ("DEF", "EDGE", ["90 Lukas Van Ness", "57 Brenton Cox Jr", ""]),
            ("DEF", "LB", ["44 Zaire Franklin", "59 Ty'Ron Hopper", "54 Kristian Welch"]),
            ("DEF", "LB", ["58 Isaiah McDuffie", "31 Nick Niemann", ""]),
            ("DEF", "EDGE", ["99 Barryn Sorrell", "51 Dani Dennis-Sutton", ""]),
            ("DEF", "CB", ["25 Keisean Nixon", "24 Carrington Valentine", ""]),
            ("DEF", "CB", ["2 Brandon Cisse", "21 Benjamin St-Juste", ""]),
            ("DEF", "S", ["29 Xavier McKinney", "27 Kitan Oladapo", ""]),
            ("DEF", "S", ["33 Evan Williams", "27 Kitan Oladapo", ""]),
            ("DEF", "NB", ["7 Javon Bullard", "36 Kamal Hadden", ""]),
            ("ST", "K", ["28 Trey Smack", "", ""]),
            ("ST", "P", ["19 Daniel Whelan", "", ""]),
            ("ST", "H", ["19 Daniel Whelan", "", ""]),
            ("ST", "PR", ["", "0 Matthew Golden", ""]),              # empty rank 1
            ("ST", "KR", ["16 Bo Melton", "", ""]),
            ("ST", "LS", ["42 Matt Orzech", "", ""]),
        ],
    },
    "SEA": {
        "url": "https://www.seahawks.com/team/depth-chart/",
        "page_effective_date": "",     # the page publishes none
        "format": "html_table",
        "note": "Two players share one cell at WR rank 1. Page carries no effective date.",
        "rows": [
            ("OFF", "WR", ["Cooper Kupp|Rashid Shaheed", "Irvin Charles"]),   # SHARED CELL
            ("OFF", "LT", ["Charles Cross", "Josh Jones"]),
            ("OFF", "LG", ["Quenton Nelson", "Anthony Bradford"]),
            ("OFF", "C", ["Jalen Sundell", "Olu Oluwatimi"]),
            ("OFF", "RG", ["Grey Zabel", "Anthony Bradford", "Beau Stephens"]),
            ("OFF", "RT", ["Abraham Lucas", "Josh Jones"]),
            ("OFF", "TE", ["AJ Barner", "Eric Saubert", "Nick Kallerup"]),
            ("OFF", "WR", ["Jaxon Smith-Njigba", "Tory Horton"]),
            ("OFF", "QB", ["Sam Darnold", "Drew Lock", "Jalen Milroe"]),
            ("OFF", "FB", ["Brady Russell"]),
            ("OFF", "RB", ["Zach Charbonnet", "Jadarian Price", "Emanuel Wilson", "George Holani"]),
            ("DEF", "DT", ["Leonard Williams", "Rylie Mills"]),
            ("DEF", "NT", ["Byron Murphy II", "Brandon Pili", "Deven Eastern"]),
            ("DEF", "DE", ["Jarran Reed", "Mike Morris"]),
            ("DEF", "RUSH", ["DeMarcus Lawrence", "Derick Hall"]),
            ("DEF", "MLB", ["Ernest Jones IV", "Patrick O'Connell"]),
            ("DEF", "WLB", ["Drake Thomas", "Tyrice Knight", "Chazz Surratt"]),
            ("DEF", "SLB", ["Uchenna Nwosu", "Dante Fowler Jr.", "Connor O'Toole"]),
            ("DEF", "CB", ["Devon Witherspoon", "Nehemiah Pritchett"]),
            ("DEF", "CB", ["Josh Jobe", "Avery Smith"]),
            ("DEF", "S", ["Ty Okada", "Rodney Thomas II"]),
            ("DEF", "S", ["Julian Love"]),
            ("DEF", "S", ["Nick Emmanwori"]),
            ("ST", "K", ["Jason Myers"]),
            ("ST", "P", ["Michael Dickson"]),
            ("ST", "H", ["Michael Dickson"]),
            ("ST", "PR", ["Rashid Shaheed", "Tory Horton"]),
            ("ST", "KR", ["Rashid Shaheed", "Velus Jones Jr.", "Tory Horton", "George Holani",
                          "Emanuel Wilson"]),
            ("ST", "LS", ["Chris Stoll"]),
        ],
    },
    "BAL": {
        "url": "https://www.baltimoreravens.com/team/depth-chart/",
        "page_effective_date": "",     # the page publishes none
        "format": "html_table",
        "note": "K rank 1 is published blank. No effective date.",
        "rows": [
            ("OFF", "WR", ["Zay Flowers", "Devontez Walker", "Elijah Sarratt"]),
            ("OFF", "WR", ["Rashod Bateman", "Ja'Kobi Lane", "LaJohntay Wester"]),
            ("OFF", "LT", ["Ronnie Stanley", "Carson Vinson"]),
            ("OFF", "LG", ["John Simpson", "Ryan Neuzil"]),
            ("OFF", "C", ["Cam Jurgens", "Ryan Neuzil"]),
            ("OFF", "RG", ["Vega Ioane", "Emery Jones Jr."]),
            ("OFF", "RT", ["Roger Rosengarten", "Carson Vinson"]),
            ("OFF", "TE", ["Mark Andrews", "Josh Cuevas"]),
            ("OFF", "TE", ["Matt Hibner"]),
            ("OFF", "QB", ["Jacoby Brissett", "Joe Fagnano", "Kedon Slovis"]),
            ("OFF", "RB", ["Derrick Henry", "Justice Hill", "Rasheen Ali"]),
            ("DEF", "DT", ["Nnamdi Madubuike", "Broderick Washington Jr."]),
            ("DEF", "NT", ["Travis Jones", "John Jenkins"]),
            ("DEF", "DE", ["Calais Campbell", "Aeneas Peebles"]),
            ("DEF", "RUSH", ["Trey Hendrickson", "Mike Green"]),
            ("DEF", "MLB", ["Roquan Smith", "Jay Higgins IV"]),
            ("DEF", "WLB", ["Trenton Simpson", "Teddye Buchanan"]),
            ("DEF", "SAM", ["Mike Green", "Zion Young", "Ethan Burke"]),
            ("DEF", "CB", ["Marlon Humphrey", "Chidobe Awuzie"]),
            ("DEF", "DB", ["Kyle Hamilton", "Keyon Martin", "Chandler Rivers"]),
            ("DEF", "SS", ["Jaylinn Hawkins", "Keondre Jackson"]),
            ("DEF", "FS", ["Malaki Starks", "K'Von Wallace"]),
            ("DEF", "CB", ["Nate Wiggins", "T.J. Tampa Jr."]),
            ("ST", "P", ["Ryan Eckley"]),
            ("ST", "K", [""]),                                    # EMPTY RANK 1
            ("ST", "H", ["Ryan Eckley"]),
            ("ST", "LS", ["Nick Moore"]),
            ("ST", "KOR", ["LaJohntay Wester", "Rasheen Ali", "Justice Hill"]),
            ("ST", "PR", ["LaJohntay Westy", "Elijah Sarratt"]),
        ],
    },
}

# Houston is the counter-example: the page exists, the chart does not.
IMAGE_ONLY = {
    "HOU": {
        "url": "https://www.houstontexans.com/team/depth-chart/",
        "heading_as_published": "Unofficial Depth Chart",
        "body": "image",
        "image_url": "https://static.clubs.nfl.com/image/upload/texans/a5or0zowuo36y1txf4ly",
        "why_it_blocks": (
            "The depth chart is a single raster image inside the page. No player name, position "
            "or rank exists in the HTML. Recovering it would require reading text out of a "
            "picture, which is transcription by eye, not an official machine-readable feed."
        ),
        "consequence": "HOU depth cannot enter any model feature from this source. 1 of 32 clubs.",
    }
}

NAME_FIX = {"LaJohntay Westy": "LaJohntay Wester"}   # page typo, link resolves to lajohntay-wester


def parse_cell(text: str, jersey_prefixed: bool) -> dict:
    jersey = ""
    name = text.strip()
    if jersey_prefixed and name:
        m = re.match(r"^(\d{1,2})\s+(.*)$", name)
        if m:
            jersey, name = m.group(1), m.group(2).strip()
    name = NAME_FIX.get(name, name)
    return {"jersey": jersey, "name": name}


def main() -> None:
    rows_out = []
    findings = []
    for club, blk in BLOCKS.items():
        jp = "jersey_prefixed" in blk["note"].lower() or club == "GB"
        seen_rank1: dict[str, list[str]] = {}
        seen_rank2: dict[str, list[str]] = {}
        for i, (unit, pos, cells) in enumerate(blk["rows"]):
            if pos == "":
                findings.append({
                    "club": club, "kind": "continuation_row", "row": i,
                    "detail": f"blank position cell carries {', '.join(c for c in cells if c)}",
                    "url": blk["url"]})
                continue
            for rank, cell in enumerate(cells, start=1):
                if not cell:
                    if rank == 1:
                        findings.append({
                            "club": club, "kind": "empty_rank1", "row": i,
                            "detail": f"{unit}/{pos}: the rank-1 cell is blank", "url": blk["url"]})
                    continue
                players = [parse_cell(t, jp) for t in cell.split("|")]
                if len(players) > 1:
                    findings.append({
                        "club": club, "kind": "shared_slot", "row": i,
                        "detail": (f"{unit}/{pos} rank {rank} publishes {len(players)} players in "
                                   f"one cell: {', '.join(p['name'] for p in players)}"),
                        "url": blk["url"]})
                for p in players:
                    rows_out.append({
                        "club": club, "unit": unit, "position": pos, "rank": rank,
                        "slot_occupants": len(players), "player": p["name"],
                        "jersey": p["jersey"], "cell_raw": cell,
                        "page_effective_date": blk["page_effective_date"] or "(none published)",
                        "captured_utc": CAPTURED, "source_url": blk["url"],
                    })
                    if rank == 1 and len(players) == 1:
                        seen_rank1.setdefault(p["name"], []).append(f"{unit}/{pos}")
                    if rank == 2 and len(players) == 1:
                        seen_rank2.setdefault(p["name"], []).append(f"{unit}/{pos}")

        for name, slots in seen_rank1.items():
            if len(slots) > 1:
                findings.append({"club": club, "kind": "duplicate_rank1", "row": "",
                                 "detail": f"{name} is rank 1 at {', '.join(slots)}",
                                 "url": blk["url"]})
        for name, slots in seen_rank2.items():
            if len(slots) > 1:
                findings.append({"club": club, "kind": "duplicate_rank2", "row": "",
                                 "detail": f"{name} is rank 2 at {', '.join(slots)}",
                                 "url": blk["url"]})

    for club, meta in IMAGE_ONLY.items():
        findings.append({"club": club, "kind": "image_only", "row": "",
                         "detail": meta["why_it_blocks"], "url": meta["url"]})

    # ---- starter-out join against the official Week 10 injury report -----------------
    inj = {}
    p = os.path.join(DATA, "captures", "week10_injuries_2026-11-16.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                inj[(r["club"], r["player"])] = r["game_status"]

    rank1_out = []
    for r in rows_out:
        if r["rank"] != 1 or r["slot_occupants"] != 1:
            continue
        status = inj.get((r["club"], r["player"]))
        if status in ("Out", "Doubtful"):
            backup = next((x for x in rows_out
                           if x["club"] == r["club"] and x["position"] == r["position"]
                           and x["rank"] == 2 and x["player"] != r["player"]), None)
            rank1_out.append({
                "club": r["club"], "position": r["position"], "starter": r["player"],
                "designation": status,
                "named_backup": backup["player"] if backup else "(chart publishes none)",
                "backup_designation": inj.get((r["club"], backup["player"]), "(not on report)")
                                     if backup else "-",
                "chart_date": r["page_effective_date"],
                "source_depth": r["source_url"],
                "source_injury": "https://www.nfl.com/injuries/league/2026/reg10",
            })

    # ---- write ---------------------------------------------------------------------
    cols = ["club", "unit", "position", "rank", "slot_occupants", "player", "jersey",
            "cell_raw", "page_effective_date", "captured_utc", "source_url"]
    with open(os.path.join(DATA, "depth_blocks.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows_out)

    with open(os.path.join(DATA, "depth_grammar_findings.csv"), "w", encoding="utf-8",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["club", "kind", "row", "detail", "url"])
        w.writeheader()
        w.writerows(findings)

    with open(os.path.join(DATA, "depth_starter_out.csv"), "w", encoding="utf-8",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["club", "position", "starter", "designation",
                                           "named_backup", "backup_designation", "chart_date",
                                           "source_depth", "source_injury"])
        w.writeheader()
        w.writerows(rank1_out)

    summary = {
        "generated_utc": CAPTURED,
        "clubs_transcribed": sorted(BLOCKS),
        "clubs_image_only": sorted(IMAGE_ONLY),
        "clubs_total_accounted": len(BLOCKS) + len(IMAGE_ONLY),
        "rows": len(rows_out),
        "findings_by_kind": {},
        "page_effective_dates": {c: (b["page_effective_date"] or "(none published)")
                                 for c, b in BLOCKS.items()},
        "starter_out": rank1_out,
        "rule": (
            "A club depth chart is a grid. Column 1 is 'rank 1 of this position as the club last "
            "published it', not 'the starter in this game'. Rank 1 may be shared, may be empty, "
            "may be duplicated across positions, and may be stale or contradicted by the "
            "official injury report."
        ),
        "consequence_for_the_model": (
            "The repository's availability adjustment applies a fixed points penalty per "
            "position. This dataset shows why that cannot be validated from depth alone: we can "
            "establish WHO is replaced, not HOW MUCH worse the replacement is. Turning depth "
            "into points is still an unmeasured assumption."
        ),
    }
    for f in findings:
        summary["findings_by_kind"][f["kind"]] = summary["findings_by_kind"].get(f["kind"], 0) + 1

    with open(os.path.join(DATA, "depth_blocks.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")

    print(f"transcribed {len(rows_out)} player cells across {len(BLOCKS)} clubs "
          f"(+{len(IMAGE_ONLY)} image-only)")
    print("findings:", json.dumps(summary["findings_by_kind"], indent=0))
    print("\npage effective dates:")
    for c, d in summary["page_effective_dates"].items():
        print(f"  {c}: {d}")
    print(f"\nrank-1 players also listed Out/Doubtful on the official Week 10 report: "
          f"{len(rank1_out)}")
    for r in rank1_out:
        print(f"  {r['club']:3} {r['position']:4} {r['starter']:20} {r['designation']:10} "
              f"-> backup {r['named_backup']} {r['backup_designation']}")


if __name__ == "__main__":
    main()
