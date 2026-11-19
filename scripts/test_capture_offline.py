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
    shutil.copy(pathlib.Path(__file__).resolve().parent / "capture_official_snapshot.py", SCRIPT)


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
# The synthetic page is for Week 11 while Week 17 is requested. An earlier
# report being served is the documented not-published-yet state, not parser drift.
r5_index = (ROOT / "snapshots/index.csv").read_text()
results.append(("earlier week served -> recorded not_published_yet rc0",
                r5.returncode == 0 and "NOT PUBLISHED YET" in r5.stdout
                and "not_published_yet" in r5_index))

# A body with a LATER week than requested is drift.
LATER = POPULATED.replace("WEEK 11", "WEEK 12").replace("reg11", "reg12")
r5b = run(LATER, week=11)
results.append(("later-week body for week 11 -> drift rc2", r5b.returncode == 2))

# Real-world serialisations that the first version missed (player links escaped
# inside embedded JSON, or relative hrefs). These must be captured, not "empty".
ESCAPED = POPULATED.replace("https://www.nfl.com/players/", "https:\\/\\/www.nfl.com\\/players\\/")
r8 = run(ESCAPED)
results.append(("escaped JSON player links -> captured rc0", r8.returncode == 0 and "captured" in r8.stdout))
RELATIVE = POPULATED.replace("https://www.nfl.com/players/", "/players/")
r9 = run(RELATIVE)
results.append(("relative player hrefs -> captured rc0", r9.returncode == 0 and "captured" in r9.stdout))

# Status cells only (no player links at all) still count as rows.
STATUS_ONLY = POPULATED.replace("https://www.nfl.com/players/", "#p")
r10 = run(STATUS_ONLY)
results.append(("status cells without profile links -> captured rc0", r10.returncode == 0 and "captured" in r10.stdout))

# Partial page (2 rows) is a parser/page-shape problem: loud failure, not "empty".
PARTIAL = POPULATED.replace("test-player-2/", "test-player-2x/")  # keep structure
PARTIAL = ('<html><head><title>x</title></head><body>' + _CHROME +
    '<h2>Injuries - WEEK 11</h2><table><tr><th>Practice Status</th><th>Game Status</th></tr>'
    '<tr><td><a href="https://www.nfl.com/players/a-one/">A</a></td><td>Full Participation in Practice</td></tr>'
    '<tr><td><a href="https://www.nfl.com/players/b-two/">B</a></td><td>Out</td></tr></table>'
    '<a href="https://www.nfl.com/injuries/league/2026/reg11">week link</a></body></html>')
r11 = run(PARTIAL)
results.append(("partial page (2 rows) -> drift rc2, nothing stored", r11.returncode == 2 and "only 2 player rows" in r11.stderr))

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
