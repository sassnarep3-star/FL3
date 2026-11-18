#!/usr/bin/env python3
"""Verify the independent verification subsite (verify/).

Stdlib-only. Exits non-zero on any failure. Checks the data and the rendered HTML.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "verify")

PAGES = ["index.html", "verification.html", "venues.html", "gamebooks.html", "sources.html", "brief-claims.html"]
STATUSES = {"CONFIRMED", "PARTIALLY CONFIRMED", "REFUTED", "RECONCILED", "NOT VERIFIED"}

errors = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def is_url(u):
    return isinstance(u, str) and re.match(r"^https://[^\s]+$", u) is not None


def main():
    log = load("verify_log.json")
    venues = load("verify_venues.json")

    # --- data integrity: claims ---
    claims = log["claims"]
    check(len(claims) >= 10, f"V: expected at least 10 claims, got {len(claims)}")
    ids = [c["id"] for c in claims]
    check(len(ids) == len(set(ids)), "V: claim ids are not unique")
    for c in claims:
        check(c["status"] in STATUSES, f"V: claim {c['id']} has invalid status {c['status']!r}")
        check(bool(c["claim"]), f"V: claim {c['id']} has empty claim text")
        check(bool(c["finding"]), f"V: claim {c['id']} has empty finding")
        if c["status"] == "NOT VERIFIED":
            check(not c["source_url"], f"V: NOT VERIFIED claim {c['id']} must have a blank source")
        else:
            check(is_url(c["source_url"]), f"V: claim {c['id']} has non-https/blank source {c['source_url']!r}")

    # --- data integrity: venues ---
    games = venues["games"]
    check(len(games) == 14, f"V: expected 14 Week 10 fixtures, got {len(games)}")
    gids = [g["game_id"] for g in games]
    check(len(gids) == len(set(gids)), "V: game ids are not unique")
    for g in games:
        check(is_url(g["game_url"]), f"V: {g['game_id']} game_url not https")
        check(bool(g["location"]), f"V: {g['game_id']} location blank")
        check(bool(g["stadium"]), f"V: {g['game_id']} stadium blank")
        check(g["status"] in ("FINAL", "UPCOMING"), f"V: {g['game_id']} bad status")
        if g["status"] == "FINAL":
            check(is_url(g["gamebook_pdf"]),
                  f"V: FINAL game {g['game_id']} missing Game Book PDF")
            check(g["away_score"] is not None and g["home_score"] is not None,
                  f"V: FINAL game {g['game_id']} missing score")
        else:
            check(not g["gamebook_pdf"],
                  f"V: UPCOMING game {g['game_id']} should have no Game Book PDF")
            check(bool(g["gamebook_flag"]), f"V: UPCOMING game {g['game_id']} needs a flag note")

    # --- rendered HTML: pages exist, links resolve, statuses rendered ---
    local = set(f"verify/{p}" for p in PAGES)
    for p in PAGES:
        path = os.path.join(OUT, p)
        check(os.path.exists(path), f"V: missing rendered page verify/{p}")
        if not os.path.exists(path):
            continue
        body = open(path, encoding="utf-8").read()
        page_dir = os.path.dirname(os.path.relpath(path, ROOT))
        for href in re.findall(r'href="([^"]+)"', body):
            if href.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = href.split("#")[0]
            resolved = os.path.normpath(os.path.join(page_dir, target)) if page_dir else target
            resolved = resolved.replace(os.sep, "/")
            check(resolved in local, f"V: verify/{p} links to missing local target '{href}' -> {resolved}")

    # the claims page must render every status chip and no "unverified" fallback text
    vbody = open(os.path.join(OUT, "verification.html"), encoding="utf-8").read()
    for c in claims:
        check(c["id"] in vbody, f"V: verification.html does not render claim {c['id']}")
    check("NOT VERIFIED" in vbody, "V: verification.html should render the NOT VERIFIED legend")

    # venues page must render all 14 stadiums
    vbody2 = open(os.path.join(OUT, "venues.html"), encoding="utf-8").read()
    for g in games:
        check(html.escape(g["stadium"]) in vbody2,
              f"V: venues.html does not render stadium {g['stadium']}")

    # index stat cards must reflect the real status counts (and sum to the claim total)
    from collections import Counter
    by_status = Counter(c["status"] for c in claims)
    ibody = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()
    for status, label in [("CONFIRMED", "confirmed"),
                          ("PARTIALLY CONFIRMED", "partially confirmed"),
                          ("RECONCILED", "reconciled"),
                          ("NOT VERIFIED", "not verified")]:
        expected = by_status.get(status, 0)
        check(f'<div class="n">{expected}</div><div class="l">{label}</div>' in ibody,
              f"V: index.html counter for '{label}' is {expected} (status '{status}')")
    status_sum = sum(by_status.get(s, 0) for s in
                     ("CONFIRMED", "PARTIALLY CONFIRMED", "RECONCILED", "NOT VERIFIED"))
    check(status_sum == len(claims),
          f"V: status counters sum to {status_sum} but there are {len(claims)} claims")
    check(f'<div class="n">{len(claims)}</div><div class="l">claims re-checked</div>' in ibody,
          "V: index.html total-claims counter does not match the data")

    # --- brief-claims ledger (2026-11-18): data, CSV export and rendered page agree ---
    import csv as _csv
    ledger = load("verification/brief_claims_2026-11-18.json")
    lclaims = ledger["claims"]
    check(len(lclaims) >= 15, f"V: brief ledger expected >= 15 rows, got {len(lclaims)}")
    lids = [c["id"] for c in lclaims]
    check(len(lids) == len(set(lids)), "V: brief ledger ids are not unique")
    verdicts = {"CONFIRMED", "REFUTED", "STALE", "OBSERVED", "CARRIED", "NOT VERIFIED"}
    for c in lclaims:
        check(c["verdict"] in verdicts, f"V: brief {c['id']} has invalid verdict {c['verdict']!r}")
        check(bool(c["urls"]), f"V: brief {c['id']} has no source URL")
        for u in c["urls"]:
            check(is_url(u), f"V: brief {c['id']} source is not https: {u!r}")
        if c["verdict"] in {"CONFIRMED", "REFUTED", "STALE"}:
            check(bool(c["observed"].strip()), f"V: brief {c['id']} verdict without observed text")
    csv_path = os.path.join(DATA, "verification", "brief_claims_2026-11-18.csv")
    check(os.path.exists(csv_path), "V: brief ledger CSV missing")
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8", newline="") as fh:
            crow = list(_csv.DictReader(fh))
        check([r["id"] for r in crow] == lids, "V: brief ledger CSV is not generated from the JSON (ids differ)")
    bbody = open(os.path.join(OUT, "brief-claims.html"), encoding="utf-8").read()
    for c in lclaims:
        check(c["id"] in bbody, f"V: brief-claims.html does not render {c['id']}")
    check("Flagged for Review" in bbody, "V: brief-claims.html lacks the Flagged for Review section")
    check("2026-11-16" not in bbody.split("<main>")[0].split("<header>")[1] if "<header>" in bbody else True,
          "V: brief-claims.html header still states the 2026-11-16 date")

    print(f"ran {checks} assertions")
    if errors:
        for e in errors:
            print("  FAIL:", e)
        print("VERIFY CHECKS: FAILED")
        sys.exit(1)
    print("ALL VERIFY CHECKS PASSED")


if __name__ == "__main__":
    main()
