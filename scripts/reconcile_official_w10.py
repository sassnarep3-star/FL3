#!/usr/bin/env python3
"""Reconcile the published Week 10 injury tables against the official capture.

Reads the official capture written from https://www.nfl.com/injuries/league/2026/reg10
(data/official/2026-w10-injury-report.csv) and compares every published copy of the
Week 10 report with it, row by row, on (club, player). Writes one row per difference
to data/official/2026-w10-reconciliation.csv and prints a summary.

Exit status is non-zero if the official capture itself fails its pinned checks, so a
broken capture can never be quietly reconciled. Differences in the *published* copies
are expected output (they are the point of the audit) and do not fail the script.

Standard library only. Deterministic: no timestamps are written into the output.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = ROOT / "data/official/2026-w10-injury-report.csv"
OUT = ROOT / "data/official/2026-w10-reconciliation.csv"
SOURCE_URL = "https://www.nfl.com/injuries/league/2026/reg10"

# Pinned expectations for the official capture (transcribed from the page on 2026-11-16:
# 14 games, 28 clubs, 347 player rows). A change here is a deliberate re-capture, not a fix.
PINNED = {"rows": 347, "games": 14, "clubs": 28}
ALLOWED_PRACTICE = {
    "Full Participation in Practice",
    "Limited Participation in Practice",
    "Did Not Participate In Practice",
}
ALLOWED_GAME = {"", "Out", "Questionable", "Doubtful"}


def load_official():
    rows = list(csv.DictReader(OFFICIAL.open(encoding="utf-8")))
    problems = []
    if len(rows) != PINNED["rows"]:
        problems.append(f"row count {len(rows)} != pinned {PINNED['rows']}")
    games = {r["game"] for r in rows}
    clubs = {r["team"] for r in rows}
    if len(games) != PINNED["games"]:
        problems.append(f"game count {len(games)} != pinned {PINNED['games']}")
    if len(clubs) != PINNED["clubs"]:
        problems.append(f"club count {len(clubs)} != pinned {PINNED['clubs']}")
    for r in rows:
        if r["practice_status"] not in ALLOWED_PRACTICE:
            problems.append(f"unknown practice status {r['practice_status']!r} for {r['player']}")
        if r["game_status"] not in ALLOWED_GAME:
            problems.append(f"unknown game status {r['game_status']!r} for {r['player']}")
        if r["src"] != "R10":
            problems.append(f"row {r['player']} lacks source code R10")
    keys = Counter((r["team"], r["player"]) for r in rows)
    dupes = [k for k, v in keys.items() if v > 1]
    if dupes:
        problems.append(f"duplicate club/player keys: {dupes}")
    return rows, problems


def load_published_csv_repo_root():
    """data/injuries_2026_wk10.csv: team, player, practice_status, game_status."""
    out = []
    path = ROOT / "data/injuries_2026_wk10.csv"
    for r in csv.DictReader(path.open(encoding="utf-8", newline="")):
        out.append((r["team"], r["player"], r["practice_status"], r["game_status"]))
    return "data/injuries_2026_wk10.csv", out


def load_published_board():
    """board/data/injuries_2026_w10.csv: team_abbr, player, practice_status, game_status."""
    out = []
    path = ROOT / "board/data/injuries_2026_w10.csv"
    for r in csv.DictReader(path.open(encoding="utf-8", newline="")):
        out.append((r["team_abbr"], r["player"], r["practice_status"], r["game_status"]))
    return "board/data/injuries_2026_w10.csv", out


def load_published_json():
    """data/injuries_week10.json: games[].teams[].players[]."""
    out = []
    data = json.loads((ROOT / "data/injuries_week10.json").read_text(encoding="utf-8"))
    for g in data["games"]:
        for t in g["teams"]:
            for p in t["players"]:
                out.append((t["abbr"], p["name"], p["practice"], p["game_status"]))
    return "data/injuries_week10.json", out


def reconcile(official_rows, label, published):
    off = {(r["team"], r["player"]): r for r in official_rows}
    pub = {}
    dup_pub = []
    for team, player, practice, game in published:
        if (team, player) in pub:
            dup_pub.append((team, player))
        pub[(team, player)] = (practice, game)
    diffs = []
    for key in sorted(set(off) | set(pub)):
        team, player = key
        o = off.get(key)
        p = pub.get(key)
        if o and not p:
            diffs.append([label, team, player, o["practice_status"], "", o["game_status"], "", "missing_from_published"])
        elif p and not o:
            diffs.append([label, team, player, "", p[0], "", p[1], "not_on_official_page"])
        else:
            kinds = []
            if o["practice_status"] != p[0]:
                kinds.append("practice_mismatch")
            if o["game_status"] != p[1]:
                kinds.append("game_status_mismatch")
            if kinds:
                diffs.append([label, team, player, o["practice_status"], p[0], o["game_status"], p[1], "+".join(kinds)])
    return diffs, dup_pub, len(published)


def main():
    official_rows, problems = load_official()
    if problems:
        print("OFFICIAL CAPTURE FAILED PINNED CHECKS:", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        return 1

    sources = [load_published_csv_repo_root(), load_published_board(), load_published_json()]
    all_diffs = []
    print(f"official capture: {len(official_rows)} rows, {PINNED['games']} games, {PINNED['clubs']} clubs")
    for label, published in sources:
        diffs, dup_pub, n = reconcile(official_rows, label, published)
        kinds = Counter(d[7] for d in diffs)
        print(f"\n{label}: {n} rows; differences: {len(diffs)}")
        for k, v in sorted(kinds.items()):
            print(f"   {k}: {v}")
        if dup_pub:
            print(f"   duplicate club/player keys in published copy: {len(dup_pub)}")
        all_diffs.extend(diffs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["published_source", "club", "player", "official_practice", "published_practice",
                    "official_game_status", "published_game_status", "difference", "official_src"])
        for d in all_diffs:
            w.writerow(d + [SOURCE_URL])
    print(f"\nwrote {OUT.relative_to(ROOT)} with {len(all_diffs)} difference rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
