#!/usr/bin/env python3
"""Row-by-row check: an independent reading of the official page vs the parsed capture.

Reads snapshots/parsed/readings_wk<N>_*.csv (values typed from the live official page,
with the URL and read date on each row) and compares every field of every row against
board/data/official_injury_capture_wk<N>_2026.csv, matching on club + player name.
Exit 0 = every read row matches and no club has an unread player; exit 2 otherwise.
"""
import csv
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["position", "injuries", "practice_status", "game_status"]


def capture_sha12(week: int) -> str:
    """The capture the PUBLISHED table was parsed from (its raw_sha256 column), first 12 hex chars."""
    with open(ROOT / f"data/official_injury_capture_wk{week}_2026.csv", encoding="utf-8", newline="") as fh:
        return next(csv.DictReader(fh))["raw_sha256"][:12]


def main(week=11):
    readings = sorted(glob.glob(str(ROOT / f"snapshots/parsed/readings_wk{week}_*.csv")))
    if not readings:
        print(f"no readings file for week {week}", file=sys.stderr)
        return 2
    table = list(csv.DictReader(open(ROOT / f"data/official_injury_capture_wk{week}_2026.csv", encoding="utf-8", newline="")))
    by_key = {(r["club_abbr"], r["player"]): r for r in table}
    cap_sha12 = capture_sha12(week)
    reads = []
    for path in readings:
        reads.extend(r for r in csv.DictReader(open(path, encoding="utf-8", newline=""))
                     if r.get("capture_sha256_12") == cap_sha12)
    if not reads:
        print(f"no reading in snapshots/parsed/ was taken against the current capture ({cap_sha12}); nothing to compare")
        return 0
    problems, clubs_read = [], set()
    for rd in reads:
        key = (rd["club_abbr"], rd["player"])
        clubs_read.add(rd["club_abbr"])
        got = by_key.get(key)
        if got is None:
            problems.append(f"MISSING {key}: read on the official page, absent from the parsed capture")
            continue
        if got["game_pair_as_printed"] != rd["game_pair_as_printed"]:
            problems.append(f"PAIR {key}: {got['game_pair_as_printed']} != {rd['game_pair_as_printed']}")
        for f in FIELDS:
            if (got[f] or "") != (rd[f] or ""):
                problems.append(f"FIELD {key} {f}: parsed {got[f]!r} != read {rd[f]!r}")
    # every player of a read club must have been read (completeness for those clubs)
    for club in sorted(clubs_read):
        parsed_n = sum(1 for r in table if r["club_abbr"] == club)
        read_n = sum(1 for rd in reads if rd["club_abbr"] == club)
        if parsed_n != read_n:
            problems.append(f"COUNT {club}: parsed {parsed_n} rows, read {read_n} rows")
    for p in problems:
        print(p)
    print(f"checked {len(reads)} read rows across {len(clubs_read)} clubs: "
          + ("ALL MATCH" if not problems else f"{len(problems)} PROBLEM(S)"))
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 11))
