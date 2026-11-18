#!/usr/bin/env python3
"""Offline tests for scripts/capture_official_snapshot.py (synthetic bodies only)."""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path(tempfile.gettempdir()) / f"fl3-snaptest-{os.getpid()}"
SCRIPT = WORK / "scripts" / "capture_official_snapshot.py"

_CHROME = '<nav class="site-chrome">' + ('<li><a href="/team/roster/club/X">roster link X</a></li>' * 400) + '</nav>'
POPULATED = (
    '<html><head><title>x</title></head><body>' + _CHROME +
    '<h2>Injuries - WEEK 11</h2><table><tr><th>Player</th><th>Position</th><th>Injuries</th>'
    '<th>Practice Status</th><th>Game Status</th></tr>'
    + ''.join(
        f'<tr><td><a href="https://www.nfl.com/players/test-player-{i}/">P{i}</a></td><td>QB</td>'
        '<td>Knee</td><td>Limited Participation in Practice</td><td>Questionable</td></tr>'
        for i in range(40))
    + '<a href="https://www.nfl.com/injuries/league/2026/reg11">week link</a></body></html>'
)
# A report for a later week than the requested one is suspicious, not an expected
# "not published yet" state. The requested-week marker is changed with the title.
FUTURE_WEEK = POPULATED.replace("WEEK 11", "WEEK 17").replace("reg11", "reg17")
EMPTY = (
    '<html><head><title>x</title></head><body>' + _CHROME +
    '<h2>Injuries - WEEK 11</h2><p>no players yet</p>'
    '<th>Practice Status</th><th>Game Status</th>'
    '<a href="https://www.nfl.com/injuries/league/2026/reg11">week link</a></body></html>'
)
DRIFT = '<html><body>Access Denied</body></html>'


def run(body: str, week: int = 11):
    f = WORK / "case.html"
    f.write_text(body, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--week", str(week), "--from-file", str(f)],
        capture_output=True, text=True, cwd=WORK,
    )


def setup():
    shutil.rmtree(WORK, ignore_errors=True)
    (WORK / "scripts").mkdir(parents=True)
    # Resolve the script relative to this checkout; do not assume an Arena-specific
    # absolute path so the test also runs on GitHub Actions and local clones.
    shutil.copy(REPO / "scripts" / "capture_official_snapshot.py", SCRIPT)


setup()
results = []

r1 = run(POPULATED)
results.append(("populated -> captured rc0", r1.returncode == 0 and "captured" in r1.stdout and (WORK / "snapshots/raw/injuries/reg11").exists()))

first_files = sorted((WORK / "snapshots/raw/injuries/reg11").glob("*.html.gz"))
first_bytes = first_files[0].read_bytes() if first_files else None
r2 = run(POPULATED)
second_files = sorted((WORK / "snapshots/raw/injuries/reg11").glob("*.html.gz"))
original_unchanged = bool(first_files and first_files[0].read_bytes() == first_bytes)
same_second_refused = r2.returncode == 2 and "refusing" in r2.stderr and len(second_files) == 1
later_second_appended = r2.returncode == 0 and "unchanged" in r2.stdout and len(second_files) == 2
results.append((
    "duplicate timestamp is refused or a later capture is appended without overwriting",
    original_unchanged and (same_second_refused or later_second_appended),
))

r3 = run(EMPTY)
results.append(("empty-but-valid -> rc0, result=empty, nothing stored", r3.returncode == 0 and "no player rows" in r3.stdout))

r4 = run(DRIFT)
results.append(("drift body -> rc2 with body snippet", r4.returncode == 2 and "Access Denied" in r4.stderr))

# An earlier report served at a future-week URL is an ordinary pre-publication
# state; a later report served for an earlier requested week is a real drift alarm.
r5 = run(POPULATED, week=17)
results.append(("earlier-week page for a future request -> not_published_yet rc0", r5.returncode == 0 and "NOT PUBLISHED YET" in r5.stdout))

r6 = run(FUTURE_WEEK, week=11)
results.append(("later-week page for an earlier request -> drift rc2", r6.returncode == 2 and "LATER week 17" in r6.stderr))

SMALL_CHALLENGE = '<html><body><th>Practice Status</th><th>Game Status</th><a href="https://www.nfl.com/injuries/league/2026/reg11">w</a>Access Denied</body></html>'
r7 = run(SMALL_CHALLENGE)
results.append(("small body with headings (challenge-shaped) -> rc2 via MIN_BYTES", r7.returncode == 2 and "Access Denied" in r7.stderr))

idx = (WORK / "snapshots/index.csv").read_text(encoding="utf-8")
results.append(("index records captured, empty and not-published states", "captured" in idx and "empty" in idx and "not_published_yet" in idx))

# Reset and verify a later capture gets a new immutable file and is marked unchanged.
setup()
run(POPULATED)
time.sleep(1.2)
r8 = run(POPULATED)
results.append((
    "later-second capture stores a new file, marks unchanged, and retains the first hash",
    r8.returncode == 0 and "unchanged" in r8.stdout and
    len(list((WORK / "snapshots/raw/injuries/reg11").glob("*.html.gz"))) == 2,
))

ok = True
for name, passed in results:
    print(("PASS " if passed else "FAIL ") + name)
    ok = ok and passed
print("ALL OFFLINE CAPTURE TESTS PASS" if ok else "SOME TESTS FAILED")
shutil.rmtree(WORK, ignore_errors=True)
sys.exit(0 if ok else 1)
