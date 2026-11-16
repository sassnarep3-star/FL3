#!/usr/bin/env python3
"""
FL3 — snapshot staleness delta.

WHY THIS EXISTS
---------------
Every page on the site is stamped "official data read 2026-11-14 UTC". Today is 2026-11-16.
Week 10's Sunday slate has been played. So a reader arriving at the dashboard is shown a
standings table and an availability report that are, quietly, two days and one full round of
games out of date. Nothing in the repo measured that gap. This script does.

WHAT IT DOES
------------
1. Compares the checked-in 2026-11-14 standings (data/2026-standings.csv) against the
   2026-11-16 official re-capture (data/captures/standings_2026-11-16.csv), per club, per field.
2. Compares the checked-in injury report (data/injuries_2026_w10.csv) against the 2026-11-16
   re-capture (data/captures/week10_injuries_2026-11-16.csv): row counts, club coverage,
   per-player game-designation changes.
3. Writes data/snapshot_delta.csv + data/snapshot_delta.json for the site.

IT DELIBERATELY DOES NOT OVERWRITE THE OLD SNAPSHOT
---------------------------------------------------
Overwriting 2026-11-14 data with 2026-11-16 data would destroy the only pre-kickoff record this
repository has, and pre-kickoff records are the whole basis of a backtest. The delta is stored
*alongside*, versioned by date. Superseding the snapshot is an integration decision recorded in
COORDINATION.md, not a side effect of a measurement.

Run: python3 scripts/snapshot_delta.py
"""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CAP = os.path.join(DATA, "captures")

FIELDS = ["w", "l", "t", "pf", "pa", "net_pts", "games"]

# The two files were written by different sessions with different column capitalisation.
# Normalise on read; never rewrite the checked-in 2026-11-14 file to make a diff easier.
ALIASES = {"W": "w", "L": "l", "T": "t", "PF": "pf", "PA": "pa",
           "PCT": "pct", "win_pct": "pct"}


def read(path):
    with open(path, encoding="utf-8-sig") as fh:
        out = []
        for r in csv.DictReader(fh):
            out.append({ALIASES.get(k, k): v for k, v in r.items()})
        return out


def main() -> None:
    old = {r["team_key"]: r for r in read(os.path.join(DATA, "2026-standings.csv"))}
    new = {r["team_key"]: r for r in read(os.path.join(CAP, "standings_2026-11-16.csv"))}

    assert set(old) == set(new), "club set changed between snapshots - investigate before publishing"

    rows = []
    changed_clubs = 0
    for key in sorted(old):
        diffs = []
        for f in FIELDS:
            o, n = old[key][f], new[key][f]
            if str(o) != str(n):
                try:
                    delta = float(n) - float(o)
                    diffs.append(f"{f} {o}->{n} ({delta:+.0f})" if delta else f"{f} {o}->{n}")
                except ValueError:
                    diffs.append(f"{f} {o}->{n}")
        if diffs:
            changed_clubs += 1
        rows.append([key, old[key]["team"], len(diffs), "; ".join(diffs) or "no change"])

    print(f"standings: {changed_clubs}/{len(old)} clubs changed between 2026-11-14 and 2026-11-16")
    for r in rows:
        if r[2]:
            print(f"  {r[0]:4} {r[2]} field(s): {r[3]}")

    # ---- injury report delta -----------------------------------------------------
    oi = read(os.path.join(DATA, "injuries_2026_w10.csv"))
    ni = read(os.path.join(CAP, "week10_injuries_2026-11-16.csv"))
    oi_clubs = {r["team_abbr"] for r in oi}
    ni_clubs = {r["club"] for r in ni}

    def key(r, a, b):
        return (r[a], r[b])

    omap = {(r["team_abbr"], r["player"]): r["game_status"] for r in oi}
    nmap = {(r["club"], r["player"]): r["game_status"] for r in ni}

    only_old = sorted(set(omap) - set(nmap))
    only_new = sorted(set(nmap) - set(omap))
    status_changed = sorted(k for k in set(omap) & set(nmap) if omap[k] != nmap[k])

    print()
    print(f"injury report: checked-in {len(oi)} rows / {len(oi_clubs)} clubs "
          f"-> live {len(ni)} rows / {len(ni_clubs)} clubs")
    print(f"  clubs only in the checked-in file : {sorted(oi_clubs - ni_clubs) or 'none'}")
    print(f"  clubs only in the live capture    : {sorted(ni_clubs - oi_clubs) or 'none'}")
    print(f"  rows only in the checked-in file  : {len(only_old)}")
    print(f"  rows only in the live capture     : {len(only_new)}")
    print(f"  same player, changed designation  : {len(status_changed)}")
    for k in status_changed:
        print(f"      {k[0]} {k[1]}: {omap[k] or '(blank)'} -> {nmap[k] or '(blank)'}")

    # Two specific claims the brief asked to be checked against the live page.
    checks = []
    for club, player in [("DET", "Kerby Joseph"), ("DET", "Cade Mays"), ("DET", "D.J. Reed")]:
        checks.append((club, player, omap.get((club, player), "<absent>"),
                       nmap.get((club, player), "<absent>")))
    print()
    print("  the three Lions cells the brief flagged as blank:")
    for c, p, o, n in checks:
        print(f"      {c} {p}: checked-in file = {o or '(blank)'} | live page = {n or '(blank)'}")

    with open(os.path.join(DATA, "snapshot_delta.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["section", "key", "label", "n_changes", "detail", "source_old", "source_new"])
        for r in rows:
            w.writerow(["standings", r[0], r[1], r[2], r[3],
                        "https://www.nfl.com/standings/ (read 2026-11-14)",
                        "https://www.nfl.com/standings/league/2026/REG (read 2026-11-16)"])
        w.writerow(["injuries_summary", "rows", "player rows", len(ni) - len(oi),
                    f"{len(oi)} -> {len(ni)}",
                    "https://www.nfl.com/injuries/league/2026/reg10 (read 2026-11-14)",
                    "https://www.nfl.com/injuries/league/2026/reg10 (read 2026-11-16)"])
        w.writerow(["injuries_summary", "clubs", "clubs covered", len(ni_clubs) - len(oi_clubs),
                    f"{len(oi_clubs)} -> {len(ni_clubs)}", "", ""])
        w.writerow(["injuries_summary", "rows_added", "player rows only in live capture",
                    len(only_new), "", "", ""])
        w.writerow(["injuries_summary", "rows_removed", "player rows only in checked-in file",
                    len(only_old), "", "", ""])
        w.writerow(["injuries_summary", "designation_changed", "same player, changed designation",
                    len(status_changed), "", "", ""])
        for c, p, o, n in checks:
            w.writerow(["lions_check", f"{c}:{p}", p, 1 if o != n else 0,
                        f"checked-in={o or '(blank)'} live={n or '(blank)'}",
                        "data/injuries_2026_w10.csv",
                        "https://www.nfl.com/injuries/league/2026/reg10"])

    summary = {
        "generated_utc": "2026-11-16T01:32Z",
        "old_snapshot": "2026-11-14",
        "new_capture": "2026-11-16",
        "standings": {
            "clubs_compared": len(old),
            "clubs_changed": changed_clubs,
            "fields_compared": FIELDS,
        },
        "injuries": {
            "rows_old": len(oi), "rows_new": len(ni),
            "clubs_old": len(oi_clubs), "clubs_new": len(ni_clubs),
            "rows_added": len(only_new), "rows_removed": len(only_old),
            "designation_changed": len(status_changed),
        },
        "brief_claims_checked": [
            {"claim": f"{c} {p} game status blank in the checked-in file",
             "checked_in_file": o or "(blank)",
             "live_page": n or "(blank)",
             "outcome": "CONFIRMED" if (o == "" ) and n else
                        ("REFUTED" if o == n else "CHANGED")}
            for c, p, o, n in checks
        ],
        "interpretation": (
            "A two-day-old snapshot is not a small staleness problem here: it predates the "
            "results of the games it prices. The correct fix is scheduled capture (retain every "
            "capture with its clock time), not a bigger one-off read."
        ),
    }
    with open(os.path.join(DATA, "snapshot_delta.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")

    print()
    print("wrote data/snapshot_delta.csv, data/snapshot_delta.json")


if __name__ == "__main__":
    main()
