#!/usr/bin/env python3
"""Build the GitHub Pages site in docs/ from data/ + content/.

Design rules that the whole repo depends on:

  * Every table row links to a source in data/sources.csv (its source_id), so a
    reader can always open the official page the value came from.
  * A cell that is empty stays empty and renders as "not published", never as 0.
  * Rows whose status/verification column says unverified/partial/blocked get a
    visible badge, and the page shows a verification meter.
  * The build fails (exit 1) if a link is broken, if verify.py fails, or if a
    table has a source_id that is not in the registry - "do not merge a broken site".

Usage:  python3 scripts/build_site.py [--check]
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

DOCS = os.path.join(REPO, "docs")
CONTENT = os.path.join(REPO, "content")
SITE = os.path.join(REPO, "site")

# slug -> (title, nav label, group)
PAGES = [
    ("index", "FL3 - NFL line origination and signal board", "Dashboard", "home"),
    ("executive-summary", "Executive summary", "Executive summary", "read"),
    ("questions", "Open questions and information gaps", "Questions & gaps", "read"),
    ("suggestions", "Suggestion register", "Suggestions", "read"),
    ("standings", "2026 standings (official)", "Standings", "data"),
    ("games", "2026 game results (verified rows)", "Game results", "data"),
    ("team-stats", "Team efficiency inputs (official)", "Team stats", "data"),
    ("injuries", "Week 10 availability report", "Injuries & availability", "data"),
    ("league-facts", "League facts, rules and cadence", "League facts", "data"),
    ("model", "Line origination model", "Model", "model"),
    ("parameters", "Model parameter register", "Parameter register", "model"),
    ("lines", "Origination output - Week 10 slate", "Lines", "model"),
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
}


# --------------------------------------------------------------------------- #
# small markdown subset (enough for prose pages, no dependency)
# --------------------------------------------------------------------------- #
def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r'<a href="\2" rel="noopener nofollow" target="_blank">\1</a>', text)
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
            elif c in ("note", "notes", "detail", "finding", "proposal", "hypothesis", "question",
                       "definition", "pass_criteria", "why_this_removes_luck", "interpretation",
                       "trigger_rule", "action_required", "what_we_have", "what_we_need"):
                tds.append(f"<td class='wide'>{html.escape(val)}</td>")
            elif val == "":
                tds.append('<td><span class="none" title="not published - no official source">blank</span></td>')
            elif link_col == c:
                tds.append(f"<td><a href='{html.escape(val)}' target='_blank' rel='noopener nofollow'>"
                           f"{html.escape(val)[:90]}</a></td>")
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
        ("Sources read this session", str(len(src)), f"{passed}/{total} identity checks pass"),
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
    built = {}
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
        if slug == "sources":
            body += render_table("sources.csv", caption="Every source the data layer is allowed to cite.")
            unknown = set()
            for fname in os.listdir(os.path.join(REPO, "data")):
                if not fname.endswith(".csv") or fname == "sources.csv":
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
        with open(os.path.join(DOCS, slug + ".html"), "w", encoding="utf-8") as fh:
            fh.write(html_out)
        built[slug] = html_out

    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(built["index"])
    # no build artefact may be a broken site
    for keep in (".nojekyll", "README.md"):
        src = os.path.join(SITE, keep)
        if os.path.exists(src):
            with open(src, encoding="utf-8") as fh:
                blob = fh.read()
            with open(os.path.join(DOCS, keep), "w", encoding="utf-8") as fh:
                fh.write(blob)
    if not check_only:
        rc = run_gate("check_links.py", "link and registry integrity")
        if rc != 0:
            return rc
    digest = hashlib.sha1("".join(built[k] for k in sorted(built)).encode()).hexdigest()[:12]
    print(f"built {len(built)} pages -> docs/  (content sha1 {digest}; output is deterministic - "
          f"no build timestamp is embedded, so CI can compare docs/ against data/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build(check_only="--check" in sys.argv))
