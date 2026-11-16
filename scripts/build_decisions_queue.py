#!/usr/bin/env python3
"""
FL3 — turn the requirement register into a decision queue.

THE PROBLEM WITH A 73-ROW REGISTER
----------------------------------
data/requirements_readiness.csv is thorough and it is not actionable. A reviewer opening it sees
73 requirements, each with a gate and a clearing number, and no way to tell which single decision
unblocks the most rows. "Review 73 rows" is not a task anyone completes; "make these five decisions"
is.

WHAT THIS DOES
--------------
Groups the requirements by the gate that blocks them, counts how many rows each gate holds, and
maps each gate to the one owner decision that would release it. Sorted by the number of rows
released. Nothing is re-scored and no status is changed: this is a view over the same CSV, so it
cannot drift from it.

It also reports, for each gate, how many of its rows currently have NO official source in the
registry — because a gate whose rows all lack a source is a procurement decision, while a gate whose
rows all have sources is an engineering decision. Those are different conversations and they were
previously indistinguishable.

Run: python3 scripts/build_decisions_queue.py
"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# gate code -> the one decision that releases it. Written by hand, because a decision is a
# judgement about ownership, not something derivable from the CSV.
DECISION = {
    "Q-01": ("License a market-price source, or accept in writing that no ROI, CLV or edge figure "
             "will ever be published.", "PROCUREMENT"),
    "G-03": ("License a market-price source, or accept in writing that no ROI, CLV or edge figure "
             "will ever be published.", "PROCUREMENT"),
    "Q-02": ("Decide the depth/availability source route: club pages (verified per club), an "
             "authorised feed, or publish the field as unknown.", "PROCUREMENT"),
    "G-02": ("Freeze the evaluation protocol - sample window, fold dates, multiplicity rule - before "
             "any comparison is run.", "PROTOCOL"),
    "G-04": ("Freeze the evaluation protocol - sample window, fold dates, multiplicity rule - before "
             "any comparison is run.", "PROTOCOL"),
    "G-12": ("Freeze the evaluation protocol - sample window, fold dates, multiplicity rule - before "
             "any comparison is run.", "PROTOCOL"),
    "G-01": ("Freeze the evaluation protocol - sample window, fold dates, multiplicity rule - before "
             "any comparison is run.", "PROTOCOL"),
    "G-10": ("Stand up scheduled capture with a clock time and an immutable store.", "ENGINEERING"),
    "G-11": ("Define the demotion state machine and who may reverse a transition.", "GOVERNANCE"),
    "G-07": ("Decide whether correlation may be measured on a priced market or only on realised "
             "outcomes.", "PROTOCOL"),
    "Q-04": ("Commit to a minimum results coverage before any rating is trusted, and accept that "
             "ratings stay opponent-unaware until it is met.", "PROTOCOL"),
}


def gate_codes(text: str) -> list[str]:
    return [c for c in re.findall(r"(?:Q|G)-\d{2}", text or "")]


def main() -> None:
    with open(os.path.join(DATA, "requirements_readiness.csv"), encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    by_gate: dict[str, dict] = defaultdict(lambda: {"rows": [], "no_source": 0})
    unblocked = []
    for r in rows:
        codes = gate_codes(r["blocking_gate"]) or ["(none stated)"]
        has_source = bool((r.get("source_id") or "").strip())
        for c in codes:
            by_gate[c]["rows"].append(r["id"])
            if not has_source:
                by_gate[c]["no_source"] += 1
        if codes == ["(none stated)"]:
            unblocked.append(r["id"])

    queue = []
    for code, info in by_gate.items():
        decision, kind = DECISION.get(code, ("No single owner decision identified - inspect the rows.",
                                             "UNCLASSIFIED"))
        queue.append({
            "gate": code,
            "rows_released": len(info["rows"]),
            "rows_without_official_source": info["no_source"],
            "blocker_type": kind,
            "decision": decision,
            "requirement_ids": ";".join(info["rows"]),
        })
    queue.sort(key=lambda q: (-q["rows_released"], q["gate"]))

    print(f"{len(rows)} requirements"
          f" -> {len(queue)} gates"
          f" -> {len({q['decision'] for q in queue})} distinct owner decisions\n")
    print(f"{'gate':8} {'rows':>4} {'no src':>6}  {'type':12} decision")
    print("-" * 100)
    for q in queue:
        print(f"{q['gate']:8} {q['rows_released']:>4} {q['rows_without_official_source']:>6}  "
              f"{q['blocker_type']:12} {q['decision'][:60]}")

    print()
    top = queue[0] if queue else None
    if top:
        print(f"The single highest-leverage decision releases {top['rows_released']} of "
              f"{len(rows)} requirements: gate {top['gate']}.")
    kinds = defaultdict(int)
    for q in queue:
        kinds[q["blocker_type"]] += q["rows_released"]
    print("Rows by blocker type (a row can sit behind two gates and is counted in each):")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print(f"  {k:12} {v}")

    with open(os.path.join(DATA, "decisions_queue.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["gate", "rows_released",
                                           "rows_without_official_source", "blocker_type",
                                           "decision", "requirement_ids"])
        w.writeheader()
        w.writerows(queue)

    with open(os.path.join(DATA, "decisions_queue.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "generated_utc": "2026-11-16T01:55Z",
            "requirements": len(rows),
            "gates": len(queue),
            "distinct_decisions": len({q["decision"] for q in queue}),
            "top_decision": top,
            "rows_by_blocker_type": dict(kinds),
            "queue": queue,
            "unclassified_gates": [q["gate"] for q in queue
                                   if q["blocker_type"] == "UNCLASSIFIED"],
            "note": (
                "Rows can sit behind more than one gate, so the per-gate counts sum to more than "
                "the requirement count. Nothing here changes a status; it is a view over "
                "data/requirements_readiness.csv."
            ),
        }, fh, indent=1)
        fh.write("\n")
    print("\nwrote data/decisions_queue.csv, data/decisions_queue.json")


if __name__ == "__main__":
    main()
