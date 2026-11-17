#!/usr/bin/env python3
"""
FL3 — assertions over the rendered `verified/` site.

A data-file check cannot catch a renderer reading the wrong file, printing a
stale constant, or emitting a link to a page that does not exist. At least one
assertion has to inspect the produced HTML. That is what this does, plus the
arithmetic re-checks, run against the committed data.

Every check prints PASS/FAIL and the script exits 1 on any failure, so it can
gate a merge.

Run: python3 scripts/check_verified_site.py
"""
from __future__ import annotations

import csv
import html.parser
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SITE = os.path.join(ROOT, "verified")

PAGES = ["index.html", "results.html", "lines.html", "injuries.html",
         "strategies.html", "verification.html", "review.html", "method.html"]

checks = 0
fails: list[str] = []


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.imgs = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self.hrefs.append(d["href"])
        if tag == "link" and d.get("href"):
            self.imgs.append(d["href"])


def main() -> int:
    results = json.load(open(os.path.join(DATA, "week_results_2026.json"), encoding="utf-8"))
    ev = json.load(open(os.path.join(DATA, "line_eval.json"), encoding="utf-8"))
    lv = json.load(open(os.path.join(DATA, "live_verification.json"), encoding="utf-8"))
    rows = list(csv.DictReader(open(os.path.join(DATA, "week_results_2026.csv"), encoding="utf-8")))

    # ---------------- corpus arithmetic, re-derived here, not trusted ----------
    game_count = len(rows)
    check(game_count == results["meta"]["games"],
          f"results corpus row count {game_count} != metadata {results['meta']['games']}")
    agg: dict[str, dict] = {}
    for r in rows:
        aw, hm = int(r["away_pts"]), int(r["home_pts"])
        for t, pf, pa in ((r["away_abbr"], aw, hm), (r["home_abbr"], hm, aw)):
            a = agg.setdefault(t, dict(w=0, l=0, t=0, pf=0, pa=0))
            a["pf"] += pf
            a["pa"] += pa
        if aw > hm:
            agg[r["away_abbr"]]["w"] += 1
            agg[r["home_abbr"]]["l"] += 1
        elif hm > aw:
            agg[r["home_abbr"]]["w"] += 1
            agg[r["away_abbr"]]["l"] += 1
        else:
            agg[r["away_abbr"]]["t"] += 1
            agg[r["home_abbr"]]["t"] += 1

    check(len(agg) == 32, f"expected 32 clubs in the corpus, found {len(agg)}")
    check(sum(a["pf"] for a in agg.values()) == sum(a["pa"] for a in agg.values()),
          "league points-for and points-against do not balance")
    check(sum(a["w"] + a["l"] + a["t"] for a in agg.values()) == 2 * game_count,
          "club games do not equal twice the game count")

    standings = {r["team"]: r for r in csv.DictReader(
        open(os.path.join(DATA, "standings_2026_wk10_verified.csv"), encoding="utf-8"))}
    check(set(standings) == set(agg), "club sets differ between corpus and standings")
    mism = []
    for t, s in standings.items():
        a = agg[t]
        for f, k in (("w", "w"), ("l", "l"), ("t", "t"), ("pf", "pf"), ("pa", "pa")):
            if int(s[f]) != a[k]:
                mism.append(f"{t}.{f}: standings {s[f]} vs corpus {a[k]}")
    check(not mism, f"standings reconciliation failed: {mism[:5]}")

    # ---------------- evaluation internals -------------------------------------
    cm = ev["committed_week10"]
    for g in cm["per_game"]:
        check(g["p_home"] is not None and 0.0 <= g["p_home"] <= 1.0,
              f"committed forecast probability out of range for {g['game']}")
        check(g["tie"] == 0, f"scored game {g['game']} was a tie; the Brier outcome needs a decision")
    wf = ev["walkforward"]
    check(wf["point"]["n"] == len(wf["per_game"]),
          "walk-forward n disagrees with its own per-game rows")
    check(len({x["week"] for x in wf["per_game"]}) >= 5, "walk-forward covers too few weeks")
    for x in wf["per_game"]:
        check(0.0 < x["p_home"] < 1.0, f"walk-forward probability out of range for {x['game']}")
    # a CI must contain its own point estimate
    for key in ("spread_rmse_gain_vs_pickem", "brier_skill_vs_coin"):
        d = wf[key]
        check(d["ci95"][0] <= d["estimate"] <= d["ci95"][1],
              f"{key}: point estimate {d['estimate']} outside its own interval {d['ci95']}")

    # ---------------- every live-verification row is well formed --------------
    for r in lv["claims"]:
        check(r["status"] in {"CONFIRMED", "STALE", "PARTLY_STALE", "NOT_REPRODUCIBLE", "UNVERIFIABLE"},
              f'{r["claim_id"]}: unknown status {r["status"]}')
        check(bool(r["live_value"]) and bool(r["repo_value"]),
              f'{r["claim_id"]}: missing one side of the comparison')
        if r["status"] == "UNVERIFIABLE":
            check(bool(r.get("source_gap")),
                  f'{r["claim_id"]}: unverifiable row must carry an explicit source gap')
        else:
            check(r["live_source"].startswith("https://"),
                  f'{r["claim_id"]}: a checkable row must link an https official source')

    # ---------------- the rendered site ---------------------------------------
    all_text = {}
    for p in PAGES:
        path = os.path.join(SITE, p)
        check(os.path.exists(path), f"missing page verified/{p}")
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8").read()
        all_text[p] = txt
        check("UNVERIFIED" not in txt or p in ("index.html", "verification.html", "review.html", "method.html"),
              f"{p}: stray UNVERIFIED marker")
        check("<title>" in txt and "<h1>" in txt, f"{p}: missing title or h1")
        # malformed nesting is invisible to a data check and renders as literal
        # markup in some readers - assert balance on the inline tags actually used
        # count opening tags that may carry attributes, e.g. <td class="mono">
        for tag in ("b", "td", "tr", "table", "span"):
            n_open = len(re.findall(rf"<{tag}[ >]", txt))
            n_close = txt.count(f"</{tag}>")
            check(n_open == n_close,
                  f"{p}: unbalanced <{tag}> tags ({n_open} open, {n_close} close)")

        lp = Links()
        lp.feed(txt)
        for href in lp.hrefs:
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            if href.startswith("http"):
                check(href.startswith("https://"),
                      f"{p}: non-https external link {href}")
                continue
            target = os.path.normpath(os.path.join(SITE, href.split("#")[0]))
            check(os.path.exists(target), f"{p}: broken internal link -> {href}")

    # ---------------- no hand-typed corpus figures ----------------------------
    # The number of games and the headline evaluation figures must come from the
    # data. Assert the rendered page agrees with the data rather than a literal.
    idx = all_text["index.html"]
    check(str(game_count) in idx, f"index.html does not show the corpus size {game_count}")
    check(f"{wf['point']['n']}" in idx, "index.html does not show the walk-forward n")
    sci = wf["spread_rmse_gain_vs_pickem"]["ci95"]
    check(f"{sci[0]:+.3f}" in idx, "index.html interval does not match the computed interval")
    check(f"{wf['point']['spread_rmse']:.2f}" in idx, "index.html spread RMSE does not match the computation")

    # the stale 136 figure must never be presented as current
    check(re.search(r"136[ -]game? corpus (is|remains) current", idx) is None,
          "index.html still presents 136 as the current corpus size")
    check("148" in idx, "index.html does not mention the verified 148-game corpus")

    # the honest verdict must actually appear
    check("not distinguishable" in idx or "no demonstrated skill" in idx,
          "index.html hides the negative result; the baseline's lack of demonstrated skill must be visible")
    check("PREREGISTRATION.md" in all_text["strategies.html"],
          "strategies.html does not link the pre-registration")
    check("LV-05" in all_text["injuries.html"],
          "injuries.html does not reference the material capture defect")

    # the Week 11 ledger must render every fixture, not a template placeholder
    st = all_text["strategies.html"]
    slate = list(csv.DictReader(open(os.path.join(DATA, "week11_slate_2026.csv"), encoding="utf-8")))
    fx = json.load(open(os.path.join(DATA, "preregistration_week11.json"), encoding="utf-8"))
    check("{rows}" not in st and "FIXTURE_HASH" not in st,
          "strategies.html still contains a template placeholder")
    check(fx["fixture_count"] == len(slate),
          f"fixture ledger has {fx['fixture_count']} forecasts against {len(slate)} scheduled games")
    for g in slate:
        check(f'{g["away_abbr"]} @ {g["home_abbr"]}' in st,
              f'strategies.html does not render the fixture {g["away_abbr"]} @ {g["home_abbr"]}')
    slate_teams = {g["away_abbr"] for g in slate} | {g["home_abbr"] for g in slate}
    check(len(slate_teams) + 6 == 32,
          f"Week 11 slate covers {len(slate_teams)} clubs; with 6 byes it must account for 32")
    for f in fx["fixtures"]:
        check(0.0 < f["p_home"] < 1.0, f"registered forecast probability out of range for {f['away']}@{f['home']}")
    check(len({(f["away"], f["home"]) for f in fx["fixtures"]}) == len(fx["fixtures"]),
          "duplicate fixture in the registered forecast ledger")

    res_html = all_text["results.html"]
    check(res_html.count('href="https://www.nfl.com/schedules/2026/by-week/week-') > 140,
          "results.html does not link an official page per game row")
    check(str(game_count) in res_html, "results.html does not state the row count")

    print(f"ran {checks} assertions")
    if fails:
        print(f"\n{len(fails)} FAILURES:", file=sys.stderr)
        for f in fails[:30]:
            print("  FAIL " + f, file=sys.stderr)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
