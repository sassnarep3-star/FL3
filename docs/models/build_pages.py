#!/usr/bin/env python3
"""
Builds docs/injuries.html and docs/data.html directly from data/*.csv so the
site tables always match the verified CSVs row-for-row. Run after
models/originate_lines.py. Stdlib only.
"""
import csv
import html
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
DOCS = os.path.join(BASE, "docs")

NAV = """  <nav class="site">
    <a href="index.html">Dashboard</a><a href="executive-summary.html">Summary</a>
    <a href="requirements.html">Requirements</a><a href="suggestions.html">Suggestions</a>
    <a href="lines.html">Lines</a><a href="injuries.html">Injuries &amp; Depth</a>
    <a href="strategies.html">Strategies</a><a href="leaderboard.html">Leaderboard</a>
    <a href="methodology.html">Methodology</a><a href="data.html">Data</a>
    <a href="sources.html">Sources</a><a href="flagged.html">Flagged</a>
  </nav>"""


def page(title, active, body, subtitle):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — FL3</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site">
  <div class="brand"><h1>FL3 · NFL Decision Intelligence</h1><span class="tag">{subtitle}</span></div>
{NAV.replace(f'href="{active}"', f'class="active" href="{active}"')}
</header>
<main>
{body}
</main>
<footer class="site">FL3 · this page is generated from the verified CSVs in data/ by models/build_pages.py — rows match the CSVs exactly</footer>
</body>
</html>
"""


def esc(s):
    return html.escape(str(s if s is not None else ""))


def src_chip(url, label="source"):
    if not url:
        return '<span class="badge b-flag">no source</span>'
    return f'<a class="src" href="{esc(url)}">{esc(label)}</a>'


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------- injuries page
def build_injuries():
    inj = read_csv("2026-week10-injuries.csv")
    defi = read_csv("2026-week10-depth-deficiencies.csv")

    games = read_csv("2026-week10-games.csv")
    game_label = {}
    for g in games:
        if g["game_id"] == "BYE":
            continue
        note = f" — {g['note']}" if g["note"] else ""
        game_label[g["game_id"]] = (
            f"{g['away']} at {g['home']} · {g['date']} {g['time_et']} · {g['tv']}{note}")

    # deficiency scoreboard
    score = defaultdict(float)
    for r in defi:
        score[(r["team"], r["side"])] += float(r["deficiency_points"])
    top = sorted(score.items(), key=lambda kv: -kv[1])

    cards = f"""
<div class="cards">
  <div class="card"><div class="num">{len(inj)}</div><div class="lbl">rows on the official Week 10 report (every row linked)</div></div>
  <div class="card"><div class="num">{sum(1 for r in inj if r['status']=='OUT')}</div><div class="lbl">OUT</div></div>
  <div class="card"><div class="num">{sum(1 for r in inj if r['status']=='DOUBTFUL')}</div><div class="lbl">DOUBTFUL</div></div>
  <div class="card"><div class="num">{sum(1 for r in inj if r['status']=='QUESTIONABLE')}</div><div class="lbl">QUESTIONABLE</div></div>
  <div class="card"><div class="num">{len(defi)}</div><div class="lbl">OUT/DOUBTFUL deficiency rows</div></div>
  <div class="card"><div class="num">{sum(1 for r in defi if r['expected_replacement'])}</div><div class="lbl">rows with chart-verified replacement</div></div>
</div>"""

    score_rows = "".join(
        f"<tr><td>{esc(t)}</td><td>{esc(s)}</td><td class='num'>{v:.2f}</td>"
        f"<td>{'OFF' if s=='OFF' else 'DEF/ST'} absences (OUT/DOUBTFUL) on the official report"
        f"</td><td><a class='src' href='https://www.nfl.com/news/nfl-week-10-injury-report-2026-season'>Official report</a></td></tr>"
        for (t, s), v in top)

    repl_rows = "".join(
        f"<tr><td>{esc(r['team'])}</td><td>{esc(r['position'])}</td><td>{esc(r['player_out'])}</td>"
        f"<td><span class='badge b-flag'>{esc(r['player_status'])}</span></td>"
        f"<td>{esc(r['player_tier'])}</td><td><strong>{esc(r['expected_replacement'])}</strong></td>"
        f"<td>{esc(r['replacement_tier'])}</td><td class='num'>{esc(r['deficiency_points'])}</td>"
        f"<td>{src_chip(r['source_url'], 'report')}{src_chip(r['tier_source_url'], 'depth chart')}</td>"
        f"<td>{esc(r['flag'])}</td></tr>"
        for r in sorted(defi, key=lambda r: (r["team"], r["position"]))
        if r["expected_replacement"])

    flagged_rows = "".join(
        f"<tr><td>{esc(r['team'])}</td><td>{esc(r['position'])}</td><td>{esc(r['player_out'])}</td>"
        f"<td><span class='badge b-flag'>{esc(r['player_status'])}</span></td>"
        f"<td></td><td><em>blank — unverified</em></td><td></td>"
        f"<td class='num'>{esc(r['deficiency_points'])}</td>"
        f"<td>{src_chip(r['source_url'], 'report')}</td>"
        f"<td>{esc(r['flag'])}</td></tr>"
        for r in sorted(defi, key=lambda r: (r["team"], r["position"]))
        if not r["expected_replacement"])

    by_game = defaultdict(list)
    for r in inj:
        by_game[r["game_id"]].append(r)
    game_blocks = []
    for gid in sorted(by_game):
        rows = "".join(
            f"<tr><td>{esc(r['team'])}</td><td>{esc(r['player'])}</td><td>{esc(r['position'])}</td>"
            f"<td>{esc(r['side'])}</td><td>{esc(r['injury'])}</td>"
            f"<td><span class='badge {'b-flag' if r['status']=='OUT' else 'b-unv'}'>{esc(r['status'])}</span></td>"
            f"<td>{esc(r['depth_tier'])}</td><td>{esc(r['expected_replacement'])}</td>"
            f"<td>{src_chip(r['source_url'], 'report')}{src_chip(r['tier_source_url'], 'chart') if r['tier_source_url'] else ''}</td>"
            f"<td>{esc(r['flag'])}</td></tr>"
            for r in sorted(by_game[gid], key=lambda r: (r["team"], r["status"], r["player"])))
        label = game_label.get(gid, gid)
        game_blocks.append(f"""
  <h3>{esc(gid)} · {esc(label)}</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Team</th><th>Player</th><th>Pos</th><th>Side</th><th>Injury</th><th>Status</th><th>Depth tier</th><th>Expected replacement</th><th>Sources</th><th>Flag</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>""")

    body = f"""
<div class="section">
  <h2>Week 10 Injury &amp; Depth-Deficiency Tracker</h2>
  <p class="lead">Source of truth: the official NFL.com Week 10 game-status report (every row linked).
  Depth tiers (1st–2nd–3rd–4th string) and replacements come only from club-published depth charts;
  where no chart row exists, the cells stay <strong>blank and flagged</strong> — never inferred.
  Deficiency points = design weights (see <a href="methodology.html">Methodology</a>), not measurements.</p>
  {cards}
  <h3>Deficiency scoreboard (OUT/DOUBTFUL weight sums)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Team</th><th>Side</th><th class="num">Deficiency pts</th><th>Basis</th><th>Source</th></tr></thead>
    <tbody>{score_rows}</tbody>
  </table></div>
  <h3>Chart-verified replacement spotlight (2nd/3rd/4th string forced up)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Team</th><th>Pos</th><th>Player out</th><th>Status</th><th>Out tier</th><th>Expected replacement</th><th>Repl. tier</th><th class="num">Def pts</th><th>Sources</th><th>Flag</th></tr></thead>
    <tbody>{repl_rows}</tbody>
  </table></div>
  <h3>Absences with NO verified replacement (blank + flagged)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Team</th><th>Pos</th><th>Player out</th><th>Status</th><th>Out tier</th><th>Replacement</th><th>Repl. tier</th><th class="num">Def pts</th><th>Source</th><th>Flag</th></tr></thead>
    <tbody>{flagged_rows}</tbody>
  </table></div>
  <div class="callout warn"><strong>Chart-vs-report irregularities:</strong> GB's club chart (Nov 10) omits
  Micah Parsons although the official report lists him OUT; DET's chart omits Kerby Joseph (also OUT on the
  report); MIN's chart lists Kirk Cousins 4th at QB days after trading for him. HOU's chart is an image
  (unreadable) and SF's chart page returned HTTP 500. All are documented on
  <a href="flagged.html">Flagged for Review</a>.</div>
  {''.join(game_blocks)}
</div>"""
    return page("Injuries & Depth", "injuries.html", body,
                "official Week 10 statuses · verified depth tiers · blanks are flagged")


# ------------------------------------------------------------------- data page
def build_data():
    std = read_csv("2026-standings.csv")
    g10 = read_csv("2026-week10-games.csv")
    g11 = read_csv("2026-week11-games.csv")
    corr = read_csv("correlation-matrix.csv")

    def game_rows(rows):
        out = []
        for g in rows:
            if g["game_id"] == "BYE":
                out.append(f"<tr><td colspan='7'><em>Bye:</em> {esc(g['home'])} "
                           f"{src_chip(g['source_url'], 'NFL.com')}</td></tr>")
                continue
            out.append(
                f"<tr><td>{esc(g['game_id'])}</td><td>{esc(g['away'])}</td><td>{esc(g['home'])}</td>"
                f"<td>{esc(g['date'])}</td><td>{esc(g['time_et'])}</td><td>{esc(g['tv'])}</td>"
                f"<td>{esc(g['note'])} {src_chip(g['source_url'], 'NFL.com')}</td></tr>")
        return "".join(out)

    std_rows = "".join(
        f"<tr><td>{esc(r['team_key'])}</td><td>{esc(r['team'])}</td>"
        f"<td class='num'>{esc(r['W'])}-{esc(r['L'])}-{esc(r['T'])}</td>"
        f"<td class='num'>{esc(r['games'])}</td><td class='num'>{esc(r['PF'])}</td>"
        f"<td class='num'>{esc(r['PA'])}</td><td class='num'>{esc(r['net_pts'])}</td>"
        f"<td class='num'>{esc(r['PF_pg'])}</td><td class='num'>{esc(r['PA_pg'])}</td>"
        f"<td class='num'>{esc(r['net_pg'])}</td><td class='num'>{esc(r['win_pct'])}</td>"
        f"<td>{esc(r['streak'])}</td><td>{src_chip(r['source_url'], 'NFL.com')}</td></tr>"
        for r in std)

    def flag_badge(flag):
        if not flag:
            return ""
        return '<span class="badge b-flag">' + esc(flag) + "</span>"

    corr_rows = "".join(
        f"<tr><td>{esc(r['metric_a'])}</td><td>{esc(r['metric_b'])}</td>"
        f"<td class='num'>{esc(r['pearson_r'])}</td><td class='num'>{esc(r['n'])}</td>"
        f"<td>{esc(r['basis'])}</td>"
        f"<td>{src_chip(r['source_url'], 'source') if r['source_url'] else ''}</td>"
        f"<td>{flag_badge(r['flag'])}</td></tr>"
        for r in corr)

    body = f"""
<div class="section">
  <h2>Data Hub — all verified entries</h2>
  <p class="lead">Every table below is generated from the CSVs in <code>data/</code> (which link their
  sources per row). CSVs are the machine-readable source of truth for the whole project.</p>

  <h3>2026 standings (through TNF, Nov 12, 2026) — all 32 teams</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Key</th><th>Team</th><th class="num">W-L-T</th><th class="num">G</th><th class="num">PF</th><th class="num">PA</th><th class="num">Net</th><th class="num">PF/g</th><th class="num">PA/g</th><th class="num">Net/g</th><th class="num">Win%</th><th>Strk</th><th>Source</th></tr></thead>
    <tbody>{std_rows}</tbody>
  </table></div>

  <h3>Week 10 slate (14 games)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>ID</th><th>Away</th><th>Home</th><th>Date</th><th>Time</th><th>TV</th><th>Notes &amp; source</th></tr></thead>
    <tbody>{game_rows(g10)}</tbody>
  </table></div>

  <h3>Week 11 lookahead (13 games)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>ID</th><th>Away</th><th>Home</th><th>Date</th><th>Time</th><th>TV</th><th>Notes &amp; source</th></tr></thead>
    <tbody>{game_rows(g11)}</tbody>
  </table></div>

  <h3>Correlation matrix (computed from the standings above)</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>Metric A</th><th>Metric B</th><th class="num">Pearson r</th><th class="num">n</th><th>Basis</th><th>Source</th><th>Flag</th></tr></thead>
    <tbody>{corr_rows}</tbody>
  </table></div>

  <h3>Machine-readable files</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>File</th><th>Contents</th><th>Rows</th></tr></thead>
    <tbody>
      <tr><td><a href="../data/2026-standings.csv">data/2026-standings.csv</a></td><td>standings + per-game rates (each row links NFL.com)</td><td class="num">32</td></tr>
      <tr><td><a href="../data/2026-week10-games.csv">data/2026-week10-games.csv</a></td><td>Week 10 slate incl. byes</td><td class="num">18</td></tr>
      <tr><td><a href="../data/2026-week11-games.csv">data/2026-week11-games.csv</a></td><td>Week 11 slate incl. byes</td><td class="num">19</td></tr>
      <tr><td><a href="../data/2026-week10-injuries.csv">data/2026-week10-injuries.csv</a></td><td>official Week 10 report, every row + depth tiers + flags</td><td class="num">160</td></tr>
      <tr><td><a href="../data/2026-week10-depth-deficiencies.csv">data/2026-week10-depth-deficiencies.csv</a></td><td>OUT/DOUBTFUL deficiency tracker</td><td class="num">76</td></tr>
      <tr><td><a href="../data/2026-week10-lines.csv">data/2026-week10-lines.csv</a></td><td>originated lines vs market + edges + flags</td><td class="num">13</td></tr>
      <tr><td><a href="../data/correlation-matrix.csv">data/correlation-matrix.csv</a></td><td>computed correlations + blank flagged cells</td><td class="num">10</td></tr>
      <tr><td><a href="../models/originate_lines.py">models/originate_lines.py</a></td><td>the deterministic engine that produced all of the above</td><td class="num">—</td></tr>
    </tbody>
  </table></div>
</div>"""
    return page("Data Hub", "data.html", body,
                "standings · schedules · correlations · CSVs with per-row sources")


with open(os.path.join(DOCS, "injuries.html"), "w", encoding="utf-8") as f:
    f.write(build_injuries())
with open(os.path.join(DOCS, "data.html"), "w", encoding="utf-8") as f:
    f.write(build_data())

# ---------------------------------------------------------------------------
# Copy repo files that the site links to into docs/ so GitHub Pages (which
# serves only docs/) has no broken links. Root copies remain the source of truth.
# ---------------------------------------------------------------------------
import shutil

for src, dst in [
    ("data", "docs/data"),
    ("research", "docs/research"),
    ("models", "docs/models"),
]:
    os.makedirs(os.path.join(BASE, dst), exist_ok=True)
    for fn in os.listdir(os.path.join(BASE, src)):
        s = os.path.join(BASE, src, fn)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(BASE, dst, fn))
print("built docs/injuries.html and docs/data.html from data/*.csv; synced docs/data, docs/research, docs/models")
