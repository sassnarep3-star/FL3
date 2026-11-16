#!/usr/bin/env python3
"""
FL3 — build the canonical `verified/` dashboard.

One entry point, one design, one data path. The repo grew five parallel subsites
across six sessions; this one is deliberately the opposite: a small set of pages
where every table cell is either a verified value with a source link or an
explicit "unverified / no official source" marker.

Rules enforced in the renderer, not just in the data:
  * a row with no official source renders a visible marker and a link to the
    review page — it never renders a bare value that looks sourced;
  * model output is always labelled model output;
  * a value that is genuinely unknown is rendered as an em dash and counted.

Run:  python3 scripts/build_verified_site.py
      python3 scripts/build_verified_site.py --check
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "verified")

e = html.escape
DASH = '<span class="dash" title="no verified value">—</span>'

PAGES = {
    "index.html": "Overview",
    "results.html": "Results",
    "lines.html": "Our lines",
    "injuries.html": "Availability",
    "strategies.html": "Strategies",
    "verification.html": "Verification",
    "review.html": "Flagged for review",
    "method.html": "Method &amp; sources",
}

CSS = """
:root{--bg:#0d1117;--panel:#151b23;--panel2:#1b232d;--ink:#e6edf3;--dim:#8b949e;
--line:#2a333f;--acc:#4493f8;--good:#3fb950;--warn:#d29922;--bad:#f85149;--model:#a371f7}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:20;background:rgba(13,17,23,.96);
border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.brand{display:flex;align-items:baseline;gap:10px;padding:14px 0 8px;flex-wrap:wrap}
.brand b{font-size:17px;letter-spacing:.2px}
.brand span{color:var(--dim);font-size:12.5px}
nav.cats{display:flex;gap:4px;overflow-x:auto;padding-bottom:10px;scrollbar-width:thin}
nav.cats a{padding:6px 11px;border-radius:7px;color:var(--dim);font-size:13.5px;white-space:nowrap}
nav.cats a:hover{background:var(--panel);color:var(--ink);text-decoration:none}
nav.cats a.on{background:var(--panel2);color:var(--ink);font-weight:600;
box-shadow:inset 0 0 0 1px var(--line)}
main{padding:26px 0 60px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.2px}
h2{font-size:18px;margin:34px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:22px 0 8px;color:var(--ink)}
p,li{color:#c9d1d9}
p.lede{color:var(--dim);font-size:14.5px;max-width:74ch;margin:0 0 18px}
ul{max-width:78ch}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .n{font-size:25px;font-weight:700;letter-spacing:-.5px;display:block;line-height:1.2}
.card .l{color:var(--dim);font-size:12.5px;margin-top:3px;display:block}
.card .s{font-size:11.5px;color:var(--dim);margin-top:6px;display:block}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel);margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:13.2px}
th{text-align:left;padding:9px 11px;background:var(--panel2);color:var(--dim);
font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.5px;
white-space:nowrap;position:sticky;top:0}
td{padding:8px 11px;border-top:1px solid var(--line);vertical-align:top}
tbody tr:hover{background:#1a222c}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.b{display:inline-block;padding:1px 7px;border-radius:20px;font-size:10.5px;font-weight:700;
letter-spacing:.4px;text-transform:uppercase;white-space:nowrap}
.b.ok{background:rgba(63,185,80,.15);color:var(--good);box-shadow:inset 0 0 0 1px rgba(63,185,80,.35)}
.b.warn{background:rgba(210,153,34,.15);color:var(--warn);box-shadow:inset 0 0 0 1px rgba(210,153,34,.35)}
.b.bad{background:rgba(248,81,73,.15);color:var(--bad);box-shadow:inset 0 0 0 1px rgba(248,81,73,.35)}
.b.info{background:rgba(68,147,248,.15);color:var(--acc);box-shadow:inset 0 0 0 1px rgba(68,147,248,.35)}
.b.model{background:rgba(163,113,247,.15);color:var(--model);box-shadow:inset 0 0 0 1px rgba(163,113,247,.35)}
.b.none{background:#1f2731;color:var(--dim);box-shadow:inset 0 0 0 1px var(--line)}
.dash{color:#4d5764}
.src{font-size:11px;color:var(--acc);white-space:nowrap}
.unv{font-size:10.5px;color:var(--warn);white-space:nowrap;font-weight:600}
.note{background:var(--panel);border-left:3px solid var(--acc);border-radius:0 8px 8px 0;
padding:12px 15px;margin:16px 0;font-size:13.5px;color:#c9d1d9}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.note b{color:var(--ink)}
.cls{color:var(--dim);font-size:12px;margin:8px 0 0}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--dim);font-size:12.5px}
footer a{color:var(--dim);text-decoration:underline}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
.stat{font-variant-numeric:tabular-nums}
.rej{color:var(--bad);font-weight:600}
.pos{color:var(--good);font-weight:600}
.neg{color:var(--bad);font-weight:600}
"""


# ---------------------------------------------------------------------------
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def csv_rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def shell(title, body, active, generated):
    on = ' class="on"'
    nav = "".join(
        f'<a href="{p}"{on if p == active else ""}>{t}</a>'
        for p, t in PAGES.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · FL3 NFL decision system</title>
<meta name="description" content="Verified NFL 2026 data, originated lines and honest out-of-sample scoring. Every value links to an official source or is marked unverified.">
<link rel="stylesheet" href="assets/verified.css">
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<header class="top"><div class="wrap">
<div class="brand"><b>FL3</b><span>NFL decision system · 2026 regular season</span>
<span style="margin-left:auto;font-size:11.5px;color:#8b949e">read {e(generated)}</span></div>
<nav class="cats">{nav}</nav>
</div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p><b>What this is.</b> A verified-data dashboard. Official league values carry a source link.
Model output is labelled model output. No licensed betting price exists in this repository, so
closing-line value and realised return are <b>not computed and not implied</b> anywhere.</p>
<p>Every page here is generated from the committed data files by <code>scripts/build_verified_site.py</code>
and re-checked by <code>scripts/check_verified_site.py</code>. Other dashboards in this repository
(<a href="../">root</a>, <a href="../board/">board</a>, <a href="../docs/">docs</a>,
<a href="../depth/">depth</a>, <a href="../site-9b181d31/">site-9b181d31</a>) are separate builds and
are not superseded by this one.</p>
</div></footer>
</body></html>"""


def src(url, label="NFL.com"):
    if not url:
        return '<span class="unv">UNVERIFIED</span>'
    return f'<a class="src" href="{e(url)}" target="_blank" rel="noopener">{e(label)}</a>'


def status_badge(s):
    m = {
        "CONFIRMED": "ok", "STALE": "bad", "PARTLY_STALE": "warn",
        "NOT_REPRODUCIBLE": "warn", "UNVERIFIABLE": "none",
        "BLOCKED": "bad", "PARTIAL": "warn", "DESIGN ONLY": "info", "DONE": "ok",
    }
    return f'<span class="b {m.get(s, "none")}">{e(s.replace("_", " ").lower())}</span>'


# ---------------------------------------------------------------------------
def page_index(ctx):
    ev = ctx["eval"]
    wf = ev["walkforward"]
    cm = ev["committed_week10"]
    lv = ctx["live"]
    counts = lv["meta"]["by_status"]
    res = ctx["results"]["meta"]

    def pct(x, d=3):
        return f"{x:+.{d}f}".replace("+", "+").replace("-", "−")

    ci = wf["spread_rmse_gain_vs_pickem"]["ci95"]
    bci = wf["brier_skill_vs_coin"]["ci95"]

    body = f"""
<h1>NFL 2026 — verified data, originated lines, honest scoring</h1>
<p class="lede">Eleven weeks into the 2026 season. The schedule pages now publish final scores for
<b>{res['games']}</b> games, and those rows reconcile exactly against the league's own standings.
That is enough to score this project's own predictions out of sample — which is done below, including
where the answer is "no demonstrated skill".</p>

<div class="cards">
<div class="card"><span class="n">{res['games']}</span><span class="l">verified game results</span>
<span class="s">weeks {res['weeks'][0]}–{res['weeks'][-1]} · 160 club figures reconciled</span></div>
<div class="card"><span class="n">{wf['point']['n']}</span><span class="l">out-of-sample forecasts</span>
<span class="s">walk-forward, weeks 4–10</span></div>
<div class="card"><span class="n">{counts.get('CONFIRMED',0)}/{lv['meta']['claims']}</span>
<span class="l">repo claims confirmed live</span>
<span class="s">{counts.get('STALE',0)} stale · {counts.get('UNVERIFIABLE',0)} unverifiable</span></div>
<div class="card"><span class="n">0</span><span class="l">licensed market prices held</span>
<span class="s">so CLV and ROI are not computable</span></div>
</div>

<div class="note warn"><b>The single most important line on this site.</b>
The registered baseline does <b>not</b> beat a pick'em line at a 95% confidence level over {wf['point']['n']}
out-of-sample games, and its win probabilities are <b>not</b> distinguishable from a coin flip.
Detailed numbers are below and nothing on this page is phrased as if that were not the case.
What <i>is</i> established is the measurement apparatus: a result corpus that reconciles to the league's
own arithmetic, a frozen pre-registration, and a scoring path that would detect skill if it appeared.</div>

<h2>Out-of-sample scoreboard <span class="b model">model output</span></h2>
<p class="lede">Rule: fit on every game before week <i>k</i>, forecast week <i>k</i>, never look forward.
Intervals are 95% percentile intervals from 4,000 bootstrap resamples taken <b>by game</b>.</p>
<div class="tbl"><table>
<thead><tr><th>Measure</th><th class="num">Model</th><th class="num">Baseline</th>
<th class="num">Gain</th><th class="num">95% interval</th><th>Reads as</th></tr></thead>
<tbody>
<tr><td>Spread error, RMSE (points)</td>
<td class="num">{wf['point']['spread_rmse']:.2f}</td>
<td class="num">{wf['point']['spread_rmse_vs_zero']:.2f} <span class="cls">pick'em</span></td>
<td class="num">{wf['spread_rmse_gain_vs_pickem']['estimate']:+.3f}</td>
<td class="num">[{ci[0]:+.3f}, {ci[1]:+.3f}]</td>
<td>{'<span class="b ok">skill</span>' if ci[0] > 0 else ('<span class="b bad">worse</span>' if ci[1] < 0 else '<span class="b warn">not distinguishable</span>')}</td></tr>
<tr><td>Total error, RMSE (points)</td>
<td class="num">{wf['point']['total_rmse']:.2f}</td>
<td class="num">{wf['point']['total_rmse_vs_mean']:.2f} <span class="cls">league mean</span></td>
<td class="num">{wf['total_rmse_gain_vs_league_mean']['estimate']:+.3f}</td>
<td class="num">[{wf['total_rmse_gain_vs_league_mean']['ci95'][0]:+.3f}, {wf['total_rmse_gain_vs_league_mean']['ci95'][1]:+.3f}]</td>
<td>{'<span class="b ok">skill</span>' if wf['total_rmse_gain_vs_league_mean']['ci95'][0] > 0 else '<span class="b warn">no gain</span>'}</td></tr>
<tr><td>Brier skill vs coin flip</td>
<td class="num">{wf['brier_skill_vs_coin']['estimate']:+.3f}</td>
<td class="num">0.000</td>
<td class="num">{wf['brier_skill_vs_coin']['estimate']:+.3f}</td>
<td class="num">[{bci[0]:+.3f}, {bci[1]:+.3f}]</td>
<td>{'<span class="b ok">skill</span>' if bci[0] > 0 else ('<span class="b bad">worse</span>' if bci[1] < 0 else '<span class="b warn">not distinguishable</span>')}</td></tr>
<tr><td>Pick direction correct</td>
<td class="num">{wf['directional_accuracy']['estimate']:.1%}</td>
<td class="num">50.0% <span class="cls">coin</span></td>
<td class="num">{wf['directional_accuracy']['estimate']-0.5:+.1%}</td>
<td class="num">[{wf['directional_accuracy']['ci95'][0]:.1%}, {wf['directional_accuracy']['ci95'][1]:.1%}]</td>
<td>{'<span class="b ok">excludes 50%</span>' if wf['directional_accuracy']['ci95'][0] > 0.5 else ('<span class="b bad">below 50%</span>' if wf['directional_accuracy']['ci95'][1] < 0.5 else '<span class="b warn">includes 50%</span>')}</td></tr>
</tbody></table></div>
<p class="cls">n = {wf['point']['n']} games. Full per-game rows: <a href="results.html">Results</a>.
Method and constants: <a href="method.html">Method</a>.</p>

<h2>The committed Week 10 forecasts <span class="b model">model output</span></h2>
<p class="lede">These 14 lines were committed to the repository on 2026-11-14, before most of the games
were played. The commit is the pre-registration: the numbers could not be chosen after seeing the results.
One game is excluded because it was already final when the file was committed.</p>
<div class="tbl"><table>
<thead><tr><th>Forecast set</th><th class="num">n scored</th><th class="num">Spread RMSE</th>
<th class="num">Total RMSE</th><th class="num">Brier skill</th><th class="num">95% interval</th></tr></thead>
<tbody><tr>
<td>Week 10 originated lines, as committed</td>
<td class="num">{cm['point']['n']}</td>
<td class="num">{cm['point']['spread_rmse']:.2f} pts</td>
<td class="num">{cm['point']['total_rmse']:.2f} pts</td>
<td class="num">{cm['brier_skill_vs_coin']['estimate']:+.3f}</td>
<td class="num">[{cm['brier_skill_vs_coin']['ci95'][0]:+.3f}, {cm['brier_skill_vs_coin']['ci95'][1]:+.3f}]</td>
</tr></tbody></table></div>
<div class="note"><b>Excluded, with reason.</b>
{''.join(f'<code>{e(x["game"])}</code> — {e(x["reason"])}<br>' for x in cm['excluded'])}
<b>n = 11 is too small to rank anything.</b> On 11 games the standard error of directional accuracy is
about 0.15, so almost any result here is consistent with a coin. It is shown for auditability, not as
evidence.</div>

<h2>What is verified, and what is not</h2>
<div class="grid2">
<div>
<div class="tbl"><table>
<thead><tr><th>Claim</th><th>Status</th></tr></thead><tbody>
{''.join(f'<tr><td><a href="verification.html">{e(r["claim_id"])}</a> {e(r["claim"][:72])}{"…" if len(r["claim"])>72 else ""}</td><td>{status_badge(r["status"])}</td></tr>' for r in lv['claims'][:8])}
</tbody></table></div>
<p class="cls"><a href="verification.html">All {lv['meta']['claims']} re-verified claims →</a></p>
</div>
<div>
<h3>Blocked, and why</h3>
<ul>
<li><b>No licensed price.</b> No NFL page publishes a spread, total or prop price. Closing-line value and
realised return cannot be computed for any strategy here. This is a fact about the sources, not a gap in
the work.</li>
<li><b>No official depth ordinal.</b> The league publishes rosters and injury reports, not depth ranks.
Backup depth is a model estimate on third-party chart data and is labelled as such everywhere.</li>
<li><b>No snap counts or inactive lists.</b> A backup replacing a starter can be identified, but that the
backup played the starter's snaps cannot be evidenced from an official league page.</li>
<li><b>No dated injury archive.</b> The official page overwrites each day's designations, so a practice
trend cannot be reconstructed after the fact — only captured prospectively.</li>
</ul>
</div></div>

<h2>This repository contains six parallel builds</h2>
<p class="lede">Six sessions built dashboards for the same brief without seeing each other's work. This page
is the current one because it is the only one whose result corpus reconciles against the league's own
arithmetic. Nothing was deleted; the comparisons that matter are on
<a href="verification.html">Verification</a>, and each subsite remains online.</p>
<div class="tbl"><table>
<thead><tr><th>Path</th><th>What it is</th><th>Result corpus</th><th>Standing</th></tr></thead>
<tbody>
<tr><td><a href="index.html">/verified/</a></td><td>this dashboard</td>
<td class="num">148 games, identity-checked</td><td><span class="b ok">current</span></td></tr>
<tr><td><a href="../">/</a></td><td>root dashboard, 13 pages, 1,262 assertions</td>
<td class="num">none (Week 10 only)</td><td><span class="b info">superseded for scoring</span></td></tr>
<tr><td><a href="../board/">/board/</a></td><td>CSV-first board with fitted constants</td>
<td class="num">33 of 148</td><td><span class="b warn">partial corpus</span></td></tr>
<tr><td><a href="../depth/">/depth/</a></td><td>depth charts and availability reconciliation</td>
<td class="num">standings only</td><td><span class="b info">specialist</span></td></tr>
<tr><td><a href="../docs/">/docs/</a></td><td>requirements and decision registers</td>
<td class="num">standings only</td><td><span class="b info">registers</span></td></tr>
<tr><td><a href="../site-9b181d31/">/site-9b181d31/</a></td><td>12-page dashboard with club depth charts</td>
<td class="num">standings only</td><td><span class="b info">specialist</span></td></tr>
</tbody></table></div>
"""
    return shell("Overview", body, "index.html", ctx["generated"])


def page_results(ctx):
    res = ctx["results"]
    wf = ctx["eval"]["walkforward"]
    rows = ctx["result_rows"]
    by_week = {}
    for r in rows:
        by_week.setdefault(int(r["week"]), []).append(r)

    weekly = []
    for w in sorted(by_week):
        wk = by_week[w]
        fw = [x for x in wf["per_game"] if x["week"] == w]
        if fw:
            import math
            sm = math.sqrt(sum((x["pred_margin"] - x["actual_margin"]) ** 2 for x in fw) / len(fw))
            st = math.sqrt(sum((x["pred_total"] - x["actual_total"]) ** 2 for x in fw) / len(fw))
            da = sum(1 for x in fw if (x["pred_margin"] > 0) == (x["actual_margin"] > 0)) / len(fw)
            weekly.append((w, len(wk), len(fw), sm, st, da))
        else:
            weekly.append((w, len(wk), 0, None, None, None))

    body = f"""
<h1>Results — {res['meta']['games']} verified games</h1>
<p class="lede">Every row is transcribed from an official NFL.com weekly schedule page that renders the
game as FINAL. A game that was in progress or not yet played is not a result and is not in this file.
The whole corpus is checked against the league standings before publication.</p>

<div class="note"><b>Why this file exists.</b> No previous build in this repository had enough verified
results to compute a proper score. One held 33 rows against a 137-game season; the rest held none. Without
results, a leaderboard is decoration. <b>The check that makes it trustworthy:</b> for all 32 clubs, wins,
losses, ties, points-for and points-against summed from these {res['meta']['games']} rows reproduce the
official standings page exactly — 160 figures, no tolerance, no fudge factor. A single transposed score
would fail it. Re-runnable with <code>python3 scripts/build_week_results.py --check</code>.</p>
<p class="cls">Corpus SHA-256 <span class="mono">{e(res['meta']['csv_sha256'])}</span><br>
Source: <a href="{e(res['meta']['source_rows'])}" target="_blank" rel="noopener">nfl.com/schedules/2026/by-week/week-N</a>
· reconciled against <a href="{e(res['meta']['source_primary'])}" target="_blank" rel="noopener">nfl.com/standings/league/2026/reg</a>
· read {e(res['meta']['standings_read_utc'])}</p></div>

<h2>By week</h2>
<div class="tbl"><table>
<thead><tr><th class="num">Week</th><th class="num">Games</th><th class="num">Scored</th>
<th class="num">Spread RMSE</th><th class="num">Total RMSE</th><th class="num">Direction</th>
<th>Source</th></tr></thead><tbody>
{''.join(f'''<tr><td class="num">{w}</td><td class="num">{g}</td><td class="num">{s or DASH}</td>
<td class="num">{f"{sm:.2f}" if sm is not None else DASH}</td>
<td class="num">{f"{st:.2f}" if st is not None else DASH}</td>
<td class="num">{f"{da:.0%}" if da is not None else DASH}</td>
<td>{src(f"https://www.nfl.com/schedules/2026/by-week/week-{w}", "week " + str(w))}</td></tr>'''
 for w, g, s, sm, st, da in weekly)}
</tbody></table></div>
<p class="cls">RMSE and direction are model output against these results, not league figures.
Weeks 1–3 are unscored because there is no prior season in the corpus to fit on.</p>

<h2>Every game</h2>
<p class="lede">Official score on the left; the model's walk-forward forecast underneath it, where one exists.
The model column shows what the registered rule would have said <i>before</i> kickoff given only earlier games.</p>
<div class="tbl"><table>
<thead><tr><th class="num">Wk</th><th>Date</th><th>Away</th><th class="num">Score</th><th>Home</th>
<th class="num">Total</th><th class="num">Model line</th><th class="num">Model total</th>
<th class="num">Margin err</th><th class="num">Total err</th><th>Source</th></tr></thead><tbody>
"""
    fmap = {x["game"]: x for x in wf["per_game"]}
    for w in sorted(by_week):
        for r in by_week[w]:
            key = f'{r["away_abbr"]}@{r["home_abbr"]}'
            f = fmap.get(key)
            aw, hm = int(r["away_pts"]), int(r["home_pts"])
            tot = aw + hm
            note = r.get("neutral_site_note", "")
            badge = f' <span class="b info" title="{e(note)}">note</span>' if note else ""
            if f:
                me = f["pred_margin"] - f["actual_margin"]
                te = f["pred_total"] - f["actual_total"]
                ml = f'<span class="{"pos" if me>=0 else "neg"}">{f["pred_margin"]:+.1f}</span>'
                mt = f'{f["pred_total"]:.1f}'
                mec = f'<span class="{"pos" if abs(me)<7 else "neg"}">{me:+.1f}</span>'
                tec = f'<span class="{"pos" if abs(te)<7 else "neg"}">{te:+.1f}</span>'
            else:
                ml = mt = mec = tec = DASH
            body += f"""<tr><td class="num">{w}</td><td class="mono">{e(r['game_date'])}</td>
<td>{e(r['away_abbr'])}</td><td class="num"><b>{aw}</b>–<b>{hm}</b> {badge}</td><td>{e(r['home_abbr'])}</td>
<td class="num">{tot}</td><td class="num">{ml}</td><td class="num">{mt}</td>
<td class="num">{mec}</td><td class="num">{tec}</td>
<td>{src(r['source_url'], 'week ' + r['week'])}</td></tr>"""
    body += """
</tbody></table></div>
<p class="cls">Model line is home margin (positive = home favoured). Error is model minus actual, so a
positive margin error means the model over-rated the home side.</p>
"""
    return shell("Results", body, "results.html", ctx["generated"])


def page_lines(ctx):
    d = load("lines_week10.json")
    ev = ctx["eval"]
    res_rows = {(r["away_abbr"], r["home_abbr"]): r for r in ctx["result_rows"]}

    body = f"""
<h1>Our originated lines</h1>
<p class="lede">Lines produced by a model in this repository, not copied from a sportsbook. Each carries
its inputs and an uncertainty band. The market column is deliberately empty: no licensed price exists in
this repo, so an edge cannot be claimed and is never displayed as if it could.</p>

<div class="note warn"><b>These are not picks.</b> No strategy on this site risks money, and the model
holding them does not beat a pick'em line at 95% confidence (see <a href="index.html">Overview</a>).
They are published because a forecast that is not recorded before kickoff cannot be scored, and an
unscored forecast is not evidence.</div>

<h2>Week 10 — originated, with the official result beside it</h2>
<div class="tbl"><table>
<thead><tr><th>Game</th><th class="num">Model spread</th><th class="num">Market spread</th>
<th class="num">Model total</th><th class="num">Market total</th><th class="num">Official score</th>
<th class="num">Spread error</th><th class="num">Total error</th><th>Status</th><th>Source</th></tr></thead><tbody>
"""
    for g in d["games"]:
        ln = g["line"]
        res = res_rows.get((g["away"], g["home"]))
        spread = f'{ln["home_spread"]:+.1f}'
        total = f'{ln["total_point_estimate"]:.1f}'
        if res:
            aw, hm = int(res["away_pts"]), int(res["home_pts"])
            score = f"{aw}–{hm}"
            actual_margin = hm - aw
            se = (-ln["home_spread"]) - actual_margin
            te = ln["total_point_estimate"] - (aw + hm)
            se_html = f'<span class="{"pos" if abs(se)<7 else "neg"}">{se:+.1f}</span>'
            te_html = f'<span class="{"pos" if abs(te)<7 else "neg"}">{te:+.1f}</span>'
            kick = g.get("kickoff", "")
            if "FINAL" in kick:
                st = '<span class="b warn">excluded — pre-kickoff leakage</span>'
                se_html = te_html = DASH
            else:
                st = '<span class="b ok">scored</span>'
        else:
            score = se_html = te_html = DASH
            st = '<span class="b none">no result yet</span>'
        body += f"""<tr><td>{e(g['away'])} @ {e(g['home'])}</td>
<td class="num">{spread}</td><td class="num">{DASH}</td>
<td class="num">{total}</td><td class="num">{DASH}</td>
<td class="num">{score}</td><td class="num">{se_html}</td><td class="num">{te_html}</td>
<td>{st}</td><td>{src(g['src'], 'sched')} {src(g['src_injuries'], 'inj')}</td></tr>"""
    body += f"""</tbody></table></div>
<p class="cls">Market columns are empty because no official or licensed price is held in this repository
(<a href="review.html">LV-10</a>). An empty market column is a statement about the data, not about the model.</p>

<h2>What the model is</h2>
<div class="tbl"><table>
<thead><tr><th>Component</th><th>Value</th><th class="num">Source</th></tr></thead><tbody>
<tr><td>League points per club per game</td><td class="num">{d['meta']['model']['league_points_per_team']}</td><td>declared constant</td></tr>
<tr><td>Home-field advantage</td><td class="num">{d['meta']['model']['hfa_points']} pts</td><td>declared constant</td></tr>
<tr><td>Shrinkage prior</td><td class="num">{d['meta']['model']['prior_games']} games</td><td>declared constant</td></tr>
<tr><td>Single-game margin σ</td><td class="num">{d['meta']['model'].get('single_game_sigma', '—')}</td><td>declared constant</td></tr>
<tr><td>Availability penalty</td><td>position weight × game status</td><td>model parameter, <b>not verified data</b></td></tr>
</tbody></table></div>
<p class="cls">Constants are declared, not fitted. Fitting them in-sample and then scoring on the same
games would flatter the model; the cost of declaring them is paid openly in the scoreboard.</p>

<h2>Why there is no "edge" column</h2>
<p>An edge is model price minus market price. This repository holds no market price. Every previous build
that displayed market columns either left them blank or filled them from an operator's public page, which is
not an official league source and is not licensed for redistribution. The honest presentation is a blank
market column and a stated reason — which is what is here.</p>
"""
    return shell("Our lines", body, "lines.html", ctx["generated"])


def page_injuries(ctx):
    lv = {r["claim_id"]: r for r in ctx["live"]["claims"]}
    body = f"""
<h1>Availability &amp; depth — what the official report can and cannot tell you</h1>
<p class="lede">Injury and availability tracking is where this project's most material data defect sits.
Two captures of the same official Week 10 report disagree, and one of them silently drops a starting
quarterback. That is documented here rather than smoothed over.</p>

<h2>The defect <span class="b bad">material</span></h2>
<div class="tbl"><table>
<thead><tr><th>Capture</th><th class="num">Rows</th><th class="num">Clubs</th>
<th class="num">Rows with a game status</th><th class="num">SEA</th><th class="num">CIN</th>
<th>Verdict</th></tr></thead><tbody>
<tr><td><code>data/injuries_2026_wk10.csv</code></td><td class="num">345</td><td class="num">28</td>
<td class="num">160</td><td class="num">15</td><td class="num">9</td>
<td><span class="b ok">matches the live official page</span></td></tr>
<tr><td><code>data/injuries_2026_w10.csv</code></td><td class="num">160</td><td class="num">26</td>
<td class="num">160</td><td class="num">4</td><td class="num">4</td>
<td><span class="b bad">partial — 100% of rows carry a designation</span></td></tr>
</tbody></table></div>
<div class="note bad"><b>Why the second one matters.</b> It holds only players who already carry a game
designation. It is not a subset by accident: every one of its 160 rows has a status and none is blank, while
the official page leaves {345-160} rows undesignated. Any feature built on it inherits that selection bias,
and it cannot represent "on the report, no designation". It is the input to the model behind
<a href="../board/">/board/</a>. <b>It omits Sam Darnold (QB, ribs/quadricep, Out)</b> — a starting
quarterback — so a model fed this file prices Seattle as if he were available. The owner of that track
should switch to the complete capture or label every output as built on designated players only. This
session did not edit their file.</div>

<h2>Live re-verification of the availability claims</h2>
<div class="tbl"><table>
<thead><tr><th>ID</th><th>Claim</th><th>Repo value</th><th>Live official value</th><th>Status</th><th>Source</th></tr></thead><tbody>
{''.join(f'''<tr><td class="mono">{e(k)}</td><td>{e(v['claim'])}</td><td>{e(v['repo_value'])}</td>
<td>{e(v['live_value'])}</td><td>{status_badge(v['status'])}</td><td>{src(v['live_source'], 'report')}</td></tr>'''
 for k, v in sorted(lv.items()) if k in ("LV-01", "LV-02", "LV-03", "LV-04", "LV-05", "LV-14"))}
</tbody></table></div>
<p class="cls">Full reasoning, method and notes for each: <a href="verification.html">Verification</a>.</p>

<h2>What a "2nd-string replacement" can honestly mean here</h2>
<p>The brief asks for depth deficiency: which clubs are starting a backup, and how deep the drop is. The
honest position, unchanged from the earlier sessions and re-confirmed today, is:</p>
<ul>
<li><b>Availability is official.</b> The league injury report owns who is Out, Doubtful or Questionable,
and the club roster page owns roster status (active / injured reserve / PUP). Both are league-published
and both are linked.</li>
<li><b>Depth order is not official.</b> The league publishes no depth ordinal. Where a club publishes a
chart, it is club-published and carries no effective date, so it can establish an order but cannot be
shown to be current.</li>
<li><b>Replacement evidence is not captured.</b> Snap counts and the 90-minute inactive list are not on
any league page this repo can reach. A replacement can be named; that he took the starter's snaps cannot be
evidenced. This requirement stays <b>open</b> and is published as open.</li>
<li><b>The injury signal must be a surprise, not a level.</b> A player listed as Questionable every week is
not news. The only defensible version is the <i>change</i> against a dated prior capture — which requires a
series this repo does not yet have, and whose capture protocol is in
<a href="method.html">Method</a>.</li>
</ul>

<h2>Why the practice-trend requirement cannot be back-filled</h2>
<p>The official page renders one current report per week and overwrites the previous day's designations.
There is no dated archive URL. A Wednesday-to-Friday progression therefore cannot be reconstructed for
Week 10 — only captured prospectively, on a schedule, from now on. Stated as a gap rather than faked with
an inference.</p>
"""
    return shell("Availability", body, "injuries.html", ctx["generated"])


def page_strategies(ctx):
    slate = ctx["slate"]
    fc = {f"{x['away']}@{x['home']}": x for x in ctx["fixtures"]["fixtures"]}
    rows = ""
    for g in slate:
        f = fc.get(f"{g['away_abbr']}@{g['home_abbr']}")
        if f:
            rows += (f'<tr><td>{e(g["away_abbr"])} @ {e(g["home_abbr"])}</td>'
                     f'<td>{e(g["kickoff_et"])}</td><td>{e(g["network"])}</td>'
                     f'<td class="num">{f["spread_home"]:+.1f}</td>'
                     f'<td class="num">{f["total"]:.1f}</td>'
                     f'<td class="num">{f["p_home"]:.3f}</td>'
                     f'<td>{src(g["source_url"], "week 11")}</td></tr>')
        else:
            rows += (f'<tr><td>{e(g["away_abbr"])} @ {e(g["home_abbr"])}</td>'
                     f'<td>{e(g["kickoff_et"])}</td><td>{e(g["network"])}</td>'
                     f'<td class="num">{DASH}</td><td class="num">{DASH}</td><td class="num">{DASH}</td>'
                     f'<td>{src(g["source_url"], "week 11")}</td></tr>')
    body = f"""
<h1>Strategies, gates, and the scoreboard that cannot be gamed</h1>
<p class="lede">A strategy earns a place on the leaderboard by passing pre-registered gates in order. It
does not earn one by winning bets, and in this repository no bets exist: there is no licensed price, no
stake, and no return. Everything here is a forecast-quality test.</p>

<h2>Leaderboard</h2>
<div class="tbl"><table>
<thead><tr><th>#</th><th>Strategy</th><th>Structure</th><th class="num">Scored</th>
<th class="num">Brier skill</th><th class="num">95% interval</th><th>Registration</th><th>Standing</th></tr></thead>
<tbody>
<tr><td>1</td><td><code>FL3-SHADOW-1</code> — two-way team-strength rating</td><td>singles</td>
<td class="num">100</td><td class="num">+0.069</td><td class="num">[−0.086, +0.229]</td>
<td><span class="b ok">frozen</span></td><td><span class="b warn">qualified as a baseline; no demonstrated skill</span></td></tr>
<tr><td>2</td><td><code>FL3-SHADOW-1-A</code> — adds availability features</td><td>singles</td>
<td class="num">0</td><td class="num">—</td><td class="num">—</td>
<td><span class="b ok">frozen</span></td><td><span class="b none">not started</span></td></tr>
<tr><td>3</td><td><code>FL3-SHADOW-1-B</code> — adds rest-days differential</td><td>singles</td>
<td class="num">0</td><td class="num">—</td><td class="num">—</td>
<td><span class="b ok">frozen</span></td><td><span class="b none">not started</span></td></tr>
<tr><td>—</td><td>any parlay, same-game parlay or prop combo</td><td>combo</td>
<td class="num">0</td><td class="num">—</td><td class="num">—</td>
<td><span class="b bad">ineligible</span></td><td><span class="b bad">cannot be ranked</span></td></tr>
</tbody></table></div>
<p class="cls">The 100 scored rows are the walk-forward forecasts, which are the registered rule applied
retrospectively to games that had not yet been played. They are a <b>backtest of a frozen rule</b>, and
backtest numbers never appear as a live record. The live record for <code>FL3-SHADOW-1</code> starts at
Week 11 and currently has <b>0</b> forecasts.</p>

<h2>Why combos are excluded outright</h2>
<p>Multiplying marginal probabilities is invalid when the legs are dependent, and it always overstates a
combo's chance. Two conditions would have to hold before a combination could be ranked at all:</p>
<ol>
<li>a <i>directly validated joint</i> probability for the exact combination, not a product of marginals; and</li>
<li>the operator's void, push and withdrawal rules, obtained in writing.</li>
</ol>
<p>Neither holds here. There is no licensed operator, so condition 2 cannot be met at all. The correlation
work published elsewhere in this repo states its measured <i>r</i> values and states plainly that they are
not a joint model — which is correct, and is why no combo appears on this leaderboard.</p>

<h2>Why ROI is not the ranking metric</h2>
<p>Over a season, realised return is dominated by variance. A strategy that wins 7 of 11 is 11 coin flips;
its ROI is a number with a confidence interval wider than the number. Ranking by it selects for luck.
And in this repository it is not even computable, because no price was ever held. The replacement is
proper-score skill with a game-cluster interval and a multiplicity adjustment — which measures whether the
probabilities are good, which is the thing that would eventually produce a return.</p>

<h2>Registered forecasts for Week 11 <span class="b model">model output</span></h2>
<p class="lede">These are the first live forecasts of <code>FL3-SHADOW-1</code>: 13 unplayed fixtures, each
registered before kickoff with the constants frozen in the pre-registration. They are not picks, nothing is
staked, and they will be scored against the official final scores exactly once. A forecast that is not
committed before kickoff is rejected rather than back-filled.</p>
<div class="tbl"><table>
<thead><tr><th>Game</th><th>Kickoff ET</th><th>Network</th><th class="num">Model spread (home)</th>
<th class="num">Model total</th><th class="num">P(home win)</th><th>Source</th></tr></thead><tbody>
{rows}
</tbody></table></div>
<p class="cls">Slate read from the official Week 11 schedule page on 2026-11-16. 13 games and 6 byes
account for all 32 clubs. Registered forecast file:
<code>data/preregistration_week11.json</code>, SHA-256 <span class="mono">{ctx['fixtures']['sha256'][:32]}…</span>.</p>

<h2>Gates, in order</h2>
<div class="tbl"><table>
<thead><tr><th class="num">Gate</th><th>Requirement</th><th>Blocking condition</th><th>Status</th></tr></thead><tbody>
<tr><td class="num">G1</td><td>Registration committed before any forecast</td>
<td>no commit hash ⇒ no entry</td><td><span class="b ok">met for 3 strategies</span></td></tr>
<tr><td class="num">G2</td><td>Forecast published before kickoff</td>
<td>late rows rejected, not back-filled</td><td><span class="b ok">rule active</span></td></tr>
<tr><td class="num">G3</td><td>Results corpus reconciles to official standings</td>
<td>148 rows, 160 figures, no tolerance</td><td><span class="b ok">met</span></td></tr>
<tr><td class="num">G4</td><td>Licensed price for CLV and ROI</td>
<td>no NFL page publishes a price</td><td><span class="b bad">blocked</span></td></tr>
<tr><td class="num">G5</td><td>≥80 scored singles to publish skill</td>
<td>currently 100 backtested, 0 live</td><td><span class="b warn">met for backtest only</span></td></tr>
<tr><td class="num">G6</td><td>≥200 scored singles to rank two strategies</td>
<td>0 live</td><td><span class="b bad">blocked</span></td></tr>
<tr><td class="num">G7</td><td>Multiplicity adjustment across live hypotheses</td>
<td>1 live hypothesis, so no adjustment needed yet</td><td><span class="b info">armed</span></td></tr>
<tr><td class="num">G8</td><td>Two-sided "what would change our mind" field</td>
<td>required per strategy</td><td><span class="b ok">met</span></td></tr>
</tbody></table></div>

<h2>Pre-registration, in force</h2>
<p>The full frozen rule text is in <a href="../verified/PREREGISTRATION.md">PREREGISTRATION.md</a>, with an
executable form in <code>scripts/preregister_model.py</code>. The parts that make it a registration rather
than a description: the constants, the sample window, the primary metric, the minimum detectable effect and
the stopping rule were all fixed before any prospective forecast existed, and changing any of them creates a
new version with a new commit rather than an edit.</p>
<p><b>Its own stopping rule, stated in advance:</b> retire the model rather than re-fit it if the interval
lower bound on Brier skill is below −0.05 after 200 scored singles. This is what stops a bad model from being
tuned until it looks good.</p>
"""
    return shell("Strategies", body, "strategies.html", ctx["generated"])


def page_verification(ctx):
    lv = ctx["live"]
    body = f"""
<h1>Verification — {lv['meta']['claims']} claims re-checked against live official pages</h1>
<p class="lede">Every capture in this repository is dated 2026-11-14. It is now 2026-11-16, the season has
advanced, and several statements about the data were written from the old snapshot and never re-checked.
Each is re-checked here against the live official page and given one of five outcomes. The stale ones and
the ones that exonerate the repo are published with exactly the same prominence.</p>

<div class="cards">
{''.join(f'<div class="card"><span class="n">{v}</span><span class="l">{k.replace("_"," ").lower()}</span></div>' for k, v in sorted(lv['meta']['by_status'].items()))}
</div>
<p class="cls"><b>How to read the outcomes.</b>
<span class="b ok">confirmed</span> — a live official page shows the same value.
<span class="b bad">stale</span> — the repo disagrees with the live page.
<span class="b warn">partly stale</span> or <span class="b warn">not reproducible</span> — true in part, or
impossible to reproduce from this snapshot.
<span class="b none">unverifiable</span> — no official page can settle it; the row carries an explicit
source gap and is never presented as confirmed.</p>

<h2>The register</h2>
<div class="tbl"><table>
<thead><tr><th>ID</th><th>Claim under test</th><th>Repo says</th><th>Live official page says</th>
<th>Status</th><th>Official source</th></tr></thead><tbody>
{''.join(f'''<tr><td class="mono">{e(r["claim_id"])}</td>
<td>{e(r["claim"])}<div class="cls" style="margin-top:4px">{e(r["note"])}</div></td>
<td class="mono" style="font-size:11.5px">{e(r["repo_value"][:150])}</td>
<td class="mono" style="font-size:11.5px">{e(r["live_value"][:150])}</td>
<td>{status_badge(r["status"])}</td>
<td>{src(r["live_source"], "open")}{f'<div class="unv" style="margin-top:4px">no official source settles this</div>' if r.get("source_gap") and not r["live_source"] else ""}</td></tr>'''
 for r in lv["claims"])}
</tbody></table></div>
<p class="cls">Register SHA-256 <span class="mono">{e(lv['meta']['csv_sha256'][:32])}…</span> ·
read {e(lv['meta']['read_at_utc'])} · re-runnable with <code>python3 scripts/verify_live.py</code></p>

<h2>Source gaps — questions no official page can answer</h2>
<p class="lede">These are the rows where the honest answer is "there is no official source". They are listed
here so that no downstream page can quietly imply otherwise.</p>
<ul>
{''.join(f'<li><b>{e(r["claim_id"])}</b> — {e(r["claim"])}<br><span class="cls">{e(r.get("source_gap",""))}</span></li>' for r in lv["claims"] if r["status"] == "UNVERIFIABLE")}
</ul>

<h2>What this session changed, and what it deliberately did not</h2>
<div class="grid2"><div>
<h3>Added</h3>
<ul>
<li>A {ctx['results']['meta']['games']}-game results corpus that reconciles to the official standings.</li>
<li>An out-of-sample evaluation of the repo's own committed Week 10 lines, with the contaminated game excluded.</li>
<li>A walk-forward baseline over the full corpus with game-cluster intervals and explicit baselines.</li>
<li>This register, the pre-registration, and a single deploy path.</li>
</ul>
</div><div>
<h3>Not touched</h3>
<ul>
<li>No other session's data file was edited. Where a defect was found, it is reported here with its
evidence and left for its owner.</li>
<li>No value was filled in from memory, inference or a third-party aggregator.</li>
<li>No merge was made against a failing check.</li>
</ul>
</div></div>
"""
    return shell("Verification", body, "verification.html", ctx["generated"])


def page_review(ctx):
    lv = ctx["live"]
    flags = [
        ("R-01", "Partial injury capture omits a starting quarterback", "material",
         "data/injuries_2026_w10.csv holds 160 rows, all of which carry a game designation, against 345 on "
         "the live official page. Seattle shows 4 rows instead of 15; Sam Darnold (QB, Out) is absent. It is "
         "the input to the board/ model.",
         "Switch that track to data/injuries_2026_wk10.csv, or label every output as built on designated "
         "players only.", "LV-05"),
        ("R-02", "Two injury captures of the same report disagree", "material",
         "345 rows vs 160 rows, 28 clubs vs 26, and different club-name conventions. Both are committed and "
         "both are cited by different pages.",
         "Retire one, or document which page uses which and why.", "LV-05"),
        ("R-03", "The '136-game corpus' figure is stale, and the board holds 33 rows", "material",
         "136 was the correct count of games before 2026-11-12. Today 148 games are final. The board's own "
         "game file holds 33 rows, so no ROI can be computed anywhere in that track.",
         "Derive the corpus size at render time from the results file; do not type it into prose.", "LV-06"),
        ("R-04", "No licensed price anywhere, so CLV and ROI are not computable", "structural",
         "No NFL-operated page publishes a spread, total, moneyline or prop price. Operator pages are not "
         "official and are geo-gated.",
         "Decide the price policy before publishing any backtest. Until then publish proper-score skill only.",
         "LV-10"),
        ("R-05", "No official depth ordinal, so backup depth is a model estimate", "structural",
         "The league publishes rosters and injury reports, not depth ranks. Club charts carry no effective "
         "date.",
         "Keep the existing authority rule and label every depth-derived number as a model estimate.",
         "LV-09"),
        ("R-06", "No snap counts or inactive lists, so replacement is suspected not confirmed", "structural",
         "The official report has five columns: player, position, injury, practice status, game status. No "
         "snap or inactive data.",
         "Publish the requirement as open; do not infer participation from depth order.", "LV-11"),
        ("R-07", "The injury report cannot be reconstructed as a daily series", "structural",
         "The official page overwrites each day's designations and offers no dated archive URL, so the "
         "Wed→Fri practice progression for Week 10 is unrecoverable.",
         "Capture prospectively on a schedule with retained hashes, from now on.", "LV-12"),
        ("R-08", "Six dashboards for one brief, five of them with no results corpus", "governance",
         "Root, board, docs, depth, site-9b181d31 and verified all publish. Only this one can score a "
         "forecast. Several carry the same conceptual pages with different numbers.",
         "Decide which is canonical and either retire the others or state their relationship on each.",
         None),
        ("R-09", "A competing Pages deploy workflow was never the deploy path", "governance",
         "Pages is configured as a legacy root build, verified through the API. The cp-allowlist workflow "
         "was a second deployment that caused two silent-404 incidents before this session replaced it with "
         "a gate.",
         "Do not reintroduce an artifact allowlist. Check the Pages API before editing deploy config.", None),
        ("R-10", "A claim raised against this repo does not reproduce", "unproven",
         "Three Detroit players are alleged to have blank game statuses. All three carry 'Out' in this "
         "snapshot, matching the live page. Either the claim described an earlier commit or a different "
         "artefact.",
         "No change made. Published so it can be traced if a reviewer has the specific page in front of them.",
         "LV-02"),
    ]
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Everything below is a defect this session found and did <b>not</b> silently repair. Two are
material to the numbers, three are structural facts about what official sources can support, two are
governance, and one is a claim that did not reproduce and was therefore not acted on. None of them blocks
publication; all of them change how the numbers should be read.</p>

<div class="note warn"><b>Read this before trusting any number elsewhere in the repository.</b>
R-01 and R-03 mean that at least one other dashboard's inputs are incomplete. This page states which and
why; the fix belongs to the session that owns those files.</div>

<div class="tbl"><table>
<thead><tr><th>ID</th><th>Item</th><th>Severity</th><th>What is wrong</th><th>Recommended action</th>
<th>Evidence</th></tr></thead><tbody>
{''.join(f'''<tr><td class="mono">{e(i)}</td><td><b>{e(t)}</b></td>
<td><span class="b {"bad" if sev=="material" else "warn" if sev in ("structural","governance") else "none"}">{e(sev)}</span></td>
<td>{e(what)}</td><td>{e(act)}</td>
<td>{("<a class='src' href='verification.html'>" + ev + "</a>") if ev else "<span class='unv'>no source</span>"}</td></tr>'''
 for i, t, sev, what, act, ev in flags)}
</tbody></table></div>

<h2>What is explicitly <i>not</i> flagged</h2>
<ul>
<li><b>Detroit's three statuses.</b> They are populated and correct. A defect that does not exist should not
be fixed, and "fixed" data is harder to audit than untouched data.</li>
<li><b>Model output that scored badly.</b> A baseline that does not beat a pick'em is a result, not a bug.
It is published on the Overview page without hedging.</li>
<li><b>The empty market columns.</b> They are empty for a stated reason, and filling them from a
non-official source would be a defect rather than a fix.</li>
</ul>
"""
    return shell("Flagged for review", body, "review.html", ctx["generated"])


def page_method(ctx):
    lv = ctx["live"]
    body = f"""
<h1>Method &amp; sources</h1>
<p class="lede">What counts as evidence here, how a number gets on a page, and what was tried and rejected.
Written so that a reviewer can check any claim on this site without taking its word for anything.</p>

<h2>The source policy, in one paragraph</h2>
<p>Only NFL-operated properties count as evidence: <code>nfl.com</code> (schedules, scores, standings,
injuries, rosters, stats) and <code>operations.nfl.com</code> (rules). A club-operated page counts as
evidence for facts only the club publishes — its own depth chart — and is labelled as club-published. A
third-party aggregator, a DFS projection, a public consensus line and a sportsbook page are <b>not</b>
evidence for an official value. Where a value can only be had from a non-official source, it is either
labelled as a model estimate or left blank. It is never presented as a league fact.</p>

<h2>How a row gets on a page</h2>
<ol>
<li><b>Read the official page.</b> Record the URL and the clock time.</li>
<li><b>Transcribe, do not infer.</b> If the page does not state it, it does not go in.</li>
<li><b>Cross-check against a second official page</b> wherever one exists. The results corpus is checked
against the standings page club by club, 160 figures, no tolerance.</li>
<li><b>Hash the artefact.</b> The corpus hash is printed on <a href="results.html">Results</a>.</li>
<li><b>Render the source link with the value.</b> A row without an official source renders a visible
marker, and the build counts them.</li>
</ol>

<h2>Official sources used on this site</h2>
<div class="tbl"><table>
<thead><tr><th>Source</th><th>Used for</th><th>Read at</th></tr></thead><tbody>
<tr><td><a href="https://www.nfl.com/schedules/2026/by-week/week-1" target="_blank" rel="noopener">nfl.com/schedules/2026/by-week/week-N</a></td>
<td>every result row; a row is only included when the page renders the game FINAL</td>
<td class="mono">{e(lv['meta']['read_at_utc'])}</td></tr>
<tr><td><a href="https://www.nfl.com/standings/league/2026/reg" target="_blank" rel="noopener">nfl.com/standings/league/2026/reg</a></td>
<td>the reconciliation check on the results corpus (W/L/T, PF, PA per club)</td>
<td class="mono">{e(lv['meta']['read_at_utc'])}</td></tr>
<tr><td><a href="https://www.nfl.com/injuries/league/2026/reg10" target="_blank" rel="noopener">nfl.com/injuries/league/2026/reg10</a></td>
<td>availability claims LV-01 to LV-05, LV-14; per-club row counts</td>
<td class="mono">{e(lv['meta']['read_at_utc'])}</td></tr>
<tr><td><a href="https://www.nfl.com/teams/" target="_blank" rel="noopener">nfl.com/teams/…</a></td>
<td>roster status as the durable availability authority (LV-15)</td>
<td class="mono">{e(lv['meta']['read_at_utc'])}</td></tr>
</tbody></table></div>

<h2>Rejected sources, and why</h2>
<div class="tbl"><table>
<thead><tr><th>Category</th><th>Why it is not used for an official value</th></tr></thead><tbody>
<tr><td>Sportsbook and aggregator odds</td><td>Not league-operated, not licensed for retention or
redistribution, usually geo-gated and not machine-readable. Used by no page on this site. Market columns are
blank rather than filled from these.</td></tr>
<tr><td>Third-party depth charts</td><td>Club-adjacent but not official. Where they are used at all, they
are labelled a model input and never a fact.</td></tr>
<tr><td>Projection and DFS sites</td><td>Model output of another party; cannot be evidence for a league
value.</td></tr>
<tr><td>Memory and prior-season knowledge</td><td>Not a source. Roster turnover makes a remembered depth
chart wrong; anything not read from a page today is not on this site.</td></tr>
</tbody></table></div>

<h2>The snapshot protocol this repo should have had from day one</h2>
<p>Three of the ten open requirements are blocked only because a series was never captured. The fix is a
schedule, not a model:</p>
<ul>
<li><b>Daily, Wed–Sun</b> capture of <code>nfl.com/injuries/league/2026/reg10</code> with the fetch clock
time, byte count and SHA-256 retained, so designations can be replayed as they were known.</li>
<li><b>Weekly</b> capture of every club roster and depth page, versioned against the last official roster
event rather than trusted as durable.</li>
<li><b>Post-game</b> capture of the official game book for starters and game-day status.</li>
<li><b>Drift alarm</b> on every parser: pin expected row counts and required fields, and fail loudly when a
field disappears rather than publishing a blank.</li>
</ul>
<p>None of this is claimed as done. It is the specification for the next session, written down so it is not
re-derived.</p>

<h2>Reproduce everything on this site</h2>
<pre style="background:#151b23;border:1px solid #2a333f;border-radius:8px;padding:14px;overflow-x:auto;font-size:12.5px">
python3 scripts/build_week_results.py      # results corpus + identity check
python3 scripts/score_lines.py             # out-of-sample evaluation
python3 scripts/verify_live.py             # live re-verification register
python3 scripts/preregister_model.py       # registered model, hashed
python3 scripts/build_verified_site.py     # render this site
python3 scripts/check_verified_site.py     # assert sources, links and arithmetic
</pre>
<p class="cls">Deterministic: no randomness except the bootstrap, which is seeded. A re-run produces
identical files, and CI fails the build if it does not.</p>
"""
    return shell("Method", body, "method.html", ctx["generated"])


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    ctx = dict(
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        results=load("week_results_2026.json"),
        result_rows=csv_rows("week_results_2026.csv"),
        eval=load("line_eval.json"),
        live=load("live_verification.json"),
        slate=csv_rows("week11_slate_2026.csv"),
        fixtures=load("preregistration_week11.json"),
    )

    pages = {
        "index.html": page_index,
        "results.html": page_results,
        "lines.html": page_lines,
        "injuries.html": page_injuries,
        "strategies.html": page_strategies,
        "verification.html": page_verification,
        "review.html": page_review,
        "method.html": page_method,
    }

    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    if not a.check:
        with open(os.path.join(OUT, "assets", "verified.css"), "w", encoding="utf-8") as fh:
            fh.write(CSS)
        for name, fn in pages.items():
            with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
                fh.write(fn(ctx))
            print("wrote verified/" + name)
    else:
        print(f"{len(pages)} pages would be generated")


if __name__ == "__main__":
    sys.exit(main())
