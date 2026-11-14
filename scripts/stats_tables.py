#!/usr/bin/env python3
"""Compute the decision math every gate and stake rule leans on.

These are closed-form results from stated assumptions (binomial / normal approximation),
not measurements, so they carry no source_id - they carry a `derivation` column instead.
Publishing them means a threshold is never argued from a gut feel in a meeting.

Output: data/decision_math.csv
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_fl3 import write_rows  # noqa: E402

Z95, Z80POW = 1.959964, 0.841621


def price_to_prob(price):
    """American price -> implied win probability (negative = lay, positive = risk)."""
    return (abs(price) / (abs(price) + 100.0)) if price < 0 else (100.0 / (price + 100.0))


def n_needed(p_true, p_market, alpha=0.05, power=0.80):
    """Sample size to tell p_true from p_market at given alpha/power (one-sample, normal approx).

    n = ((z_a * sqrt(p0(1-p0)) + z_b * sqrt(p1(1-p1))) / (p1-p0))^2
    """
    p0, p1 = p_market, p_true
    if p1 == p0:
        return float("inf")
    za = {0.05: Z95, 0.10: 1.6449, 0.01: 2.5758}[alpha]
    zb = {0.80: Z80POW, 0.90: 1.2816}[power]
    num = za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))
    return (num / (p1 - p0)) ** 2


def main() -> int:
    rows = []
    # 1. break-even at common prices
    for price in (-110, -105, -120, -130, +100, +150):
        p = price_to_prob(price)
        rows.append({
            "family": "break-even", "parameter": f"{price:+d}",
            "value": f"{p:.4f}", "unit": "win probability",
            "derivation": "American price to implied probability",
            "note": "a strategy must beat this hit rate before any edge exists at all",
        })
    # 2. how many bets to *prove* an edge
    for price in (-110, -120):
        p0 = price_to_prob(price)
        for extra in (0.01, 0.02, 0.03, 0.05):
            n = n_needed(p0 + extra, p0)
            rows.append({
                "family": "sample size", "parameter": f"{price:+d} at {extra*100:.0f} pts of hit-rate edge",
                "value": f"{n:.0f}", "unit": "independent bets (95% conf, 80% power)",
                "derivation": "one-sample normal approximation, n = (z_a*sqrt(p0q0)+z_b*sqrt(p1q1))^2 / (p1-p0)^2",
                "note": "this is the gate G-01 number: below it, the difference between skill and "
                        "luck cannot be shown, only asserted",
            })
    # 3. EV per 100 units and Kelly, at the same edges
    for price in (-110, -120):
        p0 = price_to_prob(price)
        for extra in (0.02, 0.03):
            p = p0 + extra
            b = (100.0 / abs(price)) if price < 0 else price / 100.0
            ev = p * b - (1 - p) * 1.0
            kelly = (p * (b + 1) - 1) / b
            rows.append({
                "family": "expectation", "parameter": f"{price:+d}, hit rate {p:.3f}",
                "value": f"{ev:+.4f}", "unit": "EV per 1 unit risked",
                "derivation": "EV = p*b - (1-p); Kelly = (p(b+1)-1)/b",
                "note": f"full Kelly = {kelly*100:.2f}% of bankroll; the repo stakes 0.25 Kelly "
                        f"(models/line_model.yaml) = {kelly*25:.2f}%",
            })
    # 4. parlay arithmetic - what correlation actually does to a combined price
    p_be = price_to_prob(-110)                      # 0.5238: the book's implied prob per leg
    dec_parlay = (1.0 / p_be) ** 2                  # books multiply decimals, not probabilities
    book_parlay_prob = 1.0 / dec_parlay
    p_single = p_be + 0.02                          # each leg carries a 2-pt hit-rate edge
    for label, joint in (
        ("legs independent", p_single ** 2),
        ("legs positively correlated, rho=+0.35", None),
        ("legs negatively correlated, rho=-0.35", None),
    ):
        if joint is None:
            rho = 0.35 if "positively" in label else -0.35
            s1 = s2 = math.sqrt(p_single * (1 - p_single))
            joint = min(0.999999, max(0.0, p_single ** 2 + rho * s1 * s2))
        ev = joint * dec_parlay - 1.0
        rows.append({
            "family": "parlay", "parameter": label + " (2 legs at -110, 2 pts edge each)",
            "value": f"{joint:.4f}", "unit": "joint win probability",
            "derivation": "p12 = p1*p2 + rho*sqrt(p1*q1*p2*q2); book quotes "
                          f"{dec_parlay:.3f} decimal (implied {book_parlay_prob:.4f})",
            "note": f"EV of the combined ticket = {ev:+.1%}. The book prices a parlay as if the legs "
                    f"were independent, so the entire conversation about 'correlation' is a "
                    f"conversation about this number - and about why books re-price or restrict "
                    f"same-game combinations",
        })
    rows.append({
        "family": "parlay", "parameter": "vig comparison: 2 separate bets vs 1 two-leg ticket",
        "value": f"{2 * (p_single / p_be - 1):+.4f} vs {p_single ** 2 / book_parlay_prob - 1:+.4f}",
        "unit": "EV taken separately vs combined (independent legs)",
        "derivation": "per-leg EV = p/p_be - 1; combined = (p/p_be)^2 - 1",
        "note": "with independent legs the combined ticket multiplies both the edge and the vig; "
                "it does not create value, which is why 'parlays for the sake of parlays' loses faster",
    })

    # 5. drawdown / risk of ruin intuition
    rows.append({
        "family": "risk", "parameter": "a break-even strategy (p = 0.5238 at -110)",
        "value": f"{(1 - 0.5238) * 100:.1f}", "unit": "% of individual bets that lose",
        "derivation": "1 - p",
        "note": f"a specific 10-bet losing run happens with probability {(1 - 0.5238) ** 10 * 100:.2f}% "
                "even for a perfectly priced strategy - which is why a 10-bet losing streak is evidence "
                "of nothing, and why gates are measured on hundreds of bets",
    })
    rows.append({
        "family": "risk", "parameter": "probability of a 10-bet losing streak in 200 bets (p_loss=0.476)",
        "value": f"{(1-(1-(1-0.476)**10)**200)*100:.1f}", "unit": "% (rough, independent windows)",
        "derivation": "1 - (1 - q^10)^N", "note": "shows why 'a strategy that lost' and "
                                                  "'a strategy that is bad' are different claims; "
                                                  "gate G-05 exists for this",
    })
    write_rows("decision_math.csv", rows)
    print(f"decision_math: {len(rows)} computed thresholds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
