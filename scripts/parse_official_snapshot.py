#!/usr/bin/env python3
"""Parse one immutable official injury-report capture into a row table.

Input : the newest row in snapshots/index.csv with report=injuries, week=N, result=captured.
        Its raw body is snapshots/raw/injuries/regN/<file>.html.gz (written by
        scripts/capture_official_snapshot.py, never overwritten).
Output: data/official_injury_capture_wk<N>_2026.csv   (one row per listed player; the board copies it)
        snapshots/parsed/injuries_reg<N>_<stamp>.summary.json (counts, pins, checks)

Every row carries the raw file's SHA-256, so each value can be replayed from the
exact bytes that were read. Nothing is inferred: a blank cell stays blank.

Pinned checks (any failure exits 2 and writes nothing):
  * the gzip body's SHA-256 equals the index row's sha256 (immutability);
  * the number of club sections equals the number of clubs named by the matchup strips;
  * the matchup strips form whole game pairs (an even count, two clubs per game);
  * every player row has a name, a position and a practice status (required fields);
  * the number of parsed rows equals the number of Practice Status cells in the body.

Standard library only.
"""
import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "snapshots" / "index.csv"
PARSED_DIR = ROOT / "snapshots" / "parsed"
OUT_TABLE_TMPL = "data/official_injury_capture_wk{week}_2026.csv"
SOURCE_ID_TMPL = {11: "SRC-037"}  # week -> row in board/data/sources.csv (checked below)

STRIP_ABBR = re.compile(
    r'nfl-c-matchup-strip__team-abbreviation">\s*([A-Z]{2,3})\s*</span>\s*'
    r'<a class="nfl-c-matchup-strip__team-fullname" href="/teams/[^"]+/" aria-label="[^"]*">\s*([^<]+?)\s*</a>'
)
SECTION = re.compile(r'd3-o-section-sub-title"><span>([^<]+)</span>')
ROW = re.compile(
    r'<tr><td scope="row"[^>]*><a href="/players/([^/"]+)/"[^>]*>\s*([^<]*?)\s*</a></td>'
    r'<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td></tr>'
)
PRACTICE_CELL = re.compile(
    r"Did Not Participate In Practice|Limited Participation in Practice|Full Participation in Practice"
)
COLUMNS = ["capture_utc", "raw_sha256", "raw_path", "game_pair_as_printed", "club_abbr", "club_name",
           "player", "player_profile_slug", "position", "injuries", "practice_status", "game_status",
           "source_id", "source_url"]


class Fail(Exception):
    pass


def latest_capture(week: int, sha12: str = None):
    """Newest captured row for the week, or the one whose SHA-256 starts with sha12."""
    rows = []
    with INDEX.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["report"] == "injuries" and r["week"] == str(week) and r["result"] == "captured":
                if sha12 is None or r["sha256"].startswith(sha12):
                    rows.append(r)
    if not rows:
        raise Fail(f"no captured injuries/week {week} row" + (f" with sha256 {sha12}" if sha12 else "")
                   + f" in {INDEX.relative_to(ROOT)}")
    return rows[-1]


def parse(text: str, week: int):
    """Return (game_pairs, clubs, rows, sections_with_table, no_injury_sections)."""
    strips = STRIP_ABBR.findall(text)
    if len(strips) % 2:
        raise Fail(f"odd number of matchup strips ({len(strips)}): game pairs cannot be formed")
    abbr_to_name = {}
    for abbr, nick in strips:
        if abbr_to_name.get(abbr, nick) != nick:
            raise Fail(f"club {abbr} printed with two names")
        abbr_to_name[abbr] = nick
    name_to_abbr = {v: k for k, v in abbr_to_name.items()}
    if len(name_to_abbr) != len(abbr_to_name):
        raise Fail("two clubs share one nickname")
    pairs = []
    for i in range(0, len(strips), 2):
        a, h = strips[i][0], strips[i + 1][0]
        pairs.append(f"{a} at {h}")

    heads = list(SECTION.finditer(text))
    rows, with_table, no_inj = [], [], []
    for idx, m in enumerate(heads):
        club_nick = m.group(1).strip()
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(text)
        seg = text[m.end():end]
        if club_nick not in name_to_abbr:
            raise Fail(f"section '{club_nick}' has no matchup strip")
        abbr = name_to_abbr[club_nick]
        if "No Injuries Reported" in seg[:600]:
            no_inj.append(abbr)
            continue
        if "<table" not in seg:
            raise Fail(f"section {abbr} has neither a table nor 'No Injuries Reported'")
        with_table.append(abbr)
        pair = next((p for p in pairs if abbr in p.split(" at ")), "")
        for slug, name, pos, inj, prac, game in ROW.findall(seg):
            rows.append({
                "game_pair_as_printed": pair, "club_abbr": abbr, "club_name": club_nick,
                "player": name, "player_profile_slug": slug, "position": pos.strip(),
                "injuries": inj.strip(), "practice_status": prac.strip(), "game_status": game.strip(),
            })
    return pairs, sorted(name_to_abbr.values()), rows, with_table, no_inj


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--sha12", help="parse the capture whose SHA-256 starts with this (default: newest)")
    ap.add_argument("--out", help="write the table here instead of the canonical data/ path (comparisons)")
    args = ap.parse_args(argv)
    try:
        cap = latest_capture(args.week, args.sha12)
        src_id = SOURCE_ID_TMPL.get(args.week)
        registered = {r["source_id"]: r for r in csv.DictReader(open(ROOT / "board/data/sources.csv", encoding="utf-8", newline=""))}
        if src_id not in registered or registered[src_id]["url"] != cap["url"]:
            raise Fail(f"source {src_id} for week {args.week} is not registered with URL {cap['url']}")
        raw = ROOT / cap["raw_path"]
        body = gzip.open(raw).read()
        sha = hashlib.sha256(body).hexdigest()
        if sha != cap["sha256"]:
            raise Fail(f"raw body SHA-256 {sha} != index {cap['sha256']} (immutability broken)")
        text = body.decode("utf-8", errors="replace")
        pairs, clubs, rows, with_table, no_inj = parse(text, args.week)

        if len(clubs) != 2 * len(pairs):
            raise Fail(f"{len(clubs)} clubs but {len(pairs)} game pairs")
        sections = len(with_table) + len(no_inj)
        if sections != len(clubs):
            raise Fail(f"{sections} club sections for {len(clubs)} clubs on the matchup strips")
        if len(set(with_table + no_inj)) != sections:
            raise Fail("a club appears in two sections")
        for r in rows:
            if not r["player"] or not r["position"] or not r["practice_status"]:
                raise Fail(f"required field missing in row {r}")
        cells = len(PRACTICE_CELL.findall(text))
        if cells != len(rows):
            raise Fail(f"{len(rows)} parsed rows but {cells} Practice Status cells in the body")
    except Fail as e:
        print(f"PARSE FAILURE (week {args.week}): {e}", file=sys.stderr)
        return 2

    out_rows = []
    for r in rows:
        out_rows.append({
            "capture_utc": cap["capture_utc"], "raw_sha256": cap["sha256"], "raw_path": cap["raw_path"],
            "source_id": src_id, "source_url": cap["url"], **r,
        })
    out = Path(args.out) if args.out else ROOT / OUT_TABLE_TMPL.format(week=args.week)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    stamp = Path(cap["raw_path"]).name.split("_")[0]
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "week": args.week,
        "capture_utc": cap["capture_utc"],
        "raw_path": cap["raw_path"],
        "raw_sha256": cap["sha256"],
        "raw_bytes": len(body),
        "source_url": cap["url"],
        "game_pairs": pairs,
        "clubs_on_strips": len(clubs),
        "club_sections_with_table": len(with_table),
        "club_sections_no_injuries_reported": sorted(no_inj),
        "clubs_without_section": sorted(set(clubs) - set(with_table) - set(no_inj)),
        "player_rows": len(rows),
        "practice_status_cells": cells,
        "rows_missing_game_status": sum(1 for r in rows if not r["game_status"]),
        "game_status_counts": {k: sum(1 for r in rows if r["game_status"] == k)
                               for k in sorted({r["game_status"] for r in rows})},
        "output_table": OUT_TABLE_TMPL.format(week=args.week) if not args.out else str(args.out),
        "checks": "all pinned checks passed",
    }
    if not args.out:
        (PARSED_DIR / f"injuries_reg{args.week}_{stamp}.summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"parsed {len(rows)} rows from {cap['raw_path']} (sha256 {cap['sha256'][:12]})")
    print(f"clubs: {len(clubs)} on strips, {len(with_table)} with a table, {len(no_inj)} 'No Injuries Reported'")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
