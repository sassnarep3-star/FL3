#!/usr/bin/env python3
"""
FL3 — optional refresh job.

Fetches the official NFL.com pages and reports what changed, so a human can
review a diff before committing new data.

IMPORTANT
---------
* This script NEVER writes dataset values automatically. Auto-parsing NFL.com
  HTML and committing the result would be a silent, unverifiable data pipeline.
  It fetches, hashes, and reports.
* It requires outbound network access. The default build environment for this
  repo has none (flag F08), so this is meant to run in CI or on a networked
  machine:  python3 scripts/fetch_official.py
* Exit codes: 0 = fetched and unchanged, 2 = fetched and something changed
  (review needed), 1 = network/parse failure.

Usage
-----
    python3 scripts/fetch_official.py            # report only
    python3 scripts/fetch_official.py --json     # machine-readable report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "fetch_state.json")

TARGETS = [
    ("SRC-STAND-DIV", "https://www.nfl.com/standings/division/2026/REG"),
    ("SRC-STAND-LEAGUE", "https://www.nfl.com/standings/league/2026/REG"),
    ("SRC-INJ", "https://www.nfl.com/injuries/"),
    ("SRC-SCHED", "https://www.nfl.com/schedules/2026/REG/"),
    ("SRC-TIEBREAK", "https://www.nfl.com/standings/tie-breaking-procedures"),
    ("SRC-INJ-POLICY", "https://operations.nfl.com/the-rules/nfl-injury-report-policy/"),
]

UA = "FL3-verifier/1.0 (+https://github.com/sassnarep3-star/FL3)"


def fetch(url: str) -> tuple[bool, str, str]:
    """Return (ok, sha256_hex, note). Never raises."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
        if not body:
            return False, "", "empty body"
        return True, hashlib.sha256(body).hexdigest(), f"{len(body)} bytes"
    except urllib.error.HTTPError as exc:
        return False, "", f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return False, "", f"network error: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 - report anything, never crash
        return False, "", f"{type(exc).__name__}: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    previous = {}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            previous = json.load(fh).get("sources", {})

    report = {}
    changed = []
    failed = []

    for sid, url in TARGETS:
        ok, digest, note = fetch(url)
        entry = {
            "url": url,
            "ok": ok,
            "sha256": digest,
            "note": note,
            "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if ok:
            prev = previous.get(sid, {}).get("sha256")
            entry["changed"] = bool(prev and prev != digest)
            if entry["changed"]:
                changed.append(sid)
            elif prev is None:
                entry["changed"] = None  # first observation
        else:
            failed.append((sid, note))
        report[sid] = entry

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for sid, entry in report.items():
            if entry["ok"]:
                tag = "CHANGED" if entry.get("changed") else ("new" if entry.get("changed") is None else "same")
                print(f"  {sid:20} {tag:8} {entry['note']}")
            else:
                print(f"  {sid:20} FAILED   {entry['note']}")

    # persist state only when at least one fetch succeeded, so a full network
    # outage cannot wipe the baseline
    if any(e["ok"] for e in report.values()):
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        merged = dict(previous)
        for sid, entry in report.items():
            if entry["ok"]:
                merged[sid] = entry
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump({"updated_utc": datetime.now(timezone.utc).isoformat(), "sources": merged},
                      fh, indent=2)
            fh.write("\n")

    if failed and not any(e["ok"] for e in report.values()):
        print("\nNo source reachable. Nothing was changed. See flag F08.", file=sys.stderr)
        return 1
    if failed:
        print(f"\n{len(failed)} source(s) unreachable; the rest were checked.", file=sys.stderr)
    if changed:
        print(f"\n{len(changed)} page(s) changed: {', '.join(changed)}")
        print("Review the diff and update data/*.json by hand, then re-run the verifier.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
