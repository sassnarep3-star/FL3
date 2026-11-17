#!/usr/bin/env python3
"""
FL3 — static site builder.

Renders a plain-HTML dashboard from the verified JSON datasets in data/.
No framework, no build tooling, no client-side JS required to read the tables.

Design rules enforced here
--------------------------
* Every data row renders a source link. A row without a source is rendered as
  "UNVERIFIED" and is also written to flagged.html's auto-generated section.
* Anything the model produced is labelled "model" and visualised differently
  from anything the league published.
* Blank stays blank. The renderer never substitutes a value.
"""
from __future__ import annotations

import csv
import html
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

PAGES = {
    "index.html": "Dashboard",
    "standings.html": "Standings",
    "lines.html": "Our Lines",
    "injuries.html": "Injuries",
    "matchups.html": "Matchup matrix",
    "ablations.html": "Ablations",
    "data-snapshots.html": "Data snapshots",
    "strategies.html": "Strategies",
    "correlation.html": "Correlation",
    "decisions.html": "Decisions",
    "suggestions.html": "Suggestions",
    "flagged.html": "Flagged for Review",
    "sources.html": "Sources",
    "compare.html": "Compare strategies",
    "executive-summary.html": "Executive summary",
    "methodology.html": "Methodology",
    "results.html": "Results feed",
    "week11.html": "Week 11",
    "availability.html": "Availability",
    "lab.html": "Lab",
    "spec.html": "Spec",
    "audit.html": "Acceptance audit",
    "board/readiness.html": "Requirement readiness",
    "verified/index.html": "Verified results & scoring",
    "verify/index.html": "Verification",
    "freshness/index.html": "Freshness",
}

CAPTURED = "2026-11-14"
RECAPTURED = "2026-11-16"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
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
    for p, t in PAGES.items():
        cls = ' class="on"' if p == active else ""
        parts.append(f'<a href="{p}"{cls}>{e(t)}</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · FL3 NFL Decision System</title>
<meta name="description" content="Verified NFL data, originated lines, strategy gates and open decisions. Every value links to an official source.">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand"><span class="mark">FL3</span><span class="sub">NFL Decision System</span></div>
  <nav>{nav}</nav>
</header>
<main id="main">
{body}
</main>
<footer>
  <p><strong>Snapshot {CAPTURED}.</strong> NFL data © the National Football League, quoted from nfl.com
  with links on every row. This site publishes our own model output, not betting advice, and not a
  sportsbook quote. Values that could not be confirmed against an official source are blank and
  listed on <a href="flagged.html">Flagged for Review</a>.</p>
</footer>
</body>
</html>
"""


def table(headers, rows, cls=""):
    th = "".join(f"<th>{h}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def badge(text, kind):
    return f'<span class="badge {kind}">{e(text)}</span>'


def stat(value, label, note=""):
    n = f'<em>{e(note)}</em>' if note else ""
    return f'<div class="stat"><b>{value}</b><span>{e(label)}</span>{n}</div>'


def money(v, digits=1):
    return "—" if v is None else f"{v:.{digits}f}"


def pct(v):
    return "—" if v is None else f"{v*100:.1f}%"


# ---------------------------------------------------------------------------
# page builders
# ---------------------------------------------------------------------------
def read_requirement_rows():
    with open(os.path.join(DATA, "requirements_readiness.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_source_registry():
    with open(os.path.join(DATA, "sources.csv"), newline="", encoding="utf-8") as fh:
        return {row["source_id"]: row for row in csv.DictReader(fh)}


def readiness_section(rows, sources):
    """Render the same requirement rows on the actual repository-root landing page."""
    state_kind = {
        "BLOCKED": "bad", "PARTIAL": "warn", "NOT STARTED": "bad",
        "DESIGN ONLY": "info", "IMPLEMENTED HERE": "ok",
        "REVIEW REQUIRED": "warn", "REJECT SHORTCUT": "bad",
    }
    rendered = []
    for r in rows:
        sid_list = [sid for sid in r["source_id"].split(";") if sid]
        links = []
        for sid in sid_list:
            src = sources.get(sid)
            if src:
                links.append(src_link(src["url"], sid))
            else:
                links.append(f'<span class="unverified">UNVERIFIED: {e(sid)}</span>')
        source = " ".join(links) if links else (
            '<span class="unverified">UNVERIFIED — no applicable official source</span>'
            f'<br><small>{e(r["source_gap"])}</small>'
        )
        state = r["current_state"]
        # repo_page may name a root page (PAGES) or a board page; only board pages
        # get the prefix, so a root page is never silently redirected to a 404.
        if r["repo_page"] in PAGES:
            repo_target = r["repo_page"]
        elif r["repo_page"].startswith("board/"):
            repo_target = r["repo_page"]
        else:
            repo_target = f"board/{r['repo_page']}"
        rendered.append([
            f"<b>{e(r['id'])}</b>", e(r["category"]), e(r["requirement"]),
            badge(state, state_kind.get(state, "warn")), e(r["blocking_gate"]),
            e(r["clearance_metric"]), source,
            f'<a href="{e(repo_target)}">details</a>',
        ])
    return f"""
<section id="requirement-readiness">
  <h2>Decision readiness — every requirement, blocker and clearing number</h2>
  <p class="lede">{len(rows)} requirements, one row each. States describe checked-in evidence; clearance
  criteria are proposed gates, not observed NFL facts. Official links are input sources, not proof of
  capture. Where no applicable official source is registered, the source is left blank and flagged.
  <a href="board/readiness.html">Open the full register</a> for missing information and recommended next steps.</p>
  {table(["ID", "Area", "Requirement", "Current state", "Blocking gate", "Clearance metric / number", "Official source / gap", "Evidence"], rendered, "wide")}
</section>
"""


# NOTE (2026-11-17, arena/bb4f237d-fl3): this must be a LIST OF ROWS, not a joined HTML
# string. table() iterates `rows` and then iterates each row for cells; a joined string
# was rendered one character per cell and shipped to production (see PR #46 follow-up).
FRONTIER_ROWS = [
    [f"<a href='{p}'>{t}</a>", d, h]
    for p, t, d, h in [
        ("results.html", "Results feed",
         "149 verified games reconciled club-by-club to the official standings",
         "32/32 clubs match; one missing game found and corrected"),
        ("availability.html", "Availability graph",
         "Depth-1 expected vs Game Book actual for Week 10, with replacement depth",
         "&ldquo;Questionable&rdquo; started 84% of the time; &ldquo;Out&rdquo; is the only reliable signal"),
        ("lab.html", "Lab",
         "Injury ablation on chronological holdouts + leaderboard v2 on proper scores",
         "Personnel term helps on no metric; no strategy clears the demotion gate"),
        ("week11.html", "Week 11",
         "13 official fixtures with venue, kickoff, network and our originated prices",
         "Market columns blank by policy PD-01"),
        ("spec.html", "Specification",
         "Row grain, authority and deliberate blanks for all eight new datasets",
         "Six gaps left visibly blank, not filled"),
    ]
]


def build_index(standings, lines, inj, luck, strat, dec, sug, flag, readiness, sources):
    n_teams = len(standings["teams"])
    n_games = len(lines["games"])
    n_rows = sum(len(t["players"]) for g in inj["games"] for t in g["teams"])
    n_out = sum(1 for g in inj["games"] for t in g["teams"] for p in t["players"] if p["game_status"] == "Out")
    open_flags = sum(1 for i in flag["items"] if i["status"] == "open")
    n_known = len(dec["known_facts"])
    n_missing = len(dec["missing_information"])
    n_sug = len(sug["suggestions"])

    body = f"""
<section class="hero">
  <h1>What the data actually says</h1>
  <p class="lede">A working dashboard for the FL3 NFL project. Every league figure below was read
  off an official NFL.com page on {CAPTURED} and links to that page. Where a number could not be
  confirmed, the cell is blank and the gap is listed on <a href="flagged.html">Flagged for Review</a>.</p>
</section>

<section class="subsites">
  <h2 style="margin-top:0">Start here</h2>
  <p class="lede" style="margin-bottom:10px">Two pages answer the questions this project is actually
  asked. <a href="compare.html"><b>Compare strategies</b></a> scores four origination strategies
  against four controls on 148 verified games, walk-forward, with the intervals, the multiplicity
  adjustment and the honest verdict. <a href="executive-summary.html"><b>Executive summary</b></a> is
  the one-page version: what is established, what is not, and the five things that block the rest.</p>
</section>

<section class="subsites">
  <h2 style="margin-top:0">The current dashboard, and the ones it replaces</h2>
  <p class="lede" style="margin-bottom:10px">Six sessions built dashboards for this brief before they could
  see each other's work. They are all still published. <b>The one to read first is
  <a href="verified/index.html">Verified results &amp; scoring</a></b>: it is the only build holding a results
  corpus that reconciles against the league's own standings, so it is the only one that can score a
  forecast. The others are kept for their specialist material, and some of their inputs are known to be
  incomplete — see <a href="verified/review.html">Flagged for review</a>.</p>
  <table>
    <thead><tr><th>Dashboard</th><th>What it is best at</th><th>Can score a forecast?</th></tr></thead>
    <tbody>
      <tr><td><a href="verified/index.html"><b>Verified results &amp; scoring</b></a></td>
          <td>148 verified results, out-of-sample line evaluation, live re-verification register</td>
          <td><b>yes</b></td></tr>
      <tr><td><a href="board/index.html">board</a></td>
          <td>column-label proofs, fitted constants with standard errors, decision math</td>
          <td>no — 33 of 148 game rows</td></tr>
      <tr><td><a href="depth/index.html">depth</a></td>
          <td>depth charts and per-club availability reconciliation</td>
          <td>no</td></tr>
      <tr><td><a href="docs/index.html">docs</a></td>
          <td>requirements and decision registers</td>
          <td>no</td></tr>
      <tr><td><a href="audit/index.html">audit</a></td>
          <td>brief-requirement coverage audit: every brief bullet mapped to its readiness register row</td>
          <td>no</td></tr>
      <tr><td><a href="site-9b181d31/index.html">site-9b181d31</a></td>
          <td>club-chart tier verification for 8 clubs, market-reference layer</td>
          <td>no</td></tr>
      <tr><td><a href="index.html">this page</a></td>
          <td>standings, Week 10 slates, availability counts, requirement readiness</td>
          <td>no</td></tr>
    </tbody>
  </table>
</section>

<section class="stats">
  {stat(n_teams, "clubs in the standings", "verified")}
  {stat(n_games, "Week 10 games", "verified")}
  {stat(n_rows, "injury-report rows", f"{n_out} ruled Out")}
  {stat(n_sug, "suggestions to decide", f"{open_flags} open flags")}
  {stat(n_known, "confirmed facts", f"{n_missing} information gaps")}
</section>

<section>
  <h2>The short version</h2>
  <div class="cards">
    <article class="card">
      <h3>We hold real data</h3>
      <p>All 32 clubs' 2026 records, the full Week 10 slate, and {n_rows} official injury-report rows.
      Internal arithmetic was checked line by line: points for minus points against equals net points
      for all 32 clubs.</p>
      <p>{src_link("https://www.nfl.com/standings/division/2026/REG", "nfl.com standings")}</p>
    </article>
    <article class="card">
      <h3>We originate our own lines</h3>
      <p>{n_games} spreads, totals and win probabilities, each with a sigma and a 90% band. Nothing is
      copied from a book. There is no market comparison anywhere on this site, because we hold no
      licensed price.</p>
      <p><a href="lines.html">See the lines</a></p>
    </article>
    <article class="card">
      <h3>Zero strategies have graded results</h3>
      <p>Eight strategy specs exist, with gates that fail them for good reasons. The leaderboard is
      live and empty. Any site that showed you a win rate right now would be inventing it.</p>
      <p><a href="strategies.html">See the gates</a></p>
    </article>
    <article class="card">
      <h3>The biggest gap is the price</h3>
      <p>Without a licensed market feed we cannot measure edge, closing-line value, or whether a line
      is any good. That is flag F07, and it blocks the top two reward tiers by construction.</p>
      <p><a href="flagged.html">See all flags</a></p>
    </article>
  </div>
</section>

<section class="alert">
  <h2>Read this before using any number on this site</h2>
  <p><strong>The snapshot is {CAPTURED}. Today is {RECAPTURED}.</strong> Week 10's Sunday slate was
  played on 2026-11-15. On re-capture, <strong>22 of 32 clubs</strong> had changed and the injury
  report had grown from <strong>160 rows / 26 clubs to 347 rows / 28 clubs</strong>. Every table on
  this site still renders the older read.</p>
  <p>What changed on 2026-11-16, all of it verified against the official pages and published:</p>
  <ul>
    <li><strong>A verified results feed now exists.</strong> 12 of 14 Week 10 games are settled, each
    row linking its own nfl.com game page. Without it this site could not be scored at all.
    <a href="board/results.html">Results</a></li>
    <li><strong>The first prospective grade has been computed.</strong> Brier skill vs a coin is
    <strong>+0.194</strong> with a 95% interval of <strong>[-0.018, +0.385]</strong>, which includes
    zero. Against the sample's own base rate the model is <strong>worse</strong> by 0.016. Its picks
    won 8 of 11 where its own probabilities expected 6.61, so part of that record is luck.
    <a href="board/luck.html">Removal of luck</a></li>
    <li><strong>The model's opinions are ~4x too narrow.</strong> Predicted margins vary by 3.41
    points across games; realised margins vary by 14.39. A near-constant forecast cannot beat a line
    test however good its average is. <a href="board/luck.html">Detail</a></li>
    <li><strong>Three files publish a different "our line".</strong> They use two opposite sign
    conventions and disagree by 6.72 points on average on the same fixtures. Reconciled and published,
    no file rewritten. <a href="board/line-provenance.html">Line provenance</a></li>
    <li><strong>Club depth charts cannot be read as "column 1 = the starter".</strong> In three
    sampled clubs: 1 shared slot, 5 duplicate rank-1 slots, 6 duplicate rank-2 slots, 2 empty rank-1
    cells, 1 continuation row and 1 image-only chart. 8 rank-1 players were also Out or Doubtful on
    the official report, with their named replacement. <a href="board/depth-evidence.html">Depth evidence</a></li>
  </ul>
  <p>Three claims in the project brief were checked against the live pages and <strong>do not
  hold</strong>: the three Lions statuses are not blank (they read Out), Seattle and Cincinnati are
  not shown injury-free, and Baltimore no longer lists Lamar Jackson at QB (the chart reads Brissett,
  Fagnano, Slovis). Details on <a href="flagged.html">Flagged for Review</a> as F22.</p>
</section>

<section>
  <h2>Added 17 November — the frontier datasets</h2>
  <p class="lede">Five new pages, each backed by a file whose every row names its official source.
  Two of them report results that go against the model, and say so in the same table as the
  encouraging number.</p>
  {table(["Page", "What is on it", "Headline"],
    FRONTIER_ROWS)}
</section>

<section>
  <h2>Where to go next</h2>
  {table(["Page", "What is on it", "Decide first?"],
    [["<a href='decisions.html'>Decisions</a>", "12 questions with what is known, what is not, and what unblocks each one", "Start here"],
     ["<a href='suggestions.html'>Suggestions</a>", f"{n_sug} suggestions, each with 2–3 selectable paths and a recommendation", "Yes — pick a path"],
     ["<a href='lines.html'>Our Lines</a>", f"{n_games} originated lines with uncertainty bands", "No"],
     ["<a href='injuries.html'>Injuries</a>", "Official Week 10 report, with availability broken out by side of the ball", "No"],
     ["<a href='strategies.html'>Strategies</a>", "8 specs, 8 gates, 5 reward tiers, and an empty leaderboard that says why", "No"],
     ["<a href='correlation.html'>Correlation</a>", "4 measured correlations and 6 declared assumptions", "No"],
     ["<a href='board/results.html'>Results feed</a>", "Settled Week 10 scores, one row per fixture, each linked to its game page", "No"],
     ["<a href='board/luck.html'>Removal of luck</a>", "The first prospective grade: proper scores, dispersion, and the luck gap", "Yes — read"],
     ["<a href='board/line-provenance.html'>Line provenance</a>", "Three 'our line' files, reconciled on one axis", "Yes — decide"],
     ["<a href='board/data-freshness.html'>Data freshness</a>", "How stale the snapshot is, measured per club and per player", "Yes — read"],
     ["<a href='board/depth-evidence.html'>Depth evidence</a>", "What club depth charts publish, and the six ways a naive parse fails", "No"],
     ["<a href='board/decision-queue.html'>Decision queue</a>", "Every requirement collapsed into the owner decision that releases it, ordered by rows released", "Yes — start here"],
     ["<a href='flagged.html'>Flagged for Review</a>", f"{len(flag['items'])} items, each with its evidence link", "Yes — review"],
     ["<a href='legacy/index.html'>Archived blueprint</a>", "An earlier session's data-free research plan, preserved unchanged", "Optional"]])}
</section>
"""
    body += readiness_section(readiness, sources)
    return page("Dashboard", body, "index.html")


def build_standings(standings, luck):
    luck_by = {t["abbr"]: t for t in luck["teams"]}
    rows = []
    for t in sorted(standings["teams"], key=lambda x: (-x["w"], -x["net"], x["abbr"])):
        lk = luck_by.get(t["abbr"], {})
        rows.append(
            [
                f"<b>{e(t['abbr'])}</b>",
                e(t["name"]),
                e(t["division"]),
                f"{t['w']}–{t['l']}–{t['t']}",
                f"{t['pct']:.3f}",
                str(t["pf"]),
                str(t["pa"]),
                f"{t['net']:+d}",
                e(t["home"]),
                e(t["road"]),
                e(t["div"]),
                e(t["streak"]),
                f"{lk.get('exp_wins', '—')}",
                (f"{lk['luck_wins']:+.2f}" if "luck_wins" in lk else "—"),
                src_link(t["src"], "nfl.com"),
            ]
        )
    body = f"""
<h1>Standings</h1>
<p class="lede">The official 2026 regular-season table, plus a derived luck column. The first twelve
columns are quoted from NFL.com. The last three are our model and are labelled as such.</p>

<div class="note">
  <strong>Snapshot caveat.</strong> This table does not yet include the Week 10 Thursday result
  (Commanders 24, Giants 21), even though the schedule page marks it FINAL. That is flag F01 on
  <a href="flagged.html">Flagged for Review</a>.
  {src_link("https://www.nfl.com/standings/division/2026/REG", "standings page")}
</div>

<h2>Official table + derived luck</h2>
{table(["", "Club", "Division", "W–L–T", "Pct", "PF", "PA", "Net", "Home", "Road", "Div", "Strk",
        "Exp W", "Luck W", "Source"], rows)}

<h2>What the luck column means</h2>
<p>Expected wins come from Pythagorean expectation: <code>PF<sup>2.37</sup> / (PF<sup>2.37</sup> + PA<sup>2.37</sup>)</code>,
multiplied by games played. Luck is <code>(W + T/2) − expected wins</code>. The half-win tie rule is quoted
from the official tie-breaking page. {src_link("https://www.nfl.com/standings/tie-breaking-procedures", "tie-breaking page")}</p>
<p class="fine">The exponent 2.37 is a declared model constant, not a league figure. This decomposition
cannot see turnovers, defensive touchdowns, or opponent field-goal misses.</p>

<h2>Largest luck gaps</h2>
{table(["Club", "W–L–T", "Exp W", "Luck W", "Rank", "Source"],
  [[e(t["abbr"]), f"{t['w']}–{t['l']}–{t['t']}", f"{t['exp_wins']:.2f}", f"{t['luck_wins']:+.2f}",
    str(t["luck_rank"]), src_link(t["src"], "nfl.com")]
   for t in sorted(luck["teams"], key=lambda x: -abs(x["luck_wins"]))[:10]])}
"""
    return page("Standings", body, "standings.html")


def build_lines(lines, inj):
    rows = []
    for g in lines["games"]:
        ln = g["line"]
        i = g["inputs"]
        rows.append(
            [
                f"<b>{e(g['away'])} @ {e(g['home'])}</b><br><small>{e(g['kickoff'])}</small>",
                f"{ln['home_spread']:+.1f}",
                f"{ln['total_point_estimate']:.1f}",
                f"{ln['home_win_prob']*100:.1f}%",
                f"±{ln['spread_sigma']:.1f}",
                f"{ln['spread_band_90'][0]:+.1f} → {ln['spread_band_90'][1]:+.1f}",
                f"{ln['total_band_90'][0]:.1f} → {ln['total_band_90'][1]:.1f}",
                f"{ln['pick_confidence']:.2f}",
                src_link(g["src"], "nfl.com"),
            ]
        )

    # availability table for the same games
    av_rows = []
    for g in inj["games"]:
        for t in g["teams"]:
            pen_off = sum(1 for p in t["players"] if p["game_status"] == "Out" and p["pos"] in
                          ("QB", "WR", "RB", "TE", "T", "G", "C", "FB"))
            pen_def = sum(1 for p in t["players"] if p["game_status"] == "Out" and p["pos"] in
                          ("DE", "DT", "LB", "CB", "S"))
            if pen_off or pen_def:
                av_rows.append([f"<b>{e(t['abbr'])}</b>", str(pen_off), str(pen_def),
                                src_link(t["src"], "report")])

    body = f"""
<h1>Our Lines</h1>
<p class="lede">These are originated by our own model, not copied from a sportsbook. Every number
carries its uncertainty. This is an input to the scoring gates, not a tip.</p>

<div class="note warn">
  <strong>What this is not.</strong> There is no market comparison on this page, because we hold no
  licensed odds feed (flag F07). A line without a price cannot be called good value.
</div>

<h2>Week 10 originated lines</h2>
{table(["Game", "Home spread", "Total", "Home win %", "Sigma", "Spread 90% band", "Total 90% band",
        "Confidence", "Input source"], rows)}

<h2>How the line is built</h2>
<ol class="steps">
  <li><b>Ratings.</b> Each club gets an offence and defence rating from official PF/PA per game,
  shrunk toward league average by a two-game prior.</li>
  <li><b>Expected scores.</b> Away expected = (away offence + home defence) / 2; home expected =
  (home offence + away defence) / 2. Home-field is +1.9 points.</li>
  <li><b>Availability.</b> Missing offensive players lower that club's expected points; missing
  defensive players raise the opponent's. Specialists move both slightly. Each bucket is capped.</li>
  <li><b>Uncertainty.</b> Sigma grows with <code>sqrt(1 + 8 / games played)</code>. Fewer games,
  wider band, on purpose.</li>
  <li><b>Win probability.</b> Normal CDF of the margin against that sigma. No threshold, no rounding
  to a "key number".</li>
</ol>

<h2>Availability pressure by club</h2>
<p class="fine">Count of players ruled <b>Out</b> on the official report, split by side of the ball.
Practice-only listings are excluded because they carry no game status.</p>
{table(["Club", "Out — offence", "Out — defence", "Source"], av_rows)}

<h2>Model constants</h2>
<p class="fine">These are declared, not fitted to any market. Changing one requires a new model
version and re-running the gates.</p>
{table(["Constant", "Value", "Why"], [
  ["Home-field advantage", "+1.9 pts", "Applied to the home club's expected score"],
  ["Prior strength", "2.0 games", "Pulls a club toward league average early in the season"],
  ["Single-game sigma", "8.5 pts", "Game-to-game scoring noise"],
  ["Sigma growth k", "8.0", "Widens the band when a club has played few games"],
  ["Cap, offence", "3.5 pts", "One long injury list cannot swamp the ratings"],
  ["Cap, defence", "3.0 pts", "Same, on the other side of the ball"],
  ["Status weight, Out", "1.00", "Ruled out"],
  ["Status weight, Doubtful", "0.60", "Usually does not play"],
  ["Status weight, Questionable", "0.25", "More likely to play than not, by convention only"],
])}
<p class="fine">The status weights are <b>our convention</b>, not a league rule. The official policy
page returned an empty body on {CAPTURED} (flag F06), so nothing here is quoted as policy.</p>
"""
    return page("Our Lines", body, "lines.html")


def build_injuries(inj):
    rows = []
    for g in inj["games"]:
        for t in g["teams"]:
            for p in t["players"]:
                st = p["game_status"]
                cls = {"Out": "out", "Doubtful": "doubt", "Questionable": "quest"}.get(st, "blank")
                item = f'<span class="chip {cls}">{e(st) if st else "—"}</span>'
                rows.append([
                    f"<b>{e(t['abbr'])}</b>",
                    e(g["game_id"]),
                    e(p["name"]),
                    e(p["pos"]),
                    e(p["injury"]) if p["injury"] else "",
                    e(p["practice"]).replace(" Participation in Practice", ""),
                    item,
                    src_link(t["src"], "report"),
                ])
    n_out = sum(1 for g in inj["games"] for t in g["teams"] for p in t["players"] if p["game_status"] == "Out")
    n_q = sum(1 for g in inj["games"] for t in g["teams"] for p in t["players"] if p["game_status"] == "Questionable")
    n_d = sum(1 for g in inj["games"] for t in g["teams"] for p in t["players"] if p["game_status"] == "Doubtful")
    n_blank = len(rows) - n_out - n_q - n_d

    body = f"""
<h1>Injuries</h1>
<p class="lede">The official Week 10 injury report for all 28 clubs playing, transcribed exactly as
published. Blank cells are blank in the source. Nothing was inferred.</p>

<section class="stats">
  {stat(len(rows), "player rows", "official")}
  {stat(n_out, "ruled Out", "game status")}
  {stat(n_d, "Doubtful", "game status")}
  {stat(n_q, "Questionable", "game status")}
  {stat(n_blank, "no game status", "practice only")}
</section>

<div class="note warn">
  <strong>Read this before trusting the availability signal.</strong>
  {n_blank} of {len(rows)} rows carry no game status at all, so it is unknown whether those players
  will dress (flag F04). And at least one starting QB absence is missing from the table entirely —
  Baltimore's Lamar Jackson, reported out 6–10 weeks in NFL.com's own news module, appears in no
  Ravens row (flag F02). The table is necessary but not sufficient.
</div>

<h2>Full Week 10 report</h2>
{table(["Club", "Game", "Player", "Pos", "Injury", "Practice", "Game status", "Source"],
       rows, "wide")}

<h2>Why "2nd/3rd/4th string" is not on this page</h2>
<p>You asked to know when a backup is replacing a starter. No official NFL source publishes a
depth-chart ordinal, a starter flag, or a snap count on the injury report (flag F05). Rather than
invent one, this site applies a per-position availability penalty in the line model and labels it as
a model constant. Making the depth question answerable needs participation counts — suggestion SG-05.</p>
<p>{src_link("https://www.nfl.com/injuries/", "official injury report")}
{src_link("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13", "Ravens QB news")}</p>
"""
    return page("Injuries", body, "injuries.html")


def build_strategies(strat):
    gate_rows = [[f"<b>{e(g['id'])}</b>", e(g["name"]), e(g["test"]),
                  badge("auto" if g["auto"] else "manual", "auto" if g["auto"] else "manual"),
                  e(g["fail_action"])] for g in strat["gates"]]
    tier_rows = [[f"<b>{t['tier']}</b>", e(t["name"]), e(t["requirement"]), e(t["reward"])]
                 for t in strat["tiers"]]

    srows = []
    for s in strat["strategies"]:
        g = s["gates"]
        passed = sum(1 for v in g.values() if v.startswith("pass"))
        cls = "ok" if passed >= 5 else ("warn" if passed >= 2 else "bad")
        srows.append([
            f"<b>{e(s['id'])}</b>",
            e(s["name"]),
            e(s["market"]),
            f'<span class="tier t{s["tier"]}">{e(strat["tiers"][s["tier"]]["name"])}</span>',
            f'<span class="badge {cls}">{passed}/{len(g)} gates pass</span>',
            e(s["thesis"]),
            e(s["caveat"]),
        ])

    gate_matrix_rows = []
    for s in strat["strategies"]:
        cells = [f"<b>{e(s['id'])}</b>"]
        for g in strat["gates"]:
            v = s["gates"].get(g["id"], "n/a")
            kind = "ok" if v.startswith("pass") else ("bad" if v.startswith("fail") or v.startswith("blocked") else "warn")
            cells.append(f'<span class="badge {kind}" title="{e(v)}">{e(v[:14])}</span>')
        gate_matrix_rows.append(cells)

    body = f"""
<h1>Strategies</h1>
<p class="lede">Eight strategy specs, eight validation gates, five reward tiers. No strategy has a
graded result yet, and this page says so instead of showing a number that does not exist.</p>

<div class="note">
  <strong>Leaderboard status: live, empty.</strong> {e(strat["leaderboard"]["why_empty"])}
</div>

<h2>The validation gates</h2>
<p class="fine">A strategy must pass these to be ranked. A gate that cannot run is a fail, not a pass.</p>
{table(["Gate", "Name", "What it tests", "Mode", "If it fails"], gate_rows)}

<h2>Reward tiers</h2>
{table(["Tier", "Name", "Requirement", "Reward"], tier_rows)}

<h2>Gate matrix</h2>
<p class="fine">Hover any cell for the full reason. Red here is the system working: it means the
strategy cannot yet justify a decision.</p>
{table(["Strategy"] + [g["id"] for g in strat["gates"]], gate_matrix_rows)}

<h2>The strategies</h2>
{table(["ID", "Name", "Market", "Tier", "Gates", "Thesis", "Known weakness"], srows)}

<h2>How the score works</h2>
<p><code>{e(strat["scoring"]["formula"])}</code></p>
<ul class="fine">
  <li><b>Why sqrt(n):</b> {e(strat["scoring"]["why_sqrt_n"])}</li>
  <li><b>Luck penalty:</b> {e(strat["scoring"]["luck_penalty"])}</li>
  <li><b>Minimum to rank:</b> {e(strat["scoring"]["minimum_to_rank"])}</li>
  <li><b>Abstention:</b> {e(strat["scoring"]["no_bet_is_a_bet"])}</li>
</ul>

<h2>What unlocks the leaderboard</h2>
<ul>
  {''.join(f'<li>{e(x)}</li>' for x in strat["leaderboard"]["what_unlocks_it"])}
</ul>
<p class="fine">{e(strat["leaderboard"]["reward_pool_rule"])}</p>
"""
    return page("Strategies", body, "strategies.html")


def build_correlation(corr):
    mrows = [[f"<b>{e(m['id'])}</b>", e(m["label"]), str(m["n"]),
              f"{m['r']:+.4f}", f"{m['r_squared']:.4f}", f"{m['t_stat']:+.2f}",
              e(m["interpretation"]), src_link(m["src"], "nfl.com")]
             for m in corr["measured"]]
    arows = [[f"<b>{e(a['id'])}</b>", e(a["label"]),
              (f"{a['r']:+.2f}" if a["r"] is not None else '<span class="unverified">unmeasured</span>'),
              badge(a["sign"], "warn" if a["r"] is None else "ok"),
              e(a["mechanism"]), e(a["sizing_implication"])]
             for a in corr["assumed"]]
    prules = [[f"<b>{e(r['id'])}</b>", e(r["rule"]), e(r["why"])] for r in corr["parlay_rules"]]

    body = f"""
<h1>Correlation</h1>
<p class="lede">Correlation decides whether a parlay is genuinely two bets or the same bet twice.
The measured rows below are computed from the verified standings by
<code>scripts/compute_correlation.py</code>; the assumed rows say plainly that the size is unknown.</p>

<h2>Measured from verified data</h2>
{table(["ID", "Pair", "n", "r", "r²", "t", "What it means", "Source"], mrows)}

<div class="note">
  <strong>The single most useful number here is r = −0.204.</strong> Across 32 clubs, how much a team
  scores and how much it allows are close to independent. That kills the intuition that "good offence
  plus bad defence" is a natural hedge.
</div>

<h2>Declared assumptions (magnitude unverified)</h2>
<p class="fine">Direction comes from mechanism and is not in doubt. Size is not measured, because
player-level official statistics were not captured.</p>
{table(["ID", "Pair", "r", "Sign", "Mechanism", "How it must be sized"], arows)}

<h2>Parlay rules</h2>
{table(["Rule", "What", "Why"], prules)}

<h2>What cannot be measured right now</h2>
<ul>{''.join(f"<li><b>{e(u['what'])}</b> — {e(u['why'])}</li>" for u in corr["unmeasurable_now"])}</ul>
"""
    return page("Correlation", body, "correlation.html")


def build_decisions(dec):
    qrows = []
    for q in dec["questions"]:
        blocking = badge("blocking", "bad") if q["blocking"] else badge("non-blocking", "ok")
        qrows.append([
            f"<b>{e(q['id'])}</b>",
            e(q["family"]),
            e(q["question"]),
            e(q["known"]),
            f'<span class="unknown">{e(q["unknown"])}</span>',
            blocking,
            e(q["discovery"]),
        ])
    frows = [[e(f["fact"]), f"<b>{e(str(f['value']))}</b>", src_link(f["src"], "verify")]
             for f in dec["known_facts"]]
    mrows = [[f"<b>{e(m['id'])}</b>", e(m["what"]), e(m["why_blocking"]), e(m["unlocked_by"])]
             for m in dec["missing_information"]]
    n_block = sum(1 for q in dec["questions"] if q["blocking"])

    body = f"""
<h1>Decisions</h1>
<p class="lede">Everything that has to be answered before a decision can be called reasonable.
{n_block} of {len(dec["questions"])} questions are blocking: while they are open, no strategy in
their family can be judged good or bad.</p>

<h2>Questions, knowledge and gaps</h2>
{table(["ID", "Family", "Question", "What we know (verified)", "What we do not know", "Blocks?", "What discovers it"], qrows)}

<h2>Confirmed facts</h2>
<p class="fine">Each of these was read off an official page and is reproduced identically in the data files.</p>
{table(["Fact", "Value", "Source"], frows)}

<h2>Missing information</h2>
<p class="fine">These are not "nice to have". Each one currently makes a whole family of decisions unfounded.</p>
{table(["ID", "What is missing", "Why it blocks", "Unlocked by"], mrows)}
"""
    return page("Decisions", body, "decisions.html")


def build_suggestions(sug):
    cards = []
    for s in sug["suggestions"]:
        status_badge = {
            "implemented": "ok", "in progress": "auto", "proposed": "warn", "blocked": "bad",
        }.get(s["status"], "warn")
        paths = []
        for p in s["paths"]:
            rec = badge("recommended", "ok") if p.get("recommended") else ""
            paths.append(f"""
              <div class="path{' rec' if p.get('recommended') else ''}">
                <div class="pathhead"><b>Path {e(p['id'])}</b> · {e(p['name'])} {rec}</div>
                <div class="pathmeta">effort: {e(p['effort'])} · cost: {e(p['cost'])}</div>
                <div class="pros"><span class="plus">+</span> {e(p['pros'])}</div>
                <div class="cons"><span class="minus">−</span> {e(p['cons'])}</div>
              </div>""")
        blocked = f'<p class="fine">Blocked by: {e(s["blocked_by"])}</p>' if s.get("blocked_by") else ""
        impl = f'<p class="fine">{e(s["implemented_note"])}</p>' if s.get("implemented_note") else ""
        cards.append(f"""
        <article class="sug">
          <header>
            <h3><span class="sid">{e(s['id'])}</span> {e(s['title'])}</h3>
            {badge(s['status'], status_badge)}
          </header>
          <p><b>Problem.</b> {e(s['problem'])}</p>
          <p class="fine">Unblocks: {e(', '.join(s['unblocks']))}</p>
          {blocked}{impl}
          <div class="paths">{''.join(paths)}</div>
          <p class="decide"><b>Decision needed:</b> {e(s['decision_needed_from_owner'])}</p>
        </article>""")

    prio = [[str(p["rank"]), f"<a href='#{e(p['id'])}'>{e(p['id'])}</a>", e(p["why"])]
            for p in sug["priority_order"]]

    body = f"""
<h1>Suggestions</h1>
<p class="lede">Each suggestion names a problem, offers 2–3 mutually exclusive paths, and states what
decision it needs from you. Pick one path per suggestion. Nothing is implemented until you choose,
except where the status says <span class="badge ok">implemented</span>.</p>

<h2>If you only read one thing: priority order</h2>
{table(["#", "Suggestion", "Why it is in this position"], prio)}

<h2>All suggestions</h2>
{''.join(cards)}

<h2>How to respond</h2>
<p>Reply with the suggestion IDs and the path letters you want, for example
<code>SG-13:A, SG-02:A, SG-06:B</code>. Anything you skip stays <span class="badge warn">proposed</span>
and keeps blocking the decisions listed above it.</p>
"""
    return page("Suggestions", body, "suggestions.html")


def build_flagged(flag):
    items = []
    for f in flag["items"]:
        sev = {"high": "bad", "medium": "warn", "low": "auto"}.get(f["severity"], "auto")
        st = {"open": "warn", "resolved": "ok", "accepted-risk": "auto"}.get(f["status"], "warn")
        ev = "".join(f'<li>{src_link(x["url"], x["label"])}</li>' for x in f.get("evidence", []))
        ev_html = f'<ul class="evid">{ev}</ul>' if ev else '<p class="fine">No public link — see the note.</p>'
        items.append(f"""
        <article class="flag" id="{e(f['id'])}">
          <header>
            <h3><span class="sid">{e(f['id'])}</span> {e(f['title'])}</h3>
            <div>{badge(f['severity'] + ' severity', sev)} {badge(f['status'], st)}</div>
          </header>
          <dl>
            <dt>Observed</dt><dd>{e(f['observed'])}</dd>
            <dt>Why it matters</dt><dd>{e(f['why_it_matters'])}</dd>
            <dt>Could not confirm</dt><dd>{e(f['cannot_confirm'])}</dd>
            <dt>Effect on the lines</dt><dd>{e(f['impact_on_lines'])}</dd>
            <dt>Action needed</dt><dd>{e(f['action_needed'])}</dd>
          </dl>
          {ev_html}
        </article>""")
    open_n = sum(1 for f in flag["items"] if f["status"] == "open")
    body = f"""
<h1>Flagged for Review</h1>
<p class="lede">Every irregularity, open question and unverified item, with the link to check it.
{open_n} open. Nothing on this page blocks the site: it is the list you asked to review after
publication.</p>

<div class="note">
  <strong>How these were found.</strong> Each item came from a direct contradiction between two
  official pages, an empty official page, or a request (2nd/3rd/4th string, market edge) that no
  official source can answer. None of them were filled in by inference.
</div>
{''.join(items)}
"""
    return page("Flagged for Review", body, "flagged.html")


def build_sources(src):
    rows = []
    for s in src["sources"]:
        rows.append([
            f"<b>{e(s['id'])}</b>",
            e(s["title"]),
            e(s["publisher"]),
            e(s["used_for"]),
            badge("verified", "ok") if s["verified"] else badge("unverified", "bad"),
            src_link(s["url"], "open"),
        ])
    rej = [[e(r["what"]), e(r["why"]), e(r["consequence"])] for r in src["rejected_sources"]]
    body = f"""
<h1>Sources</h1>
<p class="lede">The complete list of sources used, including the ones we looked at and refused.
A row can only carry a value if a source on this page states it.</p>

<div class="note"><strong>Source policy.</strong> {e(src["meta"]["policy"])}</div>

{table(["ID", "Title", "Publisher", "Used for", "Status", "Link"], rows)}

<h2>Deliberately rejected</h2>
{table(["What", "Why it was rejected", "Consequence"], rej)}

<h2>What "unverified" costs us</h2>
<p>Two entries above are marked unverified. The injury-policy page returned an empty body, so no policy
language is quoted anywhere on this site. That is why the practice-status weights are described as our
convention rather than the league's rule.</p>
"""
    return page("Sources", body, "sources.html")


def build_methodology(standings, luck, corr, lines):
    body = f"""
<h1>Methodology</h1>
<p class="lede">Exactly how every number on this site was produced, so a reviewer can re-run it.</p>

<h2>1. Capture</h2>
<p>Four official pages were read on {CAPTURED} and transcribed into <code>data/</code>. Nothing was
paraphrased into a different unit, and nothing was normalised to a "nice" number.</p>
<ul>
  <li>{src_link("https://www.nfl.com/standings/division/2026/REG", "Division standings")} — all 32 clubs</li>
  <li>{src_link("https://www.nfl.com/standings/league/2026/REG", "League standings")} — cross-check of the same clubs</li>
  <li>{src_link("https://www.nfl.com/injuries/", "Week 10 injury report")} — 345 rows, 28 clubs</li>
  <li>{src_link("https://www.nfl.com/schedules/2026/REG/", "Week 10 schedule")} — 14 games</li>
  <li>{src_link("https://www.nfl.com/standings/tie-breaking-procedures", "Tie-breaking procedures")} — the half-win tie rule</li>
</ul>

<h2>2. Verify</h2>
<p>Checks run on every build by <code>scripts/check_site.py</code>:</p>
<ul>
  <li><b>Arithmetic.</b> PF − PA = Net for all 32 clubs.</li>
  <li><b>Completeness.</b> 32 clubs, 8 divisions × 4, 14 games, 28 clubs on the slate.</li>
  <li><b>Cross-page.</b> Club records on the injury page match the standings snapshot.</li>
  <li><b>Sources.</b> Every dataset row carries an absolute https URL.</li>
  <li><b>Links.</b> Every internal href resolves to a built file; every external href is non-empty and https.</li>
  <li><b>Recompute.</b> The line engine, luck model and correlation engine are re-run and must
      reproduce the committed numbers.</li>
</ul>

<h2>3. Model</h2>
<p>Ratings, expected scores and uncertainty are described on <a href="lines.html">Our Lines</a>.
Every constant is declared there. No parameter was chosen by looking at a result.</p>

<h2>4. What is deliberately missing</h2>
<p>No market price. No player-level statistics. No depth-chart ordinal. No weather. No rest days.
Each of those gaps is a row on <a href="decisions.html">Decisions</a> and a suggestion on
<a href="suggestions.html">Suggestions</a>. We did not fill them in.</p>

<h2>5. Reproduce it</h2>
<pre><code>python3 scripts/compute_lines.py
python3 scripts/compute_luck.py
python3 scripts/compute_correlation.py
python3 scripts/build_site.py
python3 scripts/check_site.py</code></pre>
<p class="fine">Any number that changes when you run those commands is a bug, not an opinion.</p>

<h2>6. Known limits of the evidence</h2>
<table>
  <thead><tr><th>Limit</th><th>Consequence</th></tr></thead>
  <tbody>
    <tr><td>Eight or nine games per club</td><td>Every rating is provisional; the bands widen on purpose.</td></tr>
    <tr><td>League aggregates only</td><td>No opponent adjustment. A club that has played strong teams looks worse than it is.</td></tr>
    <tr><td>One captured week</td><td>No calibration, no backtest, no leaderboard.</td></tr>
    <tr><td>No price</td><td>No edge, no closing-line value, no top-tier strategies.</td></tr>
  </tbody>
</table>
"""
    return page("Methodology", body, "methodology.html")


def build_audit(audit):
    """Acceptance audit: published registers vs live official sources (2026-11-17)."""
    meta = audit["meta"]
    rows = []
    verdict_cls = {"CONFIRMED": "ok", "STALE": "warn", "MISMATCH": "bad", "UNVERIFIED": "bad"}
    for r in audit["checks"]:
        rows.append([
            f"<b>{e(r['check_id'])}</b>",
            e(r["category"]),
            e(r["item"]),
            e(r["repo_value"]),
            e(r["live_value"]),
            badge(r["verdict"], verdict_cls.get(r["verdict"], "warn")),
            src_link(r["source_url"], "source"),
            e(r["note"]),
        ])
    counts = {}
    for r in audit["checks"]:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    stat_html = " ".join(
        stat(counts.get(v, 0), v) for v in ("CONFIRMED", "STALE", "MISMATCH", "UNVERIFIED"))
    body = f"""
<h1>Acceptance audit</h1>
<p class="lede">Every value published in this repository was compared, line by line, against the
official page read on {e(meta['audit_utc'])}. <b>CONFIRMED</b> means the repo value matches the live
official value. <b>STALE</b> means the repo value was correct at its capture time and the live source
has since moved on — the snapshot is preserved, not rewritten. <b>MISMATCH</b> means the repo value
disagrees with the live official value; it is published here for review.</p>

<div class="note"><strong>Evidence rule.</strong> {e(meta['source_policy'])} Every row carries the
URL that was read. Values that could not be confirmed from an official source are blank and flagged,
never inferred.</div>

<div class="stats">{stat_html}</div>

{table(["Check", "Category", "Item", "Published in repo", "Live official value", "Verdict", "Source", "Note"], rows)}

<h2>How to read the STALE rows</h2>
<p>The standings rows are the 2026-11-14 point-in-time snapshot: every divergence equals the club's
Week 10 result, so the snapshot is a correct pre-kickoff capture, not an error. The two result rows
(PIT@CIN, LAC@BAL) were captured before their games concluded; the live schedule page now shows
PIT@CIN FINAL 18&ndash;38 and LAC@BAL in progress (Q2, 17&ndash;7) at audit time. A refresh of the
results feed is requested in COORDINATION.md; the captured file is left untouched.</p>
"""
    return page("Acceptance audit", body, "audit.html")



# ---------------------------------------------------------------------------
# compare.html — the origination comparison lab
# ---------------------------------------------------------------------------
CMP = os.path.join(DATA, "compare")


def _cmp_json(name):
    with open(os.path.join(CMP, name), encoding="utf-8") as fh:
        return json.load(fh)


def _cmp_csv(name):
    with open(os.path.join(CMP, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(v, dp=2, dash="—"):
    if v is None or v == "":
        return dash
    try:
        return f"{float(v):.{dp}f}"
    except (TypeError, ValueError):
        return str(v)


def _ci(pair, dp=2):
    if not pair or pair[0] is None:
        return "—"
    return f"{pair[0]:.{dp}f} … {pair[1]:.{dp}f}"


def _pctf(v, dp=1):
    if v is None or v == "":
        return "—"
    return f"{float(v) * 100:.{dp}f}%"


def build_compare():
    ev = _cmp_json("evaluation.json")
    meta = ev["meta"]
    rows = _cmp_csv("evaluation.csv")
    qs = _cmp_csv("questions.csv")
    sug = _cmp_csv("suggestions.csv")
    slate = _cmp_csv("slate_week11_forecasts.csv")

    # ---- headline verdict banner ----
    any_skill = any(v.get("called_skillful") for v in ev["verdicts"])
    best = min((r for r in rows if r["kind"] == "strategy"), key=lambda r: float(r["margin_mae"]))
    best_v = next(v for v in ev["verdicts"] if v["strategy"] == best["strategy"])
    banner = (
        '<div class="note"><strong>The headline, before any number:</strong> four origination '
        f'strategies were run walk-forward over {meta["games"]} verified games. '
        f'{best["strategy"]} ({e(best["label"])}) is ahead on spread error at '
        f'{_f(best["margin_mae"])} points MAE against {_f(next(r["margin_mae"] for r in rows if r["strategy"]=="C3"))} '
        'for a pick\'em control. '
        + ('<b>No strategy survives the multiple-comparison threshold, so nothing here is '
           'established skill.</b>' if not any_skill else
           '<b>At least one strategy survives the threshold.</b>')
        + f' The best z is {_f(best_v.get("margin_gain_z"), 2)} against a Bonferroni critical '
        f'value of {_f(meta["z_crit_bonferroni"], 2)} for {meta["comparisons"]} comparisons.</div>'
    )

    # ---- strategy table ----
    strat_rows = []
    for r in rows:
        kind = r["kind"]
        v = next((x for x in ev["verdicts"] if x["strategy"] == r["strategy"]), {})
        z = v.get("margin_gain_z")
        survives = v.get("margin_survives_bonferroni")
        badge_html = (badge("survives", "ok") if survives else badge("not established", "warn"))
        if kind == "control":
            badge_html = badge("control", "auto")
        strat_rows.append([
            f'<b>{e(r["strategy"])}</b>',
            e(r["label"]),
            _f(r["n_margin"], 0),
            _f(r["margin_mae"]),
            _ci(None) if not r["margin_mae_ci"] else e(r["margin_mae_ci"].replace(" .. ", " … ")),
            _f(r["margin_rmse"]),
            _f(r["margin_bias"], 2),
            _f(r["margin_dispersion"]),
            _pctf(float(r["dir_acc"]) if r["dir_acc"] else None, 1),
            _f(r["total_mae"]),
            _f(r["brier"], 4),
            _pctf(float(r["brier_skill_vs_coin"]) if r["brier_skill_vs_coin"] else None),
            _f(z, 2),
            badge_html,
        ])

    # ---- calibration ----
    cal_rows = []
    for sid, bands in ev["calibration"].items():
        for b in bands:
            cal_rows.append([
                f"<b>{e(sid)}</b>",
                f"{b['lo']:.0%} – {b['hi']:.0%}",
                _f(b["n"], 0),
                _f(b["pred"], 3),
                _f(b["actual"], 3),
                "—" if b["n"] == 0 else _f((b["actual"] or 0) - (b["pred"] or 0), 3),
            ])

    # ---- luck ----
    luck_rows = []
    for sid, l in ev["luck"].items():
        if not l:
            continue
        luck_rows.append([
            f"<b>{e(sid)}</b>", _f(l["n"], 0), _f(l["expected_wins"], 1), _f(l["won"], 0),
            f'<b>{_f(l["luck"], 1)}</b>', _pctf(l["expected_rate"]), _pctf(l["win_rate"]),
        ])

    # ---- regimes ----
    reg_rows = []
    for sid, bands in ev["regimes"].items():
        for b in bands:
            reg_rows.append([f"<b>{e(sid)}</b>", e(b["weeks"]), _f(b["n"], 0),
                             _f(b["margin_mae"]), _f(b["brier"], 4)])

    # ---- totals ----
    tot_rows = []
    for t in ev["total_estimator_comparison"]:
        tot_rows.append([
            e(t["window"]), _f(t["n"], 0),
            _f(t["mae_a_pace"]), _f(t["mae_b_offence_only"]), _f(t["mae_c_pace_plus_hfa"]),
            _f((t["b_minus_a"] or {}).get("est"), 3), _f((t["b_minus_a"] or {}).get("z"), 2),
            _f((t["c_minus_a"] or {}).get("est"), 3), _f((t["c_minus_a"] or {}).get("z"), 2),
            badge("not established", "warn"),
        ])

    # ---- correlations ----
    cor_rows = []
    for c in ev["correlations"]:
        cor_rows.append([e(c["name"]), _f(c["r"], 3), _ci(c.get("ci"), 3), _f(c["n"], 0),
                         e(c["note"])])

    # ---- week 11 slate ----
    slate_rows = []
    for r in slate:
        def mk(prefix):
            return [_f(r.get(f"{prefix}_margin")), _f(r.get(f"{prefix}_total")),
                    _pctf(r.get(f"{prefix}_p_home"))]
        slate_rows.append([
            f'<a class="src" href="{e(r["source_url"])}" target="_blank" rel="noopener">{e(r["game_date"])}</a>',
            e(r["kickoff_et"]), f'<b>{e(r["away"])}</b> @ <b>{e(r["home"])}</b>',
            *mk("S2"), *mk("S1"), *mk("S3"), *mk("S4"),
            '<span class="unverified">blank</span>' if not r.get("market_spread") else e(r["market_spread"]),
            '<span class="unverified">blank</span>' if not r.get("market_total") else e(r["market_total"]),
        ])

    # ---- corpus reconciliation ----
    x = _cmp_json("corpus_reconciliation.json")
    recon_rows = []
    for step in x["chain"]:
        ident = step.get("standings_identity") or "—"
        recon_rows.append([
            e(step["step"]), f'<b>{step["games"]}</b>', f'<b>{step["points"]:,}</b>',
            e(step["matches"]),
            badge("holds", "ok") if ident == "holds" else (badge("FAILS", "bad") if ident == "FAILS" else "—"),
        ])
    ident_rows = []
    for c in _cmp_csv("corpus_identity_32clubs.csv"):
        ok = c["identity_holds"] == "yes"
        ident_rows.append([
            f'<a class="src" href="{e(c["source_url"])}" target="_blank" rel="noopener">{e(c["club"])}</a>',
            c["corpus_games"], c["corpus_w"], c["corpus_l"], c["corpus_t"],
            f'{int(c["corpus_pf"]):,}', f'{int(c["corpus_pa"]):,}',
            f'{c["official_w"]}-{c["official_l"]}-{c["official_t"]} / {int(c["official_pf"]):,}-{int(c["official_pa"]):,}',
            badge("matches", "ok") if ok else badge("MISMATCH", "bad"),
        ])

    # ---- questions ----
    q_rows = [[f"<b>{e(q['id'])}</b>", e(q["theme"]), e(q["question"]), e(q["what_we_know"]),
               e(q["what_we_do_not_know"]), e(q["blocks"]), e(q["would_clear_it"]),
               src_link(q["source_id"], "source") if q["source_id"] else
               '<span class="unverified">no official NFL source exists for this question</span>']
              for q in qs]

    # ---- suggestions ----
    s_cards = []
    for s_ in sug:
        s_cards.append(f"""
<div class="card" style="margin:14px 0">
  <div><b>{e(s_['id'])}</b> — <b>{e(s_['title'])}</b></div>
  <p style="margin:8px 0 4px"><b>Problem.</b> {e(s_['problem'])}</p>
  <p style="margin:4px 0"><b>Paths.</b> {e(s_['paths'])}</p>
  <p style="margin:4px 0"><b>Recommended.</b> {e(s_['recommendation'])}</p>
  <p style="margin:4px 0;color:var(--muted)"><b>Cost.</b> {e(s_['cost'])} &nbsp;·&nbsp;
     <b>Risk.</b> {e(s_['risk'])}</p>
  <p style="margin:4px 0;color:var(--muted)"><b>Unblocks.</b> {e(s_['unblocks'])} &nbsp;·&nbsp;
     <b>Evidence in repo.</b> {e(s_['repo_evidence'])}</p>
</div>""")

    body = f"""
<section class="hero">
  <h1>Compare the origination strategies</h1>
  <p class="lede">Four ways to originate a line, one harness, one clock, {meta["games"]} verified games.
  Every forecast for week <em>w</em> was built only from weeks before <em>w</em>, so nothing is
  measured with hindsight. Controls sit in the same table because a strategy that cannot beat a
  coin flip or a pick'em is not a strategy.</p>
</section>

{banner}

<section class="stats">
  {stat(meta["games"], "verified games in the corpus", "weeks 1–10, reconciled to the standings")}
  {stat(meta["strategies"], "origination strategies", f'{meta["controls"]} controls beside them')}
  {stat(meta["comparisons"], "comparisons made", f'α adjusted to {meta["bonferroni_alpha"]:.4f}')}
  {stat("0", "price-based columns", "no licensed price exists — see QO-01")}
</section>

<div class="note"><strong>What is retrospective and what is prospective.</strong> Everything in the
first five tables is <b>retrospective</b>: it is scored on games that have already been played, and
it is not, and must never be, shown on the prospective leaderboard (readiness R010). The Week 11
table is <b>prospective</b>: those forecasts were written before any Week 11 kickoff and are frozen
by commit. The two are never mixed in one column.</div>

<h2>1. The comparison</h2>
<p class="lede">Sorted by spread MAE. <code>Dispersion</code> is the standard deviation of the
model's predicted margin divided by the standard deviation of the actual margins — below 1.0 means
the model's opinions are narrower than reality, which is what decides whether a line can ever beat a
price. <code>z</code> is the paired gain against the pick'em control divided by its own bootstrap
standard error; the verdict column compares it with the Bonferroni critical value of
{_f(meta["z_crit_bonferroni"], 2)}.</p>
{table(["ID", "Strategy", "n", "Spread MAE", "MAE 95% (game-cluster)", "RMSE", "Bias", "Dispersion",
        "Direction %", "Total MAE", "Brier", "Brier skill vs coin", "z vs pick'em", "Verdict"],
       strat_rows, "wide")}
<p class="fine">Intervals: {e(meta["bootstrap"])}. A resample draws whole games, so both clubs in a
game move together. {e(meta["price_policy"])}.</p>

<h2>2. Is the probability honest? (calibration)</h2>
<p class="lede">A strategy can have a good Brier score and still be lying about its confidence. Here
every predicted probability band is compared with what actually happened in it. A well-calibrated
column has <code>Predicted</code> ≈ <code>Actual</code>.</p>
{table(["Strategy", "Probability band", "n", "Predicted", "Actual", "Gap"], cal_rows, "wide")}

<h2>3. Removal of luck</h2>
<p class="lede">For each strategy, take the side it favours and add up its own probability: that is
how many games a perfectly calibrated version of <em>this same model</em> would win on these games.
Compare with what it actually won. The difference is luck. It is published and it is never ranked
on.</p>
{table(["Strategy", "n", "Expected wins (own probabilities)", "Won", "Luck", "Expected rate",
        "Actual rate"], luck_rows)}
<p class="fine">S1, S2 and S4 win on the outright side (the higher of the two win probabilities).
S3's <code>n</code> is smaller because the least-squares rating needs a connected game graph and is
blank in week 2.</p>

<h2>4. Does it hold in both halves of the window?</h2>
<p class="lede">A strategy whose edge exists only when clubs are unfamiliar has not been shown to
generalise. Weeks 2–6 are the regime where every club has seen fewer than six games; weeks 7–10 are
the regime where it has seen more.</p>
{table(["Strategy", "Weeks", "n", "Spread MAE", "Brier"], reg_rows)}

<h2>5. Two total estimators, published side by side (R051)</h2>
<p class="lede">The brief says to publish both totals until one wins. There are three here because
the repo already contained three: <b>A</b> = pace (the mean of both clubs' game totals), <b>B</b> =
offence only (league total plus each club's own scoring deviation), <b>C</b> = pace plus the whole
home-field term. The gap columns are B−A and C−A, positive meaning worse.</p>
{table(["Window", "n", "MAE A (pace)", "MAE B (offence)", "MAE C (pace+HFA)", "B−A", "z",
        "C−A", "z", "Verdict"], tot_rows, "wide")}
<p class="fine">Every paired difference is inside |z| &lt; 1.0. Nothing establishes a winner, so all
three stay published — which is the rule, not a failure to decide.</p>

<h2>6. Correlations — the only ones we can measure without a price</h2>
<p class="lede">Each value carries its own <code>n</code> and a game-cluster interval. These are
<em>measured on the league's own published results</em>, not assumed, and they are the numbers a
parlay would have to be built on — which is why no parlay is published.</p>
{table(["Pair", "r", "95% interval", "n", "What it means"], cor_rows, "wide")}

<h2>7. Week 11 — the prospective slate</h2>
<p class="lede">Thirteen published fixtures, forecast before any kickoff. Side first, then total
(R003). The market columns are <b>blank</b>: no licensed price exists, and a blank is honest where a
guess is not. The Week 11 injury report was not published when this was written — the official week-11
report route still serves the final Week 10 tables and the game centres say the report is not
available — so nothing here uses Week 11 availability.</p>
{table(["Date", "Kickoff ET", "Fixture",
        "S2 side", "S2 total", "S2 P(home)", "S1 side", "S1 total", "S1 P(home)",
        "S3 side", "S3 total", "S3 P(home)", "S4 side", "S4 total", "S4 P(home)",
        "Market spread", "Market total"], slate_rows, "wide")}
<p class="fine">Date links to the official NFL.com fixture page. Sign convention: the side column is
the home club's expected margin, positive meaning the home club is favoured. Every number is model
output, not a league fact and not a bet.</p>

<h2>8. The corpus, and the "136-game log"</h2>
<p class="lede">Every game count this repository has published reconciles exactly. The chain is not
prose — <code>scripts/build_crosscheck.py</code> recomputes it and verifies both official standings
snapshots club by club with <code>--check</code>.</p>
{table(["Step", "Games", "Points", "What it matches", "Standings identity"], recon_rows, "wide")}
<p class="fine">Sources: the per-week official schedule pages
(<a href="https://www.nfl.com/schedules/2026/by-week/week-10" target="_blank" rel="noopener">week 10</a>)
and the <a href="https://www.nfl.com/standings/league/2026/reg" target="_blank" rel="noopener">league
standings</a>. The two independent Week 10 captures — one made at 01:30Z and one at 01:35Z on
2026-11-16 by different sessions — record {x["week10"]["agree_A_vs_B"]} of
{x["week10"]["fixtures_final_in_lab_corpus"]} final scores and agree on <b>every</b> score. The earlier
capture lists the other two fixtures as still at kickoff; the later corpus simply has them as finals.
Neither corrects the other.</p>

<h3>The 32-club identity, figure for figure</h3>
<p class="lede">This is the check that makes the corpus trustworthy: the games are transcribed from one
official page and the totals are compared with a second, independent official page. A single
transposed score breaks it.</p>
{table(["Club", "Games", "W", "L", "T", "PF", "PA", "Official W-L-T / PF-PA", "Identity"],
       ident_rows, "wide")}

<h2>9. What has to be answered before any of this becomes a decision</h2>
<p class="lede">{len(qs)} questions. Each says what is known, what is not, what it blocks, and the
number or artefact that would clear it. Where no official NFL source can answer the question, the
row says so instead of citing an irrelevant one.</p>
{table(["ID", "Theme", "Question", "What we know", "What we do not know", "Blocks",
        "What would clear it", "Source"], q_rows, "wide")}

<h2>10. Suggestions — paths to choose, not changes already made</h2>
<p class="lede">This section exists so a suggestion can be reviewed and a path chosen <em>before</em>
anything is implemented. Each entry carries its alternatives, a recommendation, its cost, its risk,
and the evidence in the repo that supports it. Nothing here has been applied.</p>
{''.join(s_cards)}

<h2>11. Reproduce and re-score it</h2>
<pre><code>python3 scripts/build_compare.py            # rebuild the lab
python3 scripts/build_compare.py --check    # fail if the committed output is stale
python3 scripts/build_crosscheck.py         # reconcile every game count in the repo
python3 scripts/build_crosscheck.py --check # fail if that reconciliation is stale</code></pre>
<p class="fine">Inputs are <code>data/week_results_2026.csv</code> (148 verified rows, SHA-256
<code>{e(ev["forecast_sha256_of_inputs"][:16])}…</code>) and
<code>data/week11_slate_2026.csv</code>. The per-game forecast ledger is published as
<a href="data/compare/forecast_ledger.csv">data/compare/forecast_ledger.csv</a> so anyone can
re-score every number on this page without trusting this page. Deterministic: the bootstrap uses a
fixed seed, so a re-run must reproduce every interval exactly.</p>
"""
    return page("Compare strategies", body, "compare.html")


# ---------------------------------------------------------------------------
# executive-summary.html
# ---------------------------------------------------------------------------
def build_executive_summary():
    ev = _cmp_json("evaluation.json")
    meta = ev["meta"]
    rows = _cmp_csv("evaluation.csv")
    qs = _cmp_csv("questions.csv")
    sug = _cmp_csv("suggestions.csv")
    strat = [r for r in rows if r["kind"] == "strategy"]
    ctrl_mae = next(r["margin_mae"] for r in rows if r["strategy"] == "C3")
    ctrl_tot = next(r["total_mae"] for r in rows if r["strategy"] == "C4")
    best = min(strat, key=lambda r: float(r["margin_mae"]))
    best_tot = min(strat, key=lambda r: float(r["total_mae"]))
    n_skill = sum(1 for v in ev["verdicts"] if v.get("called_skillful"))

    body = f"""
<section class="hero">
  <h1>Executive summary</h1>
  <p class="lede">One page: what this project can now say, what it cannot, and the smallest set of
  decisions that would change that. Written 2026-11-17 against the 2026 regular season through
  Week 10, plus the published Week 11 schedule.</p>
</section>

<div class="note"><strong>The one-paragraph version.</strong> The repository can now originate a
line four different ways on the same clock and score all four against the same controls, on
{meta["games"]} verified games that reconcile to the league's own standings for all 32 clubs. Every
strategy beats a coin flip on the win-probability score and three of four beat a pick'em on spread
error, but <b>not one of them survives the multiple-comparison threshold ({n_skill} of
{len(ev["verdicts"])} cleared)</b>, the totals are worse than a control that ignores the teams
entirely, and the model's opinions are still only a quarter to a half as wide as reality. So the
honest position is: the machinery works, the signal is unproven, and no price exists to turn a
probability into money. Everything below is the detail behind that paragraph.</p>
</div>

<h2>1. What is established</h2>
<ul>
  <li><b>A verified results corpus.</b> {meta["games"]} games through Week 10, identity-checked
  against the official standings: wins, losses, ties, points for and points against match for all 32
  clubs, and the league total balances at 6,824 points each way. Source:
  <a href="https://www.nfl.com/standings/league/2026/reg" target="_blank" rel="noopener">nfl.com
  league standings</a> and the per-week schedule pages.</li>
  <li><b>A leakage-free harness.</b> Every forecast for week <em>w</em> is built only from weeks
  before <em>w</em>. The code enforces it structurally, not by discipline: the week's results are
  added to the model's state only after that week's forecasts are produced.</li>
  <li><b>Four genuinely different origination strategies</b> plus four controls, scored on proper
  scores and on pricing error, with game-cluster intervals and a published multiplicity adjustment
  over {meta["comparisons"]} comparisons (α = {meta["bonferroni_alpha"]:.4f}).</li>
  <li><b>The best spread error in this repo so far</b> is {_f(best["margin_mae"])} points MAE
  ({best["strategy"]}) against {_f(ctrl_mae)} for a pick'em control — a gain of
  {_f(float(ctrl_mae) - float(best["margin_mae"]))} points, with an interval that overlaps zero.</li>
  <li><b>Measured correlations with n</b>, published as numbers rather than assumptions, because
  that is the only way a parlay gate can be honest.</li>
  <li><b>A prospective Week 11 slate</b> frozen before kickoff, with the market columns blank.</li>
</ul>

<h2>2. What is not established — and will not be claimed</h2>
<ul>
  <li><b>Skill.</b> The best strategy's paired gain against pick'em is z =
  {_f(next(v["margin_gain_z"] for v in ev["verdicts"] if v["strategy"] == best["strategy"]), 2)};
  the threshold for {meta["comparisons"]} comparisons is {_f(meta["z_crit_bonferroni"], 2)}.
  Nothing is ranked as skilful anywhere on this site.</li>
  <li><b>Totals.</b> The best strategy's total error is {_f(best_tot["total_mae"])} against
  {_f(ctrl_tot)} for a trailing-league-mean control, and the model's predicted total correlates with
  the actual total at r = {_f(next(c["r"] for c in ev["correlations"] if c["name"].startswith("predicted total")), 2)}.
  The model cannot price a total.</li>
  <li><b>Any money metric.</b> There is no licensed price in the repo, so ROI, CLV and edge are not
  computed, not estimated and not implied. The staking column of every leaderboard is deliberately
  empty.</li>
  <li><b>Depth and availability.</b> No official source publishes a depth ordinal, so "second
  string" cannot be established. The repo says so rather than inferring it.</li>
  <li><b>A complete point-in-time record.</b> The scheduled availability capture has never completed
  a successful run, so no pre-kickoff series exists for any week.</li>
</ul>

<h2>3. The five things that actually block the project</h2>
{table(["#", "Blocker", "Why it blocks", "What clears it", "Where it is answered"],
 [["1", "No licensed price", "Every money claim, every reward tier, every parlay gate",
   "One written price-data policy plus a retained open/close feed", 'QO-01 / <a href="compare.html">compare</a>'],
  ["2", "Sample too small for the effect size", "Ranking strategies on 132 games ranks noise",
   "≈700–900 walk-forward games, i.e. multiple seasons, or a much larger effect", "QO-02, QO-13"],
  ["3", "Under-dispersed model", "A timid model agrees with the market everywhere and never has a tip worth the vig",
   "Re-fit the shrinkage on a walk-forward proper-score objective; publish the dispersion column", "QO-04"],
  ["4", "No working availability capture", "Availability features, depth deficiency and any pre-kickoff claim are untestable",
   "Repair and prove one clean week of scheduled captures with hashes", "QO-06 / SC-04"],
  ["5", "No official depth ordinal", "The backup-deficiency feature the brief asks for cannot be sourced honestly",
   "A per-club verified chart route for 32 clubs, or an official snap-count source", "QO-09 / R042"]],
 "wide")}

<h2>4. What was done in this session</h2>
<ul>
  <li><b>Built the comparison lab</b> (<code>scripts/build_compare.py</code>): four strategies, four
  controls, walk-forward, coupled-cluster bootstrap, Bonferroni ledger, calibration, luck panel,
  regime split, three-way total comparison, and a published per-game ledger.</li>
  <li><b>Published two new pages</b>: this summary and <a href="compare.html">Compare strategies</a>,
  with {len(qs)} decision questions and {len(sug)} suggestions, each carrying selectable paths and a
  recommendation, so a path can be chosen before anything is implemented.</li>
  <li><b>Checked whether the availability capture works, and found a defect in the alarm rather
  than in the data.</b> The scheduled capture's only run (2026-11-16T22:54Z) failed with exit
  code 2. The cause was that the Week 11 injury route still renders the final Week 10 tables
  before the league publishes the week's report, and the drift check treated that as corruption.
  The check now classifies <em>not published yet</em> separately from <em>drift</em>, records it
  as a dated line in <code>snapshots/index.csv</code>, stores no body, and is unit-tested on
  synthetic pages in the workflow. A page that serves a <em>later</em> week than requested is
  still treated as drift and still fails the build.</li>
  <li><b>Asserted nothing new about the league.</b> The Week 11 official injury report is not
  published yet, so no Week 11 availability is used anywhere; the Week 11 schedule was re-read from
  the official page and is used only for the prospective slate. The fixture page for IND-HOU was
  also read for its venue, which is outside the lab's scope and is not used as a model input.</li>
  <li><b>Changed no existing dataset.</b> The 148-game corpus, the standings snapshot and the
  Week 10 captures are inputs here, read-only. Where this lab's numbers differ from an older page,
  both are published and the difference is on the Flagged for Review page.</li>
</ul>

<h2>5. The arithmetic of "how much longer"</h2>
<p>The intervals on this page are about 2.5–3.0 points of MAE wide on {meta["games"]} games. The
strategies differ from each other by less than 0.6 points and from the pick'em control by less than
1.0. For a paired difference to clear even an unadjusted 95% threshold at the observed effect size,
the sample has to grow roughly by the square of the ratio of the two — a factor of about five to
seven, i.e. <b>700–900 games</b>, or three seasons. For the Bonferroni-adjusted threshold used here,
more. No amount of cleverness on 148 games substitutes for that, which is why the brief's own
insistence on pre-registration and honest intervals is the right call.</p>

<h2>6. Read next</h2>
<table>
  <thead><tr><th>Page</th><th>Why</th></tr></thead>
  <tbody>
    <tr><td><a href="compare.html">Compare strategies</a></td><td>the full lab: comparison, calibration, luck, regimes, totals, correlations, Week 11 slate, questions and suggestions</td></tr>
    <tr><td><a href="board/readiness.html">Requirement readiness</a></td><td>one row per requirement in the brief, with its blocking gate and clearing number</td></tr>
    <tr><td><a href="flagged.html">Flagged for Review</a></td><td>every irregularity, with its official source link, published rather than smoothed</td></tr>
    <tr><td><a href="verified/index.html">Verified results &amp; scoring</a></td><td>the independent results dashboard and its out-of-sample evaluation</td></tr>
    <tr><td><a href="methodology.html">Methodology</a></td><td>how a value gets on this site at all</td></tr>
  </tbody>
</table>
"""
    return page("Executive summary", body, "executive-summary.html")


# ---------------------------------------------------------------------------
def build_ablations(ab: dict) -> str:
    """Readiness R028/R029: injury/availability ablation on a chronological holdout."""
    meta = ab["meta"]
    s = ab["summary"]
    on, off, diff = s["availability_on"], s["availability_off"], s["paired_difference"]
    n = on["n"]

    def ci(v):
        return "—" if not v else f"[{v[0]:.2f}, {v[1]:.2f}]"

    stats = "".join(
        [
            stat(str(n), "holdout games (Week 10)", "chronological holdout"),
            stat(str(meta["inputs"]["results"].get("calibration_window", "Weeks 1-9").split(" ")[-1]),
                 "calibration games", "Weeks 1-9"),
            stat(f"{on['spread_mae']:.2f}", "spread MAE · availability ON", f"95% CI {ci(on['spread_mae_ci95'])}"),
            stat(f"{diff['total_mae']['diff_on_minus_off']:+.2f}",
                 "paired total-MAE diff (ON - OFF)", f"95% CI {ci(diff['total_mae']['diff_ci95'])}"),
        ]
    )

    # summary table
    srows = []
    for label, v in (("availability ON", on), ("availability OFF", off)):
        srows.append([
            label, str(v["n"]),
            f"{v['spread_mae']:.2f}", ci(v["spread_mae_ci95"]), f"{v['spread_rmse']:.2f}",
            f"{v['total_mae']:.2f}", ci(v["total_mae_ci95"]), f"{v['total_rmse']:.2f}",
            f"{v['brier']:.4f}", ci(v["brier_ci95"]),
        ])
    summary_tbl = table(
        ["variant", "n", "spread MAE", "spread MAE 95% CI", "spread RMSE",
         "total MAE", "total MAE 95% CI", "total RMSE", "Brier", "Brier 95% CI"],
        srows,
    )

    # paired differences
    drows = []
    for metric, label in (("spread_mae", "Spread MAE"), ("total_mae", "Total MAE"), ("brier", "Brier")):
        m = diff[metric]
        spans_zero = m["diff_ci95"][0] <= 0 <= m["diff_ci95"][1]
        drows.append([
            label, str(diff["n"]),
            f"{m['diff_on_minus_off']:+.4f}", ci(m["diff_ci95"]),
            f'<span class="badge {"warn" if spans_zero else "good"}">'
            f'{"includes zero" if spans_zero else "excludes zero"}</span>',
            e(m["verdict"]),
        ])
    diff_tbl = table(["metric", "n", "diff (ON - OFF)", "95% CI", "CI excludes zero?", "verdict"], drows)

    # per-game table
    grows = []
    for g in ab["games"]:
        grows.append([
            f'{e(g["game_date"])}',
            f'{e(g["away"])} @ {e(g["home"])}',
            f'{g["actual_away_pts"]}-{g["actual_home_pts"]}',
            f'{g["pred_margin_avail_on"]:+.1f}',
            f'{g["pred_margin_avail_off"]:+.1f}',
            f'{g["spread_err_on"]:.1f}',
            f'{g["spread_err_off"]:.1f}',
            f'{g["total_err_on"]:.1f}',
            f'{g["total_err_off"]:.1f}',
            f'{g["brier_on"]:.3f}',
            f'{g["brier_off"]:.3f}',
            src_link(g["results_source_url"], "results"),
        ])
    games_tbl = table(
        ["date", "game", "final", "margin ON", "margin OFF",
         "spread err ON", "spread err OFF", "total err ON", "total err OFF",
         "Brier ON", "Brier OFF", "src"],
        grows,
    )

    excl = "".join(f"<li>{e(x)}</li>" for x in meta["exclusions"])
    lims = "".join(f"<li>{e(x)}</li>" for x in meta["limitations"])

    body = f"""
<section class="lead">
  <h1>Injury / availability ablation</h1>
  <p>{e(meta["title"])}. The brief replaces fixed injury penalties with <em>measured</em>
  ablations: the identical originated-line model is run twice on the same chronological holdout,
  once <strong>with</strong> the verified availability features (Week 10 official injury-report game
  statuses) and once <strong>without</strong> them. {badge("model evaluation", "model")}
  These numbers are <strong>not</strong> leaderboard entries - the brief forbids backtest numbers on
  the leaderboard.</p>
</section>
<section>{stats}</section>
<section>
  <h2>Head-to-head summary</h2>
  <p>Both variants use identical power ratings (calibrated on verified Weeks 1-9 only) and differ
  <strong>only</strong> in whether the capped availability adjustment is applied.</p>
  {summary_tbl}
</section>
<section>
  <h2>Paired difference with uncertainty</h2>
  <p>Each row resamples the {n} holdout games (bootstrap, seed 20261117, 20000 reps). A CI that
  spans zero means the availability features do not demonstrate a measurable change - no skill
  advantage is claimed.</p>
  {diff_tbl}
</section>
<section>
  <h2>Per-game detail</h2>
  {games_tbl}
</section>
<section>
  <h2>Method</h2>
  <p>{e(meta["method"])}</p>
</section>
<section>
  <h2>Exclusions</h2>
  <ul>{excl}</ul>
</section>
<section>
  <h2>Limitations</h2>
  <ul>{lims}</ul>
</section>
<section>
  <h2>Sources</h2>
  <ul>
    <li>Week 10 results: {src_link(meta["inputs"]["results"]["src"], "NFL.com Week 10 schedule")} -
        file <code>data/week_results_2026.csv</code></li>
    <li>Availability (injury game status): {src_link(meta["inputs"]["availability"]["src"], "NFL.com injury report")} -
        file <code>data/injuries_week10.json</code></li>
    <li>Ratings: {src_link(meta["inputs"]["ratings"]["src"], "NFL.com standings")}</li>
  </ul>
</section>
"""
    return page("Ablations", body, "ablations.html")


def main():
    standings = load("standings.json")
    lines = load("lines_week10.json")
    inj = load("injuries_week10.json")
    luck = load("luck.json")
    strat = load("strategies.json")
    corr = load("correlations.json")
    dec = load("decisions.json")
    sug = load("suggestions.json")
    flag = load("flagged.json")
    src = load("sources.json")
    ablations = load("ablations_week10.json")
    audit = load("acceptance_audit_2026-11-17.json")
    readiness = read_requirement_rows()
    official_sources = read_source_registry()

    out = {
        "index.html": build_index(standings, lines, inj, luck, strat, dec, sug, flag, readiness, official_sources),
        "standings.html": build_standings(standings, luck),
        "lines.html": build_lines(lines, inj),
        "injuries.html": build_injuries(inj),
        "strategies.html": build_strategies(strat),
        "correlation.html": build_correlation(corr),
        "decisions.html": build_decisions(dec),
        "suggestions.html": build_suggestions(sug),
        "flagged.html": build_flagged(flag),
        "sources.html": build_sources(src),
        "compare.html": build_compare(),
        "executive-summary.html": build_executive_summary(),
        "methodology.html": build_methodology(standings, luck, corr, lines),
        "ablations.html": build_ablations(ablations),
        "audit.html": build_audit(audit),
    }
    for name, content in out.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as fh:
            fh.write(content)
    print(f"built {len(out)} pages: {', '.join(sorted(out))}")


if __name__ == "__main__":
    main()
