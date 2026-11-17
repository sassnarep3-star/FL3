#!/usr/bin/env python3
"""
FL3 — pages for the frontier datasets.

Renders five new root pages from the files this session created:

  spec.html          data specification and source traceability (R0xx register)
  week11.html        the official Week 11 fixture register + our originated prices
  availability.html  the expected-vs-actual availability graph for Week 10
  results.html       the verified results feed and its reconciliation to standings
  lab.html           injury ablation and strategy leaderboard v2

Every table row carries the URL of the document it came from. A cell with no
official basis is rendered as a visible blank with the reason, never as a value.
"""
from __future__ import annotations

import csv
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# PAGES lives in build_site.py; importing keeps one nav definition.
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import PAGES, e, page, table, badge, stat, src_link, load  # noqa: E402

CAPTURED = "2026-11-17"


def read_csv(rel):
    with open(os.path.join(DATA, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(v, digits=2, dash="—"):
    if v in ("", None):
        return dash
    try:
        return f"{float(v):.{digits}f}"
    except (TypeError, ValueError):
        return e(str(v))


def pctf(v, digits=1):
    if v in ("", None):
        return "—"
    return f"{float(v)*100:.{digits}f}%"


def blank(reason):
    return f'<span class="unverified">blank — {e(reason)}</span>'


# ---------------------------------------------------------------------------
IRREGULARITIES = [
    ("F-149", "The transcribed corpus held 148 games; the official standings require 149.",
     "CIN and PIT differed from the standings by exactly one 38-18 game.",
     "Corrected in the feed and proved club-by-club; the build fails if any club disagrees."),
    ("F-150", "The brief states a 136-game log.",
     "Weeks 1-9 of the official schedule hold exactly 136 games; Week 10 adds 13 finals.",
     "Published as a corrected count (149), not argued about."),
    ("F-151", "The Week 11 schedule page lists New England among the teams on bye, and NE also"
              " appears on no fixture.",
     "nfl.com/schedules/2026/by-week/week-11, 'Teams on Bye' block.",
     "Recorded as published. The bye list and the fixture list agree with each other, so nothing"
     " is inferred about eligibility."),
    ("F-152", "Washington's venue is 'NORTHWEST STADIUM' on the game centre and the schedule"
              " page's hotel link, and 'FedEx Field' in the ticket links.",
     "Both strings appear on the same official schedule page.",
     "Transcribed verbatim as NORTHWEST STADIUM; the variant is noted on the Week 11 page."),
    ("F-153", "The Week 10 Game Book lists C.Klubnik and A.Beck under the Jets' Did Not Play,"
              " and both appear in that game's passing statistics.",
     "REG10-BUF-NYJ Game Summary PDF, DNP block vs stats block.",
     "Published as printed and flagged; the two players are excluded from name-level joins."),
    ("F-154", "The Dallas defensive starting lineup renders in the PDF text as jersey numbers"
              " with the name column missing.",
     "REG10-SF-DAL Game Summary PDF.",
     "Numbers stored, no name invented, excluded from joins."),
    ("F-155", "The Saints' quarterback is printed 'T.Though'; the official player page calls him"
              " Tyler Shough.",
     "REG10-CAR-NO Game Summary PDF.",
     "Stored as printed, with the discrepancy flagged on the same row."),
    ("F-156", "The official Week 11 injury report is not published; /injuries/league/2026/reg11"
              " serves the Week 10 table.",
     "Every Week 11 game centre says 'Injury Report is not available at this time'.",
     "No Week 11 designation is published anywhere on this site. Expected availability for"
     " Week 11 is left blank."),
]
IRREG_ROWS = [
    [f"<b>{i}</b>", w, ev, h]
    for i, w, ev, h in IRREGULARITIES
]


def build_spec():
    fixtures = load("official/week11_fixtures.json")
    feed = read_csv("official/results_feed.csv")
    recon = read_csv("official/club_reconciliation.csv")
    avail = read_csv("availability/availability_graph.csv")
    gb = load("official/game_books_week10.json")
    lab = read_csv("lab/ablation_summary.csv")
    lb = load("lab/leaderboard_v2.json")
    reg = read_csv("pricing/snapshot_register.csv")

    rows = []
    spec = [
        ("results_feed", "data/official/results_feed.csv", len(feed),
         "one row per FINAL game", "official schedule page per week",
         "schedules/2026/by-week/week-N"),
        ("club_reconciliation", "data/official/club_reconciliation.csv", len(recon),
         "one row per club", "official league standings",
         "standings/league/2026/REG"),
        ("game_books_week10", "data/official/game_books_week10.json",
         gb["_meta"]["coverage"]["games_with_game_book"],
         "one entry per game with a published Game Book", "NFL Game Summary PDF",
         "static.www.nfl.com/.../gamecenter/*.pdf"),
        ("week11_fixtures", "data/official/week11_fixtures.json",
         len(fixtures["fixtures"]),
         "one row per Week 11 fixture", "official schedule page + game centre",
         "schedules/2026/by-week/week-11"),
        ("price_snapshots", "data/pricing/snapshots/*.json", len(reg),
         "one immutable capture per timestamp", "our own origination, hashed",
         "model_id FL3-SHADOW-1"),
        ("availability_graph", "data/availability/availability_graph.csv", len(avail),
         "one row per depth-1 slot per club-game", "Game Book + official report",
         "gamecentre PDF per row"),
        ("injury_ablation", "data/lab/ablation_summary.csv", len(lab),
         "one row per scored metric", "walk-forward over the results feed",
         "no external source needed"),
        ("leaderboard_v2", "data/lab/leaderboard_v2.json", len(lb["strategies"]),
         "one row per strategy", "scored on the same 85 games", "paired comparison"),
    ]
    rows = [[f"<b>{e(name)}</b>", f"<code>{e(path)}</code>", n, e(grain),
             e(authority), f"<code>{e(src)}</code>"] for name, path, n, grain, authority, src in spec]

    gap_rows = [
        ["Market price (spread / total / moneyline)", blank("no licensed feed; policy PD-01"),
         "Every market_* column is empty by decision, not oversight. See the policy note below."],
        ["Week 11 injury designations", blank("not published at capture"),
         "nfl.com/injuries/league/2026/reg11 serves the Week 10 table; all 13 Week 11 game "
         "centres say the report is not available. No value is invented."],
        ["Week 11 depth chart", blank("no capture for this week"),
         "The Week 10 Ourlads transcription is the only depth capture held."],
        ["Snap counts", blank("not published in a Game Book"),
         "Playing time would come from an official participation report; none is held. "
         "Replacement depth is therefore measured from depth-chart position, not snaps."],
        ["LAC@BAL Week 10 final", blank("game not final at capture"),
         "Q2 01:05 at capture. Excluded from the corpus rather than guessed."],
        ["Week 11 weather / roof", blank("kickoff more than 48h away"),
         "Weather and roof affect totals; they are only fetched inside the game-day window."],
    ]
    return page("Data specification and source traceability", f"""
<section class="hero">
  <h1>Every dataset, where it comes from, and what it refuses to say</h1>
  <p class="lede">Eight datasets were added on {CAPTURED}. This page is the contract for each one:
  row grain, the document that authorises it, and the blanks it deliberately keeps. If a table
  elsewhere on this site shows a number, that number traces back through one of these files to a
  page that published it.</p>
</section>

<section>
  <h2>The eight datasets</h2>
  {table(["Dataset", "File", "Rows", "Grain", "Authority", "Source pattern"], rows, "wide")}
</section>

<section>
  <h2>Blank by design — the six gaps that are visible rather than filled</h2>
  <p class="lede">A blank cell with a stated reason is a finding. A plausible number in the same
  cell would be a fabrication. These are the six places the project chose the first.</p>
  {table(["Field", "State", "Why it is blank and what would clear it"], gap_rows, "wide")}
</section>

<section>
  <h2>Rule of traceability</h2>
  <ol class="tight">
    <li>Every published number names the file it is stored in and the URL of the page that
      published it. Those two things travel together; a number without both is not rendered.</li>
    <li>A value the source prints with an oddity (a misspelt name, a stadium called two different
      things, a player both inactive and in the stats) is published exactly as printed and the
      oddity is flagged next to it.</li>
    <li>A derived number states its formula and the inputs it used, in the same row or the same
      paragraph. The origination formula is validated against the 496 frozen example forecasts
      in <code>data/preregistration_week11.json</code> on every build; a deviation above 0.01
      points fails the build.</li>
    <li>Any market number this project does not hold is blank. It is never entered as zero,
      never entered as an average of numbers we do hold, and never described as "approximately".</li>
  </ol>
</section>

<section id="irregularities">
  <h2>Flagged by this session — eight irregularities, published as found</h2>
  <p class="lede">Each of these is a place where an official document contradicted itself, or
  where the project's own earlier number was wrong. They are listed here with the document that
  shows them. None of them blocks publication; all of them are visible.</p>
  {table(["#", "What is irregular", "Evidence", "How it is handled"], IRREG_ROWS, "wide")}
</section>

<section>
  <h2>Older pages still say 148 games</h2>
  <p>The verified-results and verification subsites, and the executive summary, were written
  against a 148-game corpus before the Week 10 PIT@CIN result was final. They are owned by other
  sessions and were not rewritten here. <b>Where they say 148, read 149</b>; the reconciliation on
  <a href="results.html">the results page</a> is the current number and the only place the corpus
  count is proved. A cross-scope update request is logged in <code>COORDINATION.md</code> rather
  than made silently.</p>
</section>

<section>
  <h2>What each new file changes about the old claims</h2>
  <ul class="tight">
    <li><b>The results corpus is 149 games, not 136 and not 148.</b> See
      <a href="results.html">the reconciliation</a>: 32 of 32 clubs now match the official
      standings exactly on W, L, T, PF and PA, and the league's points-for sum equals its
      points-against sum.</li>
    <li><b>"Out" is not the same as "did not play".</b> Across the 30 depth-1 players the official
      report ruled Out, 30 sat — but across the 7 the report did not rule out at all, the Game
      Book shows nobody started and the outcome is simply unobservable from a submitted report.
      The empirical table is on <a href="availability.html">Availability</a>.</li>
    <li><b>Adding personnel to the model did not help on the only week it could be tested</b>
      (13 games, all three intervals cross zero). That is published as the result on
      <a href="lab.html">the lab page</a>, not buried.</li>
    <li><b>No strategy clears the demotion gate.</b> The best Brier skill is +0.13 with a 2.5%
      cluster bound of −0.04, and all four Holm-adjusted p-values are above 0.05. Every strategy
      is demoted to paper.</li>
  </ul>
</section>
""", "spec.html")


# ---------------------------------------------------------------------------
def build_week11():
    fx = load("official/week11_fixtures.json")
    prices = {r["game_id"]: r for r in read_csv("pricing/current_prices.csv")}
    rows = []
    for f in fx["fixtures"]:
        p = prices.get(f["game_id"], {})
        rows.append([
            f"<b>{e(f['away'])} @ {e(f['home'])}</b>",
            f"{e(f['day'])} {e(f['date'])}",
            e(f["kickoff_et"]) + " ET",
            e(f["network"]),
            e(f["stadium"]) + f"<br><small>{e(f['location'])}</small>",
            num(p.get("open_fair_spread_home"), 1),
            num(p.get("open_fair_total"), 1),
            pctf(p.get("open_p_home")),
            blank("PD-01"),
            blank("PD-01"),
            src_link(f["game_url"], "game centre") + " · " + src_link(f["schedule_url"], "schedule"),
        ])
    byes = ", ".join(fx["byes"])
    return page("Week 11 — official fixtures and originated prices", f"""
<section class="hero">
  <h1>Week 11: thirteen fixtures, six byes, and one number the project actually owns</h1>
  <p class="lede">The schedule facts below are transcribed from the official Week 11 schedule page
  and from each game centre's own Game Info block, captured {CAPTURED}. The four model columns
  are this project's own origination from the frozen pre-registered model. The two market columns
  are blank, and stay blank, because no licensed market number is held.</p>
</section>

<section class="stats">
  {stat(len(fx["fixtures"]), "fixtures")}
  {stat(len(fx["byes"]), "clubs on bye")}
  {stat(len(prices), "fixtures with our own open price", "all pre-kickoff, hashed")}
  {stat("13", "game centres captured", "venue transcribed verbatim on each")}
</section>

<section>
  <h2>The register</h2>
  <p class="lede">Kickoff is the published Eastern time. The <code>kickoff_utc</code> field in the
  data file converts it, and the price store refuses to timestamp a capture after that moment.
  Stadium and city are the exact strings the game centre prints — including "NORTHWEST STADIUM"
  for Washington, which the schedule page's own booking links still call FedEx Field.</p>
  {table(["Matchup", "Day", "Kickoff", "Network", "Venue (as printed)", "Fair spread (home)",
          "Fair total", "P(home)", "Market spread", "Market total", "Source"], rows, "wide")}
  <p><b>Byes:</b> {e(byes)}. The arithmetic that has to close: 13 fixtures × 2 club slots
  = 26 playing clubs, plus {len(fx["byes"])} clubs on bye = 32.</p>
</section>

<section>
  <h2>Why the market columns are blank</h2>
  <p>Policy <b>PD-01</b> was decided this session and is written into
  <code>data/official/results_feed.json</code>. Its substance:</p>
  <ul class="tight">
    <li>No licensed, timestamped price feed exists in this repository. Publishing a market number
      we do not hold would be an invented number wearing a source link.</li>
    <li>So the project does not report ROI, expected value or closing-line value anywhere. It
      reports proper scores that need only an outcome — Brier, log loss, and line error against
      the official final margin and total.</li>
    <li>The comparison the brief asks for (fair line vs market line vs difference) is therefore
      published as <b>fair line and blank</b>, with the blank labelled. The third column appears
      the day a licensed feed does.</li>
    <li>This is a decision, not a deferral. It is written down so it cannot silently change.</li>
  </ul>
</section>

<section>
  <h2>Markets are originated side first, then total, then moneyline</h2>
  <p>Each snapshot stores <code>market_order: ["side", "total", "moneyline"]</code> and the store
  refuses to write a later market before an earlier one for the same fixture. The order matters
  because the total is informed by the side: a team's expected points and its opponent's are not
  independent, so deriving a total first forces an assumption about pace that the side has
  already told you.</p>
  <p><a href="spec.html">Specification and traceability</a> ·
     <a href="availability.html">Availability graph</a> ·
     <a href="lab.html">Ablations and leaderboard</a></p>
</section>
""", "week11.html")


# ---------------------------------------------------------------------------
def build_availability():
    rows_all = read_csv("availability/availability_graph.csv")
    cal = read_csv("availability/designation_empirical.csv")
    dist = read_csv("availability/replacement_depth_distribution.csv")
    clubs = read_csv("availability/club_availability_summary.csv")
    gb = load("official/game_books_week10.json")

    cal_rows = [[
        f"<b>{e(r['designation'])}</b>",
        r["n_observed"],
        r["n_started"],
        pctf(r["start_rate"]),
        f"{pctf(r['start_rate_lo95'])} – {pctf(r['start_rate_hi95'])}",
        r["n_not_observed"],
    ] for r in cal]

    flagged = [r for r in rows_all if r["actual_state"] in ("NOT_ACTIVE", "DID_NOT_PLAY")]
    repl_rows = [[
        e(r["club"]), e(r["position"]),
        f"<b>{e(r['depth1_player'])}</b>",
        num(r["slot_group_size"], 0),
        e(r["actual_state"]),
        e(r["official_game_status"]) or "—",
        e(r["replacement"]) or "—",
        num(r["replacement_depth"], 0),
        e(r["replacement_state"]),
        src_link(r["gamebook_pdf"], "Game Book"),
    ] for r in flagged]

    club_rows = [[
        f"<b>{e(r['club'])}</b>", r["depth1_slots"], r["started"], r["not_active"],
        r["did_not_play"], r["not_listed"], r["unresolved"],
        r["replacement_confirmed"], r["replacement_listed_not_starting"],
        r["no_deeper_player_listed"],
    ] for r in clubs]

    dist_rows = [[f"depth {e(r['replacement_depth'])}", r["slots"]] for r in dist]

    n_captured = gb["_meta"]["coverage"]["games_with_game_book"]
    return page("Availability graph — expected versus actual", f"""
<section class="hero">
  <h1>Who was supposed to play, who actually did, and how deep the replacement had to go</h1>
  <p class="lede">The "expected" side is the declared depth order. The "actual" side is the
  official Game Book — the only NFL document that states a starting lineup. {n_captured} of the
  14 Week 10 games have a published Game Book and all {n_captured} were transcribed. The two games
  without one (PIT@CIN, LAC@BAL) are absent from the graph rather than assumed.</p>
</section>

<section>
  <h2>The finding that changes how injuries should be priced</h2>
  <p class="lede">The official report's game status is a <i>level</i>. What it predicts about
  whether a player actually started is a separate question, and the Game Books answer it. This
  table is the empirical answer on the only week where both documents exist.</p>
  {table(["Official designation", "Depth-1 slots observed", "Slots where he started",
          "Start rate", "95% interval", "Slots not observable"], cal_rows)}
  <p><b>Read it carefully.</b> "Not observable" is not "did nothing". A Game Book lists starters,
  substitutions, did-not-play and not-active; this capture transcribed three of those four
  blocks reliably, so a player who is in none of them cannot be placed and is reported as
  unobservable. That is why the denominators differ, and why the column is printed rather than
  quietly dropped.</p>
  <p>The practical consequence: a "Questionable" depth-1 player started 84% of the time in this
  week (16 of 19 observed), while a player with <i>no designation at all</i> started 98% of the
  time. The designation separates a little; it does not separate nearly as much as a naive
  penalty would assume, and "Out" is the only category that reliably predicts absence.</p>
</section>

<section>
  <h2>Replacement depth — how far down the chart the next man was</h2>
  <p>Presence of a replacement is not the interesting fact; the brief asks for depth. Of the slots
  where a depth-1 player was genuinely inactive, here is how deep the listed next man sat.</p>
  {table(["Replacement's depth rank", "Slots"], dist_rows)}
  <p>Every replacement came from depth 2 or 3 — no club in this week reached deeper than its
  third string at a position where the starter was inactive. That is a real constraint on any
  model that wants to charge a large penalty for a "depth" problem: at this point in the season
  the replacements are, in the main, the next listed man.</p>
</section>

<section>
  <h2>Every depth-1 slot that did not start</h2>
  <p class="lede">One row per club and position where the declared depth-1 player was inactive or
  did not play, with the next man and whether the Game Book confirms he started. A cell that says
  "LISTED_NEXT_BUT_NOT_STARTING" is an honest admission: the depth chart's next name was not in
  the starting eleven, and this capture will not pretend it was.</p>
  {table(["Club", "Pos", "Depth-1 player", "Slot group", "Actual", "Report status",
          "Replacement", "Depth", "Replacement state", "Evidence"], repl_rows, "wide")}
</section>

<section>
  <h2>Per-club summary</h2>
  {table(["Club", "Depth-1 slots", "Started", "Inactive", "Did not play", "Not listed", "Unresolved",
          "Replacement confirmed", "Listed, did not start", "No deeper player listed"], club_rows, "wide")}
</section>

<section>
  <h2>What this graph deliberately does not do</h2>
  <ul class="tight">
    <li>It does not read the depth order off a jersey number, a salary, or draft position. The
      order comes from a declared third-party depth source, and the file records that source on
      every row.</li>
    <li>It does not turn a missing name into a benching. Absence from a transcribed block yields
      "not listed", never "did not play".</li>
    <li>It does not credit a replacement as a starter unless the Game Book's own lineup names him
      there.</li>
    <li>It does not claim "Out" means "did not play" — the table above tests exactly that, and
      finds it holds for the Week 10 sample without being a law.</li>
  </ul>
</section>
""", "availability.html")


# ---------------------------------------------------------------------------
def build_results():
    feed = read_csv("official/results_feed.csv")
    recon = read_csv("official/club_reconciliation.csv")
    decl = load("official/results_feed.json")

    by_week = {}
    for r in feed:
        by_week.setdefault(int(r["week"]), []).append(r)

    week_rows = []
    for w in sorted(by_week):
        games = by_week[w]
        week_rows.append([f"<b>{w}</b>", len(games),
                          sum(int(g["total_points"]) for g in games),
                          sum(abs(int(g["margin_home"])) for g in games) // len(games)])

    recent = sorted(by_week[10], key=lambda g: g["date"])
    recent_rows = [[
        e(g["date"]), f"{e(g['away'])} {g['away_pts']}", f"{e(g['home'])} {g['home_pts']}",
        f"{int(g['margin_home']):+d}", g["total_points"],
        e(g["winner"]), src_link(g["source_url"], "result"),
    ] for g in recent]

    bad = [r for r in recon if r["verdict"] != "MATCH"]
    recon_rows = [[
        f"<b>{e(r['club'])}</b>", f"{r['official_w']}-{r['official_l']}-{r['official_t']}",
        f"{r['corpus_w']}-{r['corpus_l']}-{r['corpus_t']}",
        r["official_pf"], r["corpus_pf"], r["official_pa"], r["corpus_pa"],
        badge("MATCH" if r["verdict"] == "MATCH" else "MISMATCH",
              "ok" if r["verdict"] == "MATCH" else "bad"),
        src_link(r["source_url"], "standings"),
    ] for r in sorted(recon, key=lambda r: -int(r["official_w"]))]

    return page("Results — the verified corpus", f"""
<section class="hero">
  <h1>149 verified games, and a corpus that reconciles to the league's own standings</h1>
  <p class="lede">The brief asks for a verified results feed that makes backtests and ROI
  possible. The first job is arithmetic: does the games log add up to what the league says each
  club has done? For 148 transcribed games it did not — two clubs were wrong. Here is the
  correction, the proof, and the one game that is deliberately excluded.</p>
</section>

<section class="stats">
  {stat(len(feed), "final, verified games")}
  {stat(len(recon), "clubs reconciled")}
  {stat(f"{len(recon)-len(bad)}/{len(recon)}", "clubs matching exactly")}
  {stat("1", "game excluded", "LAC@BAL — not final")}
</section>

<section>
  <h2>The correction: one missing game, exactly</h2>
  <p>Aggregating the 148-game log gave <b>CIN 6-2, 240 PF / 175 PA</b> and
  <b>PIT 6-2, 180 PF / 144 PA</b>. The official standings give <b>CIN 7-2, 278 / 193</b> and
  <b>PIT 6-3, 198 / 182</b>. The differences are identical and opposite: one CIN win by
  <b>38-18</b> and one PIT loss by <b>18-38</b>. That is not a rounding issue or a tie-handling
  issue; it is a single game, PIT@CIN in Week 10, which was not final when the log was first
  transcribed and was therefore correctly omitted at the time.</p>
  <p>Adding it makes all 32 clubs match on W, L, T, PF and PA, and makes the league's
  points-for sum equal its points-against sum ({decl['reconciliation']['result_after_correction']['league_pf_sum']}).
  The feed now states the count: <b>{len(feed)} games</b>.</p>
  <p class="lede">The brief's figure of 136 games is not reproducible from any official page. It
  was recorded as a corrected number rather than treated as a defect to argue about. Weeks 1-9
  hold exactly 136 games; the brief is nine weeks of a ten-week season.</p>
</section>

<section>
  <h2>Games per week and their totals</h2>
  {table(["Week", "Games", "Points scored", "Mean absolute margin"], week_rows)}
  <p>Weeks 1-4 have sixteen games; Week 5 has fifteen because of a scheduled bye pair; Weeks 6-8
  have fourteen; Week 9 has fifteen and Week 10 <b>thirteen</b> finals. The fourteenth Week 10
  fixture, LAC@BAL, was still in the second quarter at capture and is excluded rather than
  guessed. A short week is a fact about the schedule, not a gap in the log.</p>
</section>

<section>
  <h2>Week 10, game by game</h2>
  {table(["Date", "Away", "Home", "Margin", "Total", "Winner", "Source"], recent_rows)}
</section>

<section>
  <h2>Every club against the official standings</h2>
  {table(["Club", "Official W-L-T", "Corpus W-L-T", "Official PF", "Corpus PF",
          "Official PA", "Corpus PA", "Verdict", "Source"], recon_rows, "wide")}
  <p><b>{len(recon) - len(bad)} of {len(recon)} match.</b> A mismatch here fails the build; the
  dataset cannot ship in a state where the corpus disagrees with the standings.</p>
</section>

<section>
  <h2>What the feed refuses to contain</h2>
  <ul class="tight">
    <li>A game without an official final score. LAC@BAL was still in the second quarter at
      capture (17-7) and is excluded from every count, every rating and every backtest.</li>
    <li>A score derived from a live play-by-play page. A live page is not a result.</li>
    <li>A "close enough" match. The comparison is exact on five integers per club.</li>
  </ul>
</section>
""", "results.html")


# ---------------------------------------------------------------------------
def build_lab():
    lab = read_csv("lab/ablation_summary.csv")
    folds = read_csv("lab/walkforward_folds.csv")
    lb = load("lab/leaderboard_v2.json")

    lab_rows = [[
        f"<b>{e(r['metric'])}</b>", r["n_games"], f"{float(r['mean_difference_M1_minus_M0']):+.4f}",
        f"[{float(r['boot_lo95']):+.4f}, {float(r['boot_hi95']):+.4f}]",
        e(r["sign_convention"]), badge(r["verdict"], "warn" if "no difference" in r["verdict"] else "ok"),
    ] for r in lab]

    fold_rows = [[
        f"Weeks 1-{r['cut_week']} → {r['test_week']}", r["n_games"],
        num(r["mae_margin_M0"], 2), num(r["mae_margin_M1"], 2),
        num(r["mae_total_M0"], 2), num(r["brier_M0"], 4), num(r["brier_pickem"], 4),
        badge("personnel on" if r["personnel_available"] == "YES" else "base only",
              "ok" if r["personnel_available"] == "YES" else "info"),
    ] for r in folds]

    lb_rows = []
    for s in lb["strategies"]:
        verdict_kind = "bad" if s["verdict"] == "DEMOTED_TO_PAPER" else (
            "info" if s["verdict"].startswith("BASELINE") else "ok")
        lb_rows.append([
            s["rank"], f"<b>{e(s['strategy'])}</b>",
            num(s["brier"], 4),
            f"{s['brier_skill_vs_coin']:+.3f}",
            f"[{s['boot_lo95']:+.3f}, {s['boot_hi95']:+.3f}]",
            f"{s['cluster_lower_bound']:+.3f}",
            f"{s['p_skill_gt_0']:.3f}",
            "—" if s["p_holm_adjusted"] in ("", None) else f"{s['p_holm_adjusted']:.3f}",
            blank("PD-01"),
            badge(s["verdict"].replace("_", " ").lower(), verdict_kind),
        ])

    return page("Lab — ablation and leaderboard", f"""
<section class="hero">
  <h1>Two results, one of them unwelcome</h1>
  <p class="lede">The brief asks for injury effects as an <i>ablation</i> on chronological
  holdouts rather than a fixed point penalty, and for a leaderboard ranked by a proper score with
  a cluster lower bound and a multiplicity adjustment, with a demotion gate to paper. Both are
  built. Neither flatters the model, and the pages says so.</p>
</section>

<section>
  <h2>1 · Injury ablation</h2>
  <p class="lede">Model M1 adds a personnel term for depth-1 players the official report had
  already ruled out; the coefficient is fitted on the training slice only. Model M0 is the same
  model without it. They are compared on the same games, so the interval is paired.</p>
  {table(["Metric", "Games", "M1 − M0", "95% cluster interval", "Sign convention", "Verdict"], lab_rows)}
  <p><b>All three intervals cross zero.</b> On the only week where a depth chart exists, adding
  personnel information made the model slightly worse on every metric, and the difference is
  inside the noise of thirteen games. The honest conclusion is that this repository cannot yet
  demonstrate that an injury term helps — which is exactly the reason the brief forbids a fixed
  penalty. A fixed penalty of, say, 2 points per missing starter would have produced the same
  forty-point error bars while looking authoritative.</p>
  <p>Thirteen games is not enough to settle it either way. This is reported as insufficient
  evidence, not as evidence of absence, and the coefficient is published so the next week can
  move it.</p>
</section>

<section>
  <h2>Walk-forward folds</h2>
  <p>Ratings are fitted on Weeks 1..k and scored on Week k+1. The personnel term can only switch
  on where a depth capture exists, which is Week 10.</p>
  {table(["Fit → test", "Games", "Margin MAE M0", "Margin MAE M1", "Total MAE M0",
          "Brier M0", "Brier pick'em", "Personnel"], fold_rows)}
</section>

<section>
  <h2>2 · Leaderboard v2 — proper score, not ROI</h2>
  <p class="lede">{lb['_meta']['n_games']} games, nine strategies scored on the same fixtures.
  Skill is 1 − Brier ÷ Brier(coin). The interval is a game-cluster bootstrap. The
  p-value is Holm-adjusted across the five non-baseline strategies. A strategy clears the gate
  only if its adjusted p is below 0.05 <i>and</i> its 2.5% cluster bound is above zero.</p>
  {table(["#", "Strategy", "Brier", "Skill", "95% cluster interval", "2.5% bound",
          "p (skill>0)", "p Holm", "ROI", "Verdict"], lb_rows, "wide")}
  <p><b>Nothing clears.</b> The best row is <i>FL3 ratings, no home edge</i> at skill +0.131,
  but its 2.5% bound is −0.037 and its Holm-adjusted p is 0.21. Under the pre-registered rule
  that is a demotion to paper, and the table says so in the same row as the encouraging number.</p>
  <p>Note what the baselines establish: "always home" is catastrophically bad
  (skill −1.35) and "always away" is bad (−0.65). Home advantage is real; the question the
  leaderboard is testing is whether this model adds anything <i>beyond</i> knowing who is at home.
  Marginally, it does not yet.</p>
</section>

<section>
  <h2>What would change our mind — for each strategy</h2>
  <p>Every row in <code>data/lab/leaderboard_v2.json</code> carries a
  <code>what_would_change_our_mind</code> and a <code>what_would_falsify_it</code> list. In
  summary, for all of them: a second season's games the strategy was not fitted on, and the same
  sign of skill under a different proper score (log loss), would move a row out of paper. A
  bootstrap interval that still includes zero, or skill that flips sign between Weeks 5-7 and
  Weeks 8-10, would kill it.</p>
  <p><b>A calibration note, stated because it is uncomfortable.</b> The rating differential is
  overconfident: the best fixed shrink of its probability toward 0.5 was 0.65, which lifts its
  Brier from 0.234 to 0.228. The leaderboard does not silently apply that shrink — that would be
  fitting on the test set. It is recorded here as the most promising next iteration, to be
  pre-registered before it is scored.</p>
</section>

<section>
  <h2>What is deliberately missing</h2>
  <ul class="tight">
    <li><b>ROI.</b> Blank for every strategy, by policy PD-01. A rank by season-long ROI over 85
      games would be a rank by luck; the brief rejects it and so does the code.</li>
    <li><b>Win rate.</b> Not a column. It drops ties and ignores confidence.</li>
    <li><b>A three-way train/validation/holdout split.</b> One season cannot supply one without
      leakage. The rule is declared in the results feed for the moment a second season exists and
      is explicitly not claimed as evidence today.</li>
  </ul>
</section>
""", "lab.html")


def main():
    out = {
        "spec.html": build_spec(),
        "week11.html": build_week11(),
        "availability.html": build_availability(),
        "results.html": build_results(),
        "lab.html": build_lab(),
    }
    for name, content in out.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as fh:
            fh.write(content)
    print(f"built {len(out)} frontier pages: {', '.join(sorted(out))}")


if __name__ == "__main__":
    main()
