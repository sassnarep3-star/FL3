#!/usr/bin/env python3
"""Diff the repo's Week 10 injury CSV against the official NFL.com capture.

Inputs : data/official_captures/nfl_week10_2026_injury_report.psv   (transcribed from
         https://www.nfl.com/injuries/league/2026/reg10, see the header of that file)
         data/injuries_2026_wk10.csv                                 (repo table under review)
Outputs: data/official_captures/nfl_week10_2026_injury_diff.csv      (one row per discrepancy)
         data/official_captures/nfl_week10_2026_manifest.json        (counts + sha256)

Stdlib only. Exit code 0 always; the discrepancy count is printed and recorded, never hidden.
"""
import csv
import hashlib
import json
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAP = ROOT / "data" / "official_captures" / "nfl_week10_2026_injury_report.psv"
REPO = ROOT / "data" / "injuries_2026_wk10.csv"
DIFF = ROOT / "data" / "official_captures" / "nfl_week10_2026_injury_diff.csv"
MANIFEST = ROOT / "data" / "official_captures" / "nfl_week10_2026_manifest.json"
SOURCE = "https://www.nfl.com/injuries/league/2026/reg10"

PRACTICE = {
    "DNP": "Did Not Participate In Practice",
    "LP": "Limited Participation in Practice",
    "FP": "Full Participation in Practice",
    "": "",
}


def parts(cell):
    """Injury cell -> frozenset of body parts (order and separator ignored)."""
    return frozenset(p.strip() for p in cell.replace(";", ",").split(",") if p.strip())


def load_official():
    rows = []
    for line in CAP.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        club, player, pos, inj, prac, game = line.split("|")
        rows.append({"club": club, "player": player, "pos": pos, "injury": inj,
                     "practice": PRACTICE[prac], "game": game})
    return rows


def load_repo():
    rows = []
    with REPO.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append({"club": r["team"], "player": r["player"], "pos": r["position"],
                         "injury": r["injuries"], "practice": r["practice_status"],
                         "game": r["game_status"]})
    return rows


def main():
    off = load_official()
    rep = load_repo()
    sha = hashlib.sha256(CAP.read_bytes()).hexdigest()

    off_by_club = collections.Counter(r["club"] for r in off)
    rep_by_club = collections.Counter(r["club"] for r in rep)
    clubs = sorted(set(off_by_club) | set(rep_by_club))

    # Key on (club, player). A duplicate key on either side is itself a discrepancy.
    off_key = collections.defaultdict(list)
    rep_key = collections.defaultdict(list)
    for r in off:
        off_key[(r["club"], r["player"])].append(r)
    for r in rep:
        rep_key[(r["club"], r["player"])].append(r)

    out = []
    for key in sorted(set(off_key) | set(rep_key)):
        club, player = key
        o = off_key.get(key, [])
        p = rep_key.get(key, [])
        if not p:
            out.append([club, player, "row", "present on official page", "MISSING from repo", "missing_in_repo"])
            continue
        if not o:
            out.append([club, player, "row", "not on official page", "present in repo", "extra_in_repo"])
            continue
        if len(o) > 1 or len(p) > 1:
            out.append([club, player, "row", f"official rows={len(o)}", f"repo rows={len(p)}", "duplicate_key"])
            continue
        a, b = o[0], p[0]
        if a["pos"] != b["pos"]:
            out.append([club, player, "position", a["pos"], b["pos"], "mismatch"])
        if parts(a["injury"]) != parts(b["injury"]):
            out.append([club, player, "injury", a["injury"] or "(blank)", b["injury"] or "(blank)", "mismatch"])
        if a["practice"] != b["practice"]:
            out.append([club, player, "practice_status", a["practice"], b["practice"] or "(blank)", "mismatch"])
        if a["game"] != b["game"]:
            out.append([club, player, "game_status", a["game"] or "(blank)", b["game"] or "(blank)", "mismatch"])

    with DIFF.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["club", "player", "field", "official_nfl_com", "repo_value", "discrepancy"])
        w.writerows(out)

    kinds = collections.Counter(r[5] for r in out)
    manifest = {
        "source_url": SOURCE,
        "capture_file": str(CAP.relative_to(ROOT)),
        "capture_sha256": sha,
        "capture_note": "sha256 covers the transcription file, not the raw HTML served by NFL.com",
        "official_rows": len(off),
        "official_clubs": len(off_by_club),
        "repo_rows": len(rep),
        "repo_clubs": len(rep_by_club),
        "official_rows_by_club": dict(sorted(off_by_club.items())),
        "repo_rows_by_club": dict(sorted(rep_by_club.items())),
        "discrepancies_total": len(out),
        "discrepancies_by_kind": dict(sorted(kinds.items())),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"official rows={len(off)} clubs={len(off_by_club)} | repo rows={len(rep)} clubs={len(rep_by_club)}")
    print(f"capture sha256={sha}")
    for c in clubs:
        if off_by_club[c] != rep_by_club[c]:
            print(f"  club count differs: {c} official={off_by_club[c]} repo={rep_by_club[c]}")
    print(f"discrepancies={len(out)} {dict(sorted(kinds.items()))}")
    print(f"wrote {DIFF.relative_to(ROOT)} and {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
