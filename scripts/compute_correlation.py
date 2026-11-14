#!/usr/bin/env python3
"""
FL3 — correlation engine.

Computes every *measured* correlation used on the site directly from
data/standings.json, so the numbers in data/correlations.json can be
reproduced and audited line by line.

Output: prints a table and rewrites the `measured` block of correlations.json
        (values only; the prose stays hand-written and reviewed).
"""
from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SRC = "https://www.nfl.com/standings/division/2026/REG"


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx * syy == 0:
        raise ValueError("zero variance")
    return sxy / math.sqrt(sxx * syy)


def t_stat(r: float, n: int) -> float:
    return r * math.sqrt((n - 2) / (1 - r * r))


def main() -> None:
    teams = json.load(open(os.path.join(DATA, "standings.json"), encoding="utf-8"))["teams"]
    gp = {t["abbr"]: t["w"] + t["l"] + t["t"] for t in teams}

    winpct = [t["pct"] for t in teams]
    pd_pg = [(t["pf"] - t["pa"]) / gp[t["abbr"]] for t in teams]
    pf_pg = [t["pf"] / gp[t["abbr"]] for t in teams]
    pa_pg = [t["pa"] / gp[t["abbr"]] for t in teams]

    pairs = [
        ("COR-01", "win% vs point differential per game", winpct, pd_pg),
        ("COR-02", "win% vs points scored per game", winpct, pf_pg),
        ("COR-03", "win% vs points allowed per game", winpct, pa_pg),
        ("COR-04", "points scored per game vs points allowed per game", pf_pg, pa_pg),
    ]

    print(f"n = {len(teams)} clubs (2026 regular season, through Week 10)")
    print(f"{'id':8}{'pair':52}{'r':>8}{'r^2':>8}{'t':>8}")
    results = {}
    for cid, label, x, y in pairs:
        r = pearson(x, y)
        results[cid] = {
            "r": round(r, 4),
            "r_squared": round(r * r, 4),
            "t_stat": round(t_stat(r, len(teams)), 2),
        }
        print(f"{cid:8}{label:52}{r:>8.4f}{r*r:>8.4f}{t_stat(r, len(teams)):>8.2f}")

    # cross-check against the stored registry so drift is caught immediately
    reg = json.load(open(os.path.join(DATA, "correlations.json"), encoding="utf-8"))
    stored = {m["id"]: m for m in reg["measured"]}
    drift = []
    for cid, vals in results.items():
        s = stored.get(cid)
        if not s:
            drift.append(f"{cid}: missing from registry")
            continue
        for k, v in vals.items():
            if abs(float(s[k]) - v) > 1e-6:
                drift.append(f"{cid}.{k}: registry={s[k]} computed={v}")
    if drift:
        print("\nDRIFT DETECTED — update data/correlations.json:")
        for d in drift:
            print("  " + d)
        raise SystemExit(1)
    print("\nregistry matches computed values: OK")


if __name__ == "__main__":
    main()
