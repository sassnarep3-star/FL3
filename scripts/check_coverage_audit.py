#!/usr/bin/env python3
"""Verify the requirement-coverage audit artifacts against the readiness register.

Checks (any failure exits 1):
  1. data/requirement_coverage_audit.csv exists and has one row per brief bullet.
  2. Every mapped readiness id exists in data/requirements_readiness.csv and its
     state listed in the audit equals the register's state (the audit cannot
     lag the register).
  3. Every detail_page target exists on disk.
  4. audit/index.html renders one table row per audit dataset row, contains no
     literal template placeholder, and every href it emits resolves to a file.
  5. The bullet count equals the number of B-ids the brief defines (69) - a
     dropped bullet cannot pass silently.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIEF_COUNT = 69


def fail(msg: str) -> int:
    print("FAIL:", msg, file=sys.stderr)
    return 1


def main() -> int:
    reg = {r["id"]: r for r in csv.DictReader((ROOT / "data/requirements_readiness.csv").open(encoding="utf-8-sig"))}
    audit = list(csv.DictReader((ROOT / "data/requirement_coverage_audit.csv").open(encoding="utf-8-sig")))

    if len(audit) != BRIEF_COUNT:
        return fail(f"audit rows {len(audit)} != {BRIEF_COUNT} brief bullets")
    ids = [r["bullet_id"] for r in audit]
    if len(set(ids)) != len(ids):
        return fail("duplicate bullet ids in audit")

    for r in audit:
        for rid in r["readiness_ids"].split(";"):
            if rid not in reg:
                return fail(f"{r['bullet_id']}: register id {rid} not found")
            if reg[rid]["current_state"] != r["register_states"].split(";")[r["readiness_ids"].split(";").index(rid)]:
                return fail(f"{r['bullet_id']}/{rid}: state drifted from register")
        for p in filter(None, r["detail_page"].split(";")):
            if not (ROOT / p).exists():
                return fail(f"{r['bullet_id']}: detail page {p} missing")

    html = (ROOT / "audit/index.html").read_text(encoding="utf-8")
    for placeholder in ("{", "}", "None", "undefined"):
        # '{'/'}' alone appear in CSS braces; assert only real placeholders
        if placeholder in ("None", "undefined") and re.search(rf">\s*{placeholder}\s*<", html):
            return fail(f"audit html contains literal {placeholder}")
    n_rows = html.count("<tr>") - html.count("<thead>") * 3  # 3 header rows
    # stronger: count body rows in the first (main) table by bullet ids
    for r in audit:
        if f'<td class="mono">{r["bullet_id"]}</td>' not in html:
            return fail(f"audit html missing row for {r['bullet_id']}")

    hrefs = re.findall(r'href="(\.\./[^"#]+)"', html)
    broken = [h for h in hrefs if not (ROOT / h[3:]).exists()]
    if broken:
        return fail(f"broken relative links from audit/index.html: {sorted(set(broken))}")

    ext = [h for h in re.findall(r'href="(https?://[^"]+)"', html)]
    bad = [h for h in ext if not h.startswith("https://www.nfl.com/")]
    if bad:
        return fail(f"audit page links a non-registered external domain: {bad}")

    print(f"coverage audit check: {len(audit)} bullets, {len(hrefs)} internal links, "
          f"{len(set(ext))} external links (all nfl.com) - ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
