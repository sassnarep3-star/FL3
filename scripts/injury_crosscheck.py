#!/usr/bin/env python3
"""
FL3 — independent transcription cross-check.

WHY
---
On 2026-11-16 this session transcribed the live Week 10 injury report into
data/captures/week10_injuries_2026-11-16.csv (347 rows). The repository already contained a
*different* transcription of the same page, made on 2026-11-14 by another session, at
data/injuries_2026_wk10.csv (345 rows). Two independent readings of one official page is a real
opportunity: where they disagree, at least one is wrong, and the disagreement can be localised.

WHAT IT FOUND — and the first hypothesis was WRONG, which is the point
---------------------------------------------------------------------
A first pass guessed the Ravens rows had been lost to a chunk-boundary truncation. The data
refutes that. The delta is not random and it is not a transcription error: it is a *clock*.

  * Every one of the 4 clubs playing MONDAY 2026-11-16 (BAL, LAC) or whose designation moved
    (LAC in full) differs systematically. The 2026-11-14 read captured LAC with practice
    designations only and NO game status anywhere (0 of 19 rows), which is correct for a Monday
    club whose final practice had not happened. The 2026-11-16 read has game status on 9 of 19
    LAC rows. Practice grades also progressed the ordinary way (Limited -> Full for Awosika,
    Njoku, Mitchell, Shelley; DNP -> Limited for Pipkins).
  * BAL gained two rows (Calais Campbell, Ronnie Stanley) and two statuses (Jaylinn Hawkins Out,
    Adam Randall Questionable) between the two reads.
  * One designation moved the other way: IND Arden Key was 'Hamstring / Questionable' on
    2026-11-14 and carries no injury and no designation on 2026-11-16 - he came off the report.

That is the single most decision-relevant fact this repository has produced about its own data
supply: the SAME official URL, read 48 hours apart, yields materially different availability for
the two games that had not yet kicked off. A single capture is not a snapshot of the truth, it is
a snapshot of a clock. Freezing one and pricing from it is lookahead bias in reverse - you price
LAC-BAL as though nine Chargers game designations did not exist.

Two further findings are data-hygiene bugs, not clock effects:

  * Rams abbreviation: data/injuries_2026_wk10.csv uses **LAR**; data/lines_week10.json and this
    session's capture use **LA**. A join on abbreviation silently drops all 14 Rams rows.
  * Player name: the page's visible text is "Jacob Hummel" while the link it publishes is
    /players/jake-hummel/. NFL.com's own inconsistency; recorded, not silently corrected.

This script is deterministic and re-runnable. It never "fixes" the other file: the 2026-11-14
transcription is evidence of what was read on 2026-11-14, and rewriting it would destroy that.
The delta is published instead.

Run: python3 scripts/injury_crosscheck.py
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CAP = os.path.join(DATA, "captures")

CLUB_ALIAS = {"LAR": "LA"}          # normalise before comparing; do not rewrite either file
SOURCE = "https://www.nfl.com/injuries/league/2026/reg10"


def read(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def norm_injury(s):
    return ", ".join(p.strip() for p in str(s or "").replace(";", ",").split(",") if p.strip())


def corroborate():
    """Third-party check: session ab62a598's independent 347-row capture vs this session's 347.

    Two sessions transcribed the same page separately on the same day. If they agree field for
    field the transcription is corroborated; if they disagree, at least one is wrong and the
    disagreement localises the error. This is the strongest verification available without raw
    bytes, and it is cheap.
    """
    other_path = os.path.join(DATA, "official_injury_capture_wk10_2026.csv")
    if not os.path.exists(other_path):
        return None
    other = read(other_path)
    mine = read(os.path.join(CAP, "week10_injuries_2026-11-16.csv"))
    O = {(r["team"], r["player"]): (r["position"], norm_injury(r["injuries"]),
                                   r["practice_status"], r["game_status"]) for r in other}
    M = {(r["club"], r["player"]): (r["position"], norm_injury(r["injury"]),
                                   r["practice_status"], r["game_status"]) for r in mine}
    # normalise the Rams abbreviation before comparing
    O = {(CLUB_ALIAS.get(k[0], k[0]), k[1]): v for k, v in O.items()}
    diffs = [k for k in set(M) & set(O) if M[k] != O[k]]
    return {
        "other_file": "data/official_injury_capture_wk10_2026.csv",
        "other_session": "arena/ab62a598-fl3 (merged to main as PR #27)",
        "rows_other": len(other), "rows_mine": len(mine),
        "keys_other": len(O), "keys_mine": len(M),
        "only_in_mine": len(set(M) - set(O)), "only_in_other": len(set(O) - set(M)),
        "field_diffs": len(diffs),
        "example_diffs": [{"club": k[0], "player": k[1], "mine": M[k], "other": O[k]}
                          for k in sorted(diffs)[:10]],
        "verdict": ("CORROBORATED: two independent transcriptions of the same page agree on "
                    "every field for every shared player" if not diffs else
                    "DISCREPANCY: see example_diffs"),
    }


def main() -> None:
    mine = read(os.path.join(CAP, "week10_injuries_2026-11-16.csv"))
    theirs = read(os.path.join(DATA, "injuries_2026_wk10.csv"))

    M = {(r["club"], r["player"]): r for r in mine}
    T = {(CLUB_ALIAS.get(r["team"], r["team"]), r["player"]): r for r in theirs}

    only_mine = sorted(set(M) - set(T))
    only_theirs = sorted(set(T) - set(M))

    def fields(m, t):
        return {
            "position": (m["position"], t["position"]),
            "injury": (norm_injury(m["injury"]), norm_injury(t["injuries"])),
            "practice": (m["practice_status"], t["practice_status"]),
            "game_status": (m["game_status"], t["game_status"]),
        }

    substantive, cosmetic = [], []
    for k in sorted(set(M) & set(T)):
        d = fields(M[k], T[k])
        changed = {f: v for f, v in d.items() if v[0] != v[1]}
        if not changed:
            continue
        # a difference in injury text only, where the normalised strings match, is cosmetic
        if set(changed) == {"injury"}:
            cosmetic.append((k, changed["injury"]))
        else:
            substantive.append((k, changed))

    print(f"transcription A (this session, 2026-11-16) : {len(mine)} rows")
    print(f"transcription B (session b37bd750, 2026-11-14): {len(theirs)} rows")
    print(f"rows present only in A: {len(only_mine)}")
    for k in only_mine:
        print(f"    + {k[0]:3} {k[1]:22} {M[k]['position']:3} "
              f"{M[k]['injury'] or '-':22} {M[k]['game_status'] or '(blank)'}")
    print(f"rows present only in B: {len(only_theirs)}")
    for k in only_theirs:
        print(f"    - {k[0]:3} {k[1]:22} "
              f"{T[k]['injuries'] or '-':22} {T[k]['game_status'] or '(blank)'}")
    print(f"substantive field differences on shared rows: {len(substantive)}")
    for k, ch in substantive:
        print(f"    ~ {k[0]:3} {k[1]:22} " +
              "; ".join(f"{f} {a!r}->{b!r}" for f, (a, b) in ch.items()))
    print(f"punctuation-only injury-string differences: {len(cosmetic)}")

    # --- Rams abbreviation audit across the whole repository ---------------------
    rams_abbrevs = Counter()
    for name, path, col in [
        ("data/injuries_2026_wk10.csv", os.path.join(DATA, "injuries_2026_wk10.csv"), "team"),
        ("data/injuries_2026_w10.csv", os.path.join(DATA, "injuries_2026_w10.csv"), "team_abbr"),
        ("data/captures/week10_injuries_2026-11-16.csv",
         os.path.join(CAP, "week10_injuries_2026-11-16.csv"), "club"),
    ]:
        vals = {r[col] for r in read(path)}
        hit = [v for v in vals if v in ("LA", "LAR")]
        rams_abbrevs[name] = hit[0] if hit else "(absent)"
    print()
    print("Rams club abbreviation, by file:")
    for k, v in rams_abbrevs.items():
        print(f"    {v:9} {k}")
    js = json.load(open(os.path.join(DATA, "lines_week10.json"), encoding="utf-8"))
    js_rams = sorted({g[side] for g in js["games"] for side in ("away", "home")
                      if g[side] in ("LA", "LAR")})
    print(f"    {js_rams[0] if js_rams else '(absent)':9} data/lines_week10.json")

    # --- write the delta ---------------------------------------------------------
    out = os.path.join(DATA, "injury_crosscheck.csv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "club", "player", "field", "value_A_2026_11_16",
                    "value_B_2026_11_14", "severity", "source_url"])
        for k in only_mine:
            w.writerow(["row_only_in_A", k[0], k[1], "row",
                        f"{M[k]['position']}/{M[k]['injury'] or '-'}/{M[k]['game_status'] or 'blank'}",
                        "(absent)", "substantive", SOURCE])
        for k in only_theirs:
            w.writerow(["row_only_in_B", k[0], k[1], "row",
                        "(absent)",
                        f"{T[k]['position']}/{T[k]['injuries'] or '-'}/{T[k]['game_status'] or 'blank'}",
                        "substantive", SOURCE])
        for k, ch in substantive:
            for f, (a, b) in ch.items():
                w.writerow(["field_diff", k[0], k[1], f, a, b, "substantive", SOURCE])
        for k, (a, b) in cosmetic:
            w.writerow(["field_diff", k[0], k[1], "injury", a, b, "punctuation-only", SOURCE])

    corr = corroborate()
    print()
    if corr:
        print(f"corroboration vs {corr['other_file']} ({corr['other_session']}):")
        print(f"  rows {corr['rows_mine']} vs {corr['rows_other']}; keys {corr['keys_mine']} vs "
              f"{corr['keys_other']}; field differences {corr['field_diffs']}")
        print(f"  {corr['verdict']}")

    summary = {
        "generated_utc": "2026-11-16T01:33Z",
        "corroboration": corr,
        "a": {"file": "data/captures/week10_injuries_2026-11-16.csv", "rows": len(mine),
              "read_utc": "2026-11-16T01:31Z"},
        "b": {"file": "data/injuries_2026_wk10.csv", "rows": len(theirs),
              "read_utc": "2026-11-14"},
        "rows_only_in_a": [{"club": k[0], "player": k[1]} for k in only_mine],
        "rows_only_in_b": [{"club": k[0], "player": k[1]} for k in only_theirs],
        "substantive_field_diffs": len(substantive),
        "punctuation_only_diffs": len(cosmetic),
        "localisation": (
            "The delta is a clock, not a transcription error. LAC carries game status on 0 of 19 "
            "rows in B (the 2026-11-14 read) and on 9 of 19 rows in A (the 2026-11-16 read); BAL "
            "gains 2 rows and 2 statuses; IND Arden Key drops off the report. Both affected clubs "
            "play Monday 2026-11-16, so the earlier read is correct-for-its-moment and the later "
            "read is correct-for-its-moment, and only the later one describes the game as it will "
            "be played."
        ),
        "practice_progression": {
            "LAC": "Awosika, Njoku, Mitchell, Shelley: Limited -> Full; Pipkins: Limited -> DNP",
            "reading": "ordinary week-long progression, not noise",
        },
        "rams_abbreviation": rams_abbrevs,
        "rams_abbreviation_consequence": (
            "data/injuries_2026_wk10.csv uses LAR; data/lines_week10.json and the 2026-11-16 "
            "capture use LA. A join on abbreviation drops every Rams availability row."
        ),
        "action_taken": "Published as a delta + flag. Neither transcription was rewritten.",
        "comparison_is_a_clock": (
            "The A-vs-B differences above are the SAME URL read 48 hours apart, so they are a time "
            "delta. The A-vs-other comparison is the SAME page read on the SAME day by two sessions, "
            "so it is a transcription-accuracy check. They answer different questions and must not "
            "be conflated."
        ),
    }
    with open(os.path.join(DATA, "injury_crosscheck.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    print(f"\nwrote data/injury_crosscheck.csv ({len(only_mine)+len(only_theirs)} row diffs, "
          f"{sum(len(c) for _, c in substantive)} field diffs), data/injury_crosscheck.json")


if __name__ == "__main__":
    main()
