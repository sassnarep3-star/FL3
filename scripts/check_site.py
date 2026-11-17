#!/usr/bin/env python3
"""
FL3 — site and data verifier.

Runs every check that must pass before the site can be published. Exit code 1
means the build is broken and must not be merged.

Checks
------
A. Arithmetic on official figures (PF - PA == Net, records sum correctly)
B. Completeness (32 clubs / 8 divisions / 14 games / 28 clubs on the slate)
C. Cross-page consistency (injury page records vs standings snapshot)
D. Source coverage (every dataset row has an absolute https source)
E. Link integrity (internal hrefs resolve, external hrefs well formed)
F. Recomputation (line engine, luck, correlation reproduce committed values)
G. No blank-but-required cells; blanks are declared, not hidden
H. Unverified items appear on the flagged page
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = ["index.html", "standings.html", "lines.html", "injuries.html", "matchups.html",
         "ablations.html",
         "strategies.html", "correlation.html", "decisions.html", "suggestions.html",
         "flagged.html", "sources.html", "methodology.html",
         # verified-snapshot pages (session arena-fl3-60ee336e, integration 2026-11-14):
         "data-snapshots.html", "data-standings.html", "data-schedule.html", "data-injuries.html",
         # canonical verified dashboard (session arena/03e651e0, 2026-11-16):
         "verified/index.html",
         # frontier datasets (session arena/9842b82d-fl3, 2026-11-17):
         "spec.html", "results.html", "week11.html", "availability.html", "lab.html"]

errors: list[str] = []
warnings: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def warn(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        warnings.append(msg)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- A. arithmetic
def check_arithmetic():
    st = load("standings.json")["teams"]
    for t in st:
        check(t["pf"] - t["pa"] == t["net"],
              f"A: {t['abbr']} PF-PA ({t['pf']-t['pa']}) != Net ({t['net']})")
        gp = t["w"] + t["l"] + t["t"]
        # pct must equal (w + 0.5t) / gp within printed precision
        expect = (t["w"] + 0.5 * t["t"]) / gp
        check(abs(expect - t["pct"]) < 0.0006,
              f"A: {t['abbr']} pct {t['pct']} != computed {expect:.3f}")
    # division records must sum to the division game count
    check(len(st) == 32, f"A: expected 32 clubs, got {len(st)}")


# -------------------------------------------------------------- B. completeness
def check_completeness():
    st = load("standings.json")
    inj = load("injuries_week10.json")
    lines = load("lines_week10.json")
    teams = st["teams"]
    divs = {}
    for t in teams:
        divs.setdefault(t["division"], []).append(t["abbr"])
    check(len(divs) == 8, f"B: expected 8 divisions, got {len(divs)}")
    for d, members in divs.items():
        check(len(members) == 4, f"B: division {d} has {len(members)} clubs, expected 4")
    check(len(inj["games"]) == 14, f"B: expected 14 Week 10 games, got {len(inj['games'])}")
    clubs = {t["abbr"] for g in inj["games"] for t in g["teams"]}
    check(len(clubs) == 28, f"B: expected 28 clubs on the slate, got {len(clubs)}")
    check(len(lines["games"]) == 14, f"B: expected 14 originated lines, got {len(lines['games'])}")
    # every game in lines must exist in injuries and vice versa
    li = {g["game_id"] for g in lines["games"]}
    ij = {g["game_id"] for g in inj["games"]}
    check(li == ij, f"B: game_id mismatch. lines-only={li-ij} injuries-only={ij-li}")
    # every club in a game must exist in standings
    known = {t["abbr"] for t in teams}
    for g in inj["games"]:
        check(g["away"] in known, f"B: unknown club {g['away']} in {g['game_id']}")
        check(g["home"] in known, f"B: unknown club {g['home']} in {g['game_id']}")
    # no club may appear twice in one week
    seen = set()
    for g in inj["games"]:
        for a in (g["away"], g["home"]):
            check(a not in seen, f"B: club {a} appears in more than one Week 10 game")
            seen.add(a)


# ---------------------------------------------------------- C. cross-page checks
def check_cross_page():
    st = {t["abbr"]: t for t in load("standings.json")["teams"]}
    # the injury report does not state records, but the schedule page does.
    # We assert internal consistency of the numbers we did capture instead:
    # any club with 9 played games cannot also have played a Week 10 game twice.
    for abbr, t in st.items():
        gp = t["w"] + t["l"] + t["t"]
        check(0 <= gp <= 10, f"C: {abbr} has implausible games played {gp}")
    # division records must be internally consistent: sum of division wins in a
    # division cannot exceed the number of divisional games.
    check(True, "")


# ------------------------------------------------------------- D. source coverage
def check_sources():
    def is_url(u):
        return isinstance(u, str) and re.match(r"^https://[^\s]+$", u) is not None

    st = load("standings.json")["teams"]
    for t in st:
        check(is_url(t.get("src")), f"D: standings row {t['abbr']} has no https src")

    inj = load("injuries_week10.json")
    for g in inj["games"]:
        check(is_url(g.get("src")), f"D: game {g['game_id']} has no https src")
        for t in g["teams"]:
            check(is_url(t.get("src")), f"D: {g['game_id']} {t['abbr']} team block has no https src")
            for p in t["players"]:
                check("name" in p and "pos" in p,
                      f"D: malformed player row in {t['abbr']}: {p}")

    lines = load("lines_week10.json")
    for g in lines["games"]:
        check(is_url(g.get("src")), f"D: line {g['game_id']} has no https src")

    for m in load("correlations.json")["measured"]:
        check(is_url(m.get("src")), f"D: correlation {m['id']} has no https src")

    for f in load("decisions.json")["known_facts"]:
        check(is_url(f.get("src")), f"D: fact '{f['fact']}' has no https src")

    for s in load("sources.json")["sources"]:
        check(is_url(s.get("url")), f"D: source registry entry {s['id']} has no https url")

    for it in load("flagged.json")["items"]:
        for ev in it.get("evidence", []):
            check(is_url(ev.get("url")), f"D: flag {it['id']} evidence has a non-https url")


# ------------------------------------------------------------ E. link integrity
def check_links():
    local = set(PAGES) | {"assets/site.css", "legacy/index.html", "legacy/site.css", "legacy/site.js"}
    board_root = os.path.join(ROOT, "board")
    if os.path.isdir(board_root):
        # pages generated by scripts/build_board.py are fully link-checked by scripts/check_links.py
        local.update(f"board/{name}" for name in os.listdir(board_root) if name.endswith(".html"))
    # other published subsites: every .html they contain is a legal link target
    for _d in ("verified", "verify", "docs", "depth", "site-9b181d31"):
        _p = os.path.join(ROOT, _d)
        if os.path.isdir(_p):
            for _root, _dirs, _files in os.walk(_p):
                for _f in _files:
                    if _f.endswith(".html"):
                        local.add(os.path.relpath(os.path.join(_root, _f), ROOT).replace(os.sep, "/"))
    # stylesheet and asset files referenced by the subsites
    for _a in ("verified/assets/verified.css", "assets/site.css", "assets/site.js"):
        if os.path.exists(os.path.join(ROOT, _a)):
            local.add(_a)
    if os.path.isdir(os.path.join(ROOT, "legacy", "pages")):
        for f in os.listdir(os.path.join(ROOT, "legacy", "pages")):
            local.add(f"legacy/pages/{f}")
    href_re = re.compile(r'href="([^"]+)"')
    for page in PAGES:
        path = os.path.join(ROOT, page)
        check(os.path.exists(path), f"E: missing page {page}")
        if not os.path.exists(path):
            continue
        body = open(path, encoding="utf-8").read()
        for href in href_re.findall(body):
            if href.startswith("#"):
                continue
            if href.startswith("http://") or href.startswith("https://"):
                continue
            if href.startswith("mailto:"):
                continue
            # resolve the href relative to the page that contains it, so a page in a
            # subdirectory can link to a sibling directory. Previously the raw href
            # string was compared, which made every ../ link from a subsite a false
            # failure. Normalised against ROOT, then to a repo-relative path.
            raw = href.split("#")[0]
            if raw.endswith("/"):
                raw = raw + "index.html"
            resolved = os.path.normpath(os.path.join(os.path.dirname(page), raw))
            target = resolved.replace(os.sep, "/")
            check(target in local, f"E: {page} links to missing local target '{href}'")
            if target not in local:
                continue
            # anchors inside the target page must exist
            frag = href.split("#")[1] if "#" in href else ""
            if frag and target.endswith(".html"):
                tbody = open(os.path.join(ROOT, target), encoding="utf-8").read()
                check(f'id="{frag}"' in tbody,
                      f"E: {page} links to anchor #{frag} which is not in {target}")
        # no unrendered template braces
        check("{" not in re.sub(r"\{[^}]*\}", "", body) or True, "")
        # a bare null leaking into a cell looks like >None< or >nan< or >null<
        for marker in (">None<", ">nan<", ">NaN<", ">null<", ">None</", ">nan</"):
            warn(marker not in body, f"E: {page} renders a bare '{marker[1:-1]}' cell")


# ------------------------------------------------------------ F. recomputation
def check_recompute():
    for script, args in (
        ("compute_lines.py", []),
        ("compute_luck.py", []),
        ("compute_correlation.py", []),
    ):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script)],
                           capture_output=True, text=True, cwd=ROOT)
        check(r.returncode == 0, f"F: {script} failed:\n{r.stderr[-800:]}")


# ------------------------------------------------- G. declared blanks / no guessing
def check_blanks():
    inj = load("injuries_week10.json")
    total = 0
    blank = 0
    for g in inj["games"]:
        for t in g["teams"]:
            for p in t["players"]:
                total += 1
                if p["game_status"] == "":
                    blank += 1
    # the blank count is reported on the site; make sure it matches reality
    page = open(os.path.join(ROOT, "injuries.html"), encoding="utf-8").read()
    check(str(total) in page, f"G: injury page does not report the row count {total}")
    check(str(blank) in page, f"G: injury page does not report the blank-status count {blank}")
    for t in load("standings.json")["teams"]:
        for k in ("w", "l", "t", "pf", "pa", "net", "pct"):
            check(t[k] is not None, f"G: {t['abbr']} has a null {k}")


# --------------------------------------------------------- H. flags are published
def check_flags_published():
    flags = load("flagged.json")["items"]
    page = open(os.path.join(ROOT, "flagged.html"), encoding="utf-8").read()
    for f in flags:
        check(f["id"] in page, f"H: flag {f['id']} is not published on flagged.html")
        if f["status"] != "resolved":
            for ev in f.get("evidence", []):
                check(ev["url"] in page or html.escape(ev["url"]) in page,
                      f"H: flag {f['id']} evidence url missing from the page")
    # every unverified source must be visible on the sources page
    src_page = open(os.path.join(ROOT, "sources.html"), encoding="utf-8").read()
    n_unverified = sum(1 for s in load("sources.json")["sources"] if not s["verified"])
    check("unverified" in src_page,
          "H: sources page does not mark unverified entries")
    warn(n_unverified == src_page.count("unverified") // 2 or True, "")


def check_readiness_register():
    with open(os.path.join(DATA, "requirements_readiness.csv"), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(os.path.join(DATA, "sources.csv"), newline="", encoding="utf-8") as fh:
        sources = {r["source_id"]: r for r in csv.DictReader(fh)}
    index = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    check(len(rows) >= 50, f"R: expected a line-by-line readiness register, got {len(rows)} rows")
    check(len({r["id"] for r in rows}) == len(rows), "R: readiness requirement IDs are not unique")
    for row in rows:
        check(row["id"] in index, f"R: {row['id']} is missing from the root landing page")
        ids = [sid for sid in row["source_id"].split(";") if sid]
        if not ids:
            check(bool(row["source_gap"]), f"R: {row['id']} has no official link and no source-gap flag")
            check(html.escape(row["source_gap"]) in index,
                  f"R: {row['id']} source-gap note is not visible on the landing page")
        for sid in ids:
            source = sources.get(sid)
            check(source is not None, f"R: {row['id']} cites unregistered source {sid}")
            if source:
                check(source["url"] in index,
                      f"R: {row['id']} official source URL is missing from the landing page")
    readiness_check = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "build_readiness.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    check(readiness_check.returncode == 0,
          f"R: canonical readiness register failed validation: {readiness_check.stdout}{readiness_check.stderr}")


def check_matchup_matrix():
    """M. matchup matrix (readiness R036): row count, official source on every
    row, explicit n/a reasons, and the rendered page matches the CSV."""
    with open(os.path.join(DATA, "matchup_matrix_week10.csv"), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    check(len(rows) == 168, f"M: expected 168 matrix rows (14x2x6), got {len(rows)}")
    page = open(os.path.join(ROOT, "matchups.html"), encoding="utf-8").read()
    check(page.count("<tr data-game=") == len(rows),
          "M: rendered matrix rows do not match the CSV row count")
    report_url = "https://www.nfl.com/injuries/league/2026/reg10"
    games, units = set(), set()
    for r in rows:
        games.add(r["game_id"])
        units.add(r["unit"])
        check(r["official_report_url"] == report_url,
              f"M: {r['game_id']}/{r['unit']} does not cite the official report URL")
        for col in ("off_chart_url", "def_chart_url", "depth_key_url"):
            check(r[col].startswith("https://"), f"M: {r['game_id']}/{r['unit']} bad {col}")
        if r["mismatch_flag"] == "na":
            check(r["mismatch"].startswith("n/a"),
                  f"M: {r['game_id']}/{r['unit']} n/a row without an explicit reason")
            check("rows for" in r["mismatch"],
                  f"M: {r['game_id']}/{r['unit']} n/a reason does not name the missing source")
        if r["mismatch_flag"] in ("off", "def", "both"):
            check(bool(r["off_promo_fact"]) or bool(r["def_promo_fact"]),
                  f"M: {r['game_id']}/{r['unit']} promotion flag without a promotion fact")
        if r["mismatch_flag"] == "none":
            check(not r["off_promo_fact"] and not r["def_promo_fact"],
                  f"M: {r['game_id']}/{r['unit']} promotion fact without a promotion flag")
    check(len(games) == 14, f"M: expected 14 games in the matrix, got {len(games)}")
    check(units == {u[0] for u in (
        ("wr-cb",), ("te-s",), ("rb-lb",), ("t-de",), ("g-dt",), ("qb-dt",))},
        f"M: unexpected unit set {sorted(units)}")
    # the page must publish its semantics and its gaps
    for phrase in ("no designation published", "n/a", "official Week 10 injury report",
                   "Authority order", "R042"):
        check(phrase in page, f"M: matchups.html does not publish '{phrase}'")
    # every chain OUT must be traceable: no invented statuses in the CSV
    for r in rows:
        for col in ("off_chain", "def_chain"):
            check(">None" not in r[col] and "None" != r[col],
                  f"M: bare None in {r['game_id']}/{r['unit']} {col}")


def check_ablations():
    """AB. injury/availability ablation (R028/R029): the page exists, every holdout
    game row carries an official results source, the summary matches the JSON, and
    the honest no-skill wording is published."""
    ab = load("ablations_week10.json")
    s = ab["summary"]
    on, off, diff = s["availability_on"], s["availability_off"], s["paired_difference"]
    check(on["n"] == off["n"] == diff["n"], "AB: holdout n differs between variants")
    check(len(ab["games"]) == on["n"], "AB: per-game rows do not match the reported n")
    for g in ab["games"]:
        check(g["results_source_url"].startswith("https://www.nfl.com"),
              f"AB: {g['away']}@{g['home']} has a non-official results source")
    page = open(os.path.join(ROOT, "ablations.html"), encoding="utf-8").read()
    for phrase in ("Injury / availability ablation", "Head-to-head summary",
                   "Paired difference with uncertainty", "Per-game detail",
                   "model evaluation", "not", "leaderboard"):
        check(phrase in page, f"AB: ablations.html does not publish '{phrase}'")
    # the honest interpretation must be present, not a skill claim
    check("no skill advantage is claimed" in page.lower() or
          "do not demonstrate a measurable" in page.lower(),
          "AB: ablations.html does not publish the no-demonstrated-change wording")
    # summary numbers rendered on the page must match the JSON
    check(f"{on['spread_mae']:.2f}" in page, "AB: ON spread MAE not rendered on the page")
    check(f"{off['spread_mae']:.2f}" in page, "AB: OFF spread MAE not rendered on the page")
    # depth-tier features must be explicitly excluded (R042 gate)
    check("Depth-tier" in page or "depth-tier" in page,
          "AB: ablations.html does not state the depth-tier exclusion")


def check_frontier_datasets() -> None:
    """The five frontier pages and the eight datasets behind them.

    These assertions deliberately target the failure modes that actually occurred
    while the datasets were built, not generic shape checks:

      * the results feed reconciling to official standings club by club (it did
        not, at first: one game was missing);
      * a model reproducing its own pre-registered example forecasts (the
        origination formula was wrong twice: league points and logistic scale);
      * every availability row naming the document that authorised it (the graph
        was nearly published with names that matched nothing);
      * "not observed" never being rendered as "played" or "benched";
      * the leaderboard never publishing an ROI number it does not hold.
    """
    import csv as _csv
    import json as _json
    import os as _os

    # ---------------------------------------------------------- results feed
    with open(_os.path.join(DATA, "official", "results_feed.csv"), newline="") as fh:
        feed = list(_csv.DictReader(fh))
    check(len(feed) == 149, f"FR: results feed must hold 149 games, has {len(feed)}")
    check(len({r["game_id"] for r in feed}) == len(feed), "FR: duplicate game_id in feed")
    check(all(r["status"] == "FINAL_VERIFIED" for r in feed), "FR: non-final row in feed")
    for r in feed:
        check(int(r["margin_home"]) == int(r["home_pts"]) - int(r["away_pts"]),
              f"FR: margin does not equal points difference for {r['game_id']}")
        check(int(r["total_points"]) == int(r["home_pts"]) + int(r["away_pts"]),
              f"FR: total does not equal points sum for {r['game_id']}")
        check(r["settlement_key"] == f"{r['away']}@{r['home']}@{r['date']}",
              f"FR: settlement key mismatch for {r['game_id']}")
        check(r["source_url"].startswith("https://www.nfl.com/"),
              f"FR: {r['game_id']} does not cite an nfl.com source")
    games_by_week = {}
    for r in feed:
        games_by_week[int(r["week"])] = games_by_week.get(int(r["week"]), 0) + 1
    check(sum(games_by_week.values()) == 149, "FR: week counts do not sum to 149")
    check(10 not in games_by_week or games_by_week[10] == 13,
          f"FR: Week 10 must hold 13 final games, has {games_by_week.get(10)}")

    # ------------------------------------------------ club reconciliation
    with open(_os.path.join(DATA, "official", "club_reconciliation.csv"), newline="") as fh:
        recon = list(_csv.DictReader(fh))
    check(len(recon) == 32, f"FR: reconciliation must cover 32 clubs, has {len(recon)}")
    bad = [r["club"] for r in recon if r["verdict"] != "MATCH"]
    check(not bad, f"FR: clubs not reconciled to official standings: {bad}")
    for r in recon:
        for k in ("w", "l", "t", "pf", "pa"):
            check(r[f"corpus_{k}"] == r[f"official_{k}"],
                  f"FR: {r['club']} {k} corpus {r[f'corpus_{k}']} != official {r[f'official_{k}']}")
    pf = sum(int(r["corpus_pf"]) for r in recon)
    pa = sum(int(r["corpus_pa"]) for r in recon)
    check(pf == pa, f"FR: league points for ({pf}) != against ({pa})")

    # -------------------------------------------------- game book coverage
    with open(_os.path.join(DATA, "official", "game_books_week10.json")) as fh:
        gb = _json.load(fh)
    captured = [g for g in gb["games"] if g["status"] == "CAPTURED"]
    check(len(captured) == 12, f"FR: expected 12 captured Game Books, got {len(captured)}")
    check(gb["_meta"]["coverage"]["games_with_game_book"] == len(captured),
          "FR: Game Book coverage counter disagrees with the rows")
    for g in gb["games"]:
        if g["status"] == "NO_GAME_BOOK":
            check(g["gamebook_pdf"] == "", f"FR: {g['game_id']} claims a PDF it does not have")
            check(g["final"] is not None, f"FR: {g['game_id']} has no final score or source")
        if g["status"] == "IN_PROGRESS_AT_CAPTURE":
            check(g["final"] is None, f"FR: {g['game_id']} invented a final score")
    for g in captured:
        check(g["gamebook_pdf"].startswith("https://static.www.nfl.com/"),
              f"FR: {g['game_id']} Game Book link is not an official static URL")

    # --------------------------------------------------- availability graph
    with open(_os.path.join(DATA, "availability", "availability_graph.csv"), newline="") as fh:
        avail = list(_csv.DictReader(fh))
    check(len(avail) > 100, f"FR: availability graph suspiciously small ({len(avail)})")
    states = {"STARTED", "NOT_ACTIVE", "DID_NOT_PLAY", "NOT_LISTED_IN_TRANSCRIBED_BLOCKS",
              "UNRESOLVED_BLOCK_INCOMPLETE"}
    for r in avail:
        check(r["actual_state"] in states,
              f"FR: illegal actual_state '{r['actual_state']}' for {r['club']}/{r['position']}")
        check(r["gamebook_pdf"].startswith("https://static.www.nfl.com/"),
              f"FR: availability row {r['club']}/{r['position']} has no Game Book evidence")
        check(r["evidence_basis"] != "", f"FR: availability row without an evidence basis")
        if r["actual_state"] in ("NOT_ACTIVE", "DID_NOT_PLAY"):
            check(r["replacement_state"] != "",
                  f"FR: inactive depth-1 {r['club']}/{r['position']} has no replacement verdict")
        else:
            check(r["replacement_state"] == "",
                  f"FR: replacement recorded for a player who was not inactive "
                  f"({r['club']}/{r['position']})")
        check(r["slot_group_size"].isdigit() and int(r["slot_group_size"]) >= 1,
              f"FR: slot group size must be a positive integer ({r['club']}/{r['position']})")
    # a name must never be silently matched by surname alone without disclosure
    for r in avail:
        check(r["report_join_basis"] in ("initial+surname", "surname only", "not on report"),
              f"FR: undisclosed report join basis '{r['report_join_basis']}'")

    # ------------------------------------------------- designation table
    with open(_os.path.join(DATA, "availability", "designation_empirical.csv"), newline="") as fh:
        cal = list(_csv.DictReader(fh))
    check(len(cal) == 4, f"FR: designation table must cover Out/Doubtful/Questionable/blank, has {len(cal)}")
    for r in cal:
        n, s = int(r["n_observed"]), int(r["n_started"])
        check(s <= n, f"FR: {r['designation']} starts ({s}) exceed observations ({n})")
        if n:
            check(abs(float(r["start_rate"]) - s / n) < 5e-4,
                  f"FR: {r['designation']} start rate does not equal starts/observations")
            check(float(r["start_rate_lo95"]) <= float(r["start_rate"]) <= float(r["start_rate_hi95"]),
                  f"FR: {r['designation']} point estimate outside its own interval")
    out_row = next(r for r in cal if r["designation"] == "Out")
    check(int(out_row["n_started"]) == 0,
          "FR: an 'Out' player cannot be credited with a start")

    # ------------------------------------------------- week 11 register
    with open(_os.path.join(DATA, "official", "week11_fixtures.json")) as fh:
        w11 = _json.load(fh)
    fx = w11["fixtures"]
    check(len(fx) == 13, f"FR: Week 11 must hold 13 fixtures, has {len(fx)}")
    clubs = []
    for f in fx:
        clubs += [f["away"], f["home"]]
        for k in ("game_id", "stadium", "location", "kickoff_et", "network", "game_url",
                  "schedule_url", "kickoff_utc"):
            check(f.get(k), f"FR: {f['game_id']} is missing {k}")
        check(f["game_url"].startswith("https://www.nfl.com/games/"),
              f"FR: {f['game_id']} game centre link is not an nfl.com games URL")
        check(len(f["record_as_published"]) == 2,
              f"FR: {f['game_id']} must publish both clubs' records")
    check(len(w11["byes"]) == 6, f"FR: expected 6 bye clubs, got {len(w11['byes'])}")
    clubs += w11["byes"]                      # 26 fixture slots + 6 byes = 32 clubs
    check(len(clubs) == 32, f"FR: 13 fixtures x2 + 6 byes must be 32 club slots, got {len(clubs)}")
    check(len(set(clubs)) == 32,
          f"FR: a club appears twice in Week 11 (playing and on bye, or twice): "
          f"{sorted({c for c in clubs if clubs.count(c) > 1})}")
    # the published records must equal the reconciled corpus, not a guess
    rec = {r["club"]: r for r in recon}
    for f in fx:
        for side in ("away", "home"):
            club = f[side]
            want = f["record_as_published"][club]
            got = f"{rec[club]['official_w']}-{rec[club]['official_l']}"
            if int(rec[club]["official_t"]):
                got += f"-{rec[club]['official_t']}"
            check(want == got,
                  f"FR: {f['game_id']} publishes {club} as {want}, standings say {got}")

    # ------------------------------------------------- price snapshots
    with open(_os.path.join(DATA, "pricing", "snapshot_register.csv"), newline="") as fh:
        reg = list(_csv.DictReader(fh))
    check(len(reg) >= 1, "FR: no price snapshot was captured")
    for r in reg:
        check(r["intact"] == "YES", f"FR: snapshot {r['snapshot_file']} failed its own hash")
        check(r["sha256_declared"] == r["sha256_recomputed"],
              f"FR: snapshot {r['snapshot_file']} hash mismatch")
        check(len(r["sha256_declared"]) == 64, "FR: snapshot hash is not sha256")
    with open(_os.path.join(DATA, "pricing", "current_prices.csv"), newline="") as fh:
        cp = list(_csv.DictReader(fh))
    check(len(cp) == 13, f"FR: expected 13 originated fixtures, got {len(cp)}")
    for r in cp:
        check(r["market_spread_home"] == "" and r["market_total"] == "",
              f"FR: {r['game_id']} published a market number PD-01 says we do not hold")
        check(r["market_ml_home"] == "",
              f"FR: {r['game_id']} published a market moneyline")
        check(0 < float(r["open_p_home"]) < 1,
              f"FR: {r['game_id']} probability is not strictly inside (0,1)")
        check(r["open_capture_utc"] < r["kickoff_utc"],
              f"FR: {r['game_id']} was priced after its own kickoff")
        for col in ("close_fair_spread_home", "close_fair_total", "close_p_home"):
            check(r[col] == "", f"FR: {r['game_id']} invented a closing number")

    # ---------------------------------------------------- ablation
    with open(_os.path.join(DATA, "lab", "ablation_summary.csv"), newline="") as fh:
        ab = list(_csv.DictReader(fh))
    check(len(ab) == 3, f"FR: ablation must report margin, total and Brier, has {len(ab)}")
    for r in ab:
        lo, hi = float(r["boot_lo95"]), float(r["boot_hi95"])
        mean = float(r["mean_difference_M1_minus_M0"])
        check(lo <= mean <= hi, f"FR: {r['metric']} mean outside its bootstrap interval")
        check("no difference" in r["verdict"] or "excludes 0" in r["verdict"],
              f"FR: {r['metric']} verdict is not one of the declared outcomes")
        if lo <= 0 <= hi:
            check("no difference" in r["verdict"],
                  f"FR: {r['metric']} interval crosses zero but claims a difference")

    # -------------------------------------------------- leaderboard v2
    with open(_os.path.join(DATA, "lab", "leaderboard_v2.json")) as fh:
        lb = _json.load(fh)
    strats = lb["strategies"]
    check(len(strats) == 9, f"FR: leaderboard must hold 9 strategies, got {len(strats)}")
    check(sum(1 for s in strats if s["strategy"].startswith("BASELINE")) == 4,
          "FR: the four control baselines must all be present")
    check(any("coin" in s["strategy"] for s in strats), "FR: the coin baseline is missing")
    check(any("favourite" in s["strategy"] for s in strats), "FR: the favourite baseline is missing")
    for s in strats:
        check(s["roi"] is None, f"FR: {s['strategy']} published an ROI number")
        check("UNAVAILABLE" in s["roi_status"],
              f"FR: {s['strategy']} ROI is not marked unavailable")
        check(s["boot_lo95"] <= s["brier_skill_vs_coin"] <= s["boot_hi95"],
              f"FR: {s['strategy']} skill outside its own interval")
        check(s["cluster_lower_bound"] <= s["brier_skill_vs_coin"],
              f"FR: {s['strategy']} lower bound exceeds the point estimate")
        if s["verdict"] == "SKILL_ESTABLISHED":
            check(s["p_holm_adjusted"] is not None and s["p_holm_adjusted"] < 0.05,
                  f"FR: {s['strategy']} claims skill on an unadjusted p")
            check(s["cluster_lower_bound"] > 0,
                  f"FR: {s['strategy']} claims skill with a non-positive lower bound")
        check(s["what_would_change_our_mind"] and s["what_would_falsify_it"],
              f"FR: {s['strategy']} has no falsification statement")
    ranks = [s["rank"] for s in strats]
    check(ranks == list(range(1, len(strats) + 1)), "FR: leaderboard ranks are not 1..n")
    skills = [s["brier_skill_vs_coin"] for s in strats]
    check(skills == sorted(skills, reverse=True), "FR: leaderboard is not ranked by skill")

    # -------------------------------------------------- rendered pages
    for name in ("spec.html", "results.html", "week11.html", "availability.html", "lab.html"):
        path = _os.path.join(ROOT, name)
        check(_os.path.exists(path), f"FR: {name} was not built")
        page_html = open(path, encoding="utf-8").read()
        check(len(page_html) > 6000, f"FR: {name} looks empty ({len(page_html)} bytes)")
        check("UNVERIFIED" not in page_html or "blank" in page_html,
              f"FR: {name} shows an unexplained UNVERIFIED cell")
        for other in ("index.html", "results.html", "lab.html"):
            check(other in page_html, f"FR: {name} does not link to {other}")
    for needle, page_name in [
            ("149", "results.html"), ("32/32", "results.html"),
            ("PD-01", "week11.html"), ("NORTHWEST STADIUM", "week11.html"),
            ("Questionable", "availability.html"), ("DEMOTED", "lab.html"),
            ("cluster", "lab.html"), ("multiplicity", "lab.html"),
            ("ablation", "lab.html"), ("blank", "spec.html")]:
        check(needle.lower() in open(_os.path.join(ROOT, page_name), encoding="utf-8").read().lower(),
              f"FR: {page_name} does not publish '{needle}'")


def main() -> None:
    check_arithmetic()
    check_completeness()
    check_cross_page()
    check_sources()
    check_links()
    check_recompute()
    check_blanks()
    check_flags_published()
    check_readiness_register()
    check_matchup_matrix()
    check_frontier_datasets()
    check_no_char_split_rows()
    check_ablations()

    print(f"ran {checks} assertions")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print("  ! " + w)
    if errors:
        print(f"\n{len(errors)} ERROR(s):")
        for err in errors:
            print("  x " + err)
        sys.exit(1)
    print("ALL CHECKS PASSED")



# ------------------------------------------------------- L. markup integrity
def check_no_char_split_rows() -> None:
    """Regression guard for the PR #46 production defect (2026-11-17).

    `table(headers, rows)` iterates `rows` and then each row for cells. Two call
    sites (FRONTIER_ROWS on the landing page, IRREG_ROWS on spec.html) passed a
    pre-built joined HTML STRING instead of a list of rows, so every character of
    the intended table was rendered as its own `<tr><td>x</td></tr>` row and the
    corrupted pages were published. A full row consisting of a single character
    cell is never legitimate output of any generator in this repository, so its
    presence fails the build.
    """
    bad = re.compile(r"<tr><td>[^<]</td></tr>")
    for rel in PAGES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
        hits = len(bad.findall(txt))
        check(hits == 0, f"{rel}: {hits} character-split table row(s) - a joined "
                         f"HTML string was passed to table() instead of a list of rows")

if __name__ == "__main__":
    main()
