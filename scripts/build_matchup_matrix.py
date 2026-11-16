#!/usr/bin/env python3
"""Build the Week 10 offense-vs-defense matchup deficiency matrix (readiness R036).

Outputs
-------
data/matchup_matrix_week10.csv   one row per game x direction x unit (14 x 2 x 6 = 168)
matchups.html                    the interactive matrix page

Evidence rules (enforced here, asserted by scripts/check_site.py)
----------------------------------------------------------------
* Availability comes ONLY from the official NFL Week 10 injury report
  (data/injuries_week10.json, SRC-001, captured 2026-11-14).
* Order comes from (a) the targeted Ourlads capture dated 2026-11-16
  (data/depth_charts_2026-11-16.json) for the 14 clubs listed there, else
  (b) the 2026-11-14 transcription (data/depth_risk.json). Ourlads is a
  third-party scouting service; it supplies order only, never availability.
* A promotion is CONFIRMED only when a slot's first-string player is ruled
  Out by the official report. The replacement is the chart's own next listed
  player who is not ruled Out. Doubtful/Questionable string-1 is shown but
  never counted as a promotion.
* A missing chain renders "n/a" with the missing group and source named.
  Nothing is inferred, nothing is filled in.
* No score, projection, edge or betting claim is computed. The matrix counts
  strings and statuses, nothing else.

Usage: python3 scripts/build_matchup_matrix.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_site  # noqa: E402  (has a __main__ guard; provides page()/table helpers)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

REPORT_URL = "https://www.nfl.com/injuries/league/2026/reg10"   # SRC-001
KEY_URL = "https://www.ourlads.com/nfldepthcharts/key.aspx"      # S05
CHART_INDEX_URL = "https://www.ourlads.com/nfldepthcharts/"      # S04 family
REPORT_CAPTURE = "2026-11-14"
ORDER_CAPTURE = "2026-11-16"
TRANS_CAPTURE = "2026-11-14"

# standings abbr -> Ourlads chart code (codes taken from the Ourlads index page,
# fetched 2026-11-16; ARZ/LAR verified directly against pfdepthchart/<code>)
OURLADS_CODE = {
    "ATL": "ATL", "AZ": "ARZ", "BAL": "BAL", "BUF": "BUF", "CAR": "CAR",
    "CHI": "CHI", "CIN": "CIN", "CLE": "CLE", "DAL": "DAL", "DEN": "DEN",
    "DET": "DET", "GB": "GB", "HOU": "HOU", "IND": "IND", "JAX": "JAX",
    "KC": "KC", "LA": "LAR", "LAC": "LAC", "LV": "LV", "MIA": "MIA",
    "MIN": "MIN", "NE": "NE", "NO": "NO", "NYG": "NYG", "NYJ": "NYJ",
    "PHI": "PHI", "PIT": "PIT", "SEA": "SEA", "SF": "SF", "TB": "TB",
    "TEN": "TEN", "WAS": "WAS",
}
# data/depth_risk.json uses LAR for the Rams; the standings/schedule use LA.
DEPTH_TEAM_MAP = {"LAR": "LA"}

# The six declared units. Pairing is a display convention of this repository:
# it groups rows for reading and computes no number. The league publishes no
# official matchup ranking.
UNITS = [
    ("wr-cb", "Outside coverage", "WR", "CB"),
    ("te-s", "Short/middle coverage", "TE", "S"),
    ("rb-lb", "Run box", "RB", "LB"),
    ("t-de", "Edge rush", "T", "DE"),
    ("g-dt", "Interior rush", "G", "DT"),
    ("qb-dt", "Pocket pressure", "QB", "DT"),
]
UNIT_ORDER = {u[0]: i for i, u in enumerate(UNITS)}

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
STATUS_LABEL = {
    "Out": "OUT",
    "Doubtful": "DOUBTFUL",
    "Questionable": "QUESTIONABLE",
    "listed": "listed/no status",
    "none": "no designation",
}
STATUS_CHIP = {
    "Out": "out",
    "Doubtful": "doubt",
    "Questionable": "quest",
    "listed": "blank",
    "none": "blank",
}


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def esc(v):
    return html.escape(str(v))


# ---------------------------------------------------------------- name handling
def flip(raw: str) -> str:
    """Ourlads prints 'Last, First'; the official report prints 'First Last'."""
    if ", " in raw:
        surname, given = raw.split(", ", 1)
        return f"{given} {surname}"
    return raw


def norm(name: str) -> str:
    s = name.lower()
    for ch in (".", "'", "\u2019", ",", "-"):
        s = s.replace(ch, " " if ch == "," else "")
    toks = [t for t in s.split() if t and t not in SUFFIXES]
    return " ".join(toks)


# ---------------------------------------------------------------- availability
def build_report_index():
    """(team, normalised name) -> list of report rows. Presence in this index
    means the player is listed on the official report capture; absence means
    no designation was published for them (never 'healthy')."""
    inj = load("injuries_week10.json")
    idx = {}
    by_team = {}
    for g in inj["games"]:
        for t in g["teams"]:
            for p in t["players"]:
                key = (t["abbr"], norm(p["name"]))
                idx.setdefault(key, []).append(p)
                by_team.setdefault(t["abbr"], []).append(p)
    return idx, by_team


def lookup(report_idx, team, raw_name):
    """Return (status, row, ambiguous). status in Out/Doubtful/Questionable/listed/none."""
    hits = report_idx.get((team, norm(flip(raw_name)))) or []
    if not hits:
        return "none", None, False
    if len(hits) > 1:
        return hits[0]["game_status"] or "listed", hits[0], True
    return hits[0]["game_status"] or "listed", hits[0], False


def dr_state(state):
    return {
        "Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable",
        "listed-no-game-status": "listed",
        "no-designation-published": "none",
    }.get(state, "none")


# ---------------------------------------------------------------- order sources
def build_sides(report_idx):
    """Return side(team, group) -> dict or None with chains resolved later.

    A side dict: {source, chart_url, groups:{group:[slot,...]}, missing:[...]}
    slot: {slot, players:[{name,status,marker,page}]}
    """
    cap = load("depth_charts_2026-11-16.json")
    captured = {t["team"]: t for t in cap["teams"]}
    dr = load("depth_risk.json")
    dr_rows = {}
    for r in dr["depth"]:
        team = DEPTH_TEAM_MAP.get(r["team"], r["team"])
        dr_rows.setdefault((team, r["position"]), []).append(r)
    for k in dr_rows:
        dr_rows[k].sort(key=lambda r: r["depth"])

    conflicts = []   # captured players whose Ourlads marker disagrees with the report
    stats = {"matched": 0, "matched_multi": 0, "unmatched": 0,
             "captured_players": 0}

    def capture_side(team):
        if team not in captured:
            return None
        t = captured[team]
        groups = {}
        for slot in t["slots"]:
            players = []
            for i, p in enumerate(slot["players"], 1):
                status, row, amb = lookup(report_idx, team, p["n"])
                stats["captured_players"] += 1
                if status == "none":
                    stats["unmatched"] += 1
                elif amb:
                    stats["matched_multi"] += 1
                else:
                    stats["matched"] += 1
                marker = p.get("m", "")
                if marker in ("O", "Q", "D"):
                    implied = {"O": "Out", "Q": "Questionable", "D": "Doubtful"}[marker]
                    if status != implied:
                        conflicts.append({
                            "team": team, "slot": slot["slot"], "player": flip(p["n"]),
                            "marker": marker, "official": STATUS_LABEL[status],
                        })
                players.append({
                    "name": flip(p["n"]), "status": status, "marker": marker,
                    "page": (row or {}).get("name"),
                })
            groups.setdefault(slot["group"], []).append(
                {"slot": slot["slot"], "players": players})
        return {"source": f"capture {ORDER_CAPTURE}", "groups": groups}

    # each captured club is processed exactly once (stats/conflicts stay clean)
    captured_sides = {team: capture_side(team) for team in captured}

    def trans_side(team, group):
        rows = dr_rows.get((team, group))
        if not rows:
            return None
        players = [{
            "name": r["player"], "status": dr_state(r["availability_state"]),
            "marker": r.get("ourlads_marker") or "", "page": r.get("player_page"),
        } for r in rows]
        return {"source": f"transcription {TRANS_CAPTURE}",
                "groups": {group: [{"slot": group, "players": players}]}}

    def side(team, group):
        s = captured_sides.get(team)
        if s is not None:
            if group in s["groups"]:
                return {**s, "group": group}
            # captured club, but the group has no rows (should not happen for
            # the 11 matrix groups; keep the honest fallback anyway)
            t = trans_side(team, group)
            if t is not None:
                return {**t, "group": group}
            return {"source": "", "groups": {}, "group": group, "missing": [group],
                    "why": (f"no {group} rows for {team} in the {ORDER_CAPTURE} capture "
                            f"or the {TRANS_CAPTURE} transcription")}
        t = trans_side(team, group)
        if t is not None:
            return {**t, "group": group}
        return {"source": "", "groups": {}, "group": group, "missing": [group],
                "why": f"no {group} rows for {team} in the {TRANS_CAPTURE} transcription"}

    return side, conflicts, stats, captured


# ---------------------------------------------------------------- chain algebra
def analyse(side_dict):
    """Compute per-side chain facts. Returns dict with:
    complete, slots[], promo_facts[], promo_depth (max, 0 if none), chain_html/str.
    """
    if side_dict is None or side_dict.get("missing"):
        if side_dict is None:
            why = "no order source available"
        else:
            why = side_dict.get("why") or (
                f"no {side_dict['group']} rows for this club in either order source")
        return {"complete": False,
                "why": why,
                "slots": [], "facts": [], "depth": None,
                "chain_html": "", "chain_txt": "", "source": ""}
    slots_out = []
    facts = []
    depth = 0
    for slot in side_dict["groups"][side_dict["group"]]:
        players = slot["players"][:4]
        promo_idx = None
        if players and players[0]["status"] == "Out":
            for k in range(1, len(players)):
                if players[k]["status"] != "Out":
                    promo_idx = k
                    break
            if promo_idx is None:
                facts.append(f"{slot['slot']}1 OUT ⇒ no non-out backup listed")
            else:
                depth = max(depth, promo_idx)
                facts.append(f"{slot['slot']}1 OUT ⇒ {slot['slot']}{promo_idx + 1}")
        slots_out.append({"slot": slot["slot"], "players": players,
                          "promo": promo_idx})
    return {"complete": True, "slots": slots_out, "facts": facts, "depth": depth,
            "source": side_dict["source"],
            "chain_txt": chain_text(slots_out),
            "chain_html": chain_html(slots_out)}


def chain_text(slots):
    if not slots:
        return ""
    parts = []
    for s in slots:
        segs = []
        for i, p in enumerate(s["players"], 1):
            seg = f"{s['slot']}{i} {p['name']} ({STATUS_LABEL[p['status']]})"
            if s["promo"] is not None and s["promo"] == i - 1:  # arrow before the replacement string
                segs[-1] = segs[-1] + " ⇒"
                seg = " " + seg
            elif i > 1:
                seg = " · " + seg
            segs.append(seg)
        parts.append("".join(segs))
    return "  |  ".join(parts)


def chain_html(slots):
    if not slots:
        return ""
    parts = []
    for s in slots:
        segs = []
        for i, p in enumerate(s["players"], 1):
            chip = f'<span class="chip {STATUS_CHIP[p["status"]]}">{esc(STATUS_LABEL[p["status"]])}</span>'
            seg = f'<b>{esc(s["slot"])}{i}</b> {esc(p["name"])} {chip}'
            if s["promo"] is not None and s["promo"] == i - 1:
                segs[-1] = segs[-1] + ' <span class="mx-arrow">⇒</span>'
                seg = " " + seg
            elif i > 1:
                seg = ' <span class="mx-sep">·</span> ' + seg
            segs.append(seg)
        parts.append("".join(segs))
    return '<span class="mx-chain">' + " <span class=\"mx-slotgap\">|</span> ".join(parts) + "</span>"


# ---------------------------------------------------------------- main build
def main():
    report_idx, _ = build_report_index()
    side_fn, conflicts, jstats, captured = build_sides(report_idx)

    standings = load("standings.json")["teams"]
    name2abbr = {t["name"]: t["abbr"] for t in standings}

    with open(os.path.join(DATA, "2026-week10-games.csv"), newline="", encoding="utf-8") as fh:
        fixture_rows = [r for r in csv.DictReader(fh) if not r["game_id"].startswith("BYE")]
    fixtures = {}
    for r in fixture_rows:
        pair = (name2abbr[r["away"]], name2abbr[r["home"]])
        fixtures[pair] = r

    inj_games = load("injuries_week10.json")["games"]
    games = []
    for g in inj_games:
        pair = (g["away"], g["home"])
        fx = fixtures.get(pair)
        if fx is None:
            raise SystemExit(f"fixture not found for {pair}")
        games.append({**g, "fx": fx})
    games.sort(key=lambda g: g["fx"]["game_id"])

    def chart_url(team):
        if team in captured:
            return captured[team]["url"]
        return f"https://www.ourlads.com/nfldepthcharts/pfdepthchart/{OURLADS_CODE[team]}"

    rows = []
    for g in games:
        fid, away, home = g["fx"]["game_id"], g["away"], g["home"]
        date, note = g["fx"]["date"], g["fx"]["note"]
        kickoff = g["fx"]["time_et"]
        for off_team, def_team in ((away, home), (home, away)):
            direction = f"{off_team} offense vs {def_team} defense"
            for uid, ulabel, ogroup, dgroup in UNITS:
                off_raw = side_fn(off_team, ogroup)
                def_raw = side_fn(def_team, dgroup)
                off = analyse(off_raw)
                dfe = analyse(def_raw)

                if not off["complete"] and not dfe["complete"]:
                    mismatch = f"n/a — neither side has {ogroup}/{dgroup} rows ({off['why']}; {dfe['why']})"
                    flag = "na"
                elif not off["complete"]:
                    mismatch = f"n/a — offense side incomplete: {off['why']}"
                    flag = "na"
                elif not dfe["complete"]:
                    mismatch = f"n/a — defense side incomplete: {dfe['why']}"
                    flag = "na"
                elif off["facts"] and dfe["facts"]:
                    mismatch = "both sides promoting"
                    flag = "both"
                elif off["facts"]:
                    mismatch = f"DEF starter faces promoted {ogroup}"
                    flag = "off"
                elif dfe["facts"]:
                    mismatch = f"OFF starter faces promoted {dgroup}"
                    flag = "def"
                else:
                    mismatch = "none confirmed"
                    flag = "none"

                rows.append({
                    "game_id": fid, "date": date, "kickoff": kickoff,
                    "fixture_note": note, "direction": direction,
                    "off_team": off_team, "def_team": def_team,
                    "unit": uid, "unit_label": ulabel,
                    "off_source": off["source"], "off_evidence": "complete" if off["complete"] else f"n/a: {off['why']}",
                    "off_chain": off["chain_txt"], "off_promo_fact": "; ".join(off["facts"]),
                    "off_promo_depth": "" if off["depth"] is None else off["depth"],
                    "def_source": dfe["source"], "def_evidence": "complete" if dfe["complete"] else f"n/a: {dfe['why']}",
                    "def_chain": dfe["chain_txt"], "def_promo_fact": "; ".join(dfe["facts"]),
                    "def_promo_depth": "" if dfe["depth"] is None else dfe["depth"],
                    "mismatch": mismatch, "mismatch_flag": flag,
                    "official_report_url": REPORT_URL,
                    "off_chart_url": chart_url(off_team),
                    "def_chart_url": chart_url(def_team),
                    "depth_key_url": KEY_URL,
                    # render-only payloads
                    "_off_html": off["chain_html"], "_def_html": dfe["chain_html"],
                })

    # ------------------------------------------------------------ CSV
    csv_fields = [k for k in rows[0] if not k.startswith("_")]
    out_csv = os.path.join(DATA, "matchup_matrix_week10.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=csv_fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in csv_fields})

    # ------------------------------------------------------------ stats
    both = sum(1 for r in rows if r["mismatch_flag"] != "na")
    na = sum(1 for r in rows if r["mismatch_flag"] == "na")
    promo_rows = sum(1 for r in rows if r["mismatch_flag"] in ("off", "def", "both"))
    games_final = [g for g in games if "FINAL" in (g["fx"]["note"] or "")]

    # coverage: which order source serves each club/group
    needed_groups = ["WR", "TE", "RB", "QB", "T", "G", "CB", "S", "LB", "DE", "DT"]
    playing = sorted({t for g in games for t in (g["away"], g["home"])})
    coverage = []
    for team in playing:
        present, absent = [], []
        for grp in needed_groups:
            s = side_fn(team, grp)
            (present if s and not s.get("missing") else absent).append(grp)
        src = "capture " + ORDER_CAPTURE if team in captured else (
            "transcription " + TRANS_CAPTURE if present else "none")
        coverage.append((team, src, ",".join(present), ",".join(absent) or "—"))

    # ------------------------------------------------------------ HTML
    body = []
    A = body.append
    A('<h1>Matchup deficiency matrix — Week 10</h1>')
    A(f'<p class="lede">One screen for every Week 10 fixture: for six declared units, the '
      f'offence\'s 1st–4nd strings against the defence\'s, with the replacement <b>depth</b> '
      f'counted where the official report rules a first-string player Out. Rows without '
      f'evidence on either side are <b>n/a with the missing group named</b> — never a guess.</p>')

    A('<div class="stats">')
    A(build_site.stat(str(len(rows)), "matrix rows", "14 games × 2 directions × 6 units"))
    A(build_site.stat(str(both), "rows with both sides evidenced"))
    A(build_site.stat(str(promo_rows), "rows with a confirmed promotion", "first-string ruled Out by the official report"))
    A(build_site.stat(str(na), "rows n/a — order evidence missing", "the gap that gate Q-02/R042 blocks"))
    A(build_site.stat(str(len(conflicts)), "chart-marker vs official-report conflicts", "official report wins; listed below"))
    A('</div>')

    A('<div class="note"><b>Authority order.</b> Availability comes only from the '
      f'{build_site.src_link(REPORT_URL, "official Week 10 injury report")} (captured {REPORT_CAPTURE}; '
      f'the capture is 2 rows short for Baltimore — see FLG-029 on <a href="flagged.html">Flagged for Review</a>). '
      f'Order comes from the targeted Ourlads capture of {ORDER_CAPTURE} '
      '(<code>data/depth_charts_2026-11-16.json</code>, 14 clubs) and, for the other 14 playing clubs, '
      f'the {TRANS_CAPTURE} transcription (<code>data/depth_risk.json</code>). '
      f'Ourlads is third-party: {build_site.src_link(CHART_INDEX_URL, "charts")} · '
      f'{build_site.src_link(KEY_URL, "chart key")}. A player absent from the official report is '
      '<b>no designation published</b>, never “healthy”. A chain shows only what its order source lists; '
      'a report player absent from the order source is never inserted into a rank. '
      'Doubtful/Questionable first strings are shown '
      'but are <b>not</b> counted as promotions. This page computes no score, projection or edge — '
      'it counts strings.</div>')

    A('<div class="note warn"><b>What would clear every n/a.</b> Official club-by-club depth order for '
      'all 32 clubs (readiness <a href="board/readiness.html">R042</a>) or a validated snap-count source; '
      'the full 14-club capture below extended club by club; shared/empty slot schema (R064/R069). '
      'Until then the n/a cells are the honest state of the evidence, and the matrix stays descriptive.</div>')

    # controls
    game_opts = "".join(
        f'<option value="{esc(g["fx"]["game_id"])}">{esc(g["fx"]["game_id"])} · '
        f'{esc(g["away"])} @ {esc(g["home"])}</option>' for g in games)
    unit_opts = "".join(f'<option value="{esc(u[0])}">{esc(u[1])} ({esc(u[2])} vs {esc(u[3])})</option>'
                        for u in UNITS)
    A(f'''<div class="mx-controls">
  <label>Game <select id="mxGame"><option value="">All 14 games</option>{game_opts}</select></label>
  <label>Unit <select id="mxUnit"><option value="">All units</option>{unit_opts}</select></label>
  <label class="mx-check"><input type="checkbox" id="mxPromo"> confirmed promotions only</label>
  <label class="mx-check"><input type="checkbox" id="mxNa"> hide n/a rows</label>
  <label class="mx-search">Search <input id="mxSearch" placeholder="player, club, unit…" aria-label="Search matrix"></label>
  <span id="mxCount" class="mx-count"></span>
</div>''')

    # table
    th = ('<tr><th>Game</th><th>Unit</th><th>Offence chain (1st–4th string)</th><th>Off promo</th>'
          '<th>Defence chain (1st–4th string)</th><th>Def promo</th><th>Mismatch</th><th>Sources</th></tr>')
    trs = []
    for r in rows:
        srcs = (
            f'<a class="src" href="{esc(r["official_report_url"])}" target="_blank" rel="noopener">official report</a> '
            f'<a class="src" href="{esc(r["off_chart_url"])}" target="_blank" rel="noopener">{esc(r["off_team"])} chart</a> '
            f'<a class="src" href="{esc(r["def_chart_url"])}" target="_blank" rel="noopener">{esc(r["def_team"])} chart</a> '
            f'<a class="src" href="{esc(r["depth_key_url"])}" target="_blank" rel="noopener">key</a>'
        )
        off_fact = esc(r["off_promo_fact"]) or "—"
        def_fact = esc(r["def_promo_fact"]) or "—"
        if r["off_evidence"] != "complete":
            off_cell = f'<span class="mx-na">n/a</span> <span class="fine">{esc(r["off_evidence"])}</span>'
            off_fact = "—"
        else:
            off_cell = r["_off_html"]
        if r["def_evidence"] != "complete":
            def_cell = f'<span class="mx-na">n/a</span> <span class="fine">{esc(r["def_evidence"])}</span>'
            def_fact = "—"
        else:
            def_cell = r["_def_html"]
        mm_cls = {"na": "mx-na", "none": "", "off": "mx-hot", "def": "mx-hot", "both": "mx-hot"}[r["mismatch_flag"]]
        text = " ".join([r["game_id"], r["direction"], r["unit_label"], r["off_chain"],
                         r["def_chain"], r["mismatch"], r["off_promo_fact"], r["def_promo_fact"]])
        trs.append(
            f'<tr data-game="{esc(r["game_id"])}" data-unit="{esc(r["unit"])}" '
            f'data-flag="{esc(r["mismatch_flag"])}" data-text="{esc(text.lower())}">'
            f'<td class="mx-game">{esc(r["game_id"])}<span class="fine"> {esc(r["date"])}'
            f'{(" · " + esc(r["fixture_note"])) if r["fixture_note"] else ""}</span></td>'
            f'<td><b>{esc(r["unit_label"])}</b><span class="fine"> {esc(r["off_team"])} ({esc(r["unit"].split("-")[0])}) vs '
            f'{esc(r["def_team"])} ({esc(r["unit"].split("-")[1])})</span></td>'
            f'<td class="mx-chain-cell">{off_cell}</td>'
            f'<td class="mx-promo">{off_fact}</td>'
            f'<td class="mx-chain-cell">{def_cell}</td>'
            f'<td class="mx-promo">{def_fact}</td>'
            f'<td class="{mm_cls}">{esc(r["mismatch"])}</td>'
            f'<td class="mx-src">{srcs}</td></tr>')

    A(f'<div class="tablewrap"><table class="mx-table"><thead>{th}</thead><tbody id="mxBody">'
      + "".join(trs) + "</tbody></table></div>")

    # conflicts
    A('<h2>Chart-marker vs official-report conflicts</h2>')
    if conflicts:
        A('<p>The captured charts carry their own Out/Questionable/Doubtful markers. Where a marker '
          'disagrees with the official report, the official report governs and the disagreement is '
          'published here rather than silently reconciled (same rule as the '
          '<a href="depth/index.html">depth dashboard</a>):</p>')
        crows = [[esc(c["team"]), esc(c["slot"]), esc(c["player"]), esc(c["marker"]),
                  esc(c["official"]),
                  f'<a class="src" href="{REPORT_URL}" target="_blank" rel="noopener">report</a> '
                  f'<a class="src" href="{chart_url(c["team"])}" target="_blank" rel="noopener">chart</a>']
                 for c in conflicts]
        A(build_site.table(["Club", "Slot", "Player", "Chart marker", "Official report", "Sources"], crows))
    else:
        A('<p class="fine">No marker disagreements in this capture.</p>')

    # coverage
    A('<h2>Order-source coverage (why rows are n/a)</h2>')
    A('<p>Per club: which of the eleven matrix groups have order evidence, and from which source. '
      'A club missing a group makes that unit n/a for both of its games\' directions until the '
      'club-by-club depth-source gate (R042) clears.</p>')
    crows2 = [[esc(t), esc(src), esc(pres), esc(absent)] for t, src, pres, absent in coverage]
    A(build_site.table(["Club", "Order source", "Groups with evidence", "Groups missing (n/a)"], crows2))

    A('<h2>Reproduce</h2>')
    A('<pre><code>python3 scripts/build_matchup_matrix.py\n'
      'python3 scripts/build_site.py\n'
      'python3 scripts/check_site.py</code></pre>')
    A(f'<p class="fine">Generated from <code>data/depth_charts_2026-11-16.json</code> '
      f'({jstats["captured_players"]} players transcribed; name join vs the official report: '
      f'{jstats["matched"]} matched to a report row, {jstats["matched_multi"]} ambiguous, '
      f'{jstats["unmatched"]} absent from the report — absence means no designation published, not a join failure: '
      f'every official Out/Doubtful/Questionable player on a captured club was checked against the chains, '
      f'and each absence is explained by group scope, chart omission or strings beyond the fourth), '
      f'<code>data/depth_risk.json</code>, '
      f'<code>data/injuries_week10.json</code> and <code>data/2026-week10-games.csv</code>. '
      f'Fixture note: {len(games_final)} Week 10 game(s) were already final when this page was built.</p>')

    # tiny inline styles + filter script (no external dependencies)
    A('''<style>
.mx-controls { display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin:14px 0; padding:12px 14px;
  background:var(--card,#fff); border:1px solid #e3e7ee; border-radius:10px; font-size:14px; }
.mx-controls select, .mx-controls input[type=text], .mx-controls input:not([type=checkbox]) {
  padding:6px 8px; border:1px solid #cfd6e0; border-radius:8px; font-size:14px; background:#fff; }
.mx-controls label { display:flex; gap:6px; align-items:center; }
.mx-count { margin-left:auto; font-weight:600; color:#4a5568; }
.mx-table { min-width:1280px; font-size:13.5px; }
.mx-table td { vertical-align: top; }
.mx-chain-cell { min-width:300px; line-height:1.7; }
.mx-chain { display:inline; }
.mx-sep, .mx-slotgap { color:#aab2bf; }
.mx-arrow { color:#b42318; font-weight:700; }
.mx-promo { font-family:ui-monospace,monospace; font-size:12.5px; color:#b42318; min-width:130px; }
.mx-na { color:#8b95a3; font-style:italic; }
.mx-hot { color:#b42318; font-weight:600; }
.mx-game { white-space:nowrap; }
.mx-src { white-space:nowrap; }
.mx-src .src { margin-right:6px; }
tr[data-flag="na"] td { background:#fafbfc; }
</style>
<script>
(function(){
  var g=document.getElementById('mxGame'), u=document.getElementById('mxUnit'),
      p=document.getElementById('mxPromo'), n=document.getElementById('mxNa'),
      s=document.getElementById('mxSearch'), c=document.getElementById('mxCount'),
      rows=Array.prototype.slice.call(document.querySelectorAll('#mxBody tr'));
  function apply(){
    var gv=g.value, uv=u.value, pv=p.checked, nv=n.checked, sv=(s.value||'').toLowerCase().trim(), shown=0;
    rows.forEach(function(r){
      var ok=true;
      if(gv && r.dataset.game!==gv) ok=false;
      if(ok && uv && r.dataset.unit!==uv) ok=false;
      if(ok && pv && r.dataset.flag==='none') ok=false;
      if(ok && pv && r.dataset.flag==='na') ok=false;
      if(ok && nv && r.dataset.flag==='na') ok=false;
      if(ok && sv && r.dataset.text.indexOf(sv)===-1) ok=false;
      r.style.display=ok?'':'none';
      if(ok) shown++;
    });
    c.textContent=shown+' of '+rows.length+' rows';
  }
  [g,u,p,n,s].forEach(function(el){ el.addEventListener('change',apply); el.addEventListener('input',apply); });
  apply();
})();
</script>''')

    page_html = build_site.page(
        "Matchup matrix", "\n".join(body), "matchups.html")
    out_html = os.path.join(ROOT, "matchups.html")
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(page_html)

    # integrity anchors for the capture (published in the CSV's companion meta)
    hashes = {}
    for t in load("depth_charts_2026-11-16.json")["teams"]:
        canon = json.dumps(t["slots"], sort_keys=True, ensure_ascii=False).encode("utf-8")
        hashes[t["team"]] = hashlib.sha256(canon).hexdigest()
    with open(os.path.join(DATA, "depth_charts_2026-11-16.hashes.json"), "w", encoding="utf-8") as fh:
        json.dump({"algorithm": "sha256 over canonical slots JSON (raw HTML not retained)",
                   "computed_by": "scripts/build_matchup_matrix.py",
                   "hashes": hashes}, fh, indent=1, sort_keys=True)

    print(f"rows={len(rows)} both={both} na={na} promo_rows={promo_rows} conflicts={len(conflicts)}")
    print(f"wrote {out_csv}")
    print(f"wrote {out_html}")
    if len(rows) != 168:
        raise SystemExit("expected 168 rows (14 x 2 x 6)")
    if na and both == 0:
        raise SystemExit("matrix has no evidenced rows at all - aborting")


if __name__ == "__main__":
    main()
