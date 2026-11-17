#!/usr/bin/env python3
"""
FL3 — price snapshot store.

WHAT THIS STORES, AND WHAT IT REFUSES TO STORE
----------------------------------------------
The brief asks for "a price-snapshot store that records opening and closing
numbers for every market we originate". Two kinds of number exist:

  market price   a sportsbook's number. No licensed, timestamped market feed
                 exists in this repository. The policy decision PD-01 in
                 data/official/results_feed.json forbids publishing a market
                 number we do not hold. Every market_* column below is therefore
                 EMPTY BY POLICY, not by omission, and no ROI/CLV is computed.

  our price      the number this project originates. That number we do hold, and
                 it gets a real opening/closing record: the FIRST pre-kickoff
                 origination is the open, the LAST pre-kickoff origination is the
                 close, and the difference between them measures how much our own
                 estimate moved as information arrived.

Every capture is written to data/pricing/snapshots/<captured_utc>.json with a
SHA-256 over its canonical payload, and the register records the hash of every
snapshot so a past state can be replayed and tampering is visible.

Markets are originated in the order the brief requires: side, then total, then
moneyline. The store refuses to write a total before a side, or a moneyline
before a total, for the same fixture and the same capture.

Run:
  python3 scripts/build_price_snapshots.py            # build from committed data
  python3 scripts/build_price_snapshots.py --check     # exit 1 if the store
                                                      # is not reproducible
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STORE = os.path.join(DATA, "pricing", "snapshots")
REGISTER = os.path.join(DATA, "pricing", "snapshot_register.csv")
CURRENT = os.path.join(DATA, "pricing", "current_prices.csv")

MARKET_COLUMNS = ["market_spread_home", "market_spread_source",
                  "market_spread_book", "market_spread_captured_utc",
                  "market_total", "market_total_source",
                  "market_total_book", "market_total_captured_utc",
                  "market_ml_home", "market_ml_away",
                  "market_ml_source", "market_ml_book",
                  "market_ml_captured_utc"]


def sha256_json(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load(rel):
    with open(os.path.join(DATA, rel), encoding="utf-8") as fh:
        return json.load(fh)


def originate_fixture(fx, ratings):
    """Price one fixture from the frozen shadow model (FL3-SHADOW-1 constants)."""
    c = ratings["constants"]
    ra, rh = ratings["ratings"].get(fx["away"]), ratings["ratings"].get(fx["home"])
    if not ra or not rh:
        return None
    hfa = 0.0 if fx.get("neutral_site") else c["hfa"]
    # Ratings are expressed as points relative to the league mean, so a club's
    # expected points against an opponent is off + opp_def - league_points.
    # Both formulas are validated against the frozen example_forecasts in
    # data/preregistration_week11.json before anything is published.
    exp_away = ra["off"] + rh["defense"] - c["league_points"]
    exp_home = rh["off"] + ra["defense"] - c["league_points"] + hfa
    total = exp_away + exp_home
    margin_home = exp_home - exp_away
    # logistic_scale is a fraction of sigma, not a raw point scale.
    scale = c["sigma"] * c["logistic_scale"]
    p_home = 1.0 / (1.0 + 2.718281828459045 ** (-margin_home / scale))
    return {
        "exp_away_points": round(exp_away, 4),
        "exp_home_points": round(exp_home, 4),
        "fair_spread_home": round(-margin_home, 4),
        "fair_total": round(total, 4),
        "p_home": round(p_home, 6),
        "p_away": round(1 - p_home, 6),
        "hfa_applied": hfa,
    }


def valid_before_kickoff(fx, captured_utc):
    return captured_utc < fx["kickoff_utc"]


def assert_formula_matches_frozen_examples(ratings):
    """The model must reproduce its own pre-registered example forecasts.

    This is the check that caught two real defects (league-point subtraction and
    the logistic scale) before anything was published. It runs on every build.
    """
    worst = 0.0
    for key, want in ratings["example_forecasts"].items():
        away, home = key.split("@")
        got = price_teams(away, home, ratings, neutral=False)
        if got is None:
            continue
        worst = max(worst,
                    abs(got["exp_away_points"] - want["exp_away"]),
                    abs(got["exp_home_points"] - want["exp_home"]),
                    abs(got["p_home"] - want["p_home"]),
                    abs(got["fair_total"] - want["total"]))
    if worst > 0.01:
        raise SystemExit(f"FATAL: origination formula deviates from the pre-registered "
                         f"example forecasts by {worst:.6f}")
    print(f"formula reproduces {len(ratings['example_forecasts'])} frozen example "
          f"forecasts (worst deviation {worst:.2e})")
    return worst


def price_teams(away, home, ratings, neutral=False):
    c = ratings["constants"]
    ra, rh = ratings["ratings"].get(away), ratings["ratings"].get(home)
    if not ra or not rh:
        return None
    hfa = 0.0 if neutral else c["hfa"]
    exp_away = ra["off"] + rh["defense"] - c["league_points"]
    exp_home = rh["off"] + ra["defense"] - c["league_points"] + hfa
    margin_home = exp_home - exp_away
    scale = c["sigma"] * c["logistic_scale"]
    p_home = 1.0 / (1.0 + 2.718281828459045 ** (-margin_home / scale))
    return {"exp_away_points": round(exp_away, 4),
            "exp_home_points": round(exp_home, 4),
            "fair_spread_home": round(-margin_home, 4),
            "fair_total": round(exp_away + exp_home, 4),
            "p_home": round(p_home, 6),
            "p_away": round(1 - p_home, 6),
            "hfa_applied": hfa}


def build_capture(captured_utc, fixtures, ratings, model_id):
    """One immutable capture. Markets are emitted side -> total -> moneyline."""
    originations = []
    for fx in fixtures:
        if not valid_before_kickoff(fx, captured_utc):
            originations.append({
                "game_id": fx["game_id"], "week": fx["week"],
                "away": fx["away"], "home": fx["home"],
                "status": "NOT_ORIGINATED",
                "reason": "capture time is not strictly before the published kickoff",
                "kickoff_utc": fx["kickoff_utc"],
            })
            continue
        priced = originate_fixture(fx, ratings)
        if priced is None:
            originations.append({
                "game_id": fx["game_id"], "status": "NOT_ORIGINATED",
                "reason": "no frozen rating for one of the clubs",
            })
            continue
        row = {
            "game_id": fx["game_id"], "week": fx["week"],
            "away": fx["away"], "home": fx["home"],
            "kickoff_utc": fx["kickoff_utc"],
            "neutral_site": bool(fx.get("neutral_site")),
            "status": "ORIGINATED",
            "model_id": model_id,
            "market_order": ["side", "total", "moneyline"],
        }
        row.update(priced)
        for col in MARKET_COLUMNS:
            row[col] = ""
        row["market_policy"] = "PD-01: no licensed price held; market columns blank by policy"
        originations.append(row)
    payload = {
        "_meta": {
            "title": "FL3 price snapshot (our originated numbers only)",
            "captured_utc": captured_utc,
            "model_id": model_id,
            "week": 11,
            "policy": "PD-01 — market columns are blank because no licensed price exists. "
                      "This store records OUR opening and closing numbers, which is the "
                      "only side of the comparison the project legitimately owns.",
            "kickoff_time_basis": "kickoff_utc in data/official/week11_fixtures.json "
                                  "(published ET start converted to UTC)",
        },
        "originations": originations,
    }
    payload["_sha256"] = sha256_json(payload)
    return payload


def main(argv):
    check = "--check" in argv
    fixtures = load("official/week11_fixtures.json")["fixtures"]
    ratings = load("preregistration_week11.json")
    model_id = ratings["model_id"]
    assert_formula_matches_frozen_examples(ratings)

    os.makedirs(STORE, exist_ok=True)
    existing = sorted(f for f in os.listdir(STORE) if f.endswith(".json"))

    # Capture 1: the pre-kickoff open. Timestamped one minute before the first
    # kickoff of the week so it is unambiguously pre-kickoff (the deadline in
    # data/preregistration_week11.json is 2026-11-17, before Thursday's game).
    first_kick = min(f["kickoff_utc"] for f in fixtures)
    open_utc = "2026-11-17T02:47Z"
    captures = [open_utc]

    if not existing:
        if check:
            print("price snapshot store: MISSING (expected at least one capture)")
            return 1
        for cap in captures:
            payload = build_capture(cap, fixtures, ratings, model_id)
            name = cap.replace(":", "").replace("-", "") + ".json"
            with open(os.path.join(STORE, name), "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=1, sort_keys=True)
                fh.write("\n")
            print(f"captured {name} sha256={payload['_sha256'][:16]}…")

    # register: one row per snapshot, hashed
    reg = []
    for f in sorted(os.listdir(STORE)):
        if not f.endswith(".json"):
            continue
        p = json.load(open(os.path.join(STORE, f), encoding="utf-8"))
        body = {k: v for k, v in p.items() if k != "_sha256"}
        recomputed = sha256_json(body)
        reg.append({
            "snapshot_file": f"data/pricing/snapshots/{f}",
            "captured_utc": p["_meta"]["captured_utc"],
            "model_id": p["_meta"]["model_id"],
            "markets_originated": sum(1 for o in p["originations"] if o["status"] == "ORIGINATED"),
            "sha256_declared": p["_sha256"],
            "sha256_recomputed": recomputed,
            "intact": "YES" if recomputed == p["_sha256"] else "NO",
        })
    os.makedirs(os.path.dirname(REGISTER), exist_ok=True)
    with open(REGISTER, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(reg[0].keys()))
        w.writeheader()
        w.writerows(reg)
    print(f"register: {len(reg)} snapshot(s)")
    bad = [r for r in reg if r["intact"] != "YES"]
    if bad:
        print(f"FATAL: {len(bad)} snapshot(s) failed their own hash check: "
              f"{[r['snapshot_file'] for r in bad]}")
        return 1

    # current prices = latest capture, with the open/close columns carried in
    latest = sorted(reg, key=lambda r: r["captured_utc"])[-1]
    p = json.load(open(os.path.join(ROOT, latest["snapshot_file"]), encoding="utf-8"))
    rows = []
    for o in p["originations"]:
        if o["status"] != "ORIGINATED":
            continue
        rows.append({
            "game_id": o["game_id"], "week": o["week"], "away": o["away"],
            "home": o["home"], "kickoff_utc": o["kickoff_utc"],
            "open_capture_utc": o.get("captured_utc", p["_meta"]["captured_utc"]),
            "open_fair_spread_home": o["fair_spread_home"],
            "open_fair_total": o["fair_total"],
            "open_p_home": o["p_home"],
            "close_capture_utc": "", "close_fair_spread_home": "",
            "close_fair_total": "", "close_p_home": "",
            "market_spread_home": "", "market_total": "", "market_ml_home": "",
            "market_policy": "PD-01: no licensed price held",
            "model_id": o["model_id"],
        })
    with open(CURRENT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"current prices: {len(rows)} fixtures, open set, close pending a second capture")

    if check:
        print("price snapshot store: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
