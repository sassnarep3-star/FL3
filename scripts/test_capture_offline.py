#!/usr/bin/env python3
"""Offline tests for scripts/capture_official_snapshot.py (synthetic bodies only)."""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/tmp/snaptest")
SCRIPT = ROOT / "scripts" / "capture_official_snapshot.py"

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
EMPTY = (
    '<html><head><title>x</title></head><body>' + _CHROME +
    '<h2>Injuries - WEEK 11</h2><p>no players yet</p>'
    '<th>Practice Status</th><th>Game Status</th>'
    '<a href="https://www.nfl.com/injuries/league/2026/reg11">week link</a></body></html>'
)
DRIFT = '<html><body>Access Denied</body></html>'


def run(body: str, week: int = 11):
    f = ROOT / "case.html"
    f.write_text(body)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--week", str(week), "--from-file", str(f)],
        capture_output=True, text=True, cwd=ROOT,
    )


def setup():
    shutil.rmtree(ROOT, ignore_errors=True)
    (ROOT / "scripts").mkdir(parents=True)
    shutil.copy("/home/user/FL3/scripts/capture_official_snapshot.py", SCRIPT)


setup()
results = []

r1 = run(POPULATED)
results.append(("populated -> captured rc0", r1.returncode == 0 and "captured" in r1.stdout and (ROOT / "snapshots/raw/injuries/reg11").exists()))

r2 = run(POPULATED)
results.append(("second same-second capture -> refusal rc2 (immutability)", r2.returncode == 2 and "refusing" in r2.stderr))

r3 = run(EMPTY)
results.append(("empty-but-valid -> rc0, result=empty, nothing stored", r3.returncode == 0 and "no player rows" in r3.stdout))

r4 = run(DRIFT)
results.append(("drift body -> rc2 with body snippet", r4.returncode == 2 and "Access Denied" in r4.stderr))

r5 = run(POPULATED, week=17)
results.append((
    "older week served for future request -> recorded as not published, no raw capture",
    r5.returncode == 0
    and "NOT PUBLISHED YET" in r5.stdout
    and "week 11" in r5.stdout
    and not (ROOT / "snapshots/raw/injuries/reg17").exists(),
))

SMALL_CHALLENGE = '<html><body><th>Practice Status</th><th>Game Status</th><a href="https://www.nfl.com/injuries/league/2026/reg11">w</a>Access Denied</body></html>'
r7 = run(SMALL_CHALLENGE)
results.append(("small body with headings (challenge-shaped) -> rc2 via MIN_BYTES", r7.returncode == 2 and "Access Denied" in r7.stderr))

idx = (ROOT / "snapshots/index.csv").read_text()
results.append(("index rows recorded", idx.count("captured") >= 1 and "empty" in idx))

# reset and check a second capture in a later second works and marks 'unchanged'
import time
setup()
run(POPULATED)
time.sleep(1.2)
r6 = run(POPULATED)
results.append(("second capture stores a new file, marks 'unchanged'", r6.returncode == 0 and "unchanged" in r6.stdout))

ok = True
for name, passed in results:
    print(("PASS " if passed else "FAIL ") + name)
    ok = ok and passed
print("ALL OFFLINE CAPTURE TESTS PASS" if ok else "SOME TESTS FAILED")
sys.exit(0 if ok else 1)
