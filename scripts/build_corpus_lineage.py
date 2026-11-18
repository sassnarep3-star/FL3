#!/usr/bin/env python3
"""Build a dated, source-linked audit of the repository's distinct results corpora.

This script does NOT fetch nfl.com and does NOT alter any historical forecast or score. It
cross-checks the committed 148-row comparison input against the 149-row corrected official-feed
snapshot, makes their different capture times explicit, and leaves the post-capture LAC@BAL outcome
blank pending a new official result capture.

Run:
    python3 scripts/build_corpus_lineage.py          # write JSON + HTML
    python3 scripts/build_corpus_lineage.py --check  # verify outputs are reproducible
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import html
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_JSON = DATA / "compare" / "corpus_lineage.json"
OUT_HTML = ROOT / "docs" / "corpus-lineage.html"

BASE_INPUT = DATA / "week_results_2026.csv"
COMPARISON_LEDGER = DATA / "compare" / "forecast_ledger.csv"
COMPARISON_EVALUATION = DATA / "compare" / "evaluation.json"
COMPARISON_RECON = DATA / "compare" / "corpus_reconciliation.json"
OFFICIAL_FEED = DATA / "official" / "results_feed.csv"
OFFICIAL_META = DATA / "official" / "results_feed.json"
OFFICIAL_RECON = DATA / "official" / "club_reconciliation.csv"

EXPECTED_BASE_GAMES = 148
EXPECTED_BRIEF_GAMES = 136
EXPECTED_CORRECTION_GAMES = 149
OFFICIAL_SCHEDULE_PREFIX = "https://www.nfl.com/schedules/2026/by-week/week-"

checks = 0


def require(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        obj = json.load(handle)
    require(isinstance(obj, dict), f"{path.relative_to(ROOT)} is not a JSON object")
    return obj


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def game_key(row: dict[str, str], *, compare: bool = False) -> tuple[str, ...]:
    if compare:
        return (row["week"], row["date"], row["away"], row["away_pts"], row["home"], row["home_pts"])
    return (row["week"], row["game_date"], row["away_abbr"], row["away_pts"],
            row["home_abbr"], row["home_pts"])


def is_official_schedule_url(url: str, week: str) -> bool:
    return url == f"{OFFICIAL_SCHEDULE_PREFIX}{int(week)}"


def official_url(url: str) -> bool:
    return url.startswith("https://www.nfl.com/") or url.startswith("https://static.www.nfl.com/")


def nice_week(week: int) -> str:
    return f"Week {week}"


def build_manifest() -> dict[str, Any]:
    base = read_csv(BASE_INPUT)
    ledger = read_csv(COMPARISON_LEDGER)
    evaluation = read_json(COMPARISON_EVALUATION)
    comparison_recon = read_json(COMPARISON_RECON)
    feed = read_csv(OFFICIAL_FEED)
    feed_meta = read_json(OFFICIAL_META)
    club_recon = read_csv(OFFICIAL_RECON)

    require(bool(base), "the captured 2026 comparison input is empty")
    base_weeks = collections.Counter(int(row["week"]) for row in base)
    base_capture_times = sorted({row["accessed_utc"] for row in base})
    schedule_urls = sorted({row["source_url"] for row in base}, key=lambda url: int(url.rsplit("-", 1)[1]))
    require(len(base) == EXPECTED_BASE_GAMES,
            f"expected the preserved comparison input to contain {EXPECTED_BASE_GAMES} rows; found {len(base)}")
    require(sum(count for week, count in base_weeks.items() if week <= 9) == EXPECTED_BRIEF_GAMES,
            "weeks 1-9 of the preserved input no longer equal the brief's 136-game window")
    require(base_weeks.get(10) == 12,
            f"expected 12 Week 10 rows in the original capture; found {base_weeks.get(10)}")
    require(base_capture_times == ["2026-11-16T01:35Z"],
            f"unexpected/mixed capture clocks in the preserved input: {base_capture_times}")
    require(len(schedule_urls) == 10,
            f"expected one official schedule URL for each of Weeks 1-10; found {len(schedule_urls)}")
    for row in base:
        require(is_official_schedule_url(row["source_url"], row["week"]),
                f"base game {game_key(row)} has a non-canonical official source URL: {row['source_url']}")

    base_keys = [game_key(row) for row in base]
    require(len(base_keys) == len(set(base_keys)), "the captured comparison input has duplicate game rows")
    ledger_keys = [game_key(row, compare=True) for row in ledger]
    require(len(ledger) == EXPECTED_BASE_GAMES,
            f"expected {EXPECTED_BASE_GAMES} rows in the comparison forecast ledger; found {len(ledger)}")
    require(collections.Counter(ledger_keys) == collections.Counter(base_keys),
            "the retrospective forecast ledger does not contain exactly the same outcomes as the captured 148-row input")
    for row in ledger:
        require(is_official_schedule_url(row["source_url"], row["week"]),
                f"comparison ledger row {game_key(row, compare=True)} has a non-official source URL")
    eval_meta = evaluation.get("meta", {})
    require(eval_meta.get("games") == EXPECTED_BASE_GAMES,
            f"comparison evaluation declares {eval_meta.get('games')} games, not {EXPECTED_BASE_GAMES}")
    require(eval_meta.get("dataset") == "retrospective",
            "the comparison output is not labelled retrospective")
    require(len([row for row in ledger if int(row["week"]) == 10]) == 12,
            "the retrospective ledger no longer has 12 Week 10 outcomes")
    require(not any(row["week"] == "10" and row["away"] == "PIT" and row["home"] == "CIN"
                    for row in ledger),
            "the post-capture PIT@CIN correction has unexpectedly entered the old comparison ledger")

    chain = comparison_recon.get("chain", [])
    require(len(chain) == 5, f"the dated comparison reconciliation has {len(chain)} steps, not 5")
    require([row.get("games") for row in chain] == [136, 1, 137, 11, 148],
            f"the preserved comparison reconciliation changed: {[row.get('games') for row in chain]}")
    require(comparison_recon.get("source", {}).get("read_utc", "").startswith("2026-11-16T01:35Z"),
            "the comparison reconciliation no longer identifies its original capture time")

    feed_meta_rec = feed_meta.get("reconciliation", {})
    declaration = feed_meta.get("corpus_declaration", {})
    feed_capture = feed_meta.get("_meta", {}).get("captured_utc", "")
    brief_metadata_note = declaration.get("note_on_the_brief", "")
    require(bool(brief_metadata_note), "the corrected-feed metadata has no note on the brief's 136-game wording")
    brief_note_denies_reproduction = "136 is not reproducible" in brief_metadata_note.lower()
    brief_window_games = sum(count for week, count in base_weeks.items() if week <= 9)
    brief_scope_conflict = brief_window_games == EXPECTED_BRIEF_GAMES and brief_note_denies_reproduction
    require(feed_capture == "2026-11-17T02:47Z",
            f"unexpected corrected-feed capture time in metadata: {feed_capture!r}")
    require(len(feed) == EXPECTED_CORRECTION_GAMES,
            f"expected {EXPECTED_CORRECTION_GAMES} rows in the captured corrected results feed; found {len(feed)}")
    require(declaration.get("games") == EXPECTED_CORRECTION_GAMES,
            f"the preregistered feed declaration says {declaration.get('games')} games")
    require(feed_meta_rec.get("corpus_games") == EXPECTED_BASE_GAMES,
            "the correction metadata no longer refers to the original 148-row input")
    require(feed_meta_rec.get("official_games_played") == EXPECTED_CORRECTION_GAMES,
            "the official games-played count in the correction metadata is not 149")
    require(feed_meta_rec.get("result_after_correction", {}).get("games") == EXPECTED_CORRECTION_GAMES,
            "the post-correction result declaration is not 149 games")

    feed_by_origin = collections.defaultdict(list)
    feed_keys = []
    ids = []
    for row in feed:
        require(row["status"] == "FINAL_VERIFIED",
                f"results-feed row {row['game_id']} is not marked FINAL_VERIFIED")
        require(is_official_schedule_url(row["source_url"], row["week"]),
                f"results-feed row {row['game_id']} has a non-official source URL: {row['source_url']}")
        key = game_key(row, compare=True)
        feed_keys.append(key)
        feed_by_origin[row["origin"]].append(row)
        ids.append(row["game_id"])
    require(len(ids) == len(set(ids)), "the results feed has duplicate game IDs")
    require(collections.Counter(game_key(row, compare=True) for row in feed_by_origin["corpus_148"])
            == collections.Counter(base_keys),
            "the corpus_148-origin rows in the corrected feed do not equal the original 148-row input")
    corrections = feed_by_origin["correction_2026-11-17"]
    require(len(corrections) == 1,
            f"expected exactly one 2026-11-17 correction row; found {len(corrections)}")
    correction = corrections[0]
    declared_correction = feed_meta_rec.get("correction", {})
    correction_expected = (
        declared_correction.get("date"), declared_correction.get("away"),
        str(declared_correction.get("away_pts")), declared_correction.get("home"),
        str(declared_correction.get("home_pts")),
    )
    require(correction["game_id"] == declared_correction.get("game_id"),
            "the results-feed correction game ID disagrees with the registered correction")
    require((correction["date"], correction["away"], correction["away_pts"], correction["home"],
             correction["home_pts"]) == correction_expected,
            "the correction row does not match the registered Week 10 score")
    require((correction["week"], correction["away"], correction["home"], correction["away_pts"],
             correction["home_pts"]) == ("10", "PIT", "CIN", "18", "38"),
            "the only added official result is no longer the recorded PIT@CIN Week 10 correction")
    require(correction["source_url"] == declared_correction.get("source_url"),
            "the correction's source URL differs from its evidence record")
    require(official_url(correction["source_url"]), "the correction row is not linked to an official NFL source")

    # The snapshot explicitly excludes LAC@BAL while its game centre showed Q2 01:05.
    # This report does not convert that capture-time state into a present-day result.
    excluded = feed_meta_rec.get("excluded_from_all_evaluation", [])
    lac_bal = next((row for row in excluded if row.get("game_id") == "REG10-LAC-BAL"), None)
    require(lac_bal is not None, "the dated feed metadata lost its LAC@BAL exclusion record")
    require(official_url(lac_bal.get("source_url", "")), "the LAC@BAL exclusion has no official game-centre source")
    require(not any(row["away"] == "LAC" and row["home"] == "BAL" for row in feed),
            "the LAC@BAL result has been added to the feed but the exclusion metadata was not versioned")
    require(not any(row["away_abbr"] == "LAC" and row["home_abbr"] == "BAL" for row in base),
            "the LAC@BAL result has unexpectedly entered the earlier comparison input")

    # Reconcile the feed's derived club record to its official-source comparison table.
    club_rows = read_csv(OFFICIAL_RECON)
    require(len(club_rows) == 32, f"expected 32 official club-reconciliation rows; found {len(club_rows)}")
    by_club: dict[str, dict[str, int]] = {}
    for row in feed:
        for club, scored, allowed in ((row["away"], int(row["away_pts"]), int(row["home_pts"])),
                                      (row["home"], int(row["home_pts"]), int(row["away_pts"]))):
            state = by_club.setdefault(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "games": 0})
            state["games"] += 1
            state["pf"] += scored
            state["pa"] += allowed
            if scored > allowed:
                state["w"] += 1
            elif scored < allowed:
                state["l"] += 1
            else:
                state["t"] += 1
    require(len(by_club) == 32, f"the results feed covers {len(by_club)} clubs, not 32")
    standings_url = feed_meta_rec.get("official_standings_url", "")
    require(official_url(standings_url), "the official standings reconciliation URL is missing or non-official")
    recon_by_club = {row["club"]: row for row in club_rows}
    require(len(recon_by_club) == 32, "club-reconciliation table has duplicate club rows")
    for club, values in by_club.items():
        row = recon_by_club.get(club)
        require(row is not None, f"club {club} is missing from the official reconciliation")
        require(row["verdict"] == "MATCH", f"club {club} is marked {row['verdict']}, not MATCH")
        require(row["source_url"] == standings_url, f"club {club} does not link to the official standings source")
        require((int(row["corpus_games"]), int(row["corpus_w"]), int(row["corpus_l"]), int(row["corpus_t"]),
                 int(row["corpus_pf"]), int(row["corpus_pa"]))
                == (values["games"], values["w"], values["l"], values["t"], values["pf"], values["pa"]),
                f"club {club} reconciliation values do not reproduce from results_feed.csv")
        require((int(row["official_w"]), int(row["official_l"]), int(row["official_t"]),
                 int(row["official_pf"]), int(row["official_pa"]))
                == (values["w"], values["l"], values["t"], values["pf"], values["pa"]),
                f"club {club} official reconciliation does not match the 149-row feed values")

    require(sum(v["pf"] for v in by_club.values()) == sum(v["pa"] for v in by_club.values()),
            "the corrected feed's league points do not balance")
    result_after = feed_meta_rec.get("result_after_correction", {})
    require(sum(v["pf"] for v in by_club.values()) == result_after.get("league_pf_sum"),
            "league points-for total disagrees with results_feed.json")
    require(sum(v["pa"] for v in by_club.values()) == result_after.get("league_pa_sum"),
            "league points-against total disagrees with results_feed.json")

    require(all(official_url(url) for url in schedule_urls), "a source schedule URL is not an official NFL URL")
    correction_url = declared_correction.get("source_url", "")
    lac_bal_url = lac_bal["source_url"]
    standings_url = feed_meta_rec["official_standings_url"]
    all_sources = list(dict.fromkeys(schedule_urls + [correction_url, lac_bal_url, standings_url]))
    require(all(official_url(url) for url in all_sources), "lineage source registry contains a non-official URL")
    for href in ("assets/style.css", "index.html", "../index.html", "../results.html",
                 "../compare.html", "../flagged.html"):
        target = (OUT_HTML.parent / href).resolve()
        require(target.is_file(), f"the generated lineage page would link to missing local target: {href}")

    return {
        "schema": "fl3.results-corpus-lineage.v1",
        "title": "Results corpus lineage — captured comparison vs corrected results feed",
        "basis": "committed repository captures only; no live NFL page fetched by this builder",
        "updated_from_current_sources": False,
        "decision": "Preserve the existing 148-row retrospective comparison output as its own version. "
                    "Do not silently overwrite its scores with the later corrected feed. The feed snapshot is "
                    "149 rows as of its recorded capture, while LAC@BAL was excluded in progress; re-capture "
                    "the official final result before describing this as the current complete Week 10 count.",
        "versions": [
            {
                "id": "brief-weeks-1-9",
                "label": "136-row Weeks 1–9 slice (labelled by the repo as the brief's 136-game log)",
                "games": EXPECTED_BRIEF_GAMES,
                "weeks": list(range(1, 10)),
                "input_file": str(BASE_INPUT.relative_to(ROOT)),
                "capture_utc": base_capture_times[0],
                "official_source_urls": [f"{OFFICIAL_SCHEDULE_PREFIX}{week}" for week in range(1, 10)],
                "meaning": "The 136 rows are exactly the captured Weeks 1–9 slice. They are not the 148-row "
                           "comparison input and are not the corrected 149-row results feed.",
            },
            {
                "id": "comparison-snapshot-148",
                "label": "Saved retrospective comparison input",
                "games": len(base),
                "weeks": sorted(base_weeks),
                "input_file": str(BASE_INPUT.relative_to(ROOT)),
                "ledger_file": str(COMPARISON_LEDGER.relative_to(ROOT)),
                "evaluation_file": str(COMPARISON_EVALUATION.relative_to(ROOT)),
                "capture_utc": base_capture_times[0],
                "official_source_urls": schedule_urls,
                "meaning": "The comparison ledger and evaluation both use these 148 captured rows, including "
                           "12 Week 10 results. They do not include the later PIT@CIN correction. The existing "
                           "metrics remain a dated retrospective output, not a rerun on the corrected feed.",
            },
            {
                "id": "corrected-results-feed-149",
                "label": "Corrected official results-feed snapshot",
                "games": len(feed),
                "weeks": sorted({int(row["week"]) for row in feed}),
                "input_file": str(OFFICIAL_FEED.relative_to(ROOT)),
                "metadata_file": str(OFFICIAL_META.relative_to(ROOT)),
                "capture_utc": feed_capture,
                "official_source_urls": [correction_url, standings_url],
                "meaning": "The committed feed contains the 148 original rows plus one officially sourced "
                           "PIT@CIN Week 10 correction, and all 32 clubs match its linked standings snapshot. "
                           "It is a dated capture, not a claim that the current Week 10 result feed is complete.",
            },
        ],
        "brief_136_review": {
            "status": "FLAGGED_FOR_REVIEW" if brief_scope_conflict else "NO_CONTRADICTION_RECORDED",
            "captured_weeks_1_9_rows": brief_window_games,
            "comparison_reconciliation_label": chain[0].get("matches", ""),
            "corrected_feed_metadata_note": brief_metadata_note,
            "finding": "The committed schedule transcript contains exactly 136 rows in Weeks 1-9, and the comparison reconciliation labels that slice as matching the brief's '136-game log'. The later results-feed metadata says 136 is not reproducible from an official page. These statements conflict if read as a blanket claim; the local evidence confirms 136 as a Weeks 1-9 slice, but does not establish whether that is the exact historical log the brief meant.",
            "decision_needed": "Confirm the intended 136-game source/window or explicitly designate the dated 148/149 snapshots as separate corpora. Do not silently reinterpret 136 as a full-season count.",
            "official_source_urls": [f"{OFFICIAL_SCHEDULE_PREFIX}{week}" for week in range(1, 10)],
        },
        "correction": {
            "game_id": correction["game_id"],
            "week": int(correction["week"]),
            "date": correction["date"],
            "away": correction["away"],
            "away_points": int(correction["away_pts"]),
            "home": correction["home"],
            "home_points": int(correction["home_pts"]),
            "origin": correction["origin"],
            "source_url": correction_url,
            "evidence_text": declared_correction.get("evidence", ""),
        },
        "unresolved_capture": {
            "game_id": lac_bal["game_id"],
            "fixture": "LAC@BAL",
            "capture_state": "excluded from the 2026-11-17T02:47Z results-feed snapshot",
            "captured_reason": lac_bal["reason"],
            "source_url": lac_bal_url,
            "current_official_final": None,
            "current_official_final_status": "NOT RECAPTURED IN THIS REPOSITORY SNAPSHOT",
            "what_clears_it": "Re-read the official game centre and, where available, the NFL Game Book; "
                              "record a timestamped final score and source hash in a new feed version. Do not "
                              "infer a score from the in-progress capture.",
        },
        "evaluation_guard": {
            "comparison_games": len(ledger),
            "comparison_dataset_type": eval_meta["dataset"],
            "correction_in_old_ledger": False,
            "historical_scores_rewritten": False,
            "next_step": "After an authorized official re-capture, create a new versioned result/evaluation "
                         "snapshot; preserve the current 148-row outputs for audit, and disclose the n and "
                         "chronological holdout used by any new score.",
        },
        "reconciliation": {
            "club_rows": len(club_rows),
            "clubs_matching": sum(1 for row in club_rows if row["verdict"] == "MATCH"),
            "league_points_for": sum(v["pf"] for v in by_club.values()),
            "league_points_against": sum(v["pa"] for v in by_club.values()),
            "official_standings_url": standings_url,
        },
        "hashes_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (BASE_INPUT, COMPARISON_LEDGER, COMPARISON_EVALUATION,
                         OFFICIAL_FEED, OFFICIAL_META, OFFICIAL_RECON)
        },
        "official_sources": all_sources,
    }


def source_links(urls: list[str], labels: list[str] | None = None) -> str:
    labels = labels or [f"Source {i + 1}" for i in range(len(urls))]
    anchors = []
    for label, url in zip(labels, urls):
        anchors.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
                       f"{html.escape(label)}</a>")
    return " · ".join(anchors)


def render_html(data: dict[str, Any]) -> str:
    versions = data["versions"]
    schedule_1_9 = versions[0]["official_source_urls"]
    schedule_1_10 = versions[1]["official_source_urls"]
    correction_url = data["correction"]["source_url"]
    standings_url = data["reconciliation"]["official_standings_url"]
    unresolved_url = data["unresolved_capture"]["source_url"]
    brief_review = data["brief_136_review"]
    brief_urls = brief_review["official_source_urls"]
    brief_status = ("<span class=\"badge badge-warn\">FLAGGED FOR REVIEW</span>"
                    if brief_review["status"] == "FLAGGED_FOR_REVIEW"
                    else "<span class=\"badge badge-ok\">NO CONFLICT RECORDED</span>")

    rows = [
        ["<b>136-row Weeks 1–9 slice</b>", "136", "Weeks 1–9", versions[0]["capture_utc"],
         html.escape(versions[0]["meaning"]), source_links(schedule_1_9, [nice_week(i) for i in range(1, 10)])],
        ["<b>Saved retrospective comparison</b>", "148", "Weeks 1–10 (12 Week 10 rows)",
         versions[1]["capture_utc"], html.escape(versions[1]["meaning"]),
         source_links(schedule_1_10, [nice_week(i) for i in range(1, 11)])],
        ["<b>Corrected results-feed snapshot</b>", "149", "Weeks 1–10 (13 Week 10 rows)",
         versions[2]["capture_utc"], html.escape(versions[2]["meaning"]),
         source_links([correction_url, standings_url], ["Week 10 schedule: PIT@CIN correction", "Official standings reconciliation"])],
        ["<b>LAC@BAL after the capture</b>", '<span class="badge badge-warn">blank</span>', "Not re-captured here",
         "2026-11-17T02:47Z capture excluded it while in progress",
         "The current final score is deliberately blank: this repository snapshot contains no later official result row. Re-capture before calling the feed current or changing the count.",
         source_links([unresolved_url, correction_url], ["Official game centre", "Week 10 schedule"])],
    ]
    table_rows = "\n".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    hashes = "\n".join(f"{name}: {digest}" for name, digest in data["hashes_sha256"].items())
    source_registry = "\n".join(f'<li><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
                                 f"{html.escape(url)}</a></li>" for url in data["official_sources"])
    json_block = html.escape(json.dumps(data, ensure_ascii=False, indent=2))

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Results corpus lineage · FL3</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="brand"><a href="../index.html">FL3</a><span class="brand-sub">Results corpus lineage</span></div>
  <div class="topbar-note">Committed snapshots only · no live NFL fetch by this report</div>
</header>
<div class="layout">
  <nav class="sidebar" aria-label="Page links">
    <div class="nav-cat"><div class="nav-cat-title">Navigate</div>
      <a class="nav-item" href="../index.html">Main dashboard</a>
      <a class="nav-item" href="index.html">Documentation dashboard</a>
      <a class="nav-item" href="../results.html">Results feed</a>
      <a class="nav-item" href="../compare.html">Strategy comparison</a>
      <a class="nav-item" href="../flagged.html">Flagged for Review</a>
    </div>
  </nav>
  <main class="content">
    <h1>Which results count is which?</h1>
    <p class="lede">This audit compares the repository's preserved 148-row retrospective input with its later
    149-row corrected results-feed snapshot. It reads committed files only; the builder does not fetch NFL.com.
    Official links are provided in every row so the underlying schedule, game centre and standings can be
    reviewed directly. No existing forecast, score or result row was changed to create this report.</p>

    <div class="cards">
      <div class="card"><div class="stat-num">136</div><div class="stat-label">Weeks 1–9 slice in the original capture</div></div>
      <div class="card"><div class="stat-num">148</div><div class="stat-label">Rows used by the retrospective comparison</div></div>
      <div class="card"><div class="stat-num">149</div><div class="stat-label">Rows in the later corrected-feed snapshot</div></div>
    </div>

    <div class="warn-note"><b>Important limitation.</b> These are versioned counts, not one interchangeable sample.
    The 148-row comparison predates the PIT@CIN correction. The 149-row feed snapshot is dated
    <code>{html.escape(versions[2]["capture_utc"])}</code> and excludes LAC@BAL while the recorded official capture
    showed it in progress. Its later final result has not been re-captured in this repository snapshot, so
    <b>149 must not be described as the current complete Week 10 result count</b>.</div>

    <h2>Counts and the evidence behind them</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Version</th><th>Games</th><th>Window / rows</th><th>Capture clock</th><th>What it means</th><th>Official source links</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table></div>

    <h2>Flagged for Review — what does “136-game log” mean?</h2>
    <div class="warn-note">{brief_status}
      <p>The committed schedule transcript has <b>{brief_review["captured_weeks_1_9_rows"]}</b> rows across Weeks 1–9, and the earlier comparison reconciliation labels that slice as matching the brief's “136-game log”. The later results-feed metadata says: <q>{html.escape(brief_review["corrected_feed_metadata_note"])}</q></p>
      <p>Those statements conflict if the latter is read as saying that 136 cannot be reproduced at all. The saved rows establish 136 as a Weeks 1–9 slice; they do <b>not</b> establish whether that is the exact historical file or time window the brief intended. Do not treat 136 as the full Week 10 count or silently substitute 148/149.</p>
      <p><b>Decision needed:</b> identify the intended 136-game source/window, or explicitly register the dated 148/149 snapshots as separate corpora. Until then, retain each version and its timestamps.</p>
      <p class="src-links">{source_links(brief_urls, [nice_week(i) for i in range(1, 10)])}</p>
    </div>

    <h2>Correction recorded after the 148-row capture</h2>
    <div class="card">
      <p><b>{html.escape(data["correction"]["game_id"])}</b> — Week {data["correction"]["week"]},
      {html.escape(data["correction"]["away"])} {data["correction"]["away_points"]},
      {html.escape(data["correction"]["home"])} {data["correction"]["home_points"]}.
      The feed records it as <code>{html.escape(data["correction"]["origin"])}</code>; the linked official Week 10
      schedule is the cited evidence. The 149-row feed then reconciles all 32 club records to the linked
      official standings snapshot ({data["reconciliation"]["clubs_matching"]}/32 MATCH; league PF = PA =
      {data["reconciliation"]["league_points_for"]:,}).</p>
      <p class="src-links">{source_links([correction_url, standings_url], ["Official Week 10 schedule", "Official league standings"])}</p>
    </div>

    <h2>What the comparison does and does not score</h2>
    <ul>
      <li>The retrospective comparison ledger has <b>{data["evaluation_guard"]["comparison_games"]}</b> rows and is labelled
      <code>{html.escape(data["evaluation_guard"]["comparison_dataset_type"])}</code>. Its score metrics must be read as the
      saved 148-row version, not as results computed on the later corrected feed.</li>
      <li>The Week 10 PIT@CIN correction is <b>not</b> in that old ledger. This report preserves the existing
      scores rather than silently adding a game after evaluation.</li>
      <li>The official results-feed metadata records LAC@BAL as excluded at the 2026-11-17 capture because
      the game was not final then. The current official final score is intentionally blank here until a
      later source read is captured and hashed.</li>
      <li>Any new evaluation should be a separately versioned run: freeze its corpus, preserve its source
      timestamps/hashes, use chronological holdouts, and publish an explicit <code>n</code> for each metric.</li>
    </ul>

    <div class="note"><b>Next clearing evidence.</b> Re-read the official LAC@BAL game centre and, where available,
    the NFL Game Book; capture a timestamp and raw-file hash; then add a new results-feed version. Only after
    that should a new, separately identified evaluation be generated. Until then the current-score field stays
    blank and no present-day final count is asserted.</div>

    <h2>Integrity fingerprints</h2>
    <p>The SHA-256 values below identify the exact committed files audited by this page. They are not hashes
    of the NFL pages themselves; the report did not fetch or archive those pages in this turn.</p>
    <div class="card"><pre>{html.escape(hashes)}</pre></div>

    <details class="card">
      <summary>Machine-readable lineage manifest</summary>
      <pre>{json_block}</pre>
    </details>

    <h2>Registered official source list</h2>
    <ul>{source_registry}</ul>
  </main>
</div>
<footer class="footer">FL3 · sourced from repository snapshots; no new NFL values inferred. A blank means the current official outcome was not re-captured in this report.</footer>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate and require committed outputs to match")
    args = parser.parse_args()
    try:
        manifest = build_manifest()
        json_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        html_text = render_html(manifest)
        outputs = ((OUT_JSON, json_text), (OUT_HTML, html_text))
        if args.check:
            stale = []
            for path, expected in outputs:
                if not path.exists() or path.read_text(encoding="utf-8") != expected:
                    stale.append(str(path.relative_to(ROOT)))
            if stale:
                print("corpus lineage outputs are missing or stale: " + ", ".join(stale), file=sys.stderr)
                return 1
        else:
            for path, content in outputs:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        print(f"Corpus lineage PASS: {EXPECTED_BRIEF_GAMES} weeks 1-9 rows; "
              f"{EXPECTED_BASE_GAMES} saved comparison rows; {EXPECTED_CORRECTION_GAMES} corrected-feed rows; "
              "LAC@BAL current outcome intentionally unverified")
        print(f"ran {checks} lineage assertions")
        return 0
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"corpus lineage ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
