#!/usr/bin/env python3
"""FL3 site generator.

Renders a static dashboard site from the verified JSON data files in data/
into docs/ (served by GitHub Pages). Every table row carries source links;
values that cannot be confirmed from an official source are rendered blank
and flagged as unverified.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def esc(v):
    if v is None:
        return ""
    return html.escape(str(v))


def link(url, label=None):
    label = label or url
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def badge(text, kind="info"):
    return f'<span class="badge badge-{kind}">{esc(text)}</span>'


def cell(v):
    """Render a cell: blank values render empty (never inferred)."""
    if v is None or v == "":
        return ""
    return esc(v)


NAV = [
    ("Overview", [
        ("index.html", "Dashboard"),
        ("executive-summary.html", "Executive Summary"),
    ]),
    ("Decisions", [
        ("questions.html", "Questions & Answers"),
        ("suggestions.html", "Suggestions"),
    ]),
    ("NFL Lines", [
        ("lines/strategies.html", "Strategies & Signals"),
        ("lines/validation.html", "Validation Gates"),
        ("lines/leaderboard.html", "Leaderboard"),
        ("lines/market-data.html", "Market Data (Lines)"),
    ]),
    ("Injuries", [
        ("injuries/injury-report.html", "Injury Report"),
        ("injuries/depth-charts.html", "Depth Charts"),
    ]),
    ("League Data", [
        ("standings.html", "2026 Standings"),
    ]),
    ("Review", [
        ("review/repo-review.html", "Repo Review"),
        ("review/flagged-review.html", "Flagged for Review"),
    ]),
]


def page(title, active, content):
    nav_html = []
    for cat, items in NAV:
        nav_html.append(f'<div class="nav-cat"><div class="nav-cat-title">{esc(cat)}</div>')
        for href, label in items:
            cls = "nav-item active" if href == active else "nav-item"
            nav_html.append(f'<a class="{cls}" href="{href}">{esc(label)}</a>')
        nav_html.append("</div>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — FL3</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="brand"><a href="index.html">FL3</a><span class="brand-sub">NFL Lines &amp; Decision Dashboard</span></div>
  <div class="topbar-note">Verified data only · blank &amp; flagged where unverified</div>
</header>
<div class="layout">
  <nav class="sidebar">
    {''.join(nav_html)}
  </nav>
  <main class="content">
    <h1>{esc(title)}</h1>
    {content}
  </main>
</div>
<footer class="footer">
  <p>FL3 — NFL lines research, injury tracking, and decision support. Every table row carries a source link. Values that cannot be confirmed from an official source are left blank and flagged as unverified.</p>
</footer>
</body>
</html>"""


def table(cols, rows, flagged_row=None):
    """cols: list of dicts with key/label/render(row)->html.
    flagged_row: optional fn(row)->bool to mark rows as flagged."""
    head = "".join(f"<th>{esc(c['label'])}</th>" for c in cols)
    body_rows = []
    for r in rows:
        flagged = flagged_row(r) if flagged_row else False
        tds = []
        for c in cols:
            val = c.get("render")(r) if c.get("render") else cell(r.get(c["key"]))
            tds.append(f"<td>{val}</td>")
        flag = f'<td class="flag-col">{badge("Unverified / needs review", "flag")}</td>' if flagged else '<td class="flag-col"></td>'
        body_rows.append(f'<tr class="{"row-flagged" if flagged else ""}">{"".join(tds)}{flag}</tr>')
    return f"""<div class="table-wrap">
<table>
<thead><tr>{head}<th>Flag</th></tr></thead>
<tbody>{''.join(body_rows)}</tbody>
</table>
</div>"""


def src_links(links):
    if not links:
        return ""
    return '<div class="src-links">' + " ".join(link(u) for u in links) + "</div>"


def build_css():
    css = """
:root {
  --bg: #f4f6f9; --card: #ffffff; --ink: #1c2530; --muted: #5c6b7a;
  --line: #dfe5ec; --accent: #14508c; --accent-soft: #e8f0f9;
  --ok: #1a7f4b; --warn: #b45309; --bad: #b42318;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--ink); line-height: 1.45; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar { display: flex; justify-content: space-between; align-items: center; background: #10243a; color: #fff; padding: 14px 28px; flex-wrap: wrap; gap: 8px; }
.brand a { color: #fff; font-size: 22px; font-weight: 700; letter-spacing: 1px; }
.brand-sub { margin-left: 12px; color: #9fb4cc; font-size: 13px; }
.topbar-note { color: #9fb4cc; font-size: 12px; }
.layout { display: flex; max-width: 1280px; margin: 0 auto; }
.sidebar { width: 230px; flex-shrink: 0; padding: 20px 14px; }
.nav-cat { margin-bottom: 16px; }
.nav-cat-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin: 10px 8px 4px; }
.nav-item { display: block; padding: 7px 12px; border-radius: 6px; color: var(--ink); font-size: 14px; }
.nav-item:hover { background: var(--accent-soft); text-decoration: none; }
.nav-item.active { background: var(--accent); color: #fff; }
.content { flex: 1; padding: 26px 30px; min-width: 0; }
h1 { font-size: 24px; margin: 0 0 14px; }
h2 { font-size: 18px; margin: 26px 0 10px; }
p, li { color: var(--ink); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 18px 20px; margin-bottom: 18px; }
.cards { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }
.cards .card { flex: 1 1 200px; margin: 0; }
.stat-num { font-size: 30px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 13px; color: var(--muted); }
.table-wrap { overflow-x: auto; background: var(--card); border: 1px solid var(--line); border-radius: 10px; margin-bottom: 18px; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; white-space: nowrap; }
th, td { padding: 8px 12px; border-bottom: 1px solid var(--line); text-align: left; }
th { background: #eef2f7; font-weight: 600; color: #33445a; position: sticky; top: 0; }
tbody tr:nth-child(even) { background: #fafbfd; }
tbody tr:hover { background: var(--accent-soft); }
.row-flagged { background: #fff4f2; }
.row-flagged:hover { background: #ffe9e5; }
.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 600; }
.badge-info { background: var(--accent-soft); color: var(--accent); }
.badge-ok { background: #e5f4ec; color: var(--ok); }
.badge-warn { background: #fdf1e0; color: var(--warn); }
.badge-flag { background: #fde9e6; color: var(--bad); }
.flag-col { width: 200px; }
.src-links { font-size: 12px; }
.src-links a { margin-right: 8px; }
.note { background: #eef4fb; border-left: 4px solid var(--accent); padding: 10px 14px; border-radius: 6px; font-size: 13.5px; }
.warn-note { background: #fff8ec; border-left: 4px solid var(--warn); padding: 10px 14px; border-radius: 6px; font-size: 13.5px; }
.filter-bar { margin: 10px 0 14px; }
.filter-bar input { padding: 8px 12px; border: 1px solid var(--line); border-radius: 6px; width: 320px; font-size: 14px; }
.footer { max-width: 1280px; margin: 0 auto; padding: 18px 30px 30px 274px; color: var(--muted); font-size: 12.5px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 860px) {
  .layout { flex-direction: column; }
  .sidebar { width: 100%; }
  .footer { padding-left: 30px; }
  .grid-2 { grid-template-columns: 1fr; }
}
"""
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    with open(os.path.join(OUT, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(css)


def render_index(data):
    standings = data["standings"]
    injuries = data["injuries"]
    lines = data["lines"]
    questions = data["questions"]
    suggestions = data["suggestions"]
    flagged = data["review"]["flagged"]
    n_flagged = sum(1 for f in flagged if f["status"] == "Needs review")
    cards = f"""
<div class="cards">
  <div class="card"><div class="stat-num">{len(standings['rows'])}</div><div class="stat-label">Standings rows verified (NFL.com)</div></div>
  <div class="card"><div class="stat-num">{len(injuries['rows'])}</div><div class="stat-label">Injury rows verified (NFL.com, Week 10)</div></div>
  <div class="card"><div class="stat-num">{len(lines['rows'])}</div><div class="stat-label">Week 10 lines tracked (all flagged unverified)</div></div>
  <div class="card"><div class="stat-num">{len(questions['rows'])} / {len(suggestions['rows'])}</div><div class="stat-label">Decision questions / Suggestions proposed</div></div>
  <div class="card"><div class="stat-num">{n_flagged}</div><div class="stat-label">Items flagged for review</div></div>
</div>"""
    cats = ""
    for cat, items in NAV:
        if cat == "Overview" and items[0][0] == "index.html":
            continue
        links = " · ".join(link(href, label) for href, label in items)
        cats += f'<div class="card"><div class="nav-cat-title">{esc(cat)}</div><p>{links}</p></div>'
    content = f"""
{cards}
<div class="card">
  <h2 style="margin-top:0">About this dashboard</h2>
  <p>FL3 collects, organizes, and analyzes NFL data with a full list of requirements: original NFL
  lines generation, signal strategies, a leaderboard competition that rewards top-performing
  strategies, validation gates, correlation values, luck removal, injury tracking with
  starter/backup (2nd/3rd/4th string) deficiency detection for offenses and defenses, and a
  decision-support workflow built on verified sources only.</p>
  <p>Every table row on this site carries a source link to an official site. Values that cannot be
  confirmed from an official source are left blank and flagged as unverified — never inferred.</p>
</div>
<div class="grid-2">
{cats}
</div>"""
    return page("Dashboard", "index.html", content)


def render_executive_summary(data):
    st = data["standings"]
    inj = data["injuries"]
    content = """
<div class="card">
  <h2 style="margin-top:0">Purpose</h2>
  <p>FL3 is a research and decision-support system for generating original NFL betting lines.
  It develops signal strategies for single bets, parlays, and player-prop combinations; treats
  strategy performance as a leaderboard competition with rewards for top performers; requires every
  strategy to pass validation gates; determines correlation values; removes luck from performance
  measurement; and tracks injuries and lineup deficiencies (starters vs 2nd/3rd/4th-string backups)
  on both offense and defense.</p>
</div>
<div class="card">
  <h2 style="margin-top:0">What was verified (this session)</h2>
  <ul>
    <li><b>2026 NFL standings</b> — all 32 teams, transcribed line by line from the official NFL.com league standings page. Source: <a href="https://www.nfl.com/standings/league/2026/reg" target="_blank" rel="noopener noreferrer">nfl.com/standings/league/2026/reg</a>.</li>
    <li><b>Week 10, 2026 injury report</b> — 345 rows covering all 14 Week 10 games (28 teams; 4 teams on bye), transcribed line by line from the official NFL.com injury report. Source: <a href="https://www.nfl.com/injuries" target="_blank" rel="noopener noreferrer">nfl.com/injuries</a>.</li>
    <li><b>Official roster status</b> — NFL.com team roster pages verified as the official source for roster status (ACT / DEV / PUP / TRD). Source: <a href="https://www.nfl.com/teams/kansas-city-chiefs/roster" target="_blank" rel="noopener noreferrer">nfl.com team roster pages</a>.</li>
    <li><b>Betting-lines access check</b> — official sportsbook pages were tested and are <b>not machine-verifiable</b> from this environment (BetMGM geo-wall, Caesars/FanDuel HTTP 500, DraftKings 404). All line values are therefore left blank and flagged unverified on the Market Data page.</li>
    <li><b>Strategy methodology</b> — signal families, validation gates, correlation handling, luck removal, and leaderboard design researched against authoritative analytics sources (FTN DVOA, Sharp Football Analysis, CLV research, luck-adjusted efficiency).</li>
  </ul>
</div>
<div class="card">
  <h2 style="margin-top:0">Key figures (verified)</h2>
  <ul>
    <li>League leaders at the Week 10 snapshot: Buffalo Bills and San Francisco 49ers (7-1, .875). Source: NFL.com standings.</li>
    <li>Lowest: Los Angeles Chargers (0-8, .000). Source: NFL.com standings.</li>
    <li>Week 10 injury report: 345 player entries across 14 games; 28 teams. Source: NFL.com injury report.</li>
    <li>Lines: 14 Week 10 games tracked; all values blank &amp; flagged (official books not machine-readable).</li>
  </ul>
</div>
<div class="card">
  <h2 style="margin-top:0">Decision state — what blocks action</h2>
  <ul>
    <li><b>Lines feed</b>: no strategy can compute edge without verified official market prices. Suggestion S02 proposes the acquisition path; decision required.</li>
    <li><b>Validation thresholds</b>: gate numeric thresholds are proposals pending the owner's decision (Q03 / S03).</li>
    <li><b>Depth-order data</b>: depth-chart ordering is not machine-verifiable from NFL.com; a source is required before deficiency scoring (Q06 / S05 / FL02).</li>
    <li><b>Jurisdiction</b>: not confirmed; affects lines access and data licensing (Q10).</li>
    <li><b>Leaderboard rewards</b>: reward tiers are proposals pending decision (Q07 / S07).</li>
  </ul>
</div>
<div class="card">
  <h2 style="margin-top:0">How decisions are made here</h2>
  <p>No change is implemented without review. The workflow is: (1) read the open questions and gaps
  on the <a href="questions.html">Questions &amp; Answers</a> page; (2) review the proposed paths on
  the <a href="suggestions.html">Suggestions</a> page; (3) choose the best path per decision;
  (4) implement only after selection. Flagged items are published on the
  <a href="review/flagged-review.html">Flagged for Review</a> page with their source links.</p>
</div>"""
    return page("Executive Summary", "executive-summary.html", content)


def render_questions(data):
    qs = data["questions"]["rows"]
    cols = [
        {"key": "id", "label": "ID"},
        {"key": "area", "label": "Area"},
        {"key": "question", "label": "Question"},
        {"key": "why_it_matters", "label": "Why it matters"},
        {"key": "what_we_know", "label": "What we know (verified)"},
        {"key": "what_we_dont_know", "label": "What we don't know"},
        {"key": "priority", "label": "Priority"},
        {"key": "suggested_action", "label": "Suggested next step"},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    content = f"""
<div class="note">These questions must be answered before any decision is made. "What we know" is limited to verified
information with sources; "What we don't know" lists genuine gaps. Suggested actions are proposals — they are
reviewed on the <a href="suggestions.html">Suggestions</a> page before any change is implemented.</div>
{table(cols, qs, flagged_row=lambda r: False)}
"""
    return page("Questions & Answers", "questions.html", content)


def render_suggestions(data):
    sg = data["suggestions"]["rows"]
    cols = [
        {"key": "id", "label": "ID"},
        {"key": "category", "label": "Category"},
        {"key": "suggestion", "label": "Suggestion"},
        {"key": "rationale", "label": "Rationale"},
        {"key": "expected_impact", "label": "Expected impact"},
        {"key": "decision_needed", "label": "Decision needed"},
        {"key": "priority", "label": "Priority"},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    content = f"""
<div class="note">Review process: each suggestion is a proposal. A reviewer compares options against the motivating
question/gap, chooses the best path, and only then is the change implemented. Suggestions are prioritized to improve
decision-making on the site and the strategy pipeline.</div>
{table(cols, sg)}
"""
    return page("Suggestions", "suggestions.html", content)


def render_standings(data):
    st = data["standings"]
    cols = [
        {"key": "team", "label": "Team"},
        {"key": "w", "label": "W"}, {"key": "l", "label": "L"}, {"key": "t", "label": "T"},
        {"key": "pct", "label": "PCT"},
        {"key": "pf", "label": "PF"}, {"key": "pa", "label": "PA"}, {"key": "net", "label": "Net"},
        {"key": "home", "label": "Home"}, {"key": "road", "label": "Road"},
        {"key": "div", "label": "Div"}, {"key": "conf", "label": "Conf"},
        {"key": "strk", "label": "Strk"}, {"key": "last5", "label": "Last 5"},
        {"key": "source", "label": "Source", "render": lambda r: link(st["source"], "NFL.com Standings")},
    ]
    content = f"""
<div class="card">
  <p><b>Dataset:</b> {esc(st['dataset'])} · <b>Retrieved:</b> {esc(st['retrieved'])} ·
  <b>Source:</b> <a href="{esc(st['source'])}" target="_blank" rel="noopener noreferrer">{esc(st['source'])}</a></p>
  <p class="src-links">All 32 teams transcribed row by row from the official NFL.com league standings page. PCT is
  winning percentage; Net is net points (PF − PA).</p>
</div>
{table(cols, st["rows"])}
"""
    return page("2026 NFL Standings", "standings.html", content)


def render_injuries(data):
    inj = data["injuries"]
    cols = [
        {"key": "game", "label": "Game"},
        {"key": "team", "label": "Team"},
        {"key": "player", "label": "Player", "render": lambda r: link(r["player_url"], r["player"])},
        {"key": "position", "label": "Pos"},
        {"key": "injury", "label": "Injury"},
        {"key": "practice", "label": "Practice status"},
        {"key": "status", "label": "Game status"},
        {"key": "source", "label": "Source", "render": lambda r: link(r["source"], "NFL.com Injury Report")},
    ]
    rows_html = table(cols, inj["rows"])
    filter_js = """<script>
function filterInjuries(v) {
  var q = v.toLowerCase().trim();
  document.querySelectorAll('#injury-table tbody tr').forEach(function (tr) {
    tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
  });
}
</script>"""
    content = f"""
<div class="card">
  <p><b>Dataset:</b> {esc(inj['dataset'])} · <b>Retrieved:</b> {esc(inj['retrieved'])} ·
  <b>Source:</b> <a href="{esc(inj['source'])}" target="_blank" rel="noopener noreferrer">{esc(inj['source'])}</a></p>
  <p class="src-links">{esc(inj['note'])}</p>
  <p class="src-links">Teams on bye in Week 10 (no Week 10 injury report): Chicago Bears, Denver Broncos, Tampa Bay
  Buccaneers, Philadelphia Eagles (per official standings).</p>
</div>
<div class="filter-bar">
  <input id="inj-filter" placeholder="Filter by team, player, position, status..." oninput="filterInjuries(this.value)">
</div>
<div id="injury-table">{rows_html}</div>
{filter_js}
"""
    return page("Injury Report (Week 10, 2026)", "injuries/injury-report.html", content)


def render_strategies(data):
    s = data["strategies"]
    sf_cols = [
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Signal"},
        {"key": "description", "label": "Description"},
        {"key": "inputs", "label": "Inputs", "render": lambda r: "<br>".join(esc(x) for x in r.get("inputs", []))},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    bt_cols = [
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Bet type"},
        {"key": "description", "label": "Approach"},
        {"key": "validation_gates", "label": "Gates", "render": lambda r: ", ".join(esc(g) for g in r.get("validation_gates", []))},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    sr_cols = [
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Rule"},
        {"key": "description", "label": "Description"},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    content = f"""
<div class="note">Research-based framework for generating useful NFL betting signals. Each strategy must pass the
validation gates on the <a href="lines/validation.html">Validation Gates</a> page. Correlation values are determined
per strategy (see Suggestion S04); luck is removed via CLV and luck-adjusted metrics (see the
<a href="lines/validation.html">Validation Gates</a> and <a href="lines/leaderboard.html">Leaderboard</a> pages).</div>
<h2>Signal families</h2>
{table(sf_cols, s["signal_families"])}
<h2>Bet-type strategies</h2>
{table(bt_cols, s["bet_types"])}
<h2>Strategy rules</h2>
{table(sr_cols, s["strategy_rules"])}
"""
    return page("Strategies & Signals", "lines/strategies.html", content)


def render_validation(data):
    v = data["validation"]
    cols = [
        {"key": "id", "label": "ID"},
        {"key": "gate", "label": "Gate"},
        {"key": "rule", "label": "Rule"},
        {"key": "pass_criteria", "label": "Pass criteria"},
        {"key": "rationale", "label": "Rationale"},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    content = f"""
<div class="note">Every strategy must pass all applicable gates before it may be scored, promoted, or earn leaderboard
rewards. Threshold values are proposals pending the owner's decision (Questions Q03, Suggestions S03).</div>
{table(cols, v["rows"])}
"""
    return page("Validation Gates", "lines/validation.html", content)


def render_leaderboard(data):
    lb = data["leaderboard"]
    sc_cols = [{"key": "id", "label": "ID"}, {"key": "metric", "label": "Metric"},
               {"key": "description", "label": "Description"},
               {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])}]
    rl_cols = [{"key": "id", "label": "ID"}, {"key": "rule", "label": "Rule"},
               {"key": "description", "label": "Description"},
               {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])}]
    rw_cols = [{"key": "tier", "label": "Tier"}, {"key": "description", "label": "Description"},
               {"key": "status", "label": "Status"}]
    content = f"""
<div class="note">The leaderboard rewards top-performing strategies on luck-adjusted, risk-controlled metrics. Raw
profit alone never earns rewards — this is how luck is kept out of the equation. Reward tiers are proposals pending
the owner's decision (Questions Q07, Suggestions S07).</div>
<h2>Scoring metrics</h2>
{table(sc_cols, lb["scoring"])}
<h2>Rules</h2>
{table(rl_cols, lb["rules"])}
<h2>Reward tiers (proposals)</h2>
{table(rw_cols, lb["rewards"], flagged_row=lambda r: "Proposal" in r.get("status", ""))}
"""
    return page("Leaderboard", "lines/leaderboard.html", content)


def render_market_data(data):
    ld = data["lines"]
    cols = [
        {"key": "game", "label": "Game"},
        {"key": "away", "label": "Away"},
        {"key": "home", "label": "Home"},
        {"key": "spread", "label": "Spread", "render": lambda r: cell(r.get("spread")) or badge("blank", "flag")},
        {"key": "total", "label": "Total", "render": lambda r: cell(r.get("total")) or badge("blank", "flag")},
        {"key": "moneyline", "label": "Moneyline", "render": lambda r: cell(r.get("moneyline")) or badge("blank", "flag")},
        {"key": "status", "label": "Status", "render": lambda r: badge(r.get("status"), "flag")},
        {"key": "sources", "label": "Official source links", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    agg = ld["aggregator_reference"]
    books = ld["official_book_links"]
    book_links = " ".join(link(u, name) for name, u in books.items())
    content = f"""
<div class="warn-note"><b>Verification status:</b> {esc(ld['status_note'])}</div>
<div class="card">
  <p><b>Non-official cross-check reference:</b> {link(agg['url'], agg['label'])} — retrieved {esc(agg['retrieved'])}.
  This aggregator is provided for manual cross-checking only; its values are NOT used to fill any table value,
  per the no-unverified-values policy.</p>
  <p><b>Official book links (manual review):</b></p>
  <div class="src-links">{book_links}</div>
</div>
{table(cols, ld["rows"], flagged_row=lambda r: r.get("spread") is None)}
"""
    return page("Market Data (Lines)", "lines/market-data.html", content)


def render_depth(data):
    d = data["depth"]
    fw_cols = [
        {"key": "id", "label": "ID"},
        {"key": "rule", "label": "Rule"},
        {"key": "description", "label": "Description"},
        {"key": "status", "label": "Status"},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    td = d["team_depth_table"]
    tcols = [
        {"key": "team", "label": "Team"},
        {"key": "qb1", "label": "QB1 (starter)", "render": lambda r: cell(r.get("qb1")) or badge("blank", "flag")},
        {"key": "qb2", "label": "QB2 (2nd string)", "render": lambda r: cell(r.get("qb2")) or badge("blank", "flag")},
        {"key": "qb3", "label": "QB3 (3rd string)", "render": lambda r: cell(r.get("qb3")) or badge("blank", "flag")},
        {"key": "status", "label": "Status", "render": lambda r: badge(r.get("status"), "flag")},
        {"key": "source", "label": "Source", "render": lambda r: link(r["source"], "NFL.com roster")},
    ]
    content = f"""
<div class="note">{esc(d['note'])}</div>
<h2>Detection framework</h2>
{table(fw_cols, d["framework"])}
<h2>Team depth order — QB position (blank &amp; flagged)</h2>
{table(tcols, td["rows"], flagged_row=lambda r: r.get("qb1") is None)}
"""
    return page("Depth Charts", "injuries/depth-charts.html", content)


def render_repo_review(data):
    rv = data["review"]
    cols = [
        {"key": "id", "label": "ID"},
        {"key": "area", "label": "Area"},
        {"key": "finding", "label": "Finding"},
        {"key": "verification", "label": "Verification performed"},
        {"key": "irregularity", "label": "Irregularity"},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    content = f"""
<div class="note">Line-by-line review of the repository. The repo was audited at the start of this session: it
contained only a README and a single initial commit. All work in this project was therefore built from scratch and
verified against official sources. Irregularities are logged below and on the
<a href="review/flagged-review.html">Flagged for Review</a> page.</div>
{table(cols, rv["repo_audit"])}
"""
    return page("Repo Review", "review/repo-review.html", content)


def render_flagged(data):
    fl = data["review"]["flagged"]
    cols = [
        {"key": "id", "label": "ID"},
        {"key": "area", "label": "Area"},
        {"key": "item", "label": "Flagged item"},
        {"key": "reason", "label": "Reason"},
        {"key": "action", "label": "Required action"},
        {"key": "status", "label": "Status", "render": lambda r: badge(r.get("status"), "flag" if r.get("status") == "Needs review" else "warn")},
        {"key": "sources", "label": "Sources", "render": lambda r: src_links(r.get("sources") or [])},
    ]
    content = f"""
<div class="warn-note">All items that are unverified, blocked, or unusual are published here with their source links so
they can be reviewed after the site is live. Flagged items do not block the site — they are requests for review.</div>
{table(cols, fl, flagged_row=lambda r: r.get("status") == "Needs review")}
"""
    return page("Flagged for Review", "review/flagged-review.html", content)


def fix_internal_links(html_str, page_rel_dir):
    """Rewrite root-relative internal hrefs to paths relative to the page's
    directory so the site works when served from GitHub Pages."""
    def repl(m):
        href = m.group(1)
        if href.startswith(("http", "mailto:", "#")):
            return f'href="{href}"'
        target = os.path.normpath(os.path.join("docs", href))
        rel = os.path.relpath(target, os.path.normpath(os.path.join("docs", page_rel_dir)))
        rel = rel.replace(os.sep, "/")
        return f'href="{rel}"'

    return re.sub(r'href="([^"]+)"', repl, html_str)


def main():
    data = {
        "standings": load("standings.json"),
        "injuries": load("injuries.json"),
        "lines": load("lines.json"),
        "questions": load("questions.json"),
        "suggestions": load("suggestions.json"),
        "strategies": load("strategies.json"),
        "validation": load("validation.json"),
        "leaderboard": load("leaderboard.json"),
        "depth": load("depth.json"),
        "review": load("review.json"),
    }
    for dirname in ("", "lines", "injuries", "review"):
        os.makedirs(os.path.join(OUT, dirname) if dirname else OUT, exist_ok=True)

    builders = [
        ("index.html", render_index),
        ("executive-summary.html", render_executive_summary),
        ("questions.html", render_questions),
        ("suggestions.html", render_suggestions),
        ("standings.html", render_standings),
        ("injuries/injury-report.html", render_injuries),
        ("lines/strategies.html", render_strategies),
        ("lines/validation.html", render_validation),
        ("lines/leaderboard.html", render_leaderboard),
        ("lines/market-data.html", render_market_data),
        ("injuries/depth-charts.html", render_depth),
        ("review/repo-review.html", render_repo_review),
        ("review/flagged-review.html", render_flagged),
    ]
    for name, fn in builders:
        path = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rendered = fn(data)
        rel_dir = os.path.dirname(name)
        rendered = fix_internal_links(rendered, rel_dir)
        with open(path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"generated {name}")
    build_css()
    print("generated assets/style.css")


if __name__ == "__main__":
    main()
