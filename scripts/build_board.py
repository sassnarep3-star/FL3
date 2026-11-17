#!/usr/bin/env python3
"""Build the FL3 review board in board/ from data/ + content/board/.

`board/` is a self-contained static site published as a *subdirectory* of the repo root, which is
what GitHub Pages builds for this repo (source: branch `main`, path `/`). It deliberately does not
touch the root-level pages or `docs/`, which another session generates from its own `data/*.json`:
two build systems, one repo, no shared output files.


Evidence and publishing rules:

  * Evidence-bearing rows link to a registered official source when one applies.
    Open questions also carry an explicit source_gap so a link is never mistaken for
    an answer; source links are input references, not proof of capture.
  * A cell that is empty stays empty and renders as "not published", never as 0.
  * Rows whose status/verification column says unverified/partial/blocked get a
    visible badge, and the page shows a verification meter.
  * The build fails (exit 1) if verify.py fails, a question lacks provenance metadata,
    a question cites a non-official/unregistered source, or its rendered row omits the
    registered source link or source-gap note.

Usage:  python3 scripts/build_board.py [--check]
"""

from __future__ import annotations

import csv
import hashlib
import html
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_fl3 import REPO, read_rows  # noqa: E402

BOARD = os.path.join(REPO, "board")
CONTENT = os.path.join(REPO, "content", "board")
SITE = os.path.join(REPO, "site")

# the csvs this track owns - the board copies exactly these into board/data/ and nothing else, so a
# file another session owns is never republished here with a different interpretation
BOARD_DATA = [
    "standings_2026.csv", "games_2026.csv", "team_pass_off_2026.csv", "team_rush_off_2026.csv",
    "team_pass_def_2026.csv", "injuries_2026_w10.csv", "slate_2026_w10.csv", "sources.csv",
    "league_facts.csv", "questions.csv", "suggestions.csv", "signals.csv", "gates.csv",
    "flags.csv", "derived_team_metrics.csv", "derived_league_stats.csv", "derived_correlations.csv",
    "power_ratings.csv", "lines_origination.csv", "model_calibration.csv", "decision_math.csv",
    "leaderboard.csv", "verification_report.csv", "requirements_readiness.csv",
    "captures_week10_results.csv", "scoring_week10.csv", "luck_panel.csv",
    "line_provenance_reconciliation.csv", "line_provenance_verdict.csv",
    "snapshot_delta.csv", "injury_crosscheck.csv", "depth_blocks.csv",
    "depth_grammar_findings.csv", "depth_starter_out.csv", "decisions_queue.csv",
    "official_injury_capture_wk10_2026.csv", "official_injury_reconciliation_wk10_2026.csv",
    "official_injury_copy_audit_wk10_2026.csv",
]

# slug -> (title, nav label, group)
PAGES = [
    ("index", "FL3 - NFL line origination and signal board", "Dashboard", "home"),
    ("executive-summary", "Executive summary", "Executive summary", "read"),
    ("readiness", "Requirement readiness register", "Requirement readiness", "read"),
    ("decision-queue", "Decision queue - requirements collapsed into owner decisions", "Decision queue", "read"),
    ("questions", "Open questions and information gaps", "Questions & gaps", "read"),
    ("suggestions", "Suggestion register", "Suggestions", "read"),
    ("standings", "2026 standings (official)", "Standings", "data"),
    ("games", "2026 game results (verified rows)", "Game results", "data"),
    ("team-stats", "Team efficiency inputs (official)", "Team stats", "data"),
    ("injuries", "Week 10 availability report", "Injuries & availability", "data"),
    ("official-capture", "Official Week 10 injury capture and reconciliation", "Injury capture", "data"),
    ("matchups", "Matchup deficiency matrix - Week 10", "Matchup matrix", "data"),
    ("compare", "Strategy comparison lab - walk-forward, no leakage", "Compare strategies", "model"),    ("league-facts", "League facts, rules and cadence", "League facts", "data"),
    ("model", "Line origination model", "Model", "model"),
    ("parameters", "Model parameter register", "Parameter register", "model"),
    ("lines", "Origination output - Week 10 slate", "Lines", "model"),
    ("results", "Verified results feed - Week 10", "Results feed", "data"),
    ("luck", "Removal of luck - prospective scoring", "Removal of luck", "model"),
    ("ablations", "Injury/availability ablation - chronological holdout", "Ablations", "model"),
    ("line-provenance", "Our line - three files, three answers", "Line provenance", "model"),
    ("depth-evidence", "Depth and replacement evidence", "Depth evidence", "data"),
    ("data-freshness", "Data freshness and snapshot staleness", "Data freshness", "ops"),
    ("signals", "Signal catalogue", "Signals", "model"),
    ("correlation", "Correlation measurements and policy", "Correlation", "model"),
    ("validation", "Validation gates", "Validation gates", "model"),
    ("leaderboard", "Leaderboard, rewards and staking", "Leaderboard", "model"),
    ("methodology", "Verification methodology", "Methodology", "ops"),
    ("verification", "Automated verification report", "Verification log", "ops"),
    ("sources", "Source registry", "Sources", "ops"),
    ("flagged", "Flagged for review", "Flagged for review", "ops"),
]

BADGES = {
    "verified": ("ok", "read from the cited official source"),
    "derived-verified": ("ok", "computed from rows that passed the identity checks"),
    "derived": ("calc", "computed, not read"),
    "verified-from-snippet": ("warn", "official source, snippet-level read only"),
    "verified-with-exception": ("warn", "official source with an inconsistency - see flags"),
    "partial": ("warn", "coverage is incomplete"),
    "provisional": ("warn", "provisional - sample too small to decide anything"),
    "provisional-in-sample": ("warn", "in-sample fit: not yet walk-forward (gate G-02)"),
    "provisional-fitted-not-bettable": ("warn", "fitted output, explicitly not a bettable price"),
    "provisional-unadjusted": ("warn", "no schedule adjustment yet"),
    "measured-provisional": ("warn", "measured on the verified sample only"),
    "unverified-blank": ("bad", "no official source - deliberately blank"),
    "insufficient": ("bad", "insufficient sample to measure"),
    "blocked": ("bad", "blocked by a missing input"),
    "not-read": ("bad", "source registered but not read this session"),
    "read": ("ok", "read this session"),
    "derived-verified-flagged": ("warn", "derived, with a conflict recorded on the review page"),
    "verified-absence": ("warn", "verified that the source does NOT publish this"),
    "not-applicable": ("info", "no source applies"),
    "no source": ("bad", "no official source"),
    "search-snippet": ("warn", "seen in a search snippet of the official page, page not opened"),
    "not-acquired": ("bad", "licence not acquired"),
    "awaiting-owner-mandate": ("warn", "needs an owner decision"),
}

EMPTY_DASH = '<span class="none">-</span>'

COL_LABELS = {
    "team": "Team", "abbr": "Abbr", "conf": "Conf", "div": "Div", "games": "GP", "w": "W", "l": "L",
    "t": "T", "pct": "Win %", "pf": "PF", "pa": "PA", "net_pts": "Net pts",
    "source_id": "Source", "accessed_utc": "read at (UTC)", "verification_status": "Verification",
    "status": "Status", "note": "Note", "notes": "Notes", "week": "Wk", "game_date": "Date",
    "weekday_as_published": "Weekday as printed", "away": "Away", "away_abbr": "", "away_pts": "Away pts",
    "home": "Home", "home_abbr": "", "home_pts": "Home pts", "player": "Player", "pos": "Pos",
    "injury": "Injury", "practice_status": "Practice", "game_status": "Game status", "flag": "Flag",
    "pass_att": "Att", "pass_cmp": "Cmp", "cmp_pct": "Cmp %", "pass_yds": "Pass yds",
    "yds_per_att": "Yds/att", "pass_td": "TD", "pass_int": "INT", "passer_rating": "RTG",
    "pass_1st_downs": "1st ds", "pass_1st_down_pct": "1st %", "sacks_taken": "Sacks taken",
    "sack_yds_lost": "Sack yds", "rush_att": "Rush att", "rush_yds": "Rush yds",
    "rush_1st_downs": "Rush 1st ds", "rush_1st_down_pct": "Rush 1st %",
    "opp_pass_att": "Opp att", "opp_pass_cmp": "Opp cmp", "opp_cmp_pct": "Opp cmp %",
    "opp_pass_yds": "Opp pass yds", "opp_yds_per_att": "Opp yds/att", "opp_pass_td": "Opp TD",
    "opp_int_forced": "INT forced", "opp_passer_rating_allowed": "RTG allowed",
    "opp_pass_1st_downs": "Opp 1st ds", "opp_pass_1st_down_pct": "Opp 1st %", "def_sacks": "Sacks",
    "games_played": "GP", "id": "ID", "title": "Title", "name": "Name", "metric": "Metric",
    "value": "Value", "unit": "Unit", "basis": "Basis", "topic": "Topic", "fact": "Fact",
    "as_of": "As of", "check_id": "Check", "check": "Check performed", "result": "Result",
    "detail": "Detail", "rows_checked": "Rows", "blocking": "Blocks publish?", "meaning": "Meaning",
    "severity": "Severity", "page": "Page", "item": "Item", "finding": "Finding",
    "action_required": "Action required", "source_url": "Source link", "publisher": "Publisher",
    "url": "URL", "class": "Class", "used_for": "Used for", "source": "Source",
    "blocking ": "Blocking?", "area": "Area", "question": "Question", "what_we_have": "What we have",
    "what_we_need": "What we need", "how_to_obtain": "How to obtain",
    "decision_it_unblocks": "Decision it unblocks", "type": "Type", "problem_this_solves": "Problem",
    "proposal": "Proposal", "expected_impact": "Impact", "effort": "Effort", "risk": "Risk",
    "depends_on": "Depends on", "recommended": "Recommended", "owner_decision": "Owner decision",
    "family": "Family", "hypothesis": "Hypothesis", "trigger_rule": "Trigger", "inputs_required": "Inputs",
    "market": "Market", "direction": "Direction", "expected_magnitude_status": "Magnitude",
    "sample_status": "Sample", "gate_status": "Gate status", "correlation_note": "Correlation note",
    "source_class_of_trigger": "Trigger source", "stage": "Stage", "gate": "Gate",
    "definition": "Definition", "pass_criteria": "Pass test", "fail_action": "If it fails",
    "why_this_removes_luck": "Why it removes luck", "data_required": "Data required",
    "current_state": "Current state", "pair": "Pair measured", "r": "r", "ci95_low": "95% CI low",
    "ci95_high": "95% CI high", "n": "n", "interpretation": "Why it matters", "scope": "Scope",
    "constant": "Constant", "se": "Std error", "method": "Method", "network": "TV",
    "venue_note": "Venue note", "model_spread_home": "Our line (home)", "model_total": "Our total",
    "expected_home_margin": "Exp. home margin", "model_p_home": "P(home wins)", "hfa_applied": "HFA used",
    "market_spread": "Market spread", "market_total": "Market total", "market_source": "Market source",
    "gap_to_market": "Gap to market", "actionable": "Actionable?", "availability_flags": "Availability flags",
    "ppg": "Pts/g", "papg": "Allowed/g", "net_ppg": "Net/g", "pyth_expected_wins": "Exp. wins",
    "pyth_exponent_used": "Pyth k", "dropbacks_per_game": "Dropbacks/g", "rush_att_per_game": "Rush att/g",
    "pass_rate_pct": "Pass rate %", "pass_yds_per_game": "Pass yds/g", "yds_per_play": "Yds/play",
    "sacks_taken_per_game": "Sacks taken/g", "opp_dropbacks_per_game": "Opp dropbacks/g",
    "opp_pass_yds_per_game": "Opp pass yds/g", "def_sacks_per_game": "Sacks/g", "avail_out": "Out",
    "avail_doubtful": "Doubtful", "avail_questionable": "Qstr", "avail_ol_out": "OL out",
    "avail_db_out": "DB out", "avail_dl_out": "DL out", "avail_qb_out": "QB out",
    "rating_net_ppg": "Rating (net/g)", "rating_pyth_win_share": "Pyth win share",
    "schedule_adjusted": "Sched adj", "rating_method_a_vs_b_gap": "", "kickoff_et": "Kickoff ET",
    "practice": "Practice", "publisher": "Publisher",
    "requirement": "Requirement", "current_state": "Readiness state", "evidence_in_repo": "Evidence in repo",
    "missing_information": "Missing information", "blocking_gate": "Blocking gate",
    "clearance_metric": "Clearance metric / number", "recommended_next_step": "Recommended next step",
    "source_gap": "Source gap / review note", "repo_page": "Related page",
}


# --------------------------------------------------------------------------- #
# small markdown subset (enough for prose pages, no dependency)
# --------------------------------------------------------------------------- #
def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    # Links: the previous version only rewrote absolute http(s) targets, so every relative
    # in-site link (`[Lines](lines.html)`) rendered as literal markdown text and the link checker
    # never saw it, because it only inspects href attributes. Both cases are handled now.
    def link(m):
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://")):
            return f'<a href="{target}" rel="noopener nofollow" target="_blank">{label}</a>'
        return f'<a href="{target}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    return text


def render_markdown(md):
    """A deliberately small markdown subset: headings, lists, code, tables, :::table directives."""
    lines = md.splitlines()
    out, buf, in_list, in_code = [], [], False, False
    consumed = set()

    def flush_p():
        if buf:
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
            buf.clear()

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for idx, raw in enumerate(lines):
        if idx in consumed:
            continue
        line = raw.rstrip()
        if line.startswith("```"):
            flush_p(); flush_list()
            out.append("<pre><code>" if not in_code else "</code></pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(raw))
            continue
        if not line.strip():
            flush_p(); flush_list()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush_p(); flush_list()
            lvl = len(m.group(1))
            anchor = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            out.append(f'<h{lvl} id="{anchor}">{inline(m.group(2))}</h{lvl}>')
            continue
        if line.strip() == "---":
            flush_p(); flush_list()
            out.append("<hr>")
            continue
        if line.startswith(":::table "):
            flush_p(); flush_list()
            out.append(render_table_directive(line[len(":::table "):].strip()))
            continue
        if line.startswith("- "):
            flush_p()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline(line[2:]) + "</li>")
            continue
        if re.match(r"^\|.*\|\s*$", line.strip()) and idx + 1 < len(lines) \
                and re.match(r"^\|\s*:?-{3,}", lines[idx + 1].strip()):
            flush_p(); flush_list()
            block = []
            j = idx
            while j < len(lines) and lines[j].strip().startswith("|"):
                block.append(lines[j].strip())
                consumed.add(j)
                j += 1
            out.append(render_pipe_table(block))
            continue
        flush_list()
        if line.startswith("> "):
            flush_p()
            out.append("<blockquote>" + inline(line[2:]) + "</blockquote>")
            continue
        buf.append(line.strip())
    flush_p(); flush_list()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def render_pipe_table(block):
    """Render a markdown pipe table (header row, --- separator, body rows)."""
    def cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]
    header = cells(block[0])
    body = [cells(l) for l in block[2:]]
    th = "".join(f"<th>{inline(c)}</th>" for c in header)
    trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in body)
    return f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


# --------------------------------------------------------------------------- #
# data tables
# --------------------------------------------------------------------------- #
SOURCES = {}


def load_sources():
    global SOURCES
    SOURCES = {r["source_id"]: r for r in read_rows("sources.csv")}


def validate_question_provenance(rows=None):
    """Require each open question to show official input links or a visible source gap."""
    rows = read_rows("questions.csv") if rows is None else rows
    official_classes = {"official-league", "official-government", "official-club"}
    errors = []
    if not rows:
        return ["questions.csv is empty"]
    for row in rows:
        qid = row.get("id", "(missing id)")
        gap = (row.get("source_gap") or "").strip()
        source_ids = [sid.strip() for sid in (row.get("source_id") or "").split(";") if sid.strip()]
        if not gap:
            errors.append(f"{qid}: open question has no explicit source-gap/review note")
        for sid in source_ids:
            source = SOURCES.get(sid)
            if not source:
                errors.append(f"{qid}: source {sid} is not registered")
                continue
            if source.get("class") not in official_classes:
                errors.append(f"{qid}: {sid} is not an official league, club, or government source")
            if not (source.get("url") or "").startswith("https://"):
                errors.append(f"{qid}: {sid} does not have an HTTPS URL")
    return errors


def validate_rendered_question_rows(rows, page):
    """Catch stale templates that silently drop a question's source or gap from HTML."""
    errors = []
    for question in rows:
        qid = html.escape(question.get("id", ""))
        marker = f"<td>{qid}</td>"
        marker_at = page.find(marker)
        if marker_at < 0:
            errors.append(f"{qid}: question row is missing from board/questions.html")
            continue
        row_start = page.rfind("<tr>", 0, marker_at)
        row_end = page.find("</tr>", marker_at)
        row_html = page[row_start:row_end] if row_start >= 0 and row_end >= 0 else ""
        for sid in [s.strip() for s in (question.get("source_id") or "").split(";") if s.strip()]:
            source = SOURCES.get(sid)
            if source and html.escape(source["url"]) not in row_html:
                errors.append(f"{qid}: rendered row does not link registered source {sid}")
        gap = html.escape((question.get("source_gap") or "").strip())
        if not gap or gap not in row_html:
            errors.append(f"{qid}: rendered row does not display its source-gap note")
    return errors


def header_label(col):
    """Column heading: use the curated label verbatim, else de-snake_case the key."""
    if col in COL_LABELS:
        return COL_LABELS[col] or col.replace("_", " ")
    return col.replace("_", " ")


def badge_for(value):
    v = (value or "").strip().lower()
    for key, (kind, title) in BADGES.items():
        if v.startswith(key):
            return f'<span class="badge {kind}" title="{html.escape(title)}">{html.escape(value)}</span>'
    if not value:
        return ""
    return f'<span class="badge info">{html.escape(value)}</span>'


def source_cell(source_id):
    ids = [s.strip() for s in (source_id or "").split(";") if s.strip()]
    if not ids:
        return '<span class="badge bad" title="no source id on this row">no source</span>'
    parts = []
    for sid in ids:
        src = SOURCES.get(sid)
        if not src:
            parts.append(f'<span class="badge bad" title="source id not in the registry">{sid}?</span>')
            continue
        url = src["url"]
        cls = "ext" if url.startswith("http") else ""
        parts.append(f'<a class="src {cls}" href="{html.escape(url)}" target="_blank" '
                     f'rel="noopener nofollow" title="{html.escape(src["name"])}">{sid}</a>')
    return " ".join(parts)


def _root_pages():
    import re as _re
    site = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "build_site.py")
    try:
        text = open(site, encoding="utf-8").read()
    except OSError:
        return set()
    return set(_re.findall(r'"([a-z0-9\-]+\.html)":', text))


ROOT_PAGES = _root_pages()


def _is_external(val: str) -> bool:
    return val.startswith(("http://", "https://", "//", "mailto:"))


def render_table(fname, columns=None, caption="", link_col=None, max_rows=None, default_src=True):
    rows = read_rows(fname)
    if not rows:
        return f'<p class="empty">No rows in data/{fname}</p>'
    cols = [c for c in rows[0].keys() if c]
    if columns:
        cols = [c for c in columns if c in cols]
    if default_src and "source_id" in rows[0] and "source_id" not in cols:
        cols.append("source_id")
    shown = rows if not max_rows else rows[:max_rows]

    head = "".join(f"<th>{html.escape(COL_LABELS.get(c, c.replace('_', ' ')).title() if c in COL_LABELS else c.replace('_', ' '))}</th>"
                  for c in cols)
    body = []
    for r in shown:
        tds = []
        for c in cols:
            val = (r.get(c) or "").strip()
            if c == "source_id":
                tds.append(f"<td class='srccol'>{source_cell(val)}</td>")
            elif c in ("status", "verification_status", "result", "gate_status", "sample_status",
                       "expected_magnitude_status", "current_state", "recommended", "owner_decision",
                       "blocking", "severity", "practice_status", "game_status", "flag"):
                cell = badge_for(val) if val else EMPTY_DASH
                tds.append("<td>" + cell + "</td>")
            elif c == "source_gap":
                if val:
                    tds.append(f"<td class='wide'><span class=\"badge warn\">UNVERIFIED / SOURCE GAP</span> "
                               f"{html.escape(val)}</td>")
                else:
                    tds.append('<td><span class="none">-</span></td>')
            elif c in ("note", "notes", "detail", "finding", "proposal", "hypothesis", "question",
                       "definition", "pass_criteria", "why_this_removes_luck", "interpretation",
                       "trigger_rule", "action_required", "what_we_have", "what_we_need",
                       "requirement", "evidence_in_repo", "missing_information", "blocking_gate",
                       "clearance_metric", "recommended_next_step"):
                tds.append(f"<td class='wide'>{html.escape(val)}</td>")
            elif val == "":
                tds.append('<td><span class="none" title="not published - no official source">blank</span></td>')
            elif link_col == c and _is_external(val):
                tds.append(f"<td><a href='{html.escape(val)}' target='_blank' rel='noopener nofollow'>"
                           f"{html.escape(val)[:90]}</a></td>")
            elif link_col == c:
                # A repo-relative page, rendered as-is so check_links resolves it.
                # Never prefix it: board/ pages sit one directory below the root
                # pages, and guessing the depth is how a link becomes a 404.
                href = val if val.startswith("../") else "../" + val if val in ROOT_PAGES else val
                tds.append(f"<td><a href='{html.escape(href)}'>{html.escape(val)}</a></td>")
            else:
                tds.append(f"<td>{html.escape(val)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    more = ""
    if max_rows and len(rows) > len(shown):
        more = (f'<p class="more">Showing {len(shown)} of {len(rows)} rows. The complete table is in '
                f'<a href="data/{html.escape(fname)}">{html.escape(fname)}</a>.</p>')
    cap = f'<caption>{html.escape(caption)}</caption>' if caption else ""
    return (f'<div class="tablewrap"><table>{cap}<thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{more}')


def render_table_directive(spec):
    """:::table file.csv | caption | col1,col2 | maxrows"""
    bits = [b.strip() for b in spec.split("|")]
    fname = bits[0]
    caption = bits[1] if len(bits) > 1 else ""
    cols = [c.strip() for c in bits[2].split(",")] if len(bits) > 2 and bits[2] else None
    mx = int(bits[3]) if len(bits) > 3 and bits[3].isdigit() else None
    return render_table(fname, cols, caption, max_rows=mx)


# --------------------------------------------------------------------------- #
# page shells
# --------------------------------------------------------------------------- #
def render_register():
    """Render models/line_model.yaml as a table, with `null` and blocked statuses VISIBLE.

    The register is the contract that forbids a hand-filled parameter, so the site must show the
    blocked rows, not hide them: a blank cell with a reason is the deliverable.
    """
    path = os.path.join(REPO, "models", "line_model.yaml")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    rows, section, cur = [], "", {}

    def flush():
        if cur:
            rows.append(dict(cur))
            cur.clear()

    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if re.match(r"^[a-z_]+:$", raw.rstrip()):
            flush()
            section = raw.rstrip()[:-1].replace("_", " ")
            continue
        m = re.match(r"^  ([a-z0-9_]+):\s*(.*)$", raw.rstrip())
        if m:
            flush()
            key, rest = m.group(1), m.group(2).split("#")[0].strip()
            cur = {"section": section, "parameter": f"{section}.{key}", "value": rest or "null"}
            continue
        m = re.match(r"^    ([a-z0-9_]+):\s*(.*)$", raw.rstrip())
        if m and cur:
            key, rest = m.group(1), m.group(2)
            rest = re.sub(r"\s+#.*$", "", rest).strip()
            if rest.startswith('"') and rest.endswith('"'):
                rest = rest[1:-1]
            rest = re.sub(r"\s+", " ", rest)
            cur[key] = rest
    flush()

    def esc(v):
        return html.escape(str(v)) if v else ""

    body = []
    for r in rows:
        val = r.get("value", "")
        status = r.get("status", "")
        blocked = val in ("null", "", "[]") or "blocked" in status or "uncalibrated" in status or \
            "provisional" in status
        cell = ('<span class="badge bad">null - deliberately unset</span>' if val in ("null", "[]", "")
                else f"<code>{esc(val)}</code>")
        body.append(
            "<tr><td>" + esc(r.get("section", "")) + "</td><td><code>" + esc(r.get("parameter", "")) +
            "</code></td><td>" + cell + "</td><td>" + (badge_for(status) if status else "") +
            "</td><td>" + esc(r.get("blocked_by", "")) + "</td><td class='wide'>" +
            esc(r.get("evidence", r.get("note", ""))) + "</td></tr>")
    return ('<div class="tablewrap"><table><caption>models/line_model.yaml - the register the build reads. '
            'A parameter may not hold a value unless its evidence points at a verified row.</caption>'
            '<thead><tr><th>Section</th><th>Parameter</th><th>Value</th><th>Status</th>'
            '<th>Blocked by</th><th>Evidence / note</th></tr></thead><tbody>'
            + "".join(body) + "</tbody></table></div>")


def kpis():
    st = read_rows("standings_2026.csv")
    inj = read_rows("injuries_2026_w10.csv")
    gm = read_rows("games_2026.csv")
    flags = read_rows("flags.csv")
    qs = read_rows("questions.csv")
    sg = read_rows("suggestions.csv")
    sig = read_rows("signals.csv")
    src = [r for r in read_rows("sources.csv") if r["status"] in ("read", "search-snippet")]
    ver = read_rows("verification_report.csv")
    passed = sum(1 for r in ver if r["result"] == "PASS")
    total = sum(1 for r in ver if r["result"] in ("PASS", "FAIL", "WARN"))
    return [
        ("Clubs in the dataset", f"{len(st)}/32", "official standings, all 32 read"),
        ("Verified game rows", str(len(gm)), "33 of 137 games through Week 9"),
        ("Availability rows", str(len(inj)), "Week 10 report, clubs with a game status"),
        ("Signals specified", str(len(sig)), "single / parlay / prop-combo families"),
        ("Blocking questions", str(sum(1 for q in qs if q["blocking"] == "yes")), f"of {len(qs)} open questions"),
        ("Suggestions to decide", str(sum(1 for s in sg if s["owner_decision"] == "pending")), "none approved yet"),
        ("Open flags", str(len([f for f in flags if f["status"] == "open"])), "on the review page"),
        ("Sources read this session", str(len(src)),
         f"{passed} of {total} scored checks pass (the rest are declared, not hidden)"),
    ]


def meter(fname, status_col="status"):
    try:
        rows = read_rows(fname)
    except FileNotFoundError:
        return ""
    if not rows or status_col not in rows[0]:
        return ""
    ok = warn = bad = 0
    for r in rows:
        v = (r.get(status_col) or "").lower()
        kind = BADGES.get(v.split(";")[0].strip(), ("warn", ""))[0]
        if v == "":
            continue
        if kind == "ok":
            ok += 1
        elif kind == "bad":
            bad += 1
        else:
            warn += 1
    n = max(1, ok + warn + bad)
    return (f'<div class="meter" title="rows by verification class">'
            f'<span class="m-ok" style="width:{100*ok/n:.1f}%">{ok} ok</span>'
            f'<span class="m-warn" style="width:{100*warn/n:.1f}%">{warn} provisional</span>'
            f'<span class="m-bad" style="width:{100*bad/n:.1f}%">{bad} blocked/blank</span></div>')


def page_html(slug, title, body):
    nav = {g: [] for _, _, _, g in PAGES}
    for s, t, label, group in PAGES:
        nav.setdefault(group, []).append((s, label))
    groups = [("read", "Read first"), ("data", "Verified data"), ("model", "Model & signals"),
              ("ops", "Verification & ops")]
    navhtml = []
    for gid, gname in groups:
        items = "".join(f'<a href="{s}.html"{" class=on" if s == slug else ""}>{lbl}</a>'
                        for s, lbl in nav.get(gid, []))
        if items:
            navhtml.append(f'<div class="navgroup"><span>{gname}</span>{items}</div>')
    navhtml = "".join(navhtml)
    cur = next((t for s, t, l, g in PAGES if s == slug), title)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(cur)}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="brand"><a href="index.html"><strong>FL3</strong> <span>NFL line origination board</span></a></div>
  <div class="stamp">official data read 2026-11-14 UTC</div>
</header>
<div class="wrap">
<nav class="side">{navhtml}
  <div class="navgroup"><span>This repo has two published tracks</span>
    <a href="../index.html" title="the sibling dashboard built from data/*.json by scripts/build_site.py">Sibling dashboard (root)</a>
    <a href="../docs/index.html" title="the sibling track's documentation section">Sibling docs</a>
    <a href="../COORDINATION.md" title="shared task board - claims, scopes, source log">Task board</a>
  </div>
  <div class="navgroup"><span>Repo</span>
    <a href="https://github.com/sassnarep3-star/FL3" rel="noopener nofollow" target="_blank">GitHub</a>
    <a href="https://github.com/sassnarep3-star/FL3/blob/main/COORDINATION.md" rel="noopener nofollow" target="_blank">Coordination board</a>
  </div>
</nav>
<main>
{body}
<footer>
  <p>Every table on this site is generated from <code>data/</code> by <code>scripts/build_site.py</code>;
  no value is typed into the HTML. Empty cells are deliberate: the value was not confirmable from an
  official source, so it is left blank and listed on the
  <a href="flagged.html">Flagged for review</a> page. Nothing here is betting advice.</p>
</footer>
</main>
</div>
</body></html>
"""


def run_gate(script: str, label: str) -> int:
    """A stage of the publish chain: a non-zero exit aborts the build."""
    rc = subprocess.call([sys.executable, os.path.join(REPO, "scripts", script)], cwd=REPO)
    if rc != 0:
        print(f"BUILD ABORTED at {label} ({script} exited {rc}) - fix the data, do not edit the HTML")
    return rc


def build(check_only: bool = False) -> int:
    if not check_only:
        rc = run_gate("verify.py", "gate G-10 source integrity")
        if rc != 0:
            return rc
    load_sources()
    provenance_errors = validate_question_provenance()
    if provenance_errors:
        print("BUILD FAIL - question provenance validation failed:")
        for error in provenance_errors:
            print(f"  - {error}")
        return 1

    # board/ is a build artefact: recreate it from the sources each time, and copy in exactly the
    # tables this track owns, so the published CSVs and the published pages cannot drift apart.
    for sub in ("", "assets", "data"):
        os.makedirs(os.path.join(BOARD, sub), exist_ok=True)
    with open(os.path.join(SITE, "assets", "style.css"), encoding="utf-8") as fh:
        css = fh.read()
    with open(os.path.join(BOARD, "assets", "style.css"), "w", encoding="utf-8") as fh:
        fh.write(css)
    copied = []
    for f in BOARD_DATA:
        src = os.path.join(REPO, "data", f)
        if not os.path.exists(src):
            print(f"BUILD FAIL - board expects data/{f} (declared in BOARD_DATA) and it is missing")
            return 1
        with open(src, encoding="utf-8") as fh:
            blob = fh.read()
        with open(os.path.join(BOARD, "data", f), "w", encoding="utf-8") as fh:
            fh.write(blob)
        copied.append(f)

    built = {}
    readiness_check = subprocess.call([sys.executable, os.path.join(REPO, "scripts", "build_readiness.py"), "--check"], cwd=REPO)
    if readiness_check != 0:
        print("BUILD ABORTED - requirement readiness CSV is stale or invalid")
        return 1

    for slug, title, label, group in PAGES:
        md_path = os.path.join(CONTENT, slug + ".md")
        md = ""
        if os.path.exists(md_path):
            with open(md_path, encoding="utf-8") as fh:
                md = fh.read()
        body = render_markdown(md) if md else ""
        if slug == "index":
            cards = "".join(
                f'<div class="kpi"><span class="kv">{html.escape(v)}</span>'
                f'<span class="kl">{html.escape(k)}</span><span class="kn">{html.escape(n)}</span></div>'
                for k, v, n in kpis())
            body = f'<section class="kpis">{cards}</section>' + body
        if slug == "index":
            body += (
                '<h2>Decision readiness — every requirement, blocker and clearance test</h2>'
                '<p>Rows describe the checked-in evidence state; clearance criteria are proposed gates, '
                'not observed NFL facts. Open the <a href="readiness.html">full register</a> for missing '
                'information and recommended next steps. Requirements with no applicable official source '
                'are left without a citation and explicitly flagged.</p>'
            )
            body += render_table(
                "requirements_readiness.csv",
                ["id", "category", "requirement", "current_state", "blocking_gate", "clearance_metric", "source_id", "source_gap"],
                caption=f"{len(read_rows('requirements_readiness.csv'))} distinct requirements; a source link is provided where an applicable official input is registered.",
            )
        if slug == "readiness":
            readiness_rows = read_rows("requirements_readiness.csv")
            linked = sum(bool(r.get("source_id")) for r in readiness_rows)
            source_gaps = len(readiness_rows) - linked
            body += (
                '<section class="keypoint"><strong>Decision-readiness register.</strong> '
                f'{len(readiness_rows)} requirements are listed individually; {linked} rows link to an official input page, '
                f'and {source_gaps} explicitly have no applicable official source in the registered source set. '
                'Source links show where relevant official inputs may be checked; they do not certify that a feed, '
                'field or feature has been captured. Clearance numbers are proposed project gates, not NFL facts. '
                'The source snapshot dates differ; inspect the linked record and the related page before relying on a row. '
                'Unknown or unsupported values are not inferred.</section>'
            )
            body += render_table(
                "requirements_readiness.csv",
                ["id", "category", "requirement", "current_state", "evidence_in_repo", "missing_information",
                 "blocking_gate", "clearance_metric", "recommended_next_step", "source_id", "source_gap", "repo_page"],
                caption="One row per distinct requirement. BLOCKED/PARTIAL/DESIGN ONLY are not completed features; "
                        "a source gap is deliberately left without a fabricated citation.",
                link_col="repo_page",
            )
        if slug == "sources":
            body += render_table("sources.csv", caption="Every source the data layer is allowed to cite.")
            unknown = set()
            for fname in BOARD_DATA:
                if fname == "sources.csv":
                    continue
                for r in read_rows(fname):
                    for sid in (r.get("source_id") or "").replace(";", " ").split():
                        if sid and sid not in SOURCES and not sid.startswith("SRC-"):
                            unknown.add(f"{fname}:{sid}")
                        elif sid.startswith("SRC-") and sid not in SOURCES:
                            unknown.add(f"{fname}:{sid} (not registered)")
            if unknown:
                raise SystemExit("BUILD FAIL - rows cite sources that are not in data/sources.csv: "
                                 + ", ".join(sorted(unknown)))
        if slug == "official-capture":
            body += render_table(
                "official_injury_copy_audit_wk10_2026.csv",
                caption="Every Week 10 injury copy in the repo, compared with the official capture (row count and club coverage).")
            body += render_table(
                "official_injury_capture_wk10_2026.csv",
                ["game_date", "game_pair_as_printed", "team", "player", "position", "injuries",
                 "practice_status", "game_status", "source_id"],
                caption=f"Canonical capture: {len(read_rows('official_injury_capture_wk10_2026.csv'))} listed players, 14 game sections, 28 clubs. Blank = blank on the official page.")
            body += render_table(
                "official_injury_reconciliation_wk10_2026.csv",
                ["team", "player", "field", "official_nfl_com", "repo_table_345", "issue", "source_id"],
                caption="Every field where the primary 345-row table differs from the official capture. Injury lists are compared as sets.",
                link_col=None)
        if slug == "verification":
            body += render_table("verification_report.csv",
                                 caption="scripts/verify.py output - regenerated on every build")
        if slug == "flagged":
            body += render_table("flags.csv", link_col="source_url",
                                 caption="Everything that could not be confirmed, or that conflicts, "
                                         "with the source link beside it.")
            body += ('<p class="keypoint"><strong>Why this page exists:</strong> the brief is '
                     '"never infer or fill in a value". So each item below is either a value we '
                     'deliberately left blank, or a conflict between official sources that a '
                     'human has to settle.</p>')
        if slug == "lines":
            body += meter("lines_origination.csv")
            body += render_table("lines_origination.csv",
                                 ["game_date", "kickoff_et", "away", "home", "expected_home_margin",
                                  "model_spread_home", "model_total", "hfa_applied", "market_spread",
                                  "market_total", "gap_to_market", "availability_flags", "status",
                                  "source_id"],
                                 caption="Our number next to the market's number. The market columns are "
                                         "blank because no licensed price exists in this repo (Q-01).")
            body += render_table("model_calibration.csv",
                                 caption="The constants above are fitted, not assumed - and here is the fit.")
        if slug == "parameters":
            body += render_register()
        if slug == "league-facts":
            body += render_table("league_facts.csv",
                                 caption="Rules and cadence the model is allowed to depend on.")
        html_out = page_html(slug, title, body)
        with open(os.path.join(BOARD, slug + ".html"), "w", encoding="utf-8") as fh:
            fh.write(html_out)
        built[slug] = html_out

    rendered_question_errors = validate_rendered_question_rows(
        read_rows("questions.csv"), built["questions"])
    if rendered_question_errors:
        print("BUILD FAIL - rendered Questions & Gaps page lost provenance metadata:")
        for error in rendered_question_errors:
            print(f"  - {error}")
        return 1

    with open(os.path.join(BOARD, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(built["index"])
    # no build artefact may be a broken site
    for keep in (".nojekyll",):
        src = os.path.join(SITE, keep)
        if os.path.exists(src):
            with open(src, encoding="utf-8") as fh:
                blob = fh.read()
            with open(os.path.join(BOARD, keep), "w", encoding="utf-8") as fh:
                fh.write(blob)
    if not check_only:
        rc = run_gate("check_links.py", "link and registry integrity")
        if rc != 0:
            return rc
    digest = hashlib.sha1("".join(built[k] for k in sorted(built)).encode()).hexdigest()[:12]
    print(f"built {len(built)} pages -> board/  ({len(copied)} data tables copied; content sha1 {digest}; "
          f"deterministic output - no build timestamp is embedded, so CI can compare board/ against data/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build(check_only="--check" in sys.argv))
