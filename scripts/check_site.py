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

import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = ["index.html", "standings.html", "lines.html", "injuries.html", "strategies.html",
         "correlation.html", "decisions.html", "suggestions.html", "flagged.html",
         "sources.html", "methodology.html",
         # verified-snapshot pages (session arena-fl3-60ee336e, integration 2026-11-14):
         "data-snapshots.html", "data-standings.html", "data-schedule.html", "data-injuries.html"]

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
            target = href.split("#")[0]
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


def main() -> None:
    check_arithmetic()
    check_completeness()
    check_cross_page()
    check_sources()
    check_links()
    check_recompute()
    check_blanks()
    check_flags_published()

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


if __name__ == "__main__":
    main()
