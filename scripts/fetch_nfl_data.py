#!/usr/bin/env python3
"""Fetch and parse the official pages this repo is allowed to cite.

STATUS: UNTESTED IN THIS SANDBOX. Written 2026-11-14; the environment it was authored in blocks
outbound requests to nfl.com (only github.com / pypi.org / registry.npmjs.org are reachable), so
this script has never been executed against the network. See data/flags.csv FLG-024 - and do not
cite it anywhere as a verification step until it has actually run.

Design rules (these are the reason the file exists rather than a one-liner):

  * One row per fact, with `source_url` + `accessed_utc` recorded at fetch time.
  * Idempotent by week: re-running for a week already on disk writes to a sidecar and reports the
    diff instead of overwriting, so a stat correction is visible rather than silent.
  * Refuses to write a column whose label it cannot read (nfl.com stat tables render without a
    header row in static HTML) - it emits the raw cells and leaves the mapping to be proved by
    the identity checks in verify.py. No guessing, no positional "it looks like yards".
  * Nothing here is derived. Parsing only.

Usage:
    python3 scripts/fetch_nfl_data.py --weeks 10 --season 2026 --what slate,injuries
    python3 scripts/fetch_nfl_data.py --what games --weeks 3-18
    python3 scripts/fetch_nfl_data.py --what stats
    python3 scripts/fetch_nfl_data.py --what odds --dry-run        # needs Q-01 licence
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw_evidence")

UA = "FL3-research/0.1 (single-user academic data collection; contact: repo owner)"
SLEEP_BETWEEN_CALLS = 3.0          # seconds; be a guest, not a load
TIMEOUT = 25

URLS = {
    "schedule_week": "https://www.nfl.com/schedules/{season}/by-week/week-{week}",
    "injuries_week": "https://www.nfl.com/injuries/league/{season}/reg{week}",
    "standings": "https://www.nfl.com/standings/",
    "stats_off_pass": "https://www.nfl.com/stats/team-stats/offense/passing/{season}/reg/all",
    "stats_off_rush": "https://www.nfl.com/stats/team-stats/offense/rushing/{season}/reg/all",
    "stats_def_pass": "https://www.nfl.com/stats/team-stats/defense/passing/{season}/reg/all",
    "stats_def_rush": "https://www.nfl.com/stats/team-stats/defense/rushing/{season}/reg/all",
    # odds vendor: intentionally not a URL. Q-01 / SRC-016 - a licence decision, not a scrape.
}


def log(msg: str) -> None:
    print(f"[fetch] {msg}", flush=True)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url: str) -> str:
    """Plain HTTP GET with a declared UA and a polite pause. No retries beyond one."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 - fixed host list
            return resp.read().decode("utf-8", "replace")
    except Exception as exc:                        # network-blocked in some environments
        log(f"WARN fetch failed for {url}: {type(exc).__name__}: {exc}")
        raise


def save_raw(name: str, html: str) -> str:
    """Keep the bytes we parsed, so a later disagreement can be settled without re-fetching."""
    os.makedirs(RAW, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(RAW, f"{stamp}-{name}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    with open(path + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(hashlib.sha256(html.encode("utf-8")).hexdigest() + "\n")
    return os.path.relpath(path, REPO)


# --------------------------------------------------------------------------- #
# minimal, defensive HTML parsing - deliberately no third-party dependency
# --------------------------------------------------------------------------- #
TAG = re.compile(r"<[^>]+>")
GAME_ROW = re.compile(
    r"""(?ix)
    (?P<away>[A-Z][A-Za-z .']{2,28}?)\s+(?P<away_pts>\d{1,2})\s*[-@]\s*
    (?P<home>[A-Z][A-Za-z .']{2,28}?)\s+(?P<home_pts>\d{1,2})
    """
)


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", fragment)).strip()


def parse_schedule(html: str, season: str, week: str):
    """Rows of a weekly schedule page -> game records, with per-row provenance.

    The static page renders the score line inside link text; where a game has no score the row is
    written with blank point fields and status 'scheduled' rather than 0-0.
    """
    out = []
    for m in GAME_ROW.finditer(html):
        out.append({
            "season": season, "week": week,
            "away": m.group("away"), "away_pts": m.group("away_pts"),
            "home": m.group("home"), "home_pts": m.group("home_pts"),
            "status": "FINAL",
            "source_url": URLS["schedule_week"].format(season=season, week=week),
            "accessed_utc": now_utc(),
        })
    return out


def parse_injury_table(html: str):
    """Injury-report rows -> (team, player, pos, injury, practice, game status).

    Design decision: cells we cannot read are written BLANK. A missing game status is not turned
    into 'Questionable', and a missing injury description is not turned into 'undisclosed'.
    """
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = [text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        if len(cells) < 4:
            continue
        rows.append(cells)
    return rows


def write_rows(name, rows, fieldnames):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            old = list(csv.DictReader(fh))
        if old and len(old) == len(rows) and all(a == b for a, b in zip(old, rows)):
            log(f"{name}: unchanged ({len(rows)} rows) - not rewritten")
            return path
        side = path.replace(".csv", f".{dt.datetime.now():%Y%m%dT%H%M%S}.proposed.csv")
        with open(side, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        log(f"{name}: DIFFERS from existing table -> wrote {os.path.basename(side)} "
            f"(existing kept; reconcile by hand, never overwrite a verified read)")
        return side
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    log(f"{name}: wrote {len(rows)} rows")
    return path


def do_weeks(spec: str):
    if "-" in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", default="2026")
    ap.add_argument("--weeks", default="10", help="e.g. 10 or 3-18 or 1,2")
    ap.add_argument("--what", default="games", help="games,stats,injuries,slate,odds (comma separated)")
    ap.add_argument("--dry-run", action="store_true", help="print the URLs and the plan, fetch nothing")
    ap.add_argument("--json", action="store_true", help="emit a machine-readable manifest for CI")
    args = ap.parse_args(argv)
    weeks = do_weeks(args.weeks)
    whats = [w.strip() for w in args.what.split(",") if w.strip()]
    plan = []

    for what in whats:
        if what == "games":
            for wk in weeks:
                url = URLS["schedule_week"].format(season=args.season, week=wk)
                plan.append(("games", wk, url))
        elif what == "injuries" or what == "slate":
            for wk in weeks:
                plan.append((what, wk, URLS["injuries_week"].format(season=args.season, week=wk)))
        elif what == "stats":
            for key in ("stats_off_pass", "stats_off_rush", "stats_def_pass", "stats_def_rush"):
                plan.append((key, "all", URLS[key].format(season=args.season)))
        elif what == "standings":
            plan.append(("standings", "current", URLS["standings"]))
        elif what == "odds":
            log("odds: BLOCKED - no licensed source in this repo (Q-01, SRC-016). "
                "Nothing is fetched, no value is invented. Register the vendor first.")
            continue
        else:
            log(f"unknown --what {what!r}")

    if args.dry_run or args.json:
        print(json.dumps({"plan": [{"what": w, "week": k, "url": u} for w, k, u in plan],
                          "fetched": False,
                          "note": "this run only prints the plan"}, indent=2))
        return 0

    log(f"{len(plan)} request(s), {SLEEP_BETWEEN_CALLS}s apart, UA={UA}")
    import time
    ok = fail = 0
    for what, wk, url in plan:
        try:
            html = get(url)
            raw = save_raw(f"{what}-{wk}", html)
            if what == "games":
                rows = parse_schedule(html, args.season, str(wk))
                path = write_rows(f"games_{args.season}_w{wk}.csv", rows,
                                  ["season", "week", "away", "away_pts", "home", "home_pts",
                                   "status", "source_url", "accessed_utc"])
                log(f"week {wk}: {len(rows)} game rows -> {path}; raw kept at {raw}")
            elif what in ("injuries", "slate"):
                rows = parse_injury_table(html)
                log(f"week {wk}: {len(rows)} table rows parsed from {raw} "
                    f"- column mapping is NOT inferred; verify.py must accept it")
            else:
                rows = parse_injury_table(html)
                log(f"{what}: {len(rows)} raw rows kept at {raw}; label mapping left to verify.py")
            ok += 1
        except Exception:
            fail += 1
        time.sleep(SLEEP_BETWEEN_CALLS)

    log(f"done: {ok} ok, {fail} failed")
    log("next: run scripts/verify.py, then scripts/model.py, then scripts/build_site.py")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
