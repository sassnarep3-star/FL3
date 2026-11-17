#!/usr/bin/env python3
"""
FL3 — freshness subsite verifier (session arena/4ac55b56-fl3).

Checks the dated freshness captures in data/freshness/ and the rendered
freshness/*.html pages. Exits non-zero on any failure.

Checks:
  A. manifest structure and URL policy
  B. live standings: 32 clubs, uniqueness, PCT = (W+0.5T)/(W+L+T), NET = PF-PA,
     sum(PF) = sum(PA)
  C. Week 11 schedule: 13 games, 26 playing clubs + 6 byes = 32, no overlap,
     every row sourced, venue present
  D. Week 10 results: 14 games, 28 clubs, 13 FINAL + 1 anomalous MNF, sourced
  E. delta file: 32 rows, classification counts, reflected deltas equal each
     club's Week 10 game score, bye/not-reflected rows all-zero, committed
     values match data/standings.json exactly (LA->LAR alias)
  F. findings: 6 items, unique ids, sourced, https-only
  G. rendered HTML: four pages exist, no UNVERIFIED badges, tag balance,
     every data row carries a source link
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "freshness")
OUT = os.path.join(ROOT, "freshness")

PAGES = ["index.html", "standings.html", "schedule.html", "findings.html"]

NFL_ABBR = {
    "AZ", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LAC", "LV", "MIA", "MIN", "NE", "NO", "NYG",
    "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS", "LAR",
}

errors = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)
    mark = "PASS" if cond else "FAIL"
    print(f"[  {mark}] {msg}")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def is_official_url(url):
    return bool(re.match(r"^https://(www\.)?(nfl\.com|media\.nfl\.com|operations\.nfl\.com)/", url))


def main():
    mf = load("manifest.json")
    st = load("standings_live_2026-11-17.json")
    sch = load("schedule_w11_2026-11-17.json")
    res = load("results_w10_2026-11-17.json")
    delta = load("delta_standings_2026-11-17.json")
    findings = load("findings.json")

    # ---- A. manifest -------------------------------------------------------
    check(isinstance(mf.get("sources"), list) and len(mf["sources"]) == 6,
          "A1 manifest lists the 6 official sources fetched")
    check(all(is_official_url(s["url"]) for s in mf["sources"]),
          "A2 every manifest source URL is an official nfl.com / media.nfl.com URL")
    check(mf.get("fetched_utc") == "2026-11-17",
          "A3 manifest fetch date is 2026-11-17")

    # ---- B. live standings ------------------------------------------------
    teams = st["teams"]
    check(len(teams) == 32, f"B1 live standings hold 32 clubs (found {len(teams)})")
    abbrs = [t["abbr"] for t in teams]
    check(len(set(abbrs)) == 32, "B2 live standings club codes are unique")
    check(set(abbrs) == NFL_ABBR, "B3 live standings cover exactly the 32 official club codes")
    bad_pct = [t["abbr"] for t in teams
               if abs(t["pct"] - (t["w"] + 0.5 * t["t"]) / (t["w"] + t["l"] + t["t"])) > 0.001]
    check(not bad_pct, f"B4 PCT = (W + 0.5·T)/(W+L+T) for all 32 clubs (bad: {bad_pct})")
    bad_net = [t["abbr"] for t in teams if t["net"] != t["pf"] - t["pa"]]
    check(not bad_net, f"B5 NET = PF − PA for all 32 clubs (bad: {bad_net})")
    sum_pf = sum(t["pf"] for t in teams)
    sum_pa = sum(t["pa"] for t in teams)
    check(sum_pf == sum_pa,
          f"B6 sum(PF) = sum(PA) across the 32 as printed ({sum_pf} vs {sum_pa})")
    check(all(is_official_url(t["src"]) for t in teams),
          "B7 every standings row carries an official source link")

    # ---- C. Week 11 schedule ----------------------------------------------
    games = sch["games"]
    check(len(games) == 13, f"C1 Week 11 holds 13 games (found {len(games)})")
    playing = set()
    for g in games:
        playing.add(g["away"])
        playing.add(g["home"])
        check(is_official_url(g["src"]) and g["src"].startswith("https://www.nfl.com/games/"),
              f"C2 game centre source for {g['away']}@{g['home']}")
        check(bool(g["location"].strip()) and bool(g["stadium"].strip()),
              f"C3 venue present for {g['away']}@{g['home']}")
    check(len(playing) == 26, f"C4 26 distinct playing clubs (found {len(playing)})")
    byes = set(sch["bye_clubs"])
    check(len(byes) == 6, f"C5 6 bye clubs (found {len(byes)})")
    check(not (playing & byes), "C6 no club is both playing and on bye")
    check(len(playing) + len(byes) == 32, "C7 playing clubs + bye clubs = 32")
    check(len(playing | byes) == 32, "C8 the 32 clubs are exactly the union of playing and bye")

    # ---- D. Week 10 results ------------------------------------------------
    rrows = res["games"]
    check(len(rrows) == 14, f"D1 Week 10 holds 14 games (found {len(rrows)})")
    rclubs = set()
    for g in rrows:
        rclubs.add(g["away"])
        rclubs.add(g["home"])
        check(is_official_url(g["src"]) and g["src"].startswith("https://www.nfl.com/games/"),
              f"D2 result source for {g['away']}@{g['home']}")
    check(len(rclubs) == 28, f"D3 28 distinct clubs played Week 10 (found {len(rclubs)})")
    finals = [g for g in rrows if g["status"] == "FINAL"]
    anomalous = [g for g in rrows if "LIVE" in g["status"]]
    check(len(finals) == 13 and len(anomalous) == 1,
          f"D4 13 FINAL + 1 anomalous MNF row ({len(finals)}/{len(anomalous)})")
    mnf = anomalous[0]
    check(mnf["away"] == "LAC" and mnf["home"] == "BAL" and mnf["away_score"] == 17
          and mnf["home_score"] == 7,
          "D5 the anomalous MNF row records the displayed 17-7 LAC@BAL score")

    # ---- E. delta ----------------------------------------------------------
    rows = delta["rows"]
    check(len(rows) == 32, f"E1 delta holds 32 rows (found {len(rows)})")
    from collections import Counter
    counts = Counter(r["classification"] for r in rows)
    check(counts.get("reflected") == 24, f"E2 24 reflected rows (found {counts.get('reflected')})")
    check(counts.get("bye (week 10)") == 4,
          f"E3 4 Week-10 bye rows (found {counts.get('bye (week 10)')})")
    not_ref = {r["abbr"] for r in rows if r["classification"] == "not reflected on standings page"}
    check(not_ref == {"WAS", "NYG", "BAL", "LAC"},
          f"E4 not-reflected rows are exactly WAS/NYG/BAL/LAC (found {sorted(not_ref)})")

    # committed values in the delta file must match data/standings.json exactly
    with open(os.path.join(ROOT, "data", "standings.json"), encoding="utf-8") as fh:
        committed = {"LAR" if t["abbr"] == "LA" else t["abbr"]: t
                     for t in json.load(fh)["teams"]}
    mismatch = []
    for r in rows:
        c = committed.get(r["abbr"])
        if not c:
            mismatch.append((r["abbr"], "missing in committed"))
            continue
        for key_c, key_d in (("w", "committed_w"), ("l", "committed_l"), ("t", "committed_t"),
                             ("pct", "committed_pct"), ("pf", "committed_pf"),
                             ("pa", "committed_pa"), ("net", "committed_net")):
            if c[key_c] != r[key_d]:
                mismatch.append((r["abbr"], key_c))
    check(not mismatch, f"E5 committed values match data/standings.json line by line (bad: {mismatch})")

    # internal consistency of the delta file itself
    bad = []
    for r in rows:
        if (r["live_w"] - r["committed_w"] != r["dw"] or r["live_l"] - r["committed_l"] != r["dl"]
                or r["live_t"] - r["committed_t"] != r["dt"]
                or r["live_pf"] - r["committed_pf"] != r["dpf"]
                or r["live_pa"] - r["committed_pa"] != r["dpa"]):
            bad.append(r["abbr"])
    check(not bad, f"E6 delta arithmetic is internally consistent (bad: {bad})")

    # reflected rows: PF/PA deltas must equal the club's Week 10 game score
    game_score = {}
    for g in rrows:
        game_score[g["away"]] = (g["away_score"], g["home_score"])
        game_score[g["home"]] = (g["home_score"], g["away_score"])
    bad = []
    for r in rows:
        if r["classification"] != "reflected":
            continue
        pf_g, pa_g = game_score.get(r["abbr"], (None, None))
        if pf_g is None or r["dpf"] != pf_g or r["dpa"] != pa_g:
            bad.append((r["abbr"], r["dpf"], r["dpa"], pf_g, pa_g))
    check(not bad, f"E7 reflected deltas equal each club's Week 10 game score (bad: {bad})")

    # bye and not-reflected rows must be all-zero
    bad = [r["abbr"] for r in rows
           if r["classification"] in ("bye (week 10)", "not reflected on standings page")
           and (r["dw"] or r["dl"] or r["dt"] or r["dpf"] or r["dpa"])]
    check(not bad, f"E8 bye / not-reflected rows carry zero deltas (bad: {bad})")

    # ---- F. findings -------------------------------------------------------
    fitems = findings["findings"]
    check(len(fitems) == 6, f"F1 six findings (found {len(fitems)})")
    ids = [f["id"] for f in fitems]
    check(len(set(ids)) == 6 and ids == [f"F-FRESH-{i:02d}" for i in range(1, 7)],
          f"F2 finding ids are F-FRESH-01..06, unique (found {ids})")
    check(all(is_official_url(f["src"]) for f in fitems),
          "F3 every finding links an official source")
    check(all(f.get("severity") in ("high", "medium", "info") for f in fitems),
          "F4 every finding has a severity")

    # ---- G. rendered HTML --------------------------------------------------
    for p in PAGES:
        path = os.path.join(OUT, p)
        check(os.path.exists(path), f"G1 page exists: freshness/{p}")
        if not os.path.exists(path):
            continue
        html_text = open(path, encoding="utf-8").read()
        check("UNVERIFIED" not in html_text, f"G2 freshness/{p} renders no UNVERIFIED badges")
        for tag in ("table", "thead", "tbody", "tr", "td", "th"):
            opens = len(re.findall(rf"<{tag}[\s>]", html_text))
            closes = len(re.findall(rf"</{tag}>", html_text))
            check(opens == closes, f"G3 freshness/{p} <{tag}> tags balanced ({opens}/{closes})")
        # every data row on standings/schedule/findings must carry a source link
        if p in ("standings.html", "schedule.html", "findings.html"):
            trs = re.findall(r"<tr>(.*?)</tr>", html_text, re.S)
            data_rows = [t for t in trs if "<td" in t]
            unsourced = [i for i, t in enumerate(data_rows) if 'class="src"' not in t]
            check(not unsourced,
                  f"G4 freshness/{p}: all {len(data_rows)} data rows carry a source link"
                  f" (unsourced row indexes: {unsourced})")

    print()
    if errors:
        print(f"FRESHNESS CHECKS: {checks} checks, {len(errors)} FAILED")
        for err in errors:
            print("  -", err)
        return 1
    print(f"FRESHNESS CHECKS: {checks} checks, ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
