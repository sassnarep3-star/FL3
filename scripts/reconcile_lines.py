#!/usr/bin/env python3
"""
FL3 — line-provenance reconciliation (rewritten, game_id-keyed).

THE PROBLEM
-----------
Three files in this repository each publish "our line" for the same Week 10 games, and they
disagree with each other by double-digit points:

  A data/lines_week10.json        -> rendered on the live site by scripts/build_site.py
  B data/lines_origination.csv    -> rendered on board/lines by scripts/build_board.py
  C data/2026-week10-lines.csv    -> carries market quotes from ESPN/SBR, no engine writes it

WAS-NYG is the clearest case. It finished WAS 24 – NYG 21 (away by 3).
  A (own axis) says home -4.1   -> ~7 points the wrong side of the result
  B says home +3.5              -> ~6.5 points the wrong side of the result, other direction
  C does not price the game at all
A and B are ~7.6 points apart from each other on the same fixture. Both are labelled ours.

CONVENTION AUDIT — the root cause
---------------------------------
scripts/compute_lines.py emits `home_spread: round(-margin, 1)`, i.e. spread-on-the-home-team,
negative = home favoured. scripts/model.py emits `expected_home_margin`, positive = home wins.
The two files are therefore on inverted axes AND different levels. Anything that compares them
naively (or joins them by team name) will produce garbage.

This script puts all three on ONE axis — signed home margin, positive = home wins by that many
— publishes the disagreements, records which files the site actually renders, and scores each
against the settled results captured 2026-11-16. n is small (12 settled games) and is stated
everywhere; no p-values or confidence intervals are invented from it.

Run: python3 scripts/reconcile_lines.py
"""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CAP = os.path.join(DATA, "captures")

RESULT_SRC = "https://www.nfl.com/schedules/2026/by-week/week-10"


def rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build():
    # Canonical join key is the game_id from the official slate (W10-01 … W10-14).
    # The 2026-11-16 results capture carries game_id + club abbreviations, so it serves as the
    # bridge between A's "WAS-NYG-W10" form and everyone else's "W10-01" form.
    res = {}
    abbr = {}                                    # game_id -> (away_abbr, home_abbr)
    with open(os.path.join(CAP, "week10_results_2026-11-16.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            abbr[r["game_id"]] = (r["away"], r["home"])
            if r["away_pts"] and r["home_pts"]:
                res[r["game_id"]] = (int(r["away_pts"]), int(r["home_pts"]))

    slate = {}
    for r in rows("2026-week10-games.csv"):
        if r["game_id"].startswith("W10-"):
            slate[r["game_id"]] = (r["away"], r["home"])

    pair_to_gid = {v: k for k, v in abbr.items()}

    a_raw = {}
    js = json.load(open(os.path.join(DATA, "lines_week10.json"), encoding="utf-8"))["games"]
    for g in js:
        gid = pair_to_gid.get((g["away"], g["home"]))
        if gid:
            a_raw[gid] = f(g["line"]["home_spread"])

    # B is keyed by full club names only -> resolve through the slate
    name_to_gid = {v: k for k, v in slate.items()}
    b = {}
    for r in rows("lines_origination.csv"):
        gid = name_to_gid.get((r["away"], r["home"]))
        if gid:
            b[gid] = f(r["expected_home_margin"])

    c = {}
    for r in rows("2026-week10-lines.csv"):
        c[r["game_id"]] = f(r["model_home_margin"])

    return slate, abbr, a_raw, b, c, res


def main():
    slate, abbr, a_raw, b, c, res = build()

    hdr = (f"{'game':7} {'pair':9} {'A':>6} {'B':>6} {'C':>6} {'result':>7} "
           f"{'A err':>6} {'B err':>6} {'C err':>6}")
    print(hdr)
    print("-" * len(hdr))

    table, errs = [], {"A": [], "B": [], "C": []}
    pairs = []

    for gid in sorted(slate):
        away, home = abbr.get(gid, ("?", "?"))
        # A's published axis is home_spread (negative = home favoured) -> invert to home margin
        a_m = None if a_raw.get(gid) is None else -a_raw[gid]
        b_m, c_m = b.get(gid), c.get(gid)
        if gid in res:
            ap, hp = res[gid]
            actual = hp - ap
            result_s = f"{ap}-{hp}"
        else:
            actual, result_s = None, "n/f"

        def err(x):
            return "" if (x is None or actual is None) else f"{x - actual:+.1f}"

        print(f"{gid:7} {away}-{home:4} "
              f"{'' if a_m is None else format(a_m,'+.1f'):>6} "
              f"{'' if b_m is None else format(b_m,'+.1f'):>6} "
              f"{'' if c_m is None else format(c_m,'+.1f'):>6} "
              f"{result_s:>7} {err(a_m):>6} {err(b_m):>6} {err(c_m):>6}")

        if actual is not None:
            for k, v in (("A", a_m), ("B", b_m), ("C", c_m)):
                if v is not None:
                    errs[k].append(v - actual)
        if a_m is not None and b_m is not None:
            pairs.append(a_m - b_m)

        table.append([gid, away, home,
                      "" if a_m is None else round(a_m, 1),
                      "" if b_m is None else round(b_m, 1),
                      "" if c_m is None else round(c_m, 1),
                      "" if actual is None else actual])

    def mae(v):
        return sum(abs(x) for x in v) / len(v) if v else float("nan")

    def bias(v):
        return sum(v) / len(v) if v else float("nan")

    print("-" * len(hdr))
    print("Aggregate on the 12 settled games (signed home margin, pts):\n")
    print(f"  {'series':28} {'n':>2} {'MAE':>6} {'bias':>7}")
    for k, label in (("A", "A lines_week10.json"), ("B", "B lines_origination.csv"),
                     ("C", "C 2026-week10-lines.csv")):
        v = errs[k]
        print(f"  {label:28} {len(v):>2} {mae(v):>6.2f} {bias(v):>+7.2f}")

    naive = [0 - (hp - ap) for ap, hp in res.values()]
    print(f"  {'naive: home margin = 0':28} {len(naive):>2} {mae(naive):>6.2f} {bias(naive):>+7.2f}")

    print()
    if pairs:
        print(f"A vs B, our own two files, same {len(pairs)} games: "
              f"mean |difference| = {mae(pairs):.2f} pts, "
              f"mean signed difference = {bias(pairs):+.2f} pts")
        print("  (a mean absolute difference larger than either series' own error vs. the result "
              "means at least one of the two cannot be describing the same quantity)")

    out = os.path.join(DATA, "line_provenance_reconciliation.csv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["game_id", "away", "home", "A_home_margin", "B_home_margin",
                    "C_home_margin", "actual_home_margin", "settled",
                    "source_A", "source_B", "source_C", "source_result"])
        for r in table:
            gid = r[0]
            w.writerow(r + ["yes" if gid in res else "no",
                            "data/lines_week10.json (rendered by scripts/build_site.py line 306)",
                            "data/lines_origination.csv (rendered by scripts/build_board.py)",
                            "data/2026-week10-lines.csv (no generator writes this file)",
                            RESULT_SRC])
    print(f"\nwrote data/line_provenance_reconciliation.csv ({len(table)} games)")

    # a machine-readable verdict block the site can quote
    verdict = {
        "generated_at_utc": "2026-11-16T01:30Z",
        "settled_games": len(res),
        "convention_note": (
            "All values are signed home margin: positive = home team wins by that many points. "
            "A is published in the repository as home_spread (negative = home favoured) and is "
            "inverted here to compare on one axis."
        ),
        "mae": {k: round(mae(errs[k]), 3) for k in errs},
        "bias": {k: round(bias(errs[k]), 3) for k in errs},
        "naive_home_zero_mae": round(mae(naive), 3),
        "n_by_series": {k: len(errs[k]) for k in errs},
        "ab_disagreement_mean_abs": round(mae(pairs), 3) if pairs else None,
        "rendered_by_live_site": "A",
        "caveat": (
            "n=12 settled games. This is a provenance check, not a model evaluation: with 12 "
            "observations nothing here supports a claim that any series has skill."
        ),
    }
    with open(os.path.join(DATA, "line_provenance_verdict.json"), "w", encoding="utf-8") as fh:
        json.dump(verdict, fh, indent=1)
        fh.write("\n")

    flat = [["metric", "value", "note"]]
    flat.append(["settled_games", verdict["settled_games"],
                 "of 14; SNF and MNF had not finished at capture"])
    for k, note in (("A", "data/lines_week10.json - what the live root site renders"),
                    ("B", "data/lines_origination.csv - what board/lines renders"),
                    ("C", "data/2026-week10-lines.csv - no generator writes this file")):
        flat.append([f"mae_{k}", verdict["mae"][k], note])
    for k in ("A", "B", "C"):
        flat.append([f"n_{k}", verdict["n_by_series"][k], "settled games with a value"])
    for k in ("A", "B", "C"):
        flat.append([f"bias_{k}", verdict["bias"][k], "positive = model too home"])
    flat.append(["naive_home_zero_mae", verdict["naive_home_zero_mae"],
                 "benchmark: always forecast a pick em"])
    flat.append(["A_vs_B_mean_abs_disagreement", verdict["ab_disagreement_mean_abs"],
                 "two of our own files, same fixtures"])
    flat.append(["convention", verdict["convention_note"], ""])
    flat.append(["caveat", verdict["caveat"], ""])
    with open(os.path.join(DATA, "line_provenance_verdict.csv"), "w", encoding="utf-8",
              newline="") as fh:
        csv.writer(fh).writerows(flat)


if __name__ == "__main__":
    main()
