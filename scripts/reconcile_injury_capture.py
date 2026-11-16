#!/usr/bin/env python3
"""Reconcile the official NFL.com Week 10 injury-report capture against every repo copy.

Input (hand-maintained transcription, one line per listed player, grouped by game):
  data/official_capture/nfl-injury-report-2026-reg10.psv
      Source: https://www.nfl.com/injuries/league/2026/reg10  (captured 2026-11-16 UTC)

Outputs (regenerated on every run; never edit by hand):
  data/official_injury_capture_wk10_2026.csv        canonical table: one row per listed player, source_id + source_url
  data/official_injury_reconciliation_wk10_2026.csv every field-level difference against data/injuries_2026_wk10.csv
  data/official_capture/manifest-2026-reg10.json    counts, per-club counts, copy audit, sha256 of the transcription

Exit 1 only on structural failure of the capture (game/club/row counts, unknown status words, malformed lines).
Differences against repo copies are NOT failures: they are published on the board as flags for review.
"""
import csv
import hashlib
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAP_DIR = DATA / "official_capture"
PSV = CAP_DIR / "nfl-injury-report-2026-reg10.psv"
REPO_CSV = DATA / "injuries_2026_wk10.csv"
OUT_CAPTURE = DATA / "official_injury_capture_wk10_2026.csv"
OUT_RECON = DATA / "official_injury_reconciliation_wk10_2026.csv"
OUT_AUDIT = DATA / "official_injury_copy_audit_wk10_2026.csv"
MANIFEST = CAP_DIR / "manifest-2026-reg10.json"

SOURCE_URL = "https://www.nfl.com/injuries/league/2026/reg10"
SOURCE_ID = "SRC-018"          # registered in data/sources.csv (this capture)
CAPTURE_DATE = "2026-11-16"    # UTC date of the fetch-tool read

PRACTICE_OK = {
    "Full Participation in Practice",
    "Limited Participation in Practice",
    "Did Not Participate In Practice",
    "",
}
GAME_OK = {"Out", "Doubtful", "Questionable", ""}
MONTHS = {"Nov": "11"}

EXPECTED_GAMES = 14
EXPECTED_CLUBS = 28
EXPECTED_GAME_CLUBS = 28

GAME_HEADER = re.compile(r"^## GAME (\d+) \| (\w{3}) (\w{3}) (\d{1,2}) .*\| (\w+) vs (\w+)\s*$")


def parse_capture():
    rows, games, errors = [], [], []
    current = None
    with PSV.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#") and not line.startswith("## GAME"):
                continue
            if line.startswith("## GAME"):
                m = GAME_HEADER.match(line)
                if not m:
                    errors.append(f"line {lineno}: unparseable game header {line!r}")
                    current = None
                    continue
                num, _dow, mon, day, away, home = m.groups()
                current = {
                    "num": int(num),
                    "game_date": f"{CAPTURE_DATE[:4]}-{MONTHS[mon]}-{int(day):02d}",
                    "pair": f"{away} vs {home}",
                    "clubs": {away, home},
                }
                games.append(current)
                continue
            parts = line.split("|")
            if len(parts) != 6:
                errors.append(f"line {lineno}: expected 6 pipe fields, got {len(parts)}: {line!r}")
                continue
            team, player, pos, inj, prac, game = [p.strip() for p in parts]
            if current is None:
                errors.append(f"line {lineno}: player row before any game header ({player})")
                continue
            if team not in current["clubs"]:
                errors.append(f"line {lineno}: {team} is not a club of game {current['num']} ({current['pair']})")
            if prac not in PRACTICE_OK:
                errors.append(f"line {lineno}: unknown practice status {prac!r} ({player})")
            if game not in GAME_OK:
                errors.append(f"line {lineno}: unknown game status {game!r} ({player})")
            if not player:
                errors.append(f"line {lineno}: blank player name")
            opponent = next(iter(current["clubs"] - {team}), "")
            rows.append({
                "week": "10",
                "game_date": current["game_date"],
                "game_pair_as_printed": current["pair"],
                "team": team,
                "opponent": opponent,
                "player": player,
                "position": pos,
                "injuries": inj,
                "practice_status": prac,
                "game_status": game,
                "source_id": SOURCE_ID,
                "source_url": SOURCE_URL,
                "capture_date": CAPTURE_DATE,
            })
    return rows, games, errors


def norm_injuries(value):
    """Repo writes multi-injury cells as 'A; B' and NFL.com as 'A, B'. Compare as a set, not as text."""
    parts = [x.strip() for x in value.replace(";", ",").split(",")]
    return ", ".join(sorted(x for x in parts if x))


def load_repo():
    with REPO_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


CLUB_CODE = {
    "Arizona Cardinals": "AZ", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR", "Chicago Bears": "CHI", "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL", "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN", "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
}


def copy_audit(official_rows):
    """Row and club coverage of every other Week 10 injury copy in the repo (read-only)."""
    official_clubs = {r["team"] for r in official_rows}
    audit = []

    def add(name, path, rows, team_key):
        clubs = set()
        for r in rows:
            v = r.get(team_key, "").strip()
            if v and len(v) > 3:           # full club name -> the three-letter code used on the official page
                v = CLUB_CODE.get(v, "UNMAPPED:" + v)
            if v:
                clubs.add(v)
        audit.append({
            "file": path,
            "data_rows": len(rows),
            "clubs_present": len(clubs),
            "clubs_missing_vs_official": sorted(official_clubs - clubs),
        })

    for rel, key in [
        ("data/injuries_2026_wk10.csv", "team"),
        ("data/injuries_2026_w10.csv", "team"),
        ("board/data/injuries_2026_w10.csv", "team"),
        ("data/2026-week10-injuries.csv", "team"),
    ]:
        p = ROOT / rel
        if p.exists():
            with p.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            add(rel, rel, rows, key)
    for rel in ["data/injuries_2026_wk10.json", "data/injuries_2026_w10.json"]:
        p = ROOT / rel
        if p.exists():
            obj = json.loads(p.read_text(encoding="utf-8"))
            n = len(obj.get("report", [])) if isinstance(obj, dict) else len(obj)
            audit.append({"file": rel, "data_rows": n, "clubs_present": "see file", "clubs_missing_vs_official": "not computed"})
    return audit


def main():
    rows, games, errors = parse_capture()
    teams = Counter(r["team"] for r in rows)
    fails = list(errors)

    if len(games) != EXPECTED_GAMES:
        fails.append(f"expected {EXPECTED_GAMES} game sections, found {len(games)}")
    if len(teams) != EXPECTED_GAME_CLUBS:
        fails.append(f"expected {EXPECTED_GAME_CLUBS} clubs on the report, found {len(teams)}")
    if any(c == 0 for c in teams.values()):
        fails.append("a club section has zero listed players")
    if len(rows) != len({(r["team"], r["player"]) for r in rows}):
        fails.append("duplicate (team, player) rows in the capture")

    # ---- canonical capture table -----------------------------------------------
    cols = ["week", "game_date", "game_pair_as_printed", "team", "opponent", "player", "position",
            "injuries", "practice_status", "game_status", "source_id", "source_url", "capture_date"]
    with OUT_CAPTURE.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---- reconciliation against the repo's primary Week 10 table ----------------
    repo = load_repo()
    repo_index = {}
    for r in repo:
        repo_index.setdefault((r["team"], r["player"]), []).append(r)
    cap_index = {(r["team"], r["player"]): r for r in rows}

    diffs = []  # team, player, field, official, repo, issue
    for key, cap in cap_index.items():
        if key not in repo_index:
            diffs.append([cap["team"], cap["player"], "row", "listed on official report", "absent from repo table", "missing row"])
            continue
        if len(repo_index[key]) > 1:
            diffs.append([cap["team"], cap["player"], "row", "one row", f"{len(repo_index[key])} rows in repo", "duplicate row"])
        rr = repo_index[key][0]
        for field in ("position", "injuries", "practice_status", "game_status"):
            ov = cap[field]
            rv = (rr.get(field) or "").strip()
            if field == "injuries":
                ov, rv = norm_injuries(ov), norm_injuries(rv)
            if ov != rv:
                issue = "blank in repo" if not rv else ("blank on official report" if not ov else "value differs")
                diffs.append([cap["team"], cap["player"], field, ov or "(blank)", rv or "(blank)", issue])
    for key, rr in repo_index.items():
        if key not in cap_index:
            diffs.append([rr[0]["team"], rr[0]["player"], "row", "not on official report", "present in repo table", "extra row"])

    with OUT_RECON.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["team", "player", "field", "official_nfl_com", "repo_table_345", "issue", "source_id", "source_url"])
        for d in diffs:
            w.writerow(d + [SOURCE_ID, SOURCE_URL])

    audit = copy_audit(rows)
    with OUT_AUDIT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["file", "data_rows", "clubs_present", "clubs_missing_vs_official", "source_id", "source_url"])
        for a in audit:
            missing = a["clubs_missing_vs_official"]
            w.writerow([a["file"], a["data_rows"], a["clubs_present"],
                        ";".join(missing) if isinstance(missing, list) else missing,
                        SOURCE_ID, SOURCE_URL])

    # ---- manifest ----------------------------------------------------------------
    sha = hashlib.sha256(PSV.read_bytes()).hexdigest()
    per_club = {
        t: {
            "listed_players": teams[t],
            "with_injury_entry": sum(1 for r in rows if r["team"] == t and r["injuries"]),
            "with_game_status": sum(1 for r in rows if r["team"] == t and r["game_status"]),
            "out": sum(1 for r in rows if r["team"] == t and r["game_status"] == "Out"),
        }
        for t in sorted(teams)
    }
    manifest = {
        "source_url": SOURCE_URL,
        "source_id": SOURCE_ID,
        "capture_date_utc": CAPTURE_DATE,
        "capture_method": "manual line-by-line transcription of the fetch-tool read (8 chunks); raw HTML was not retained, so no byte-level page hash exists",
        "transcription_file": str(PSV.relative_to(ROOT)),
        "transcription_sha256": sha,
        "game_sections": len(games),
        "clubs": len(teams),
        "listed_rows": len(rows),
        "rows_with_injury_entry": sum(1 for r in rows if r["injuries"]),
        "rows_with_game_status": sum(1 for r in rows if r["game_status"]),
        "reconciled_against": str(REPO_CSV.relative_to(ROOT)),
        "repo_table_rows": len(repo),
        "field_differences_vs_repo": len(diffs),
        "copy_audit": audit,
        "per_club": per_club,
        "structural_failures": fails,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"official capture: {len(games)} game sections, {len(teams)} clubs, {len(rows)} listed rows")
    print(f"  rows with an injury entry: {manifest['rows_with_injury_entry']}; with a game status: {manifest['rows_with_game_status']}")
    print(f"repo primary table: {len(repo)} rows; reconciliation rows (differences): {len(diffs)}")
    for a in manifest["copy_audit"]:
        print(f"  copy {a['file']}: {a['data_rows']} data rows")
    print(f"transcription sha256: {sha}")
    if fails:
        print("STRUCTURAL FAILURES:")
        for f in fails:
            print("  -", f)
        return 1
    print("STRUCTURE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
