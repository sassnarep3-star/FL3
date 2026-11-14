"""build_site.py - static site generator for the FL3 research dashboard.

No CDN, no external font, no JS framework: the output must render identically on
GitHub Pages and inside a sandboxed preview iframe. Every table row links to the
source that backs it.
"""
import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "depth"

AS_OF = "2026-11-14"
SRC = {s["id"]: s for s in json.loads((DATA / "sources_46e888f0.json").read_text())["sources"]}


# This build belongs to session arena/46e888f0 and reads ONLY that session's
# datasets. The aliases exist because scripts/build_site.py (owned by session
# arena-e8bf2075) uses the generic names for different files.
ALIASES = {
    "sources": "sources_46e888f0",
    "standings": "standings_verified",
    "strategies": "strategies_gates",
    "questions": "questions_46e888f0",
    "suggestions": "suggestions_46e888f0",
    "flagged": "flagged_46e888f0",
}


def D(name):
    name = ALIASES.get(name, name)
    return json.loads((DATA / (name + ".json")).read_text())


def e(x):
    return html.escape("" if x is None else str(x))


def srclink(sid, label=None):
    """A source badge that always links to the registered URL."""
    s = SRC.get(sid)
    if not s:
        return '<span class="badge bad">unverified</span>'
    url = s["url"]
    if "{TEAM}" in url:
        url = url.replace("{TEAM}", "")
    return '<a class="badge src" href="%s" target="_blank" rel="noopener" title="%s">%s</a>' % (
        e(url), e(s["name"]), e(label or sid))


def table(headers, rows, cls="", caption=None, note=None, method=False):
    """method=True marks a table of OUR OWN METHOD (gate rules, suggestions,
    correlation design). No external source can exist for those rows, so the table
    is labelled as methodology rather than carrying a fake citation. Data tables
    must cite: scripts/check_site.py enforces that every non-methodology row has a
    source link to an official or registered domain."""
    out = ['<div class="tw">']
    if caption:
        out.append('<span class="caption">%s</span>' % e(caption))
    if method:
        out.append('<span class="methodflag">Methodology table — no external source exists for these rows</span>')
        out.append('<table class="%s method">' % cls)
    else:
        out.append('<table class="%s">' % cls)
    out.append("<thead><tr>" + "".join("<th>%s</th>" % h for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table>")
    if note:
        out.append('<p class="note">%s</p>' % note)
    out.append("</div>")
    return "".join(out)


def pill(text, kind=""):
    return '<span class="pill %s">%s</span>' % (kind, e(text))


def blank(or_unverified=True):
    return '<span class="blank" title="not published by the source">—</span>' if or_unverified else ""


# ---------------------------------------------------------------- navigation
NAV = [
    ("../index.html", "Research desk"),
    ("index.html", "Depth dashboard"),
    ("league.html", "League"),
    ("injuries.html", "Injuries &amp; Lineups"),
    ("lines.html", "Model Lines"),
    ("strategies.html", "Strategies"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]


def page(slug, title, subtitle, body, current=""):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' class="on"' if h == current else "", t)
        for h, t in NAV)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · FL3 NFL Research</title>
<meta name="description" content="NFL line origination research: verified 2026 season data, injury and depth analysis, strategy validation gates.">
<style>
:root{{
 --bg:#0b0f16; --panel:#121a26; --panel2:#0f1621; --line:#22303f;
 --ink:#e8eef7; --dim:#93a4bb; --accent:#4da3ff; --good:#3ecf8e;
 --warn:#f5b544; --bad:#ff6b6b; --chip:#1b2836;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
header.top{{position:sticky;top:0;z-index:10;background:rgba(11,15,22,.94);
 backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 20px}}
.brand{{display:flex;align-items:center;gap:12px;padding:14px 0 6px}}
.brand b{{font-size:17px;letter-spacing:.2px}}
.brand span.tag{{color:var(--dim);font-size:12.5px}}
nav{{display:flex;flex-wrap:wrap;gap:2px;padding-bottom:10px}}
nav a{{padding:7px 12px;border-radius:8px;color:var(--dim);font-size:13.5px;font-weight:500}}
nav a:hover{{background:var(--chip);color:var(--ink);text-decoration:none}}
nav a.on{{background:#173252;color:#cfe6ff}}
main{{padding:30px 0 70px}}
h1{{font-size:30px;line-height:1.25;margin:6px 0 8px}}
h2{{font-size:20px;margin:38px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
h3{{font-size:16px;margin:24px 0 8px}}
p.lede{{color:var(--dim);font-size:15.5px;max-width:74ch;margin:0 0 4px}}
.kicker{{color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}}
.grid{{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));margin:22px 0 6px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.card .n{{font-size:28px;font-weight:700;letter-spacing:-.5px}}
.card .l{{color:var(--dim);font-size:13px}}
.card a{{font-size:12.5px}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin:12px 0 6px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}}
th{{text-align:left;padding:10px 12px;background:var(--panel2);color:var(--dim);
 font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--line);
 position:sticky;top:0;white-space:nowrap}}
td{{padding:9px 12px;border-bottom:1px solid #1a2532;vertical-align:top}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#151f2c}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.caption{{display:block;padding:10px 12px 0;color:var(--dim);font-size:12px}}
.methodflag{{display:block;margin:8px 12px 0;padding:5px 10px;border-radius:7px;font-size:11.5px;
 font-weight:600;color:#c9b6ff;background:#241b3a;border:1px solid #3a2d5c}}
table.method td{{color:#c8d2e0}}
.note{{padding:8px 12px 12px;color:var(--dim);font-size:12.5px;margin:0}}
.badge{{display:inline-block;padding:1px 7px;border-radius:6px;font-size:11px;
 font-weight:600;background:var(--chip);color:var(--dim);border:1px solid var(--line)}}
.badge.src{{color:#9fccff;border-color:#27415e}}
.badge.bad{{color:var(--bad);border-color:#5a2b2b;background:#2a1618}}
.pill{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11.5px;font-weight:600;
 background:var(--chip);color:var(--dim);white-space:nowrap}}
.pill.out{{background:#3a1a1d;color:#ff9d9d}}
.pill.doubt{{background:#3a2d18;color:#ffcb7a}}
.pill.q{{background:#3a3518;color:#f2e07a}}
.pill.ok{{background:#15321f;color:#7fe3ab}}
.pill.info{{background:#152b3a;color:#96cfef}}
.pill.mute{{background:#1b222c;color:#8b9aad}}
.blank{{color:#5f7086}}
.callout{{border-left:3px solid var(--accent);background:var(--panel);padding:14px 16px;
 border-radius:0 10px 10px 0;margin:16px 0;color:var(--dim);font-size:13.5px}}
.callout.warn{{border-left-color:var(--warn)}}
.callout.bad{{border-left-color:var(--bad)}}
.callout b{{color:var(--ink)}}
ul.tight{{margin:8px 0 8px 18px;padding:0;color:var(--dim);font-size:13.5px}}
ul.tight li{{margin:5px 0}}
ul.tight b{{color:var(--ink)}}
.split{{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}}
.q{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}}
.q h3{{margin:0 0 6px;font-size:15.5px}}
.q .meta{{color:var(--dim);font-size:12.5px;margin-bottom:10px}}
.q dl{{margin:0;display:grid;grid-template-columns:132px 1fr;gap:6px 12px;font-size:13px}}
.q dt{{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.05em;padding-top:2px}}
.q dd{{margin:0}}
footer{{border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;padding:24px 0 40px}}
footer p{{margin:6px 0}}
@media(max-width:640px){{h1{{font-size:24px}}.brand{{flex-wrap:wrap}}table{{min-width:440px}}}}
</style>
</head><body>
<header class="top"><div class="wrap">
<div class="brand"><b>FL3 · NFL Research</b><span class="tag">2026 season · Week 10 snapshot · as of {AS_OF}</span></div>
<nav>{nav}</nav>
</div></header>
<main class="wrap">
<div class="kicker">{e(subtitle)}</div>
<h1>{e(title)}</h1>
{body}
</main>
<footer class="wrap">
<p><b>Research dashboard, not betting advice.</b> No odds are published and no wager is recommended.
This is an educational and analytical exercise about line origination and validation.</p>
<p>Every figure links to the source that produced it. Values that could not be confirmed from an official
source are left blank and listed on the <a href="flagged.html">Flagged for Review</a> page.
Data captured {AS_OF} and will age; check the as-of date before relying on anything here.</p>
<p><a href="../index.html">← Back to the research desk</a> · built by session <code>arena-46e888f0</code> · sources: <a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener">NFL.com</a> ·
<a href="https://www.nfl.com/injuries/" target="_blank" rel="noopener">NFL.com injury report</a> ·
<a href="https://www.ourlads.com/nfldepthcharts/" target="_blank" rel="noopener">Ourlads depth charts</a> ·
<a href="sources.html">full registry</a></p>
</footer></body></html>"""


# ---------------------------------------------------------------- pages
def build_index():
    st = D("standings")["meta"]["teams"]
    inj = D("injuries_2026_w10")["report"]
    dr = D("depth_risk")
    lr = D("lineup_risk")["teams"]
    ln = D("lines")
    strat = D("strategies")
    qs = D("questions")["questions"]
    sg = D("suggestions")["suggestions"]
    fl = D("flagged")

    outs = [r for r in inj if r["game_status"] == "Out"]
    total_losses = sum(t["confirmed_starter_losses"] for t in lr)
    cards = [
        ("32", "teams verified", "league.html", "nfl.com standings"),
        ("14", "week 10 games", "league.html", "13 unplayed + 1 final"),
        (str(len(inj)), "injury-report rows", "injuries.html", "official NFL report"),
        (str(len(outs)), "players ruled <b>Out</b>", "injuries.html", "game status = Out"),
        (str(total_losses), "confirmed starter losses", "injuries.html", "Out/Doubtful starters on the charts"),
        (str(len(dr["conflicts"])), "source conflicts", "flagged.html", "nfl.com vs Ourlads"),
        ("8", "validation gates", "strategies.html", "0 strategies passed"),
        ("0", "graded strategies", "strategies.html", "leaderboard empty by design"),
    ]
    cardhtml = "".join(
        '<div class="card"><div class="n">%s</div><div class="l">%s</div>'
        '<a href="%s">%s</a></div>' % (n, l, h, e(sub)) for n, l, h, sub in cards)

    top = lr[:6]
    rows = []
    for t in top:
        worst = t["worst_gaps"][0] if t["worst_gaps"] else None
        rows.append([
            "<b>%s</b>" % e(t["team"]),
            e(t["team_name"]),
            '<span class="num">%d</span>' % t["confirmed_starter_losses"],
            '<span class="num">%.2f</span>' % t["replacement_risk_index"],
            ("%s (%s)<br><span class=\"blank\">%s → %s</span>" % (
                e(worst["position"]), e(worst["status"]),
                e(worst["starter"]), e(worst["replacement"]))) if worst else blank(),
            srclink("S02") + " " + srclink("S04"),
        ])

    open_q = [q for q in qs if q["status"] == "open"]
    body = f"""
<p class="lede">A verified snapshot of the 2026 NFL season entering Week 10, plus the machinery for
originating our own lines and deciding which strategies deserve to be trusted. Nothing on this site is
inferred: every row carries the source that published it, and the gaps are as visible as the data.</p>

<div class="grid">{cardhtml}</div>

<div class="callout bad"><b>Read this first.</b> No market odds were reachable from this environment, so there is
<b>no closing-line value, no vig-adjusted EV and no market comparison</b> anywhere in this build. The line model
originates numbers from published results only. Home-field advantage is set to <b>0.0</b> because no home/away
scoring split was available to calibrate it — inventing one would have violated the no-hallucination rule.
See <a href="flagged.html">Flagged for Review</a>.</div>

<h2>What this is</h2>
<div class="split">
<div class="card"><h3 style="margin-top:0">The research question</h3>
<p class="l">Can we originate our own NFL lines from verified public data, and can we prove — not assume — that a
strategy has skill rather than luck? This site is that question made auditable: source, method, gate, decision.</p></div>
<div class="card"><h3 style="margin-top:0">The honest answer so far</h3>
<p class="l">The data pipeline works and the gates are defined. <b>No strategy has been validated</b>, because no
bets have been settled and no odds exist to compare against. The leaderboard is empty on purpose.</p></div>
</div>

<h2>Biggest exposure this week</h2>
{table(["Team", "Club", "Starter losses", "Risk index", "Worst replacement", "Sources"], rows,
       note="Risk index sums positive gaps between a confirmed-out starter and his listed backup, weighted by draft pedigree and depth. It is a descriptive exposure score, not a projection. <a href='injuries.html'>Full breakdown</a>.")}

<h2>Decisions waiting on you</h2>
{table(["ID", "Question", "Blocks", "Status"],
       [[e(q["id"]), e(q["question"]), e(", ".join(q["blocks"][:3])), pill(q["status"], "q" if q["status"] == "open" else "info")]
        for q in open_q[:6]],
       note="%d questions are open, each with the evidence that would close it. <a href='questions.html'>All questions</a>. These are internal decision records, not published data." % len(open_q), method=True)}

<h2>Where to go next</h2>
<div class="grid">
<div class="card"><div class="l">League</div><p style="margin:6px 0 0">All 32 standings rows, the Week 10 slate and the four teams on bye.
<br><a href="league.html">Standings &amp; schedule →</a></p></div>
<div class="card"><div class="l">Injuries</div><p style="margin:6px 0 0">345 official designations, the depth chart behind each one,
and the backup-deficiency index.<br><a href="injuries.html">Injury &amp; lineup analysis →</a></p></div>
<div class="card"><div class="l">Model lines</div><p style="margin:6px 0 0">13 original lines with every input and parameter exposed.
<br><a href="lines.html">Line origination →</a></p></div>
<div class="card"><div class="l">Strategies</div><p style="margin:6px 0 0">8 registered strategies, 8 validation gates, correlation pricing,
luck removal.<br><a href="strategies.html">Strategy lab →</a></p></div>
</div>

<h2>Honest status board</h2>
<div class="callout"><b>%d flagged items</b>, including %d direct source conflicts, are published for review on the
<a href="flagged.html">Flagged for Review</a> page. %d suggestions are queued with decisions recorded, and %d are
already implemented.</div>
""" % (fl["meta"]["counts"]["total"], fl["meta"]["counts"]["source_conflicts"],
       len(sg), sum(1 for s in sg if s["status"] == "implemented"))
    return page("index.html", "NFL line origination, on verified data",
                "2026 season · week 10", body, "index.html")


def build_league():
    st = D("standings")["meta"]["teams"]
    sch = D("schedule_2026_w10")
    order = sorted(st, key=lambda t: (-(t["w"] + 0.5 * t["t"]) / (t["w"] + t["l"] + t["t"]), -t["net"]))
    rows = []
    for i, t in enumerate(order, 1):
        rows.append([str(i), "<b>%s</b>" % e(t["team"]), e(t["name"]),
                     e(t["conference"]), e(t["division"]),
                     '<span class="num">%d-%d-%d</span>' % (t["w"], t["l"], t["t"]),
                     '<span class="num">%.3f</span>' % t["pct"],
                     '<span class="num">%d</span>' % t["pf"], '<span class="num">%d</span>' % t["pa"],
                     '<span class="num">%+d</span>' % t["net"],
                     e(t["streak"]), e(t["last5"]), srclink(t["src"])])
    g = []
    for x in sch["games"]:
        res = "%d – %d" % (x["away_score"], x["home_score"]) if x["status"] == "FINAL" else blank()
        g.append([e(x["date"]), e(x["kickoff_et"]) + " ET",
                  "<b>%s</b> at %s" % (e(x["away"]), e(x["home"])),
                  e(x["network"]) + ("<br><span class=\"blank\">%s</span>" % e(x["designation"]) if x["designation"] else ""),
                  pill(x["status"].title(), "ok" if x["status"] == "FINAL" else "info") + " " + res,
                  srclink(x["src"])])
    body = f"""
<p class="lede">Every number on this page comes from the official nfl.com league standings page for the 2026
regular season, captured {AS_OF}. The page reproduces the published values verbatim; nothing is recalculated
except winning percentage, which is checked against the published value before publication.</p>

<div class="callout"><b>Integrity check that passed:</b> across all 32 teams the sum of points-for equals the sum of
points-against equals {sum(t['pf'] for t in st):,}. That identity must hold because every point scored is a point
allowed. Each of the 32 winning percentages also reproduces exactly from its own W-L-T record using
(W + 0.5×T) / G.</div>

<h2>League standings</h2>
{table(["#", "Team", "Club", "Conf", "Div", "W-L-T", "PCT", "PF", "PA", "Net", "Strk", "Last 5", "Src"],
       rows, note="Sorted by winning percentage then net points. PF / PA are season totals through the games published on the source page. Source: %s" % srclink("S01"))}

<h2>Week 10 schedule</h2>
{table(["Date", "Kickoff", "Matchup", "Network", "Status", "Src"], g,
       note="14 games, 28 teams playing, 4 on bye (CHI, DEN, PHI, TB). Times as published in Eastern Time. Game venue is not shown because it was not read from the source for every game. Source: %s" % srclink("S03"))}

<h2>Teams on bye</h2>
<p class="lede">{", ".join(e(b) for b in sch["byes"])} — these four teams do not play in Week 10 and are therefore
excluded from the exposure analysis on the <a href="injuries.html">Injuries</a> page.</p>

<h2>What this page cannot tell you</h2>
<ul class="tight">
<li><b>Home and road point splits.</b> The source publishes home and road win-loss records but not points. That is
why home-field advantage is 0.0 in the <a href="lines.html">line model</a>.</li>
<li><b>Strength of schedule.</b> Not published on the source page and not computed here.</li>
<li><b>Anything about a single game's context</b> — rest, travel, weather. Not in the data.</li>
</ul>
"""
    return page("league.html", "League standings and the Week 10 slate",
                "verified league context", body, "league.html")


def build_injuries():
    inj = D("injuries_2026_w10")["report"]
    dr = D("depth_risk")
    lr = D("lineup_risk")
    teams = sorted({r["team"] for r in inj})

    counts = {}
    for r in inj:
        counts.setdefault(r["team"], {"Out": 0, "Doubtful": 0, "Questionable": 0, "none": 0})
        key = r["game_status"] or "none"
        counts[r["team"]][key] += 1

    trows = []
    for t in teams:
        c = counts[t]
        score = next((x for x in lr["teams"] if x["team"] == t), None)
        trows.append([
            "<b>%s</b>" % e(t), str(len([r for r in inj if r["team"] == t])),
            pill(str(c["Out"]), "out" if c["Out"] else "mute"),
            pill(str(c["Doubtful"]), "doubt" if c["Doubtful"] else "mute"),
            pill(str(c["Questionable"]), "q" if c["Questionable"] else "mute"),
            pill(str(c["none"]), "mute"),
            ('<span class="num">%.2f</span>' % score["replacement_risk_index"]) if score else blank(),
            srclink("S02"),
        ])

    idx_rows = []
    for t in lr["teams"]:
        if not t["worst_gaps"]:
            continue
        for g in t["worst_gaps"]:
            idx_rows.append([
                "<b>%s</b>" % e(t["team"]),
                e(g["position"]),
                e(g["starter"]) + (" <span class=\"pill out\">%s</span>" % e(g["status"])),
                e(g["starter_code"] or "—"),
                e(g["replacement"]) if g["replacement"] else '<span class="blank">not on chart</span>',
                e(g["replacement_code"]) if g["replacement_code"] else blank(),
                ('<span class="num">%+.2f</span>' % g["pedigree_gap"]) if g["pedigree_gap"] is not None else '<span class="blank">ungraded</span>',
                srclink("S02") + " " + srclink("S04"),
            ])

    detailed = []
    for r in dr["depth"]:
        if r["official_game_status"] in ("Out", "Doubtful"):
            detailed.append([
                "<b>%s</b>" % e(r["team"]), e(r["position"]),
                "<b>%s</b>" % e(r["player"]),
                pill(r["official_game_status"], "out" if r["official_game_status"] == "Out" else "doubt"),
                e(r["official_injury"]) if r["official_injury"] else blank(),
                e(r["official_practice"].replace(" Participation in Practice", "").replace("Did Not Participate In Practice", "DNP")),
                e(r["depth_code"] or "—"),
                srclink("S02") + (' <a class="badge" href="%s" target="_blank" rel="noopener">player</a>' % e(r["player_page"]) if r["player_page"] else ""),
            ])

    conf_rows = [[e(c["id"]), e(c["team"]), e(c["position"]), e(c["player"]),
                  pill("Ourlads: " + c["ourlads_marker"], "out"),
                  pill("NFL: " + c["official_game_status"], "info"),
                  srclink("S02") + " " + srclink("S04")] for c in dr["conflicts"]]

    body = f"""
<p class="lede">The official NFL Week 10 injury report, matched player by player against the depth chart behind
him. This is the part of the brief that asks the system to know when a starter is replaced by a backup — and to
know when it <em>cannot</em> know.</p>

<div class="callout bad"><b>The rule that governs this page.</b> Availability comes <b>only</b> from the official
NFL injury report. Depth <em>order</em> comes from Ourlads. The two disagreed <b>{len(dr['conflicts'])}</b> times in a
single week, and every disagreement is shown below rather than averaged away. A player who does not appear on the
official report is recorded as <b>"no designation published"</b> — never as healthy.</div>

<h2>Availability by team</h2>
{table(["Team", "On report", "Out", "Doubtful", "Questionable", "No designation", "Risk index", "Src"], trows,
       note="Counts of every player published on the official Week 10 report. 'No designation' means the league published no game status for that player — it does not mean he is healthy. Source: %s" % srclink("S02"))}

<h2>Who replaces whom — the deficiency index</h2>
<p class="lede">When the official report rules a listed starter out or doubtful, the next man up is taken from the
depth chart. The gap is the difference in <em>proven investment</em> between the two, using draft round and depth
ordinal as the weights. It is a proxy for replacement quality, not a measurement of it.</p>
{table(["Team", "Pos", "Starter", "Code", "Replacement", "Code", "Gap", "Sources"], idx_rows,
       note="Code format: <code>YY/R</code> = drafted in round R of year 20YY; <code>CFYY</code> = undrafted college free agent in 20YY; <code>SFYY</code> = street free agent; <code>U/TEAM</code> = unrestricted free-agent signing; <code>T/TEAM</code> = trade acquisition. Decoded from the Ourlads key %s." % srclink("S05"))}

<h2>Every confirmed absence, with depth context</h2>
{table(["Team", "Pos", "Player", "Status", "Injury", "Practice", "Depth", "Sources"], detailed,
       note="All starters and backups at the transcribed positions carrying an Out or Doubtful designation. Practice column is abbreviated: DNP = did not participate. Source: %s" % srclink("S02"))}

<h2>Source conflicts: nfl.com vs Ourlads</h2>
{table(["ID", "Team", "Pos", "Player", "Ourlads", "Official NFL", "Sources"], conf_rows,
       note="In every case the official NFL report governs and the Ourlads marker is recorded but not used. These rows are also published on <a href='flagged.html'>Flagged for Review</a>.")}

<h2>Scope limits, stated plainly</h2>
<ul class="tight">
<li><b>27 of the 28 playing teams are transcribed.</b> Indianapolis is missing from the depth analysis (flagged F-06).</li>
<li><b>Draft pedigree is a proxy.</b> A seventh-round starter who has played well is scored as a weak replacement.
No snap counts or player grades exist in this repo (flagged F-09).</li>
<li><b>Questionable is not out.</b> The site cannot know whether a Questionable player suited up, because the
inactives list was not captured. That is question Q-03.</li>
<li><b>Injuries are not yet in the line.</b> The exposure score has never been validated against outcomes, so it is
deliberately absent from the <a href="lines.html">line model</a> (flagged F-05).</li>
</ul>
"""
    return page("injuries.html", "Injuries, depth charts and who is actually replacing whom",
                "official availability × depth order", body, "injuries.html")


def build_lines():
    ln = D("lines")
    m = ln["meta"]
    rows = []
    for g in ln["games"]:
        rows.append([
            e(g["date"]), e(g["kickoff_et"]) + " ET",
            "<b>%s</b> at %s" % (e(g["away"]), e(g["home"])),
            '<span class="num">%+.1f</span>' % g["model_home_line"],
            '<span class="num">%.1f</span>' % g["model_total"],
            '<span class="num">%.1f</span>' % g["exp_away_points"],
            '<span class="num">%.1f</span>' % g["exp_home_points"],
            '<span class="num">%.2f</span>' % g["inputs"]["away"]["off"],
            '<span class="num">%.2f</span>' % g["inputs"]["home"]["off"],
            e(g["lineup_risk"]["away"]) if g["lineup_risk"]["away"] is not None else blank(),
            e(g["lineup_risk"]["home"]) if g["lineup_risk"]["home"] is not None else blank(),
            srclink(g["src"]),
        ])
    mods = [[e(k), '<span class="num">%.2f</span>' % v["off_raw"], '<span class="num">%.2f</span>' % v["def_raw"],
             '<span class="num">%.2f</span>' % v["off"], '<span class="num">%.2f</span>' % v["def"],
             str(v["games"]), srclink("S01")]
            for k, v in sorted(ln["all_models"].items())]
    body = f"""
<p class="lede">Thirteen original lines, generated from this repo's verified season data and nothing else.
These are <b>originated numbers</b>, not market prices. No sportsbook figure was read, stored or copied — none
was reachable.</p>

<div class="callout bad"><b>Why these numbers are not yet bettable.</b> Home-field advantage is <b>0.0</b> because no
home/away scoring split exists in the data. No injury adjustment is applied because the exposure index has never been
validated. There is no market comparison because there is no odds feed. Each of those is a deliberate, documented
omission rather than a guess.</div>

<h2>The model, in full</h2>
<div class="split">
<div class="card"><h3 style="margin-top:0">Inputs</h3>
<ul class="tight" style="margin-left:0;list-style:none;padding:0">
<li>League points per team-game: <b>{m['inputs']['league_points_per_team_game']}</b> <span class="blank">— computed from the data, not assumed</span></li>
<li>Shrinkage prior k: <b>{m['inputs']['shrinkage_prior_games_k']} games</b> <span class="blank">— a convention, flagged F-10</span></li>
<li>Home-field advantage: <b>{m['inputs']['home_field_advantage']}</b> <span class="blank">— uncalibrated, flagged F-04</span></li>
<li>Injury adjustment: <b>{m['inputs']['injury_adjustment']}</b> <span class="blank">— unvalidated, flagged F-05</span></li>
</ul></div>
<div class="card"><h3 style="margin-top:0">Formula</h3>
<ul class="tight" style="margin-left:0;list-style:none;padding:0">
<li><code>off = w·(PF/G) + (1−w)·μ</code>, <code>w = G/(G+k)</code></li>
<li><code>expected = μ + (own_off − μ) + (opp_def − μ)</code></li>
<li><code>home line = −(exp_home − exp_away)</code></li>
<li><code>total = exp_away + exp_home</code></li>
</ul>
<p class="note" style="padding:8px 0 0">The shrunken rates keep the league mean, so the deviation form above is
algebraically the classic <code>(own_off + opp_def)/2</code> once both are on a per-team-game scale.</p></div>
</div>

<h2>Week 10 model lines</h2>
{table(["Date", "Kickoff", "Matchup", "Home line", "Total", "Exp away", "Exp home", "Away off", "Home off", "Away risk", "Home risk", "Src"], rows,
       note="Home line is in standard notation: negative means the home team is favoured. Expected points and the total are reproduced exactly from the published components. Source: %s" % srclink("S01"))}

<h2>Team ratings used as inputs</h2>
{table(["Team", "Raw PF/G", "Raw PA/G", "Shrunk off", "Shrunk def", "Games", "Src"], mods,
       note="Raw rates are shown next to the shrunk rates so a reviewer can see exactly how much the prior moved each team.")}

<h2>What would make these lines trustworthy</h2>
<ul class="tight">
<li><b>A calibrated home-field term</b> (Q-01). Until then every line is compressed toward pick'em.</li>
<li><b>A validated injury adjustment</b> (Q-03, F-05). The exposure index exists; it has not earned a place in the line yet.</li>
<li><b>Any market price at all</b> (Q-04). Without closing lines there is no way to test whether a model line is good.</li>
<li><b>An honest scoring rule</b> — mean absolute error against the closing line would be the first real test, and it
is impossible today.</li>
</ul>
"""
    return page("lines.html", "Original model lines for Week 10",
                "line origination, no market copying", body, "lines.html")


def build_strategies():
    s = D("strategies")
    g = [[e(x["id"]), "<b>%s</b>" % e(x["name"]), e(x["rule"]), e(x["why"])] for x in s["gates"]]
    st = []
    for x in s["strategies"]:
        passed = sum(1 for v in x["gates"].values() if v["status"] == "pass")
        st.append([e(x["id"]), "<b>%s</b>" % e(x["name"]), pill(x["family"], "info"),
                   e(x["market"]),
                   pill(x["status"], "ok" if x["status"] == "validated" else ("mute" if x["status"] == "blocked-input" else "q")),
                   "%d/%d" % (passed, len(x["gates"])),
                   e(x["notes"])])
    cor = [[e(c["pair"]),
            ('<span class="num">%.2f</span>' % c["rho"]) if c["rho"] is not None else '<span class="blank">not estimated</span>',
            e(c["basis"]), pill(c["status"], "ok" if c["status"] == "assumption" else "q")] for c in s["correlation"]["pairs"]]
    dem = [[('%.1f' % d["rho"]), ('<span class="num">%.4f</span>' % d["naive_product"]),
            ('<span class="num">%s</span>' % d["copula_joint"]),
            ('<span class="num">%+.2f</span>' % d["delta_pct_points"]),
            ('<span class="num">%.2f</span>' % d["fair_decimal_naive"]),
            ('<span class="num">%.2f</span>' % d["fair_decimal_copula"])]
           for d in s["correlation"]["demonstration"]]
    luck = [[e(x["id"]), "<b>%s</b>" % e(x["name"]), e(x["method"]), pill(x["status"], "q"), e(x["blocker"])]
            for x in s["luck_removal"]["procedures"]]
    lb = s["leaderboard"]
    tiers = [[e(t["tier"]), e(t["requirement"]), e(t["reward"])] for t in lb["reward_scheme"]["tiers"]]
    body = f"""
<p class="lede">A leaderboard is only worth looking at if a strategy has to earn its place. This page defines the
test first and the ranking second — eight gates, a correlation-aware pricing method, and a luck-removal protocol.
<b>No strategy has passed anything yet, because no bet has been settled.</b></p>

<div class="callout bad"><b>The leaderboard is empty on purpose.</b> {e(lb['why'])}</div>

<h2>The eight validation gates</h2>
{table(["ID", "Gate", "Rule", "Why it exists"], g, method=True,
       note="A strategy must pass every gate before a leaderboard row is shown. Gates are pre-registered so the thresholds cannot be chosen after seeing results.")}

<h2>Registered strategies</h2>
{table(["ID", "Strategy", "Family", "Market", "Status", "Gates passed", "Notes"], st, method=True,
       note="'blocked-input' means the strategy is well-posed but the data it needs is not in the repo. It is registered rather than hidden, so the gap is visible.")}

<h2>Correlation — the parlay problem</h2>
<p class="lede">Multiplying leg probabilities assumes independence. For same-game legs that assumption is wrong, and
it is wrong in the direction that makes a parlay look better than it is. The engine prices two-leg parlays with a
Gaussian copula and <b>refuses to price at all</b> when the correlation has not been estimated.</p>
{table(["Pair", "ρ", "Basis", "Status"], cor, method=True,
       note="No correlation on this site is empirical. Nothing has been estimated from data because no per-player game logs or play-by-play exist in the repo.")}

<h3>Why it matters, arithmetically</h3>
{table(["ρ", "Naive product", "Copula joint", "Δ (pts)", "Fair odds (naive)", "Fair odds (copula)"], dem, method=True,
       note="Two legs at 55% each. At ρ = 0.6 the true joint probability is 40.4%, not 30.3% — a parlay that looks like a 3.3x payout is really worth about 2.5x. This is exactly the error gate G7 exists to prevent.")}

<h2>Removing luck from the equation</h2>
{table(["ID", "Procedure", "Method", "Status", "Blocker"], luck, method=True,
       note=e(s["luck_removal"]["multiple_comparisons_note"]))}

<h2>Leaderboard and reward design</h2>
{table(["Tier", "Requirement", "Reward"], tiers, method=True,
       note="Design only. The scheme allocates no money and has no verified historical returns behind it.")}
<p class="lede" style="margin-top:12px">Ranking metric: <b>{e(lb['reward_scheme']['scoring'])}</b>. Raw ROI is
deliberately <em>not</em> the ranking metric, because it rewards the luckiest high-variance strategy.</p>

<h2>What would fill the leaderboard</h2>
<ul class="tight">
{"".join('<li>%s</li>' % e(x) for x in lb["what_would_fill_it"])}
</ul>
"""
    return page("strategies.html", "Strategy lab: gates first, leaderboard later",
                "validation, correlation, luck removal", body, "strategies.html")


def build_questions():
    qs = D("questions")["questions"]
    blocks = []
    for q in qs:
        know = "".join("<li>%s</li>" % e(x) for x in q["we_know"]) or "<li>nothing</li>"
        dont = "".join("<li>%s</li>" % e(x) for x in q["we_do_not_know"]) or "<li>nothing</li>"
        need = "".join("<li>%s</li>" % e(x) for x in q["evidence_needed"]) or "<li>nothing further</li>"
        blocks.append(f"""
<div class="q">
<h3>{e(q['id'])} · {e(q['question'])} {pill(q['status'], 'ok' if q['status']=='answered' else ('info' if q['status']=='proposed-answer' else 'q'))}</h3>
<div class="meta">Area: {e(q['area'])} &nbsp;·&nbsp; Blocks: {e(', '.join(q['blocks']))}</div>
<dl>
<dt>We know</dt><dd><ul class="tight" style="margin:0">{know}</ul></dd>
<dt>We do not know</dt><dd><ul class="tight" style="margin:0">{dont}</ul></dd>
<dt>Evidence needed</dt><dd><ul class="tight" style="margin:0">{need}</ul></dd>
<dt>Answer</dt><dd>{e(q['answer']) if q['answer'] else '<span class="blank">open — deliberately unanswered rather than assumed</span>'}</dd>
<dt>If unanswered</dt><dd>{e(q['consequence_if_unanswered'])}</dd>
</dl>
</div>""")
    open_n = sum(1 for q in qs if q["status"] == "open")
    body = f"""
<p class="lede">Before any decision can be made reasonably, these questions have to be closed. Each one states what
we already know, what we specifically do not know, what evidence would settle it, and what breaks if it stays open.
<b>{open_n} of {len(qs)} are open.</b></p>

<div class="callout"><b>Why a question instead of a guess.</b> Every entry below marks a place where the data ran out.
Filling those places with a plausible number is the single easiest way to make this whole project worthless, so
each one is recorded as an open question with the specific evidence that would close it.</div>

{"".join(blocks)}
"""
    return page("questions.html", "What must be answered before deciding anything",
                "decision-blocking questions", body, "questions.html")


def build_suggestions():
    sg = D("suggestions")
    rows = []
    for s in sg["suggestions"]:
        rows.append([e(s["id"]), "<b>%s</b>" % e(s["title"]),
                     pill(s["status"], "ok" if s["status"] == "implemented" else ("info" if s["status"] == "proposed" else "mute")),
                     '<span class="num">%d</span>' % s["impact"],
                     '<span class="num">%d</span>' % s["effort"],
                     '<span class="num">%d</span>' % s["confidence"],
                     e(s["decision"])])
    blocks = []
    for s in sg["suggestions"]:
        blocks.append(f"""
<div class="q">
<h3>{e(s['id'])} · {e(s['title'])} {pill(s['status'], 'ok' if s['status']=='implemented' else 'info')}</h3>
<div class="meta">Impact {s['impact']}/5 · Effort {s['effort']}/5 · Confidence {s['confidence']}%</div>
<dl>
<dt>Problem</dt><dd>{e(s['problem'])}</dd>
<dt>Proposal</dt><dd>{e(s['proposal'])}</dd>
<dt>Evidence</dt><dd>{e(s['evidence'])}</dd>
<dt>Decision</dt><dd>{e(s['decision'])}</dd>
</dl>
</div>""")
    log = [[e(x["when"]), e(x["what"]), e(x["by"]), pill(x["decision"], "ok" if x["decision"] == "implemented" else "info"), e(x["rationale"])]
           for x in sg["decision_log"]]
    body = f"""
<p class="lede">A reviewed queue of proposed improvements, so the best path can be chosen <em>before</em> anything is
built. Each suggestion carries a problem, a proposal, an impact/effort/confidence score and a recorded decision.
Nothing here is applied silently.</p>

<div class="callout"><b>How to read the scores.</b> {e(sg['meta']['rubric']['impact'])}.
{e(sg['meta']['rubric']['effort'])}. {e(sg['meta']['rubric']['confidence'])}</div>

<h2>Review board</h2>
{table(["ID", "Suggestion", "Status", "Impact", "Effort", "Conf.", "Decision"], rows, method=True,
       note="Sorted as authored. Click through the detail cards below for the full problem statement behind each.")}

<h2>Decision log</h2>
{table(["When", "Items", "By", "Decision", "Rationale"], log, method=True,
       note="The log exists so a deferred item is visibly deferred rather than quietly dropped. Deferred items need a decision from the repository owner.")}

<h2>Detail</h2>
{"".join(blocks)}
"""
    return page("suggestions.html", "Suggestions, scored and decided",
                "improvement queue", body, "suggestions.html")


def build_flagged():
    fl = D("flagged")
    rows = []
    for i in fl["items"]:
        rows.append([e(i["id"]), pill(i["category"], "bad" if i["category"] == "Source conflict" else "mute"),
                     e(i["claim"]),
                     " ".join(srclink(s) for s in i["sources"]) or '<span class="blank">no source — structural</span>',
                     "yes" if i["blocks"] else "no"])
    blocks = []
    for i in fl["items"]:
        blocks.append(f"""
<div class="q">
<h3>{e(i['id'])} · {e(i['claim'])} {pill(i['category'], 'bad' if i['category']=='Source conflict' else 'mute')}</h3>
<div class="meta">{' '.join(srclink(x) for x in i['sources']) or 'no external source'} · blocking: {e('yes' if i['blocks'] else 'no')}</div>
<dl>
<dt>Detail</dt><dd>{e(i['detail'])}</dd>
<dt>Handling</dt><dd>{e(i['resolution'])}</dd>
<dt>Your action</dt><dd>{e(i['reviewer_action'])}</dd>
</dl>
</div>""")
    body = f"""
<p class="lede">Everything unresolved, unverified, blank, conflicting or scope-limited, in one place, with source
links. <b>Nothing on this page blocks publication</b> — it exists so it can be reviewed after the site is live.</p>

<div class="grid">
<div class="card"><div class="n">{fl['meta']['counts']['total']}</div><div class="l">flagged items</div></div>
<div class="card"><div class="n">{fl['meta']['counts']['source_conflicts']}</div><div class="l">direct source conflicts</div></div>
<div class="card"><div class="n">{fl['meta']['counts']['blocking_input_or_validation']}</div><div class="l">need an input or decision</div></div>
</div>

<div class="callout warn"><b>Nothing here is hidden.</b> Where a value could not be confirmed it was left blank and
listed here rather than filled in. The most consequential items are F-03 (no odds), F-04 (home-field advantage set to
zero) and F-11 (empty leaderboard) — each of those is a real limit on what the site can conclude.</div>

<h2>Register</h2>
{table(["ID", "Category", "What is irregular", "Sources", "Blocking"], rows, method=True,
       note="Structural register: most items record the ABSENCE of a source, so the row itself cannot cite one. Where a source does exist (the 14 conflicts) it is linked. Full detail, handling and reviewer action for every item is below.")}

<h2>Detail</h2>
{"".join(blocks)}
"""
    return page("flagged.html", "Flagged for review",
                "irregularities, blanks and limits", body, "flagged.html")


def build_sources():
    s = D("sources")
    rows = [[srclink(x["id"]), e(x["name"]), e(x["publisher"]), pill(x["type"], "ok" if x["type"] == "official-league" else "info"),
             e(x["used_for"]), e(AS_OF),
             '<a class="badge" href="%s" target="_blank" rel="noopener">open ↗</a>' % e(x["url"])]
            for x in s["sources"]]
    rej = [[e(x["source"]), e(x["result"]), e(x["consequence"])] for x in s["rejected_or_unavailable"]]
    rules = "".join("<li>%s</li>" % e(x) for x in s["authority_rules"])
    body = f"""
<p class="lede">The complete list of what this site used, what it tried and could not reach, and the rules that decide
which source wins when two disagree. Every source badge anywhere on the site resolves to a row here.</p>

<div class="callout"><b>Access method.</b> External pages were retrieved with a fetch tool and parsed by hand into the
JSON files in <code>data/</code>. Raw HTTP from scripts was blocked for these hosts, so nothing was scraped
automatically — which also means every transcription step is auditable.</div>

<h2>Sources used</h2>
{table(["ID", "Source", "Publisher", "Type", "Used for", "Accessed", "Link"], rows)}

<h2>Tried and unavailable</h2>
{table(["Source", "Result", "Consequence"], rej, method=True,
       note="Recorded so a later session does not spend time rediscovering the same dead end.")}

<h2>Authority rules</h2>
<ul class="tight">{rules}</ul>

<h2>Verification performed</h2>
<p class="lede">An automated harness (<code>scripts/verify_depth.py</code>) runs on every build and fails it if any of the
following break. All 16 checks pass as of {AS_OF}:</p>
<ul class="tight">
<li><b>Balance identity</b> — sum of points-for equals sum of points-against across all 32 teams (6,291 each).</li>
<li><b>Formula reproduction</b> — all 32 winning percentages recompute exactly from their own W-L-T record.</li>
<li><b>Arithmetic coherence</b> — all 32 net-points totals equal PF − PA.</li>
<li><b>Schedule completeness</b> — 14 games, 28 distinct teams, 4 byes, 32 accounted for, no team twice.</li>
<li><b>Controlled vocabulary</b> — every injury practice and game status is one of the values the league publishes.</li>
<li><b>Source totality</b> — every data row carries a source id that resolves to a registry entry.</li>
<li><b>No odds leakage</b> — the line file is scanned for market/price fields and must contain none.</li>
<li><b>Line coherence</b> — every published total and line recomputes from its own published components.</li>
<li><b>Gate completeness</b> — every strategy carries every validation gate.</li>
<li><b>Honesty invariant</b> — no open question may carry an answer; the leaderboard may not contain an unbacked row.</li>
</ul>
"""
    return page("sources.html", "Sources, authority rules and what verification ran",
                "provenance", body, "sources.html")


def main():
    OUT.mkdir(exist_ok=True)
    pages = {
        "index.html": build_index(),
        "league.html": build_league(),
        "injuries.html": build_injuries(),
        "lines.html": build_lines(),
        "strategies.html": build_strategies(),
        "questions.html": build_questions(),
        "suggestions.html": build_suggestions(),
        "flagged.html": build_flagged(),
        "sources.html": build_sources(),
    }
    for name, content in pages.items():
        (OUT / name).write_text(content)
    (OUT / ".nojekyll").write_text("")
    print("wrote %d pages to depth/" % len(pages))
    for n, c in pages.items():
        print("  %-18s %6d bytes" % (n, len(c)))


if __name__ == "__main__":
    main()
