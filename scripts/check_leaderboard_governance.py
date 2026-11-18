#!/usr/bin/env python3
"""R010 governance guard: backtest numbers must never appear on the prospective leaderboard.

Requirement (brief): "Pre-register every strategy; forbid backtest numbers from ever appearing
on the leaderboard." Readiness row R010 asks for machine-enforced dataset-type labels and a CI
check that rejects a backtest-origin row in the prospective leaderboard.

What this script enforces (exit 1 on any failure):

  1. The retrospective ranking (data/lab/leaderboard_v2.{csv,json}) is labelled
     dataset_type=RETROSPECTIVE_BACKTEST and prospective=false on the file AND on every row,
     and its CSV and JSON hold the same strategies.
  2. The page that shows that ranking (lab.html) carries the visible RETROSPECTIVE label.
  3. The prospective leaderboard files (data/leaderboard.csv, board/data/leaderboard.csv,
     data/dashboard/leaderboard.json) hold no backtest-origin row: no numeric skill / Brier / ROI /
     CLV result, no reference to the retrospective file, and no dataset_type=RETROSPECTIVE value.
  4. Any prospective row that DOES carry a numeric result must carry a forecast timestamp that
     precedes its kickoff. Today there are zero such rows, so the check asserts zero.

Deterministic, read-only, standard library only.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RETRO_CSV = "data/lab/leaderboard_v2.csv"
RETRO_JSON = "data/lab/leaderboard_v2.json"
RETRO_PAGE = "lab.html"
PROSPECTIVE_CSVS = ["data/leaderboard.csv", "board/data/leaderboard.csv"]
PROSPECTIVE_JSON = ["data/dashboard/leaderboard.json"]

RESULT_COLUMNS = ["beats_close_pct", "mean_clv_pts", "log_loss_vs_market", "roi_units",
                  "luck_adjusted_roi", "max_drawdown"]
NUMERIC_KEYS = {"brier", "brier_skill_vs_coin", "roi", "roi_units", "cluster_lower_bound",
                "skill", "clv", "mean_clv_pts", "luck_adjusted_roi"}
NUMBER = re.compile(r"^[+-]?\d+(\.\d+)?$")

failures: list[str] = []
passes: list[str] = []


def check(cond: bool, ok_msg: str, bad_msg: str) -> None:
    (passes if cond else failures).append(ok_msg if cond else bad_msg)


def read_text(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_csv(rel: str) -> list[dict]:
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def walk_numeric_keys(node, found: list[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if k.lower() in NUMERIC_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                found.append(f"{k}={v}")
            walk_numeric_keys(v, found)
    elif isinstance(node, list):
        for v in node:
            walk_numeric_keys(v, found)


def main() -> int:
    # 1. retrospective ranking labelled on file and on every row
    meta_doc = json.loads(read_text(RETRO_JSON))
    meta = meta_doc.get("_meta", {})
    check(meta.get("dataset_type") == "RETROSPECTIVE_BACKTEST" and meta.get("prospective") is False,
          "R010-1 retrospective ranking: file-level dataset_type=RETROSPECTIVE_BACKTEST, prospective=false",
          f"R010-1 FAIL: file-level label missing or wrong: {meta.get('dataset_type')!r}, {meta.get('prospective')!r}")

    json_rows = meta_doc.get("strategies", [])
    bad_json = [r.get("strategy") for r in json_rows
                if r.get("dataset_type") != "RETROSPECTIVE_BACKTEST" or r.get("prospective") is not False]
    check(bool(json_rows) and not bad_json,
          f"R010-1 retrospective ranking: all {len(json_rows)} JSON rows labelled RETROSPECTIVE_BACKTEST",
          f"R010-1 FAIL: JSON rows without the retrospective label: {bad_json or 'no rows'}")

    csv_rows = read_csv(RETRO_CSV)
    header = list(csv_rows[0].keys()) if csv_rows else []
    check("dataset_type" in header and "prospective" in header,
          "R010-1 retrospective ranking: CSV header carries dataset_type and prospective",
          "R010-1 FAIL: CSV header lacks dataset_type/prospective columns")
    bad_csv = [r.get("strategy") for r in csv_rows
               if r.get("dataset_type") != "RETROSPECTIVE_BACKTEST" or r.get("prospective") != "false"]
    check(bool(csv_rows) and not bad_csv,
          f"R010-1 retrospective ranking: all {len(csv_rows)} CSV rows labelled",
          f"R010-1 FAIL: CSV rows without the retrospective label: {bad_csv or 'no rows'}")
    same = [r["strategy"] for r in csv_rows] == [r["strategy"] for r in json_rows]
    check(same and len(csv_rows) == len(json_rows) > 0,
          "R010-1 retrospective ranking: CSV and JSON list the same strategies in the same order",
          "R010-1 FAIL: CSV and JSON disagree on the strategy list")

    # 2. visible label on the page that renders the ranking
    page = read_text(RETRO_PAGE)
    check("RETROSPECTIVE BACKTEST" in page and "not the prospective leaderboard" in page,
          "R010-2 lab.html: visible RETROSPECTIVE label above the ranking table",
          "R010-2 FAIL: lab.html does not carry the RETROSPECTIVE label")

    # 3. prospective leaderboards contain no backtest-origin rows
    for rel in PROSPECTIVE_CSVS:
        rows = read_csv(rel)
        numeric = [(r.get("strategy_id"), c, r.get(c)) for r in rows for c in RESULT_COLUMNS
                   if (r.get(c) or "").strip() != ""]
        numeric = [x for x in numeric if x[2] is not None]
        leaked = [x for x in numeric if NUMBER.match(x[2].strip())]
        text = read_text(rel)
        refs = ("leaderboard_v2" in text) or ("RETROSPECTIVE" in text) or ("lab/" in text)
        check(not leaked and not refs,
              f"R010-3 {rel}: {len(rows)} rows, no numeric result cells, no reference to the retrospective ranking",
              f"R010-3 FAIL {rel}: numeric result cells {leaked[:3]} or a retrospective reference")

    for rel in PROSPECTIVE_JSON:
        doc = json.loads(read_text(rel))
        found: list[str] = []
        walk_numeric_keys(doc, found)
        text = read_text(rel)
        refs = ("leaderboard_v2" in text) or ("RETROSPECTIVE" in text)
        check(not found and not refs,
              f"R010-3 {rel}: no numeric result keys, no reference to the retrospective ranking",
              f"R010-3 FAIL {rel}: numeric result keys {found[:3]} or a retrospective reference")

    # 4. any prospective row with a numeric result must be timestamped before kickoff
    prospective_with_results = 0
    for rel in PROSPECTIVE_CSVS:
        for r in read_csv(rel):
            if any(NUMBER.match((r.get(c) or "").strip()) for c in RESULT_COLUMNS):
                prospective_with_results += 1
    check(prospective_with_results == 0,
          "R010-4 prospective leaderboard: 0 rows carry a numeric result, so 0 need a pre-kickoff timestamp",
          f"R010-4 FAIL: {prospective_with_results} prospective rows carry numeric results and no timestamp rule is enforced")

    for p in passes:
        print("PASS  " + p)
    for f in failures:
        print("FAIL  " + f)
    if failures:
        print(f"\nR010 GOVERNANCE: {len(failures)} FAILURE(S)")
        return 1
    print(f"\nR010 GOVERNANCE: ALL {len(passes)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
