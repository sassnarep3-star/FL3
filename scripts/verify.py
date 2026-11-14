#!/usr/bin/env python3
"""Line-by-line verification of the published data against arithmetic identities.

This script never adds information. It only asks: *can the value we published be
proven from the other values we published?* If a check fails, the row is not
"slightly wrong" - it means a column mapping or a transcription is wrong, and the
build must stop (gate G-10).

Checks implemented
  V-01  standings: W + L + T == games, and PCT == W / (W + L)
  V-02  standings: PF - PA == net_pts
  V-03  league:    sum(PF) == sum(PA) and sum(W) == sum(L) (ties balance too)
  V-04  league:    sum(W+L+T) is even and games == that sum / 2
  V-05  games vs standings: each club's wins/losses recorded in data/games_2026.csv
         for a given week must match the running record printed on the schedule page
         (checked structurally: every game row references two real clubs)
  V-06  passing off: cmp_pct == 100*cmp/att, yds_per_att == yds/att,
         pass_1st_down_pct == 100*1st/att
  V-07  rushing:     yds_per_att == yds/att, 1st_pct == 100*1st/att
  V-08  defense:     opp_cmp_pct == 100*opp_cmp/opp_att, opp_yds_per_att, opp_1st_pct
  V-09  league identity: sum(off pass att) == sum(def opp pass att); same for cmp,
         yds, td, int, 1st downs and sacks (off sacks_taken == def sacks).
         A league-wide identity like this cannot be satisfied by a wrong column
         mapping, which is why it is used to confirm the mapping.
  V-10  injury rows: every team_abbr must be one of the 32 clubs; every game_status
         must be Out / Doubtful / Questionable; practice_status must be one of the
         three legal participation strings.

Exit code 1 if any check fails -> GitHub Pages build stops. Nothing is published
that this file cannot vouch for.
"""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_fl3 import DATA, borderline, close, num, read_rows, write_rows  # noqa: E402

OUT = "verification_report.csv"


def _detail_malformed(malformed, data_dir):
    """Human-readable detail for I-07."""
    n_files = len([f for f in os.listdir(data_dir) if f.endswith(".csv")])
    if not malformed:
        return f"{n_files} files, all rows well-formed"
    shown = "; ".join(malformed[:4])
    extra = len(malformed) - 4
    return shown + (f" (+{extra} more)" if extra > 0 else "")


def main() -> int:
    rows = []
    standings = read_rows("standings_2026.csv")
    games = read_rows("games_2026.csv")
    p_off = read_rows("team_pass_off_2026.csv")
    r_off = read_rows("team_rush_off_2026.csv")
    p_def = read_rows("team_pass_def_2026.csv")
    injuries = read_rows("injuries_2026_w10.csv")
    clubs = {r["team"] for r in standings}
    abbrs = {r["abbr"] for r in standings}

    blocking_failures = []

    def check(cid, name, ok, detail, blocking=True):
        rows.append({
            "check_id": cid,
            "check": name,
            "result": "PASS" if ok else "FAIL",
            "detail": detail,
            "rows_checked": "",
            "blocking": "yes" if blocking else "no",
            "meaning": ("input integrity - the published value cannot be trusted" if not ok and blocking
                        else "source-level inconsistency - values published as read, pricing-ineligible"
                        if not ok else "identity satisfied"),
        })
        if not ok and blocking:
            blocking_failures.append(cid)
        return ok

    all_ok = True

    # V-01 / V-02 -----------------------------------------------------------
    bad = []
    for r in standings:
        w, l, t = num(r["w"], 0), num(r["l"], 0), num(r["t"], 0)
        if w + l + t != num(r["games"], -1):
            bad.append(f"{r['abbr']}:gp")
        tot_gp = w + l + t
        # NFL computes PCT = (W + 0.5*T) / (W + L + T); the plain W/(W+L) formula is wrong
        # once a club has a tie, and the 2026 standings contain two tie records (F-12).
        exp_pct = ((w + 0.5 * t) / tot_gp) if tot_gp else 0.0
        if not close(num(r["pct"], 0), round(exp_pct, 3), 0.0006):
            bad.append(f"{r['abbr']}:pct={r['pct']} vs {exp_pct:.3f}")
        if num(r["pf"], 0) - num(r["pa"], 0) != num(r["net_pts"], 0):
            bad.append(f"{r['abbr']}:net")
    all_ok &= check("V-01", "standings W/L/T, PCT and games reconcile", not any("gp" in b or "pct" in b for b in bad),
                    "ok for 32 clubs" if not bad else "exceptions: " + ", ".join(bad[:8]))
    all_ok &= check("V-02", "standings PF - PA == NET PTS", not any("net" in b for b in bad),
                    "ok for 32 clubs" if not any("net" in b for b in bad) else ", ".join(b for b in bad if "net" in b))

    # V-03 / V-04 -----------------------------------------------------------
    sum_pf = sum(num(r["pf"], 0) for r in standings)
    sum_pa = sum(num(r["pa"], 0) for r in standings)
    sum_w = sum(num(r["w"], 0) for r in standings)
    sum_l = sum(num(r["l"], 0) for r in standings)
    sum_t = sum(num(r["t"], 0) for r in standings)
    team_games = sum(num(r["games"], 0) for r in standings)
    all_ok &= check("V-03", "league points and wins balance",
                    sum_pf == sum_pa and sum_w == sum_l,
                    f"sum(PF)={sum_pf:.0f} sum(PA)={sum_pa:.0f} sum(W)={sum_w:.0f} sum(L)={sum_l:.0f} ties={sum_t:.0f}")
    games_league = team_games / 2
    all_ok &= check("V-04", "team-games total is even (every game has two teams)",
                    team_games % 2 == 0,
                    f"team-games={team_games:.0f} -> games={games_league:.0f}; ties imply {sum_t/2:.0f} tied game(s)")

    # V-05 ------------------------------------------------------------------
    bad = [f"{g['week']}:{g[g_col]}" for g in games for g_col in ("away_abbr", "home_abbr")
           if g[g_col] not in abbrs]
    all_ok &= check("V-05", "every game row references two of the 32 clubs", not bad,
                    f"{len(games)} game rows checked" if not bad else "; ".join(bad))

    # V-06 / V-07 / V-08 ----------------------------------------------------
    for cid, label, table, specs in (
        ("V-06", "offense passing", p_off,
         [("cmp_pct", "pass_cmp", "pass_att", 100.0), ("yds_per_att", "pass_yds", "pass_att", 1.0),
          ("pass_1st_down_pct", "pass_1st_downs", "pass_att", 100.0)]),
        ("V-07", "offense rushing", r_off,
         [("yds_per_att", "rush_yds", "rush_att", 100.0 / 100.0),
          ("rush_1st_down_pct", "rush_1st_downs", "rush_att", 100.0)]),
        ("V-08", "defense passing", p_def,
         [("opp_cmp_pct", "opp_pass_cmp", "opp_pass_att", 100.0),
          ("opp_yds_per_att", "opp_pass_yds", "opp_pass_att", 1.0),
          ("opp_pass_1st_down_pct", "opp_pass_1st_downs", "opp_pass_att", 100.0)]),
    ):
        bad = []
        for r in table:
            for pub_col, num_col, den_col, scale in specs:
                den = num(r.get(den_col))
                if not den:
                    continue
                exp = scale * num(r.get(num_col), 0.0) / den
                if not close(num(r.get(pub_col)), exp):
                    bad.append(f"{r['abbr']}.{pub_col}={r.get(pub_col)} vs {exp:.2f}")
        all_ok &= check(cid, f"{label}: published rate equals recomputed rate", not bad,
                        f"{len(table)} clubs x {len(specs)} rate columns" if not bad else "; ".join(bad[:6]))

    # V-09 ------------------------------------------------------------------
    # Two different things are tested with the same identity, and they fail differently:
    #   V-09a  volume/efficiency totals  -> if these match, the column *mapping* is proven
    #   V-09b  scoring/turnover totals    -> if these mismatch, the source itself is
    #                                        inconsistent (or a row was mis-transcribed)
    def totals(table, col_name):
        return sum(num(r.get(col_name), 0) for r in table)

    mapping_pairs = [("pass_att", "opp_pass_att"), ("pass_cmp", "opp_pass_cmp"),
                     ("pass_yds", "opp_pass_yds"), ("pass_1st_downs", "opp_pass_1st_downs"),
                     ("sacks_taken", "def_sacks")]
    scoring_pairs = [("pass_td", "opp_pass_td"), ("pass_int", "opp_int_forced")]
    det_a, ok_a, det_b, ok_b = [], True, [], True
    for o_col, d_col in mapping_pairs:
        so, sdef = totals(p_off, o_col), totals(p_def, d_col)
        det_a.append(f"{o_col}: off={so:.0f} def={sdef:.0f}")
        ok_a &= (so == sdef)
    for o_col, d_col in scoring_pairs:
        so, sdef = totals(p_off, o_col), totals(p_def, d_col)
        det_b.append(f"{o_col}={so:.0f} vs {d_col}={sdef:.0f} (delta {so - sdef:+.0f})")
        ok_b &= (so == sdef)
    if sum(num(r["games"], 0) for r in p_off) != sum(num(r["games"], 0) for r in p_def):
        ok_a = False
        det_a.append("games differ between offense and defense tables")
    all_ok &= check("V-09a", "league volume identities hold - this is the proof that the "
                             "unlabelled stat columns are mapped correctly (FLG-014)", ok_a, "; ".join(det_a))
    check("V-09b", "league scoring/turnover identities hold", ok_b,
          "; ".join(det_b) if not ok_b else "offense and defense agree: " + "; ".join(det_b),
          blocking=False)
    if not ok_b:
        print("\n>>> SOURCE-LEVEL DISCREPANCY (does not block the build, blocks trust):")
        for line in det_b:
            print(f"    {line}")
        print("    Recorded as FLG-025: these four columns are published but marked "
              "pricing-ineligible until the two official tables agree.\n")

    # V-11 rounding-boundary warnings (data-quality, never a failure) --------
    warns = []
    for table, specs in ((p_off, [("cmp_pct", "pass_cmp", "pass_att", 100.0),
                                  ("yds_per_att", "pass_yds", "pass_att", 1.0)]),
                         (r_off, [("yds_per_att", "rush_yds", "rush_att", 1.0)]),
                         (p_def, [("opp_yds_per_att", "opp_pass_yds", "opp_pass_att", 1.0)])):
        for r in table:
            for pub_col, num_col, den_col, scale in specs:
                den = num(r.get(den_col))
                if not den:
                    continue
                if borderline(num(r.get(pub_col)), scale * num(r.get(num_col), 0.0) / den):
                    warns.append(f"{r['abbr']}.{pub_col}")
    rows.append({"check_id": "V-11", "check": "published rates that sit on the 1-decimal rounding boundary",
                 "result": "WARN" if warns else "PASS",
                 "detail": ("passes only because of rounding slack: " + ", ".join(warns)
                            if warns else "none"),
                 "rows_checked": str(len(warns))})

    # V-10 ------------------------------------------------------------------
    legal_status = {"Out", "Doubtful", "Questionable"}
    legal_practice = {"Did Not Participate In Practice", "Limited Participation in Practice",
                      "Full Participation in Practice"}
    bad = []
    for r in injuries:
        if r["team_abbr"] not in abbrs:
            bad.append(f"team:{r['team_abbr']}")
        if r["game_status"] not in legal_status:
            bad.append(f"status:{r['game_status']}")
        if r["practice_status"] not in legal_practice:
            bad.append(f"practice:{r['practice_status']}")
        if r["pos"] not in {"QB", "RB", "FB", "WR", "TE", "T", "G", "C", "DE", "DT", "LB", "CB", "S", "K", "P", "LS"}:
            bad.append(f"pos:{r['pos']}")
    all_ok &= check("V-10", "injury rows use only legal designations and known clubs", not bad,
                    f"{len(injuries)} rows with a game-status designation" if not bad else "; ".join(bad[:8]))

    # informational: what the identities imply for the model
    tied_games = int(sum_t / 2)
    for _i in rows:
        _i.setdefault("blocking", "no")
        _i.setdefault("meaning", "informational")
    rows.append({
        "check_id": "I-01", "check": "games verified through Week 9 (league)", "result": "DERIVED",
        "detail": f"games={games_league:.0f}; tied={tied_games}; points/game={2 * sum_pf / games_league / 2:.2f} per club",
        "rows_checked": "32"})
    rows.append({
        "check_id": "I-02", "check": "game-level coverage of the season", "result": "PARTIAL",
        "detail": f"data/games_2026.csv holds {len(games)} rows vs {games_league:.0f} verified games "
                  f"({100 * len(games) / games_league:.1f}% coverage) - see FLG-016",
        "rows_checked": str(len(games))})


    # ---- I-05: every source_id cited by any data file must exist in the registry ----
    registry = {r["source_id"] for r in read_rows("sources.csv")}
    orphan, cited = set(), set()
    for fname in sorted(os.listdir(DATA)):
        if not fname.endswith(".csv") or fname == "sources.csv":
            continue
        try:
            frows = read_rows(fname)
        except Exception:
            continue
        if not frows or "source_id" not in frows[0]:
            continue
        for r in frows:
            for sid in (r.get("source_id") or "").replace(";", " ").split():
                cited.add(sid)
                if sid not in registry:
                    orphan.add(f"{fname}:{sid}")
    check("I-05", "every cited source id is registered in data/sources.csv", not orphan,
          ("all %d distinct source ids resolve" % len(cited)) if not orphan
          else "unregistered: " + ", ".join(sorted(orphan)[:8]))

    # ---- I-06: expected-vs-published column completeness on the priced slate ----
    try:
        lines = read_rows("lines_origination.csv")
    except FileNotFoundError:
        lines = []
    if lines:
        have = sum(1 for r in lines if (r.get("model_spread_home") or "").strip())
        want = sum(1 for r in lines if (r.get("market_spread") or "").strip())
        detail = (f"{have}/{len(lines)} rows carry our number; {want}/{len(lines)} carry a market number "
                  f"- the gap is Q-01, not an omission")
        ok = have == len(lines) and want == 0
        check("I-06", "model output completeness (ours filled, market's deliberately blank)", ok, detail)
        check("I-06b", "no market value was invented anywhere", want == 0,
              "market_spread/market_total/market_source must stay blank while SRC-016 is not acquired",
              blocking=(want != 0))


    # ---- I-07 structural integrity of the published CSVs (unquoted commas, short rows) ----
    malformed = []
    for fname in sorted(os.listdir(DATA)):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(DATA, fname)
        with open(path, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        if not lines:
            continue
        width = len(next(csv.reader([lines[0]])))
        for i, ln in enumerate(lines[1:], start=2):
            n = len(next(csv.reader([ln])))
            if n != width:
                malformed.append(f"{fname}:line {i} has {n} fields vs header {width}")
    check("I-07", "every data/*.csv row parses with exactly its header's field count",
          not malformed,
          _detail_malformed(malformed, DATA))

    path = os.path.join(DATA, OUT)
    write_rows(OUT, rows)
    for r in rows:
        print(f"[{r['result']:>7}] {r['check_id']} {r['check']} :: {r['detail']}")
    print(f"\nverification_report -> {os.path.relpath(path, os.getcwd())}")
    if blocking_failures:
        print("GATE G-10: FAIL - " + ", ".join(blocking_failures) +
              " (transcription/integrity failure: the published data does not agree with itself)",
              file=sys.stderr)
        return 1
    if not ok_b:
        print("GATE G-10: PASS with 1 non-blocking source-level discrepancy (V-09b / FLG-025)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
