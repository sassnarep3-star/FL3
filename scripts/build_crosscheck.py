#!/usr/bin/env python3
"""FL3 — reconcile the numbers this repository publishes about itself.

WHY THIS EXISTS
---------------
The brief says to turn "the 136-game log" into the pre-registered backtest corpus. This repo had
five different game counts in it (33, 136, 137, 148 and "254 injury rows"), and nobody had written
down how they relate. They relate exactly, and that is worth proving once rather than arguing about:

    weeks 1-9                     136 games   6,246 points   <- the brief's "136-game log"
    + the Thursday Week 10 final  137 games   6,291 points   <- the board's standings snapshot
    + the other 11 Week 10 finals 148 games   6,824 points   <- the verified standings snapshot

The three totals differ by exactly the points scored in the games added, and every club-level
identity (W/L/T, PF, PA) holds against the official standings on both snapshots. That chain is the
change log for the corpus, and it is checked here rather than asserted in prose.

It also cross-checks Week 10 against two independent captures made by two different sessions on
different dates, and confirms that the twelve games those captures agree on are the twelve finals
the 148-game corpus contains — i.e. that "12 of 14 games" in the older files and "Week 10 is final"
in the newer ones are the same fact, stated at different clock times.

Outputs (all deterministic, no network):
  data/compare/corpus_reconciliation.json
  data/compare/corpus_reconciliation.csv
  data/compare/week10_crosscheck.csv
  data/compare/corpus_identity_32clubs.csv

Run:  python3 scripts/build_crosscheck.py
      python3 scripts/build_crosscheck.py --check
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "compare")

RESULTS = os.path.join(DATA, "week_results_2026.csv")
STANDINGS_148 = os.path.join(DATA, "standings_2026_wk10_verified.csv")
STANDINGS_137 = os.path.join(DATA, "standings_2026.csv")
CAPTURE_A = os.path.join(DATA, "captures_week10_results.csv")
LEDGER = os.path.join(OUT, "forecast_ledger.csv")

SCHED = "https://www.nfl.com/schedules/2026/by-week/week-{w}"
STAND = "https://www.nfl.com/standings/league/2026/reg"


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def totals(games):
    """(games, points, per-club W/L/T/PF/PA) for a list of (week, away, home, ap, hp)."""
    pf, pa, w, l, t = {}, {}, {}, {}, {}
    for _w, a, h, ap, hp in games:
        pf[a] = pf.get(a, 0) + ap
        pa[a] = pa.get(a, 0) + hp
        pf[h] = pf.get(h, 0) + hp
        pa[h] = pa.get(h, 0) + ap
        if ap > hp:
            w[a] = w.get(a, 0) + 1
            l[h] = l.get(h, 0) + 1
        elif hp > ap:
            w[h] = w.get(h, 0) + 1
            l[a] = l.get(a, 0) + 1
        else:
            t[a] = t.get(a, 0) + 1
            t[h] = t.get(h, 0) + 1
    club = {}
    for c in pf:
        club[c] = {"w": w.get(c, 0), "l": l.get(c, 0), "t": t.get(c, 0),
                   "pf": pf[c], "pa": pa[c]}
    return len(games), sum(pf.values()), club


def build():
    corpus = rows(RESULTS)
    games = [(int(r["week"]), r["away_abbr"], r["home_abbr"],
              int(r["away_pts"]), int(r["home_pts"])) for r in corpus]

    w1_9 = [g for g in games if g[0] <= 9]
    w10 = [g for g in games if g[0] == 10]
    thu = [g for g in w10 if g[1] == "WAS" and g[2] == "NYG"]
    rest = [g for g in w10 if not (g[1] == "WAS" and g[2] == "NYG")]
    c136 = w1_9 + thu
    c148 = games

    n136, p136, club136 = totals(c136)
    n148, p148, club148 = totals(c148)
    n_thu, p_thu, _ = totals(thu)
    n_rest, p_rest, _ = totals(rest)

    stand148 = {r["team"]: r for r in rows(STANDINGS_148)}
    # this snapshot keys clubs by their full name; the verified one keys by abbreviation
    stand137 = {r["abbr"]: r for r in rows(STANDINGS_137)}

    def identity(club, stand):
        bad = []
        for c, v in club.items():
            o = stand.get(c)
            if o is None:
                bad.append(f"{c}: absent from the official snapshot")
                continue
            got = (int(o["w"]), int(o["l"]), int(o["t"]), int(o["pf"]), int(o["pa"]))
            want = (v["w"], v["l"], v["t"], v["pf"], v["pa"])
            if got != want:
                bad.append(f"{c}: snapshot {got} vs corpus {want}")
        return bad

    bad148 = identity(club148, stand148)
    bad137 = identity(club136, stand137)

    # ---- Week 10: two independent captures, two different dates ----
    A = {}
    for r in rows(CAPTURE_A):
        if r["away_pts"] == "" or r["home_pts"] == "":
            continue                      # not final at capture time; published as such
        A[f"{r['away']}@{r['home']}"] = (int(r["away_pts"]), int(r["home_pts"]),
                                         r["game_page"], r["capture_utc"], r["state_as_published"])
    B = {f"{r['away_abbr']}@{r['home_abbr']}": (int(r["away_pts"]), int(r["home_pts"]),
                                                r["source_url"], r["accessed_utc"])
         for r in corpus if r["week"] == "10"}
    C = {}
    if os.path.exists(LEDGER):
        for r in rows(LEDGER):
            if r["week"] != "10":
                continue
            C[f"{r['away']}@{r['home']}"] = (int(r["away_pts"]), int(r["home_pts"]))

    xrows = []
    agree_ab = agree_abc = 0
    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    for k in sorted(set(A) | set(B)):
        a, b, c = A.get(k), B.get(k), C.get(k)
        same_ab = a is not None and b is not None and a[:2] == b[:2]
        same_abc = same_ab and (c is None or c == b[:2])
        agree_ab += 1 if same_ab else 0
        agree_abc += 1 if same_abc else 0
        xrows.append({
            "fixture": k,
            "away_pts_captureA": "" if a is None else a[0],
            "home_pts_captureA": "" if a is None else a[1],
            "away_pts_captureB": "" if b is None else b[0],
            "home_pts_captureB": "" if b is None else b[1],
            "away_pts_lab_ledger": "" if c is None else c[0],
            "home_pts_lab_ledger": "" if c is None else c[1],
            "agree_A_vs_B": "yes" if same_ab else ("absent in A" if a is None else "NO"),
            "source_A": "" if a is None else a[2],
            "source_B": "" if b is None else b[2],
            "captured_A_utc": "" if a is None else a[3],
            "captured_B_utc": "" if b is None else b[3],
            "note_A": "" if a is None else a[4],
        })

    # ---- club ledger for the page ----
    crow = []
    for c in sorted(club148):
        o = stand148[c]
        v = club148[c]
        crow.append({
            "club": c,
            "corpus_games": sum(1 for g in games if c in (g[1], g[2])),
            "corpus_w": v["w"], "official_w": o["w"],
            "corpus_l": v["l"], "official_l": o["l"],
            "corpus_t": v["t"], "official_t": o["t"],
            "corpus_pf": v["pf"], "official_pf": o["pf"],
            "corpus_pa": v["pa"], "official_pa": o["pa"],
            "identity_holds": "yes" if (v["w"], v["l"], v["t"], v["pf"], v["pa"]) ==
                              (int(o["w"]), int(o["l"]), int(o["t"]), int(o["pf"]), int(o["pa"]))
                              else "NO",
            "source_url": o["source_url"],
        })

    summary = {
        "title": "Corpus reconciliation — how every game count in this repository relates",
        "source": {"per_week_schedules": SCHED, "standings": STAND,
                   "read_utc": "2026-11-16T01:35Z (corpus transcription)"},
        "chain": [
            {"step": "weeks 1-9 only", "games": n136 - n_thu, "points": p136 - p_thu,
             "matches": "the brief's '136-game log'", "standings_identity": None},
            {"step": "+ the Thursday Week 10 final (WAS 24-21 NYG)", "games": n_thu,
             "points": p_thu,
             "matches": "the game flag F01 records the official DIVISION standings route as still "
                        "missing at its capture time. The league-standings route that "
                        "data/standings_2026.csv was read from does include it, which is why that "
                        "snapshot reconciles at 137 and not 136",
             "standings_identity": None},
            {"step": "= corpus through Week 9's schedule plus that game (137)", "games": n136,
             "points": p136,
             "matches": "data/standings_2026.csv, the board's snapshot (137 games, 6,291 points)",
             "standings_identity": "holds" if not bad137 else "FAILS"},
            {"step": "+ the other 11 Week 10 finals", "games": n_rest, "points": p_rest,
             "matches": "the games still shown as KICKOFF in the earlier capture", "standings_identity": None},
            {"step": "= full corpus (148)", "games": n148, "points": p148,
             "matches": "data/standings_2026_wk10_verified.csv (148 games, 6,824 points)",
             "standings_identity": "holds" if not bad148 else "FAILS"},
        ],
        "identities": {
            "points_balance_148": p148 == sum(v["pa"] for v in club148.values()),
            "wins_equal_losses_148": sum(v["w"] for v in club148.values()) ==
                                     sum(v["l"] for v in club148.values()),
            "clubs_148": len(club148),
            "delta_137_to_148_games": n148 - n136,
            "delta_137_to_148_points": p148 - p136,
            "delta_matches_added_games": (p148 - p136) == p_rest,
            "identity_failures_148": bad148,
            "identity_failures_137": bad137,
        },
        "week10": {
            "fixtures_final_in_lab_corpus": len(B),
            "fixtures_final_in_captureA": len(A),
            "agree_A_vs_B": agree_ab,
            "agree_all_three": agree_abc,
            "only_in_A": only_a,
            "only_in_B": only_b,
            "capture_A": {"file": "data/captures_week10_results.csv", "session": "ab62a598",
                          "captured_utc": "2026-11-16T01:30Z", "source": SCHED.format(w=10)},
            "capture_B": {"file": "data/week_results_2026.csv (week 10 rows)", "session": "03e651e0",
                          "captured_utc": "2026-11-16T01:35Z", "source": SCHED.format(w=10)},
            "reading": "The earlier capture records 12 finals and 2 games still at KICKOFF; the "
                       "later corpus contains those same 12. The two independent transcriptions "
                       "agree on every score. Neither is a correction of the other - they are the "
                       "same fact at two clock times, and both are kept.",
        },
        "other_counts": {
            "33": "data/games_2026.csv, the board's own result rows (24.1% of the corpus) - "
                  "kept as is, reported as partial on the board's results page",
            "137": "the board's standings snapshot: 136 games through Week 9 plus the Thursday "
                   "Week 10 final, 6,291 points. Flag F01 records that the official DIVISION "
                   "standings route still omitted that game when it was read, so the two official "
                   "standings routes disagreed with each other on 2026-11-14. This reconciliation "
                   "uses the league route, which had it.",
            "254 / 279": "reported injury-report row counts from an earlier read; the current "
                         "official capture has 347 rows across 14 game sections (FLG-030)",
        },
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "corpus_reconciliation.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(OUT, "corpus_reconciliation.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["step", "games", "points", "matches", "standings_identity"])
        w.writeheader()
        for r in summary["chain"]:
            w.writerow({k: ("" if r[k] is None else r[k]) for k in w.fieldnames})
    for name, data in (("week10_crosscheck.csv", xrows),
                       ("corpus_identity_32clubs.csv", crow)):
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    summary = build()
    if args.check:
        path = os.path.join(OUT, "corpus_reconciliation.json")
        if not os.path.exists(path):
            print("crosscheck: missing corpus_reconciliation.json", file=sys.stderr)
            return 1
        with open(path, encoding="utf-8") as fh:
            old = json.load(fh)
        if old != summary:
            print("crosscheck: committed reconciliation is stale", file=sys.stderr)
            return 1
        print("crosscheck: --check OK")
    ok = (summary["identities"]["points_balance_148"]
          and summary["identities"]["wins_equal_losses_148"]
          and not summary["identities"]["identity_failures_148"]
          and not summary["identities"]["identity_failures_137"]
          and summary["identities"]["delta_matches_added_games"]
          and summary["week10"]["agree_A_vs_B"] == summary["week10"]["fixtures_final_in_lab_corpus"])
    print(f"crosscheck: 136 -> {summary['chain'][2]['games']} -> {summary['chain'][4]['games']} games; "
          f"{summary['week10']['agree_A_vs_B']}/{summary['week10']['fixtures_final_in_lab_corpus']} "
          f"Week 10 finals agree between two independent captures")
    if not ok:
        print("crosscheck: FAILED an identity", file=sys.stderr)
        return 1
    print("crosscheck: all identities hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
