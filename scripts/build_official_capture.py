#!/usr/bin/env python3
"""Render official-capture.html: the official Week 10 injury-report capture and its reconciliation.

Inputs (all checked in, no network access needed):
  data/official/2026-w10-injury-report.csv   the capture, one row per player listed on the page
  data/official/2026-w10-reconciliation.csv  every difference against each published copy
Both are produced by scripts/reconcile_official_w10.py, which this script imports so the page
and the audit use the same loaders and the same pinned checks.

Output is deterministic (no timestamps). Every table row carries a link to the official page.
Run:  python3 scripts/build_official_capture.py   (then scripts/check_links.py covers it)
"""
import csv
import html
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import reconcile_official_w10 as rec  # noqa: E402

OUT_DIR = ROOT
OUT = ROOT / "official-capture.html"
SRC = rec.SOURCE_URL
CAPTURE_DATE = "2026-11-16"


def esc(v):
    return html.escape(str(v), quote=True)


def chip(status):
    if not status:
        return '<span class="chip blank">&mdash;</span>'
    cls = {"Out": "out", "Doubtful": "doubt", "Questionable": "quest"}.get(status, "")
    return f'<span class="chip {cls}">{esc(status)}</span>'


def page(title, body):
    nav = [
        ("index.html", "Dashboard"),
        ("injuries.html", "Injury report"),
        ("flagged.html", "Flagged for review"),
        ("sources.html", "Sources"),
    ]
    navhtml = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | FL3</title>
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="index.html">FL3 &middot; NFL decision system</a>
<nav>{navhtml}</nav></div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap"><p class="muted">Official source for every row: <a href="{SRC}" rel="noopener">NFL.com 2026 injury report, Week 10</a>.
Model output is never shown on this page. Nothing here is betting advice.</p></footer>
</body>
</html>
"""


def main():
    official_rows, problems = rec.load_official()
    if problems:
        print("official capture failed pinned checks; refusing to render", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        return 1

    sources = [rec.load_published_csv_repo_root(), rec.load_published_board(), rec.load_published_json()]
    recon_rows = []
    summary = []
    off_keys = {(r["team"], r["player"]) for r in official_rows}
    for label, published in sources:
        diffs, dup_pub, n = rec.reconcile(official_rows, label, published)
        kinds = Counter(d[7] for d in diffs)
        pub_keys = {(t, p) for t, p, _, _ in published}
        missing = sum(1 for k in off_keys if k not in pub_keys)
        rows_compared = len(off_keys & pub_keys)
        summary.append((label, n, rows_compared, missing, kinds, len(diffs)))
        recon_rows.extend(diffs)

    body = []
    body.append(f"""<section class="hero">
<p class="eyebrow">Official source capture &middot; Week 10, 2026 regular season</p>
<h1>NFL.com injury report, captured {CAPTURE_DATE}</h1>
<p class="lede">Every player row on the official Week 10 report, transcribed as published, then compared line by line
with each copy of the Week 10 table in this repository. Where the repository copy disagrees with the official
page, the difference is listed below rather than silently overwritten.</p>
<p class="lede"><a href="https://github.com/sassnarep3-star/FL3/blob/main/data/official/2026-w10-injury-report.csv">Capture CSV</a>
&middot; <a href="https://github.com/sassnarep3-star/FL3/blob/main/data/official/2026-w10-reconciliation.csv">Reconciliation CSV</a>
&middot; <a href="{SRC}" rel="noopener">Official page</a></p>
</section>""")

    body.append("<h2>1. Capture checks (pinned)</h2>")
    games = sorted({r["game"] for r in official_rows})
    clubs = sorted({r["team"] for r in official_rows})
    body.append('<div class="tablewrap"><table><thead><tr><th>Check</th><th>Expected</th><th>Found</th><th>Result</th></tr></thead><tbody>')
    checks = [
        ("Player rows on the page", rec.PINNED["rows"], len(official_rows)),
        ("Games (match-ups) on the page", rec.PINNED["games"], len(games)),
        ("Clubs with at least one row", rec.PINNED["clubs"], len(clubs)),
    ]
    for name, exp, found in checks:
        ok = "pass" if exp == found else "FAIL"
        body.append(f"<tr><td>{esc(name)}</td><td>{exp}</td><td>{found}</td><td>{ok}</td></tr>")
    body.append("</tbody></table></div>")
    body.append('<p class="muted">Each row also passed: a known practice status, a known game status (or none), no duplicate club/player key. '
                'Game order follows the page; the page lists the first club of each match-up first, which is not necessarily the home club.</p>')

    body.append("<h2>2. Reconciliation against each published copy</h2>")
    body.append('<div class="tablewrap"><table><thead><tr><th>Published copy</th><th>Rows</th><th>Official rows found in it</th>'
                '<th>Official rows missing from it</th><th>Status or practice differences</th><th>All differences</th></tr></thead><tbody>')
    for label, n, cmp_n, missing, kinds, total in summary:
        mism = sum(v for k, v in kinds.items() if "mismatch" in k)
        body.append(f"<tr><td><code>{esc(label)}</code></td><td>{n}</td><td>{cmp_n}</td><td>{missing}</td><td>{mism}</td><td>{total}</td></tr>")
    body.append("</tbody></table></div>")
    body.append('<p class="muted">A difference is either a player missing from the published copy, a player present in the copy but absent from the official page, '
                'or a practice/game-status value that differs. The published copies were captured on 2026-11-14 and carry no per-row fetch time, '
                'so this page cannot tell whether a difference is a transcription error or a later change on the official page.</p>')

    body.append("<h2>3. Differences, row by row</h2>")
    body.append('<div class="tablewrap"><table class="wide"><thead><tr><th>Published copy</th><th>Club</th><th>Player</th>'
                '<th>Official practice</th><th>Published practice</th><th>Official game status</th><th>Published game status</th><th>Difference</th><th>Source</th></tr></thead><tbody>')
    for d in recon_rows:
        label, club, player, op, pp, og, pg, kind = d
        body.append(
            f"<tr><td><code>{esc(label)}</code></td><td>{esc(club)}</td><td>{esc(player)}</td><td>{esc(op) or '&mdash;'}</td>"
            f"<td>{esc(pp) or '&mdash;'}</td><td>{chip(og)}</td><td>{chip(pg)}</td><td>{esc(kind)}</td>"
            f'<td><a class="src" href="{SRC}" rel="noopener">official</a></td></tr>')
    body.append("</tbody></table></div>")

    body.append("<h2>4. The official capture, every row</h2>")
    body.append('<p class="muted">Practice status is the page\'s Practice Status column; game status is the Game Status column. Blank game status means the page printed none.</p>')
    body.append('<div class="tablewrap"><table class="wide"><thead><tr><th>Game</th><th>Day</th><th>Club</th><th>Player</th><th>Pos</th>'
                '<th>Injury</th><th>Practice</th><th>Game status</th><th>Source</th></tr></thead><tbody>')
    for r in official_rows:
        body.append(
            f"<tr><td>{esc(r['game'])}</td><td>{esc(r['game_day'])} {esc(r['kickoff_et'])} ET</td><td><b>{esc(r['team'])}</b></td>"
            f"<td>{esc(r['player'])}</td><td>{esc(r['position'])}</td><td>{esc(r['injury'])}</td><td>{esc(r['practice_status'])}</td>"
            f"<td>{chip(r['game_status'])}</td>"
            f'<td><a class="src" href="{SRC}" rel="noopener">official</a></td></tr>')
    body.append("</tbody></table></div>")

    body.append("<h2>5. Notes for review</h2><ul>"
                "<li>The brief stated 279 rows and 2 no-injury sections for this report. The page as captured on "
                f"{CAPTURE_DATE} lists {len(official_rows)} player rows across {len(games)} games and {len(clubs)} clubs. "
                "The 279 figure is not reproduced.</li>"
                "<li>The Lions game-status cells for Kerby Joseph, Cade Mays and D.J. Reed read <b>Out</b> on the official page, and "
                "<b>Out</b> in the published injury page. The blank-cell problem is not present in the current copies.</li>"
                "<li>The JSON copy uses the club code <code>LA</code> for the Rams; the official page and the other copies use <code>LAR</code>.</li>"
                "<li>The official page lists the linebacker as <i>Jacob Hummel</i> (Texans, Groin, Questionable; link slug <code>jake-hummel</code>); the main CSV copy spells it <i>Jake Hummel</i> and omits the official row for Jacob Hummel.</li>"
                "<li>Published copies disagree with the official page for Monday's Chargers-Ravens rows and two Ravens rows (Hawkins, Randall) and for the Rams block in the JSON copy. "
                "Each listed difference was checked against the page text captured here.</li>"
                "<li>Model inputs (originated lines, lineup weights) still read the existing published copy. This page does not change any model output.</li>"
                "</ul>")

    body.append("<h2>6. Scheduled captures of the official report</h2>")
    idx = ROOT / "snapshots/index.csv"
    if idx.exists() and idx.read_text(encoding="utf-8").strip():
        snaps = list(csv.DictReader(idx.open(encoding="utf-8", newline="")))
        body.append('<div class="tablewrap"><table class="wide"><thead><tr><th>Captured (UTC)</th><th>Week</th><th>HTTP</th>'
                    '<th>Bytes</th><th>SHA-256 (first 12)</th><th>Player links</th><th>vs previous</th><th>Stored file</th></tr></thead><tbody>')
        for s_ in snaps:
            body.append(f"<tr><td>{esc(s_['capture_utc'])}</td><td>{esc(s_['week'])}</td><td>{esc(s_['http_status'])}</td>"
                        f"<td>{esc(s_['bytes'])}</td><td><code>{esc(s_['sha256'][:12])}</code></td><td>{esc(s_['player_links'])}</td>"
                        f"<td>{esc(s_['change_vs_previous'])}</td><td><a href=\"https://github.com/sassnarep3-star/FL3/blob/main/{esc(s_['raw_path'])}\">gz</a></td></tr>")
        body.append("</tbody></table></div>")
    else:
        body.append('<p><b>No scheduled capture has run yet.</b> The snapshot workflow '
                    '(<code>.github/workflows/snapshot.yml</code>) runs twice a day Wednesday to Monday, UTC, once it is on <code>main</code>. '
                    'Until a capture exists, this table is empty and the history of the injury report cannot be replayed.</p>')

    html_out = page("Official Week 10 injury capture", "\n".join(body))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_out, encoding="utf-8")
    print(f"built {OUT.relative_to(ROOT)}: {len(official_rows)} official rows, {len(recon_rows)} differences listed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
