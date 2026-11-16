#!/usr/bin/env python3
"""Render the independent official-source verification subsite (verify/).

Deterministic, stdlib-only. Reads data/verify_log.json and data/verify_venues.json
and writes plain HTML into verify/. No randomness, no network.
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "verify")

CSS = """
:root { --ink:#11161c; --mut:#5b6572; --line:#dfe3e8; --bg:#f6f7f9; --card:#fff;
        --acc:#0b5fff; --ok:#0a7d3c; --warn:#8a5a00; --bad:#b3261e; --chip:#eef1f5; }
* { box-sizing: border-box; }
body { margin:0; font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--bg); }
header { background:#0b1220; color:#fff; padding:18px 28px; }
header h1 { margin:0; font-size:20px; letter-spacing:.2px; }
header p { margin:4px 0 0; color:#aab4c2; font-size:13px; }
nav { background:#111a2b; padding:0 28px; }
nav a { display:inline-block; color:#cfd8e6; text-decoration:none; padding:11px 14px; font-size:14px; }
nav a:hover { color:#fff; background:#1b2740; }
nav a.active { color:#fff; border-bottom:3px solid var(--acc); }
main { max-width:1080px; margin:0 auto; padding:26px 22px 60px; }
h2 { font-size:20px; margin:26px 0 10px; }
h3 { font-size:16px; margin:18px 0 8px; }
p.lede { color:var(--mut); max-width:780px; }
table { width:100%; border-collapse:collapse; background:var(--card); margin:12px 0;
        border:1px solid var(--line); border-radius:8px; overflow:hidden; }
th, td { text-align:left; padding:9px 11px; border-bottom:1px solid var(--line); font-size:14px; vertical-align:top; }
th { background:#f0f2f6; font-weight:600; }
tr:last-child td { border-bottom:none; }
a { color:var(--acc); text-decoration:none; word-break:break-all; }
a:hover { text-decoration:underline; }
.chip { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:600; background:var(--chip); }
.chip.CONFIRMED { background:#e3f5ea; color:var(--ok); }
.chip.PARTIALLY_CONFIRMED { background:#fdf1dc; color:var(--warn); }
.chip.REFUTED { background:#fbe3e1; color:var(--bad); }
.chip.RECONCILED { background:#e6effd; color:var(--acc); }
.chip.NOT_VERIFIED { background:#eceff3; color:var(--mut); }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; margin:14px 0; }
.card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:14px 16px; }
.card .n { font-size:24px; font-weight:700; }
.card .l { color:var(--mut); font-size:13px; }
.fine { color:var(--mut); font-size:13px; }
code { background:#eef1f5; padding:1px 5px; border-radius:4px; font-size:13px; }
"""

NAV = [
    ("index.html", "Verification"),
    ("verification.html", "Claims log"),
    ("venues.html", "Venues"),
    ("gamebooks.html", "Game Books"),
    ("sources.html", "Sources"),
]


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def esc(x):
    return html.escape("" if x is None else str(x))


def page(title, active, body):
    nav = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - FL3 verification</title>
<style>{CSS}</style></head>
<body>
<header><h1>FL3 &mdash; Independent Official-Source Verification</h1>
<p>Every claim re-checked against live NFL.com / NFL Media pages on 2026-11-16. Values not confirmed are left blank and flagged.</p></header>
<nav>{nav}</nav>
<main>{body}</main>
</body></html>"""


def status_chip(status):
    return f'<span class="chip {esc(status.replace(" ", "_"))}">{esc(status)}</span>'


def build_index(log, venues):
    claims = log["claims"]
    by_status = {}
    for c in claims:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
    games = venues["games"]
    finals = sum(1 for g in games if g["status"] == "FINAL")
    cards = "".join(
        f'<div class="card"><div class="n">{n}</div><div class="l">{esc(l)}</div></div>'
        for n, l in [
            (len(claims), "claims re-checked"),
            (by_status.get("CONFIRMED", 0), "confirmed"),
            (by_status.get("PARTIALLY CONFIRMED", 0), "partially confirmed"),
            (by_status.get("RECONCILED", 0), "reconciled"),
            (by_status.get("NOT VERIFIED", 0), "not verified"),
            (len(games), "fixtures venue-verified"),
            (finals, "final games with Game Book"),
        ]
    )
    body = f"""
<h2>What this is</h2>
<p class="lede">A line-by-line re-verification of the specific claims raised in the project brief against
official NFL sources. Each claim carries the exact official page it was checked against. Where an official
source does not state a fact, the value is left blank and the claim is marked <b>NOT VERIFIED</b> &mdash;
never inferred. This is a verification record, not a model output or a bet.</p>
<div class="cards">{cards}</div>
<h2>How to read it</h2>
<p class="lede">Open the <a href="verification.html">Claims log</a> for the claim-by-claim findings and sources,
the <a href="venues.html">Venues</a> page for the transcribed fixture venues, the
<a href="gamebooks.html">Game Books</a> page for the official Game Book PDF route, and the
<a href="sources.html">Sources</a> page for the full registry.</p>
<h2>Method</h2>
<p class="lede">{esc(log["_meta"]["method"])}</p>
<p class="fine">Session <code>arena/7e2496c2-fl3</code> &middot; captured {esc(log["_meta"]["captured_utc"])} UTC.</p>
"""
    return page("Verification", "index.html", body)


def build_verification(log):
    rows = []
    for c in log["claims"]:
        src = (f'<a href="{esc(c["source_url"])}">source</a>' if c["source_url"]
               else '<span class="fine">no source &mdash; flagged</span>')
        rows.append(
            "<tr>"
            f'<td><b>{esc(c["id"])}</b><br><span class="fine">{esc(c["requirement"])}</span></td>'
            f'<td>{status_chip(c["status"])}</td>'
            f'<td>{esc(c["claim"])}</td>'
            f'<td>{esc(c["finding"])}</td>'
            f'<td>{src}<br><span class="fine">{esc(c["source_title"])}</span></td>'
            f'</tr>'
        )
    body = f"""
<h2>Claims log</h2>
<p class="lede">One row per claim raised in the brief. <b>Status</b> is the result of checking the claim
against the official source on 2026-11-16. <b>Requirement</b> links back to the readiness register
(<code>data/requirements_readiness.csv</code>).</p>
<table>
<thead><tr><th>ID</th><th>Status</th><th>Claim</th><th>Finding (official source)</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<h3>Status legend</h3>
<ul>
<li><b>CONFIRMED</b> &mdash; the claim matches the official source exactly.</li>
<li><b>PARTIALLY CONFIRMED</b> &mdash; the official source supports part of the claim.</li>
<li><b>REFUTED</b> &mdash; the official source contradicts the claim as stated.</li>
<li><b>RECONCILED</b> &mdash; the cited numbers differ from an independent recount; the qualitative point is settled.</li>
<li><b>NOT VERIFIED</b> &mdash; no official source was available; the value stays blank and flagged.</li>
</ul>
<p class="fine">Legend source: {esc(log["_meta"]["status_legend"].get("NOT VERIFIED", ""))}</p>
"""
    return page("Claims log", "verification.html", body)


def build_venues(venues):
    rows = []
    for g in venues["games"]:
        score = (f'{g["away_score"]}&ndash;{g["home_score"]}'
                 if g["away_score"] is not None else '<span class="fine">&mdash;</span>')
        rows.append(
            "<tr>"
            f'<td><b>{esc(g["game_id"])}</b></td>'
            f'<td>{esc(g["date"])} {esc(g["day"])}<br><span class="fine">{esc(g["kickoff_et"])} ET</span></td>'
            f'<td>{esc(g["away"])} @ {esc(g["home"])}</td>'
            f'<td>{score}</td>'
            f'<td>{status_chip(g["status"])}</td>'
            f'<td>{esc(g["location"])}</td>'
            f'<td><b>{esc(g["stadium"])}</b></td>'
            f'<td><a href="{esc(g["game_url"])}">game centre</a></td>'
            f'</tr>'
        )
    body = f"""
<h2>Week 10 fixture venues</h2>
<p class="lede">{esc(venues["_meta"]["source_policy"])}</p>
<table>
<thead><tr><th>Game</th><th>Date / kickoff</th><th>Matchup</th><th>Score</th><th>Status</th>
<th>Location</th><th>Stadium</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<p class="fine">Captured {esc(venues["_meta"]["captured_utc"])} UTC. {esc(venues["_meta"]["note"])}</p>
"""
    return page("Venues", "venues.html", body)


def build_gamebooks(venues):
    rows = []
    for g in venues["games"]:
        if g["gamebook_pdf"]:
            pdf = f'<a href="{esc(g["gamebook_pdf"])}">Download Game Book (PDF)</a>'
        else:
            pdf = '<span class="fine">not yet published &mdash; flagged</span>'
        rows.append(
            "<tr>"
            f'<td><b>{esc(g["game_id"])}</b></td>'
            f'<td>{esc(g["away"])} @ {esc(g["home"])}</td>'
            f'<td>{status_chip(g["status"])}</td>'
            f'<td>{pdf}</td>'
            f'<td><a href="{esc(g["game_url"])}">game centre</a></td>'
            f'</tr>'
        )
    body = f"""
<h2>Official Game Book register</h2>
<p class="lede">The official NFL.com game-centre page publishes a <b>Download Game Book (PDF)</b> link for each
completed fixture. This is the verified official route for actual starters and game-day status (requirement R026).
The PDF contents are not yet parsed here &mdash; only the route and the per-game link are verified.</p>
<table>
<thead><tr><th>Game</th><th>Matchup</th><th>Status</th><th>Game Book PDF</th><th>Game centre</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<p class="fine">Games not yet final at capture have no Game Book published; those cells are blank and flagged.</p>
"""
    return page("Game Books", "gamebooks.html", body)


def build_sources(log, venues):
    sources = []
    seen = set()
    for c in log["claims"]:
        if c["source_url"] and c["source_url"] not in seen:
            seen.add(c["source_url"])
            sources.append((c["source_url"], c["source_title"], c["id"]))
    for g in venues["games"]:
        u = g["game_url"]
        if u not in seen:
            seen.add(u)
            sources.append((u, f'{g["away"]} @ {g["home"]} game centre', g["game_id"]))
    rows = "".join(
        f'<tr><td><a href="{esc(u)}">{esc(u)}</a></td><td>{esc(t)}</td><td><span class="fine">{esc(i)}</span></td></tr>'
        for u, t, i in sources
    )
    body = f"""
<h2>Source registry (this verification)</h2>
<p class="lede">Every URL consulted for this verification pass. All are official NFL-operated properties
(nfl.com, media.nfl.com, static.www.nfl.com). No third-party aggregator was used to establish a value.</p>
<table>
<thead><tr><th>URL</th><th>What it is</th><th>Used by</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<h3>Dated schedule announcement</h3>
<p class="lede">The league's official 2026 schedule announcement (requirement R025):
<a href="https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced">2026 NFL Schedule Announced</a>
&mdash; NFL Media, dated <b>May 14, 2026</b>. The live schedule hub is
<a href="https://www.nfl.com/schedules/2026/REG10">NFL.com Week 10 schedule</a>.</p>
"""
    return page("Sources", "sources.html", body)


def main():
    os.makedirs(OUT, exist_ok=True)
    log = load("verify_log.json")
    venues = load("verify_venues.json")
    pages = {
        "index.html": build_index(log, venues),
        "verification.html": build_verification(log),
        "venues.html": build_venues(venues),
        "gamebooks.html": build_gamebooks(venues),
        "sources.html": build_sources(log, venues),
    }
    for name, content in pages.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"wrote verify/{name} ({len(content)} bytes)")
    print("VERIFY BUILD: OK")


if __name__ == "__main__":
    main()
