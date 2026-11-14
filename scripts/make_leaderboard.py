#!/usr/bin/env python3
"""Build data/leaderboard.csv from the strategy registry.

The board is an *empty scoreboard with a real schema*, by design: no metric is filled until a settled
bet exists against a timestamped, sealed prediction. Filling a cell with an estimate here would be the
exact failure mode the rest of the repo is organised to prevent.

It also enforces two structural facts a human tends to forget:
  * strategies that share a causal driver are shown as one exposure group, so six "independent"
    injury-report angles cannot be presented as six edges (gate G-08);
  * every row states which gate it is stuck on, so "why is the board blank" has a per-row answer.

Usage: python3 scripts/make_leaderboard.py
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_fl3 import REPO, read_rows, write_rows  # noqa: E402

REGISTRY = os.path.join(REPO, "models", "strategy_registry.yaml")

COLUMNS = ["strategy_id", "strategy", "family", "tier", "exposure_group", "bets", "beats_close_pct",
           "mean_clv_pts", "log_loss_vs_market", "roi_units", "luck_adjusted_roi", "max_drawdown",
           "gate_status", "status", "config_hash", "correlation_to_same_driver", "source_id"]

BLOCKING_GATES = {
    "Q-01": "G-03 (CLV) + G-06 (executable prices) - no market data",
    "Q-02": "G-01 sample blocked upstream - lineups unavailable",
    "Q-03": "availability module not computable - IR invisible",
    "Q-04": "G-01/G-05 - only 33 of 137 verified games ingested",
    "Q-07": "G-07 - correlation not measured",
    "Q-08": "player-level rates absent - props unpriceable",
    "Q-09": "G-13 - push/tie treatment unconfirmed",
}


def parse_registry(path):
    """Deliberately tiny YAML reader: this file is ours, flat and list-shaped - no dependency needed."""
    items, cur, mode = [], None, None
    with open(path, encoding="utf-8") as fh:
        for raw in fh.read().splitlines():
            if not raw.strip() or raw.strip().startswith("#"):
                continue
            if raw.startswith("strategies:"):
                mode = "strategies"
                continue
            if mode != "strategies":
                continue
            if raw.startswith("  - "):
                cur = {}
                items.append(cur)
                body = raw[4:]
            elif raw.startswith("    ") and cur is not None and ":" in raw:
                body = raw.strip()
            else:
                continue
            key, _, val = body.partition(":")
            key = key.strip().lstrip("-").strip()
            val = val.split("#")[0].strip()
            if val.startswith("[") and val.endswith("]"):
                val = [x.strip() for x in re.split(r",\s*", val[1:-1]) if x.strip()]
            cur[key] = val
    return [i for i in items if i.get("id")]


def main() -> int:
    signals = {r["id"]: r for r in read_rows("signals.csv")}
    try:
        ledger = read_rows("bet_ledger.csv")
    except FileNotFoundError:
        ledger = []
        print("leaderboard: no data/bet_ledger.csv yet - the board is a schema, not a record")
    settled = {}
    for bet in ledger:
        settled.setdefault(bet.get("strategy_id", ""), []).append(bet)

    rows = []
    for st in parse_registry(REGISTRY):
        sid = st["id"]
        sig = signals.get(st.get("signal", ""), {})
        mine = settled.get(sid, [])
        drivers = st.get("same_driver") or []
        n_share = len(drivers) if isinstance(drivers, list) else 0
        group = sid if not n_share else f"{sid} + {n_share} same-driver"
        blocked = st.get("blocked_by") or []
        if isinstance(blocked, str):
            blocked = [blocked]
        gates = sorted({BLOCKING_GATES.get(q, q) for q in blocked if q})
        rows.append({
            "strategy_id": sid,
            "strategy": st.get("name", ""),
            "family": st.get("family", sig.get("family", "")),
            "tier": st.get("tier", "spec"),
            "exposure_group": group,
            "bets": str(len(mine)),
            "beats_close_pct": "",
            "mean_clv_pts": "",
            "log_loss_vs_market": "",
            "roi_units": "",
            "luck_adjusted_roi": "",
            "max_drawdown": "",
            "gate_status": ("no blockers listed" if not gates else "blocked - " + "; ".join(gates)),
            "status": "no settled bets" if not mine else "tracking",
            "config_hash": st.get("config_hash", "") or "unsealed (no live tier yet)",
            "correlation_to_same_driver": sig.get("correlation_note", ""),
            "source_id": "SRC-001;SRC-002;SRC-003;SRC-004;SRC-005;SRC-006;SRC-007",
        })
    write_rows("leaderboard.csv", rows, COLUMNS)
    live = sum(1 for r in rows if r["bets"] != "0")
    print(f"leaderboard: {len(rows)} strategies, {live} with settled bets "
          f"(blank cells are deliberate - see models/leaderboard.yaml)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
