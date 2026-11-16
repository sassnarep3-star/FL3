#!/usr/bin/env python3
"""Capture one immutable, hashed snapshot of an official NFL.com injury report.

What it does (one run = one capture):
  1. GET https://www.nfl.com/injuries/league/2026/reg<WEEK> with a plain User-Agent.
  2. Refuse to store anything that fails the drift checks below (exit 2, nothing written).
  3. Store the raw body gzip-compressed at snapshots/raw/<report>/reg<WEEK>/<UTC>_<sha12>.html.gz
     - a file that already exists is never overwritten (immutability).
  4. Append one line to snapshots/index.csv with the UTC time, HTTP status, byte count,
     full SHA-256, file path, the count of player links found, and whether the body changed
     since the previous capture of the same report/week ("changed" / "unchanged" / "first").

Drift checks (any failure = exit 2, which fails the scheduled workflow loudly):
  - HTTP status must be 200.
  - Body must be at least MIN_BYTES long.
  - Body must contain the headings the parser depends on: "Practice Status", "Game Status",
    and the report path for the requested week.
  - At least one player link (nfl.com/players/) must be present.

Standard library only. Exit codes: 0 captured, 2 drift/fetch failure (nothing written), 1 usage error.
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "snapshots"
INDEX = SNAP / "index.csv"
MIN_BYTES = 20_000
UA = "FL3-snapshot/1.0 (+https://github.com/sassnarep3-star/FL3; official report capture)"
INDEX_HEADER = [
    "capture_utc", "report", "season", "week", "url", "http_status", "bytes", "sha256",
    "raw_path", "player_links", "change_vs_previous", "result",
]


def report_url(week: int) -> str:
    return f"https://www.nfl.com/injuries/league/2026/reg{week}"


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"fetch error: {e}", file=sys.stderr)
        return 0, b""


def check_body(body: bytes, week: int, status: int):
    """Return a list of drift problems. Empty list = safe to store."""
    problems = []
    if status != 200:
        problems.append(f"HTTP status {status}")
    if len(body) < MIN_BYTES:
        problems.append(f"body {len(body)} bytes < {MIN_BYTES}")
    text = body.decode("utf-8", errors="replace")
    for needle in ("Practice Status", "Game Status", f"/injuries/league/2026/reg{week}"):
        if needle not in text:
            problems.append(f"missing expected text {needle!r}")
    if text.count("nfl.com/players/") < 1:
        problems.append("no player links found")
    return problems


def previous_hash(report: str, week: int):
    if not INDEX.exists():
        return None
    last = None
    with INDEX.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["report"] == report and row["week"] == str(week) and row["result"] == "captured":
                last = row["sha256"]
    return last


def append_index(row: dict):
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    new = not INDEX.exists()
    with INDEX.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=INDEX_HEADER, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--week", type=int, required=True, help="NFL week number, e.g. 11")
    ap.add_argument("--report", default="injuries", help="report name used in paths")
    ap.add_argument("--from-file", help="test only: read the body from this file instead of the network")
    args = ap.parse_args(argv)
    if not 1 <= args.week <= 22:
        print("week must be 1-22", file=sys.stderr)
        return 1

    url = report_url(args.week)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    if args.from_file:
        status, body = 200, Path(args.from_file).read_bytes()
    else:
        status, body = fetch(url)

    problems = check_body(body, args.week, status)
    sha = hashlib.sha256(body).hexdigest()
    if problems:
        print(f"DRIFT/FETCH FAILURE for {url}: " + "; ".join(problems), file=sys.stderr)
        print(f"nothing stored. status={status} bytes={len(body)} sha256={sha}", file=sys.stderr)
        return 2

    prev = previous_hash(args.report, args.week)
    change = "first" if prev is None else ("unchanged" if prev == sha else "changed")
    rel = Path("snapshots/raw") / args.report / f"reg{args.week}" / f"{stamp}_{sha[:12]}.html.gz"
    out = ROOT / rel
    if out.exists():
        print(f"refusing to overwrite existing snapshot {rel}", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(filename=str(out), mode="wb", mtime=0) as fh:
        fh.write(body)

    links = body.decode("utf-8", errors="replace").count("nfl.com/players/")
    append_index({
        "capture_utc": now.isoformat().replace("+00:00", "Z"),
        "report": args.report, "season": 2026, "week": args.week, "url": url,
        "http_status": status, "bytes": len(body), "sha256": sha,
        "raw_path": rel.as_posix(), "player_links": links,
        "change_vs_previous": change, "result": "captured",
    })
    print(f"captured {url} -> {rel.as_posix()} ({len(body)} bytes, sha256 {sha[:12]}, {change})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
