#!/usr/bin/env python3
"""
FL3 — freshness subsite builder (session arena/4ac55b56-fl3).

Renders freshness/index.html, freshness/standings.html, freshness/schedule.html
and freshness/findings.html from the dated captures in data/freshness/.

Design rules (same as the rest of the repo):
* Every data row renders a source link to the official page it was read from.
* Blank stays blank; nothing is inferred.
* Model/derived values are labelled; league facts are not mixed with them.
"""
from __future__ import annotations

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "freshness")
OUT = os.path.join(ROOT, "freshness")

NAV = [
    ("index.html", "Freshness"),
    ("standings.html", "Standings delta"),
    ("schedule.html", "Week 11 slate"),
    ("findings.html", "Findings"),
]


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


e = html.escape


def src_link(url, label="source"):
    if not url:
        return '<span class="unverified">UNVERIFIED</span>'
    return f'<a class="src" href="{e(url)}" target="_blank" rel="noopener">{e(label)}</a>'


def page(title, body, active):
    parts = []
    for href, label in NAV:
        cls = ' class="on"' if href == active else ""
        parts.append(f'<a href="{href}"{cls}>{e(label)}</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · FL3 Freshness</title>
<meta name="description" content="Official-source freshness pass for the FL3 NFL decision system: live standings delta, Week 11 slate with venues, and flagged findings.">
<link rel="stylesheet" href="../assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand"><span class="mark">FL3</span><span class="sub">Freshness pass · 2026-11-17</span></div>
  <nav><a href="../index.html">Dashboard</a>{nav}</nav>
</header>
<main id="main">
{body}
</main>
</body>
</html>
"""


def table(headers, rows):
    head = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows)
    return f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table>"


def build_index(mf, st, dw11, res, findings):
    live = st["teams"]
    delta = load("delta_standings_2026-11-17.json")["rows"]
    from collections import Counter
    counts = Counter(r["classification"] for r in delta)
    reflected = counts.get("reflected", 0)
    bye = counts.get("bye (week 10)", 0)
    not_ref = counts.get("not reflected on standings page", 0)

    body = f"""
<section class="hero">
  <h1>Official-source freshness pass — 2026-11-17</h1>
  <p class="lede">Every figure on this subsite was read off a live official NFL.com or
  media.nfl.com page on <b>2026-11-17 (UTC)</b> and links to that page. It measures how far
  the committed <b>2026-11-14</b> snapshot has drifted from the live source, and publishes
  the delta rather than overwriting the snapshot.</p>
</section>

<section>
  <h2>What was re-verified</h2>
  {table(
      ["Source", "Fetched (UTC)", "What it proved"],
      [
          [src_link(s["url"], s["role"]), e(mf["fetched_utc"]), e(s["what"])]
          for s in mf["sources"]
      ])}
</section>

<section>
  <h2>Snapshot drift in one line</h2>
  <p class="lede">The committed standings snapshot is <b>3 days old</b> and pre-dates the
  Week 10 Sunday slate. Comparing it with the live page:</p>
  {table(
      ["Measure", "Value", "Detail"],
      [
          ["Clubs compared", "32", "committed snapshot vs live league standings page"],
          ["Results reflected on the live page", str(reflected),
           "PF/PA deltas match each club's Week 10 game score exactly"],
          ["Week 10 bye clubs", str(bye), "CHI, DEN, PHI, TB — no game, no delta"],
          ["Played but NOT reflected", str(not_ref),
           "WAS/NYG (TNF) and BAL/LAC (MNF) — see findings F-FRESH-02, F-FRESH-03"],
          ["Week 11 injury report", "not yet published",
           "the reg11 URL serves the Week 10 report — see F-FRESH-01"],
          ["Week 11 slate", "13 games + 6 byes",
           "venues transcribed from all 13 official game centres — see F-FRESH-06"],
      ])}
</section>

<section>
  <h2>Subpages</h2>
  {table(
      ["Page", "Contents"],
      [
          ['<a href="standings.html"><b>Standings delta</b></a>',
           "Live 2026-11-17 standings for all 32 clubs, and the per-club delta against the "
           "committed 2026-11-14 snapshot with a classification per row"],
          ['<a href="schedule.html"><b>Week 11 slate</b></a>',
           "The 13 Week 11 fixtures with official game-centre venues, the 6 bye clubs, and the "
           "Week 10 results as displayed on the schedule page"],
          ['<a href="findings.html"><b>Findings</b></a>',
           "Six dated findings (F-FRESH-01 … F-FRESH-06), each with its official source link"],
      ])}
</section>

<section>
  <h2>Method in one paragraph</h2>
  <p class="lede">Values were transcribed from the official pages through the agent's fetch
  tool; the fetch tool does not retain raw response bytes, so the transcription is the
  capture record and is checked arithmetically by <code>scripts/check_freshness.py</code>
  (PCT = (W + 0.5·T)/(W+L+T), NET = PF − PA, sum(PF) = sum(PA), deltas against each
  club's Week 10 game score). Where the official page does not state a value, the cell is
  blank and the item is listed under Findings. Nothing was inferred or corrected.</p>
</section>
"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Freshness", body, "index.html"))


def build_standings(st, delta):
    rows = []
    for t in st["teams"]:
        rows.append([
            f'<b>{e(t["abbr"])}</b> {e(t["name"])}',
            str(t["w"]), str(t["l"]), str(t["t"]), f'{t["pct"]:.3f}',
            str(t["pf"]), str(t["pa"]), str(t["net"]),
            src_link(t["src"]),
        ])
    live_table = table(
        ["Club", "W", "L", "T", "PCT", "PF", "PA", "NET", "Source"], rows)

    drows = []
    for r in delta["rows"]:
        cls = r["classification"]
        badge = {
            "reflected": '<span class="badge good">reflected</span>',
            "bye (week 10)": '<span class="badge">bye (W10)</span>',
            "not reflected on standings page": '<span class="badge bad">not reflected</span>',
            "no week-10 game found": '<span class="badge warn">no game found</span>',
        }.get(cls, e(cls))
        drows.append([
            f'<b>{e(r["abbr"])}</b>',
            f'{r["committed_w"]}-{r["committed_l"]}-{r["committed_t"]}',
            f'{r["live_w"]}-{r["live_l"]}-{r["live_t"]}',
            f'{r["dw"]:+d}/{r["dl"]:+d}/{r["dt"]:+d}',
            f'{r["dpf"]:+d} / {r["dpa"]:+d}',
            badge,
            src_link(r["src"]),
        ])
    delta_table = table(
        ["Club", "Committed 2026-11-14", "Live 2026-11-17", "Δ W/L/T", "Δ PF / Δ PA",
         "Classification", "Source"],
        drows)

    body = f"""
<section class="hero">
  <h1>Standings: live capture and delta</h1>
  <p class="lede">Top table: the live league standings page as fetched on
  <b>2026-11-17</b>. Bottom table: the same clubs against the committed
  <b>2026-11-14</b> snapshot, with the delta and a classification. "Reflected" rows are
  verified line-by-line: the PF/PA deltas equal the club's own Week 10 game score.</p>
</section>

<section>
  <h2>Live standings — 2026-11-17</h2>
  {live_table}
  <p class="note">Source: {src_link(st["meta"]["source"])}. The live page reflects the
  Week 10 Sunday slate only; the TNF and MNF results are excluded from the page itself
  (F-FRESH-02, F-FRESH-03).</p>
</section>

<section>
  <h2>Delta vs the committed 2026-11-14 snapshot</h2>
  {delta_table}
  <p class="note">The committed snapshot's club code <b>LA</b> for the Rams is mapped to
  <b>LAR</b> for the delta only (flag F27); the committed file is not edited.</p>
</section>
"""
    with open(os.path.join(OUT, "standings.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Standings delta", body, "standings.html"))


def build_schedule(dw11, res):
    rows = []
    for g in dw11["games"]:
        rows.append([
            f'<b>{e(g["away"])}</b> @ <b>{e(g["home"])}</b>',
            e(g["date"]), e(g["time"]), e(g["network"]),
            e(g["location"]), e(g["stadium"]),
            src_link(g["src"], "game centre"),
        ])
    slate = table(
        ["Fixture", "Date", "Time", "Network", "Location", "Stadium", "Source"], rows)

    bye_rows = [[f'<b>{e(b)}</b>', src_link(dw11["meta"]["source"])] for b in dw11["bye_clubs"]]
    bye_table = table(["Bye club", "Source"], bye_rows)

    rrows = []
    for g in res["games"]:
        status = e(g["status"])
        cls = "bad" if "LIVE" in g["status"] else ""
        rrows.append([
            f'<b>{e(g["away"])}</b> {g["away_score"]} @ <b>{e(g["home"])}</b> {g["home_score"]}',
            e(g["slot"]),
            f'<span class="badge {cls}">{status}</span>',
            src_link(g["src"], "game page"),
        ])
    results = table(["Week 10 result", "Slot", "Status", "Source"], rrows)

    body = f"""
<section class="hero">
  <h1>Week 11 slate and Week 10 results</h1>
  <p class="lede">The Week 11 schedule as published on <b>2026-11-17</b>, with the venue
  and location of every fixture transcribed from its own official game centre. The Week 10
  results table records exactly what the official schedule page displayed on the same date
  — including the Monday game whose final score is not published (F-FRESH-03).</p>
</section>

<section>
  <h2>Week 11 fixtures — 13 games</h2>
  {slate}
</section>

<section>
  <h2>Week 11 bye clubs — 6</h2>
  {bye_table}
</section>

<section>
  <h2>Week 10 results — as displayed 2026-11-17</h2>
  {results}
  <p class="note">The MNF row is reproduced exactly as the official schedule page displayed
  it on 2026-11-17 ("Q2 / Live", 17-7). Its final score is not published on the page, so
  the final-score cell is blank and the row is flagged — no result is inferred.</p>
</section>
"""
    with open(os.path.join(OUT, "schedule.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Week 11 slate", body, "schedule.html"))


def build_findings(findings):
    rows = []
    for f in findings["findings"]:
        sev = {"high": "bad", "medium": "warn", "info": ""}.get(f["severity"], "")
        rows.append([
            f'<b>{e(f["id"])}</b>',
            f'<span class="badge {sev}">{e(f["severity"])}</span>',
            e(f["title"]),
            e(f["detail"]),
            src_link(f["src"]),
        ])
    table_html = table(["ID", "Severity", "Finding", "Detail", "Source"], rows)

    body = f"""
<section class="hero">
  <h1>Freshness findings — flagged for review</h1>
  <p class="lede">This is the <b>Flagged for Review</b> page for the 2026-11-17
  official-source freshness pass: six dated findings, each linking the official page it
  was read from. None of these were silently corrected, and none block the merge — they
  are published here for review.</p>
</section>

<section>
  {table_html}
</section>
"""
    with open(os.path.join(OUT, "findings.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Findings", body, "findings.html"))


def main():
    os.makedirs(OUT, exist_ok=True)
    mf = load("manifest.json")
    st = load("standings_live_2026-11-17.json")
    dw11 = load("schedule_w11_2026-11-17.json")
    res = load("results_w10_2026-11-17.json")
    findings = load("findings.json")
    build_index(mf, st, dw11, res, findings)
    build_standings(st, load("delta_standings_2026-11-17.json"))
    build_schedule(dw11, res)
    build_findings(findings)
    print("freshness pages written:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
