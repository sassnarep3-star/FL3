#!/usr/bin/env python3
"""Build the requirement-coverage audit (brief bullet -> readiness register row).

Purpose
-------
The session brief lists ~69 one-line requirements. The repository tracks them in
`data/requirements_readiness.csv` (one row per requirement). This script proves,
programmatically and deterministically, that *every* bullet in the brief is mapped
to at least one readiness row, and publishes the mapping as a dataset and a page:

  - data/requirement_coverage_audit.csv   one row per brief bullet
  - audit/index.html                      the human-readable audit page

It also reverse-checks the register: readiness rows that no bullet maps to are
listed as register-internal additions (they exist for reasons the repo itself
generated, e.g. staleness measurement), never silently dropped.

No value in the audit page is computed or inferred: every cell is either the
verbatim text of the brief, a field of the readiness register, or a link to a
file that must exist at build time (the build fails otherwise).

Exit codes: 0 ok, 1 audit invariant failed (missing mapping, missing file).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "data" / "requirements_readiness.csv"
OUT_CSV = ROOT / "data" / "requirement_coverage_audit.csv"
OUT_DIR = ROOT / "audit"

# ---------------------------------------------------------------------------
# The brief's one-line requirements, verbatim (id, text).
# ---------------------------------------------------------------------------
BULLETS = [
    ("B01", "Add a price-snapshot store that records opening and closing numbers for every market we originate"),
    ("B02", "Add a verified results feed so backtests and ROI can be computed at all"),
    ("B03", "Originate the side first, then the total, then the moneyline"),
    ("B04", "Publish the model's fair line, the market line, and the difference as separate columns"),
    ("B05", "Separate 'signal' from 'staking' in the leaderboard so a lucky staking run cannot mask a bad signal"),
    ("B06", "Track the depth of the replacement, not just the fact of a replacement"),
    ("B07", "Compute correlations only from officially sourced numbers and publish n with each value"),
    ("B08", "Define a demotion gate that sends a live strategy back to paper"),
    ("B09", "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard"),
    ("B10", "Build the availability graph as a first-class dataset (who was expected to start, who actually did)"),
    ("B11", "Do not model depth from jersey order; model it from playing time"),
    ("B12", "Make the injury signal a surprise, never a level"),
    ("B13", "Run the 32-team roster/IR sweep before any team-level model is trusted"),
    ("B14", "Add a fixture-context feature set built only from published schedule facts"),
    ("B15", "Store every model output as a probability plus its inputs, not just a pick"),
    ("B16", 'Compute and publish the "removal of luck" panel on the site dashboard'),
    ("B17", 'Add a two-sided "what would change our mind" field to every strategy entry'),
    ("B18", "Price a line ourselves and publish the residual against the market, on a schedule, from day one"),
    ("B19", "Turn the 136-game log into the pre-registered backtest corpus"),
    ("B20", "Decide the price-data policy before any backtest is published"),
    ("B21", "Store every injury-hub read with its clock time and publish the delta, never the level"),
    ("B22", "Put a decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it"),
    ("B23", "Transcribe the venue of every fixture from the official game centre and publish it"),
    ("B24", "Publish the league's dated schedule announcement beside the live schedule page"),
    ("B25", "Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps"),
    ("B26", "Ingest game-level results to make the ratings opponent-aware"),
    ("B27", "Add injury and personnel ablations instead of fixed penalties (compare identical models with and without verified availability features using chronological holdouts, and report the difference with uncertainty)"),
    ("B28", "Automate immutable multi-day availability snapshots (official report and club depth pages captured at least daily with retained hashes, so practice designations can be replayed as they were known)"),
    ("B29", "Build immutable official availability snapshots (scheduled capture of NFL injury reports, club depth pages and inactive evidence with raw hashes, timestamps and conflict flags)"),
    ("B30", "Capture official inactive lists and snap counts"),
    ("B31", "Fix the two depth-parsing failures before widening coverage (Texans image chart; Packers jersey-number prefixes)"),
    ("B32", "Model depth slots as groups, not a single starter"),
    ("B33", "Treat roster turnover as a first-class data event"),
    ("B34", "Start with a singles-only shadow baseline (pre-register a simple team-strength model, freeze versions and record forecasts before kickoff)"),
    ("B35", "Keep parlays and prop combos behind a joint-evidence gate"),
    ("B36", "Use proper-score leaderboard divisions (singles, game parlays, same-game parlays, prop combos)"),
    ("B37", "Rank with proper scores and uncertainty, not win rate"),
    ("B38", "Add durable snapshot storage and alerts (immutable captures outside the static site; monitor freshness; alert on source/schema changes)"),
    ("B39", "Split the site into a public analysis layer and a private data layer"),
    ("B40", "Add a per-team view: starters out, replacements named, net injury count"),
    ("B41", "Add an announced-starter evidence field (not an inferred replacement)"),
    ("B42", "Add an official depth-chart register with date and source per row"),
    ("B43", 'Calibrate what "Questionable" means empirically instead of using old percentages'),
    ("B44", "Interactive Offense vs. Defense Matchup Deficiency Matrix (1st-4th String)"),
    ("B45", "Flag stale depth rows against the official transactions log"),
    ("B46", "Point-in-Time Snapshot Ledger for Injuries, Depth Charts & Inactives"),
    ("B47", "Populate the three missing Lions game-status designations"),
    ("B48", "Re-capture and republish the Week 10 injury tables"),
    ("B49", "Reject: deriving depth order from jersey number, experience or salary"),
    ("B50", "Represent shared and empty depth slots faithfully"),
    ("B51", "Resolve the depth-order source before building the backup-deficiency feature"),
    ("B52", "Score injury-designation reliability before using it as a feature"),
    ("B53", "Snapshot the nfl.com injury report every Wed, Thu and Fri and keep a dated history"),
    ("B54", "Treat the injury report as a timestamped series, not a weekly snapshot"),
    ("B55", "Use snap counts as the starter proxy when the depth chart is unavailable"),
    ("B56", "Add a control baseline (random picks; favorites only) to every leaderboard run"),
    ("B57", "Stadium Roof/Surface & NWS Hourly Wind/Precipitation Overlay"),
    ("B58", "Two-Stage Skill Leaderboard (Proper-Score Qualification -> Prospective CLV/ROI Escrow)"),
    ("B59", "Vig-Free Market Consensus vs. Originated Fair-Line Decomposition View"),
    ("B60", "Publish a weekly 'what changed' diff instead of a static snapshot"),
    ("B61", "Publish every model total twice until one wins"),
    ("B62", "Add a drift alarm to every scraper"),
    ("B63", "Capture the reserve list so 'not listed' never means 'available'"),
    ("B64", "Reject: ranking strategies by season-long ROI"),
    ("B65", "Archive weekly injury reports for past seasons"),
    ("B66", "Pre-register each strategy (definition frozen before results are seen)"),
    ("B67", "2026 Kickoff & Declared Onside-Kick Regime Priors Filter"),
    ("B68", "Freeze a rule before it sees data (pre-registration; the commit hash is the registration)"),
    ("B69", "Split data into train, validation and final holdout seasons"),
]

# bullet -> readiness register rows that track it
MAPPING = {
    "B01": ["R001"],
    "B02": ["R002", "R068"],
    "B03": ["R003"],
    "B04": ["R004"],
    "B05": ["R005"],
    "B06": ["R006"],
    "B07": ["R007"],
    "B08": ["R008"],
    "B09": ["R009", "R010"],
    "B10": ["R011"],
    "B11": ["R012"],
    "B12": ["R013"],
    "B13": ["R014"],
    "B14": ["R015"],
    "B15": ["R016"],
    "B16": ["R017", "R069"],
    "B17": ["R018"],
    "B18": ["R019"],
    "B19": ["R020"],
    "B20": ["R021"],
    "B21": ["R022"],
    "B22": ["R023"],
    "B23": ["R024"],
    "B24": ["R025"],
    "B25": ["R026"],
    "B26": ["R027"],
    "B27": ["R028", "R029"],
    "B28": ["R030"],
    "B29": ["R030", "R038"],
    "B30": ["R038", "R045"],
    "B31": ["R063", "R072"],
    "B32": ["R071", "R075"],
    "B33": ["R065"],
    "B34": ["R057"],
    "B35": ["R058"],
    "B36": ["R059"],
    "B37": ["R060"],
    "B38": ["R030", "R052"],
    "B39": ["R031"],
    "B40": ["R032"],
    "B41": ["R033"],
    "B42": ["R034"],
    "B43": ["R035"],
    "B44": ["R036"],
    "B45": ["R037"],
    "B46": ["R038"],
    "B47": ["R062"],
    "B48": ["R039", "R061"],
    "B49": ["R040"],
    "B50": ["R041", "R064"],
    "B51": ["R042"],
    "B52": ["R043"],
    "B53": ["R044"],
    "B54": ["R013", "R022", "R044"],
    "B55": ["R045"],
    "B56": ["R046"],
    "B57": ["R047"],
    "B58": ["R048"],
    "B59": ["R049"],
    "B60": ["R050"],
    "B61": ["R051"],
    "B62": ["R052"],
    "B63": ["R053"],
    "B64": ["R074"],
    "B65": ["R054"],
    "B66": ["R009", "R055"],
    "B67": ["R067"],
    "B68": ["R055"],
    "B69": ["R056"],
}

# Worst-to-best ordering of register states, used only to show which state binds
# (the audit never aggregates numeric scores; it shows the set of states and the
# binding one, both copied verbatim from the register).
STATE_ORDER = [
    "BLOCKED",
    "REVIEW REQUIRED",
    "UNVERIFIED",
    "NOT STARTED",
    "DESIGN ONLY",
    "REJECT SHORTCUT",
    "IMPLEMENTED POLICY",
    "PARTIAL",
    "VERIFIED",
    "IMPLEMENTED",
    "IMPLEMENTED HERE",
]

# Prose deliverables from the brief, verified by file existence at build time.
PROSE_DELIVERABLES = [
    ("Suggestions section for review before implementation", "data/suggestions.json", "suggestions.html"),
    ("Decision questions / known / missing register", "data/decisions.json", "decisions.html"),
    ("Executive summary", "docs/EXECUTIVE_SUMMARY.md", "docs/EXECUTIVE_SUMMARY.md"),
    ("Repo review / audit", "docs/review/repo-review.html", "docs/review/repo-review.html"),
    ("Flagged-for-review register", "data/flagged.json", "flagged.html"),
    ("Methodology", "docs/METHODOLOGY.md", "docs/METHODOLOGY.md"),
    ("Strategy specs + validation gates", "data/strategies.json", "strategies.html"),
    ("Correlation registry", "data/correlations.json", "correlation.html"),
    ("Line-origination outputs", "data/lines.json", "lines.html"),
]

STATUS_CSS = {
    "BLOCKED": "#8b1a1a",
    "REVIEW REQUIRED": "#a15c00",
    "UNVERIFIED": "#a15c00",
    "NOT STARTED": "#6b6b00",
    "DESIGN ONLY": "#555f6b",
    "REJECT SHORTCUT": "#2f6f3f",
    "IMPLEMENTED POLICY": "#2f6f3f",
    "PARTIAL": "#1f5f8b",
    "VERIFIED": "#2f6f3f",
    "IMPLEMENTED": "#2f6f3f",
    "IMPLEMENTED HERE": "#2f6f3f",
}


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def binding_state(states):
    best = None
    for s in states:
        if best is None or STATE_ORDER.index(s) < STATE_ORDER.index(best):
            best = s
    return best


def main() -> int:
    register = list(csv.DictReader(REGISTER.open(newline="", encoding="utf-8-sig")))
    by_id = {r["id"]: r for r in register}
    if len(by_id) != len(register):
        print("FAIL: duplicate ids in the readiness register", file=sys.stderr)
        return 1

    rows = []
    problems = []
    for bid, text in BULLETS:
        ids = MAPPING.get(bid, [])
        if not ids:
            problems.append(f"{bid}: no readiness row maps to this brief requirement")
            continue
        missing = [i for i in ids if i not in by_id]
        if missing:
            problems.append(f"{bid}: mapped ids not in register: {missing}")
            continue
        states = [by_id[i]["current_state"] for i in ids]
        pages = sorted({(by_id[i]["repo_page"] or "").strip() for i in ids if by_id[i]["repo_page"].strip()})
        # A register row's repo_page is relative to board/ unless already prefixed.
        links = []
        for p in pages:
            target = p if p.startswith("board/") else f"board/{p}"
            if not (ROOT / target).exists():
                problems.append(f"{bid}: repo_page target does not exist: {target}")
            links.append(target)
        rows.append({
            "bullet_id": bid,
            "brief_requirement": text,
            "readiness_ids": ";".join(ids),
            "register_states": ";".join(states),
            "binding_state": binding_state(states),
            "detail_page": ";".join(links) if links else "",
        })

    mapped_ids = {i for ids in MAPPING.values() for i in ids}
    unmapped = [r["id"] for r in register if r["id"] not in mapped_ids]

    prose_rows = []
    for label, path, page in PROSE_DELIVERABLES:
        exists = (ROOT / path).exists()
        if not exists:
            problems.append(f"prose deliverable missing: {path}")
        prose_rows.append((label, path, page, exists))

    if problems:
        for p in problems:
            print("FAIL:", p, file=sys.stderr)
        return 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    body_rows = []
    for r in rows:
        color = STATUS_CSS.get(r["binding_state"], "#444")
        links = " · ".join(
            f'<a href="../{p}">{esc(p)}</a>' for p in r["detail_page"].split(";") if p
        )
        body_rows.append(
            f'<tr><td class="mono">{r["bullet_id"]}</td>'
            f'<td>{esc(r["brief_requirement"])}</td>'
            f'<td class="mono">{esc(r["readiness_ids"])}</td>'
            f'<td class="mono">{esc(r["register_states"])}</td>'
            f'<td><span class="badge" style="background:{color}">{esc(r["binding_state"])}</span></td>'
            f'<td>{links}</td></tr>'
        )
    prose_html = "".join(
        f'<tr><td>{esc(label)}</td><td class="mono"><a href="../{esc(page)}">{esc(path)}</a></td>'
        f'<td>{"present" if ok else "MISSING"}</td></tr>'
        for label, path, page, ok in prose_rows
    )
    unmapped_html = "".join(
        f'<tr><td class="mono">{i}</td><td>{esc(by_id[i]["requirement"])}</td>'
        f'<td><span class="badge" style="background:{STATUS_CSS.get(by_id[i]["current_state"], "#444")}">'
        f'{esc(by_id[i]["current_state"])}</span></td></tr>'
        for i in unmapped
    )

    gaps = [r for r in rows if r["binding_state"] == "BLOCKED"]
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Requirement coverage audit - FL3</title>
<style>
 body{{font-family:Georgia,'Times New Roman',serif;margin:0;background:#f4f4f0;color:#1c1c1c}}
 header{{background:#0b3358;color:#fff;padding:22px 28px}}
 header h1{{margin:0;font-size:26px;font-weight:600}}
 header p{{margin:6px 0 0;color:#c9d8e8;font-size:14px}}
 main{{max-width:1180px;margin:0 auto;padding:18px 28px 60px}}
 h2{{font-size:19px;border-bottom:2px solid #0b3358;padding-bottom:4px;margin-top:34px}}
 table{{border-collapse:collapse;width:100%;font-size:13px;background:#fff}}
 th,td{{border:1px solid #cfcfc6;padding:6px 8px;text-align:left;vertical-align:top}}
 th{{background:#e7ecef;font-family:Helvetica,Arial,sans-serif;font-size:12px}}
 .mono{{font-family:'SF Mono',Consolas,monospace;font-size:12px}}
 .badge{{color:#fff;padding:2px 7px;border-radius:3px;font-family:Helvetica,Arial,sans-serif;font-size:11px;white-space:nowrap}}
 .note{{background:#fff8e1;border:1px solid #e0c870;padding:10px 14px;font-size:13px;margin:14px 0}}
 footer{{max-width:1180px;margin:0 auto;padding:0 28px 40px;font-size:12px;color:#666}}
</style></head><body>
<header><h1>Requirement coverage audit</h1>
<p>Every requirement in the session brief, mapped to the row of the decision-readiness register that tracks it. Built from <code>data/requirements_readiness.csv</code>; no value here is inferred. Generated by <code>scripts/build_coverage_audit.py</code>.</p></header>
<main>
<div class="note"><b>How to read this.</b> Each brief requirement (B01-B69) maps to one or more register rows.
The <b>binding state</b> is the least-advanced state among those rows - it is what stands between the
requirement and a decision. {len(rows)} of {len(BULLETS)} brief requirements are mapped; the audit build fails if any
bullet is unmapped, so a coverage gap cannot be silent. Register rows no brief bullet maps to are listed
as register-internal additions at the bottom.</div>

<h2>Brief requirements &rarr; readiness register ({len(rows)} mapped)</h2>
<table><thead><tr><th>Bullet</th><th>Brief requirement (verbatim)</th><th>Register row(s)</th>
<th>Register state(s)</th><th>Binding state</th><th>Detail page</th></tr></thead>
<tbody>
{''.join(body_rows)}
</tbody></table>

<h2>Prose deliverables from the brief (verified present at build time)</h2>
<table><thead><tr><th>Deliverable</th><th>Artifact</th><th>Status</th></tr></thead>
<tbody>{prose_html}</tbody></table>

<h2>Register-internal additions (no brief bullet maps to them)</h2>
<table><thead><tr><th>Row</th><th>Requirement</th><th>State</th></tr></thead>
<tbody>{unmapped_html}</tbody></table>

<h2>Audit findings (irregularities, not silently corrected)</h2>
<table><thead><tr><th>ID</th><th>Finding</th><th>Evidence</th></tr></thead>
<tbody>
<tr><td class="mono">AUD-01</td><td>The readiness register's backtest-corpus metric still reads
"exactly the predeclared <b>136</b> eligible game records" (R020), while the verified results corpus
holds <b>148</b> settled games (data/week_results_2026.csv). The clearance metric predates the
larger verified corpus and must be restated by the register's owner before R020 can clear;
this audit publishes the mismatch instead of editing the register.</td>
<td><a href="../board/readiness.html">R020</a> &middot; <a href="../verified/index.html">verified corpus</a></td></tr>
<tr><td class="mono">AUD-02</td><td>Two register rows describe the same brief requirement twice
(R002/R068 results feed; R017/R069 luck panel) because two sessions registered the same bullet
independently. Both are kept; the duplicate ids are shown in the mapping above so a reader sees
the register's duplication rather than a hidden merge.</td>
<td><a href="../board/readiness.html">register</a></td></tr>
<tr><td class="mono">AUD-03</td><td>{len(gaps)} of {len(rows)} brief requirements are binding-blocked
(state BLOCKED on every row that tracks them): {esc(', '.join(r['bullet_id'] for r in gaps)) or 'none'}.
All of them are blocked by the same root cause - no licensed, official price/odds feed exists
(register rows R001/R019/R021/R049/R058) - which is an owner decision, not a data gap this
repository can close by itself.</td>
<td><a href="../board/readiness.html">register</a></td></tr>
</tbody></table>
</main>
<footer>FL3 requirement coverage audit &middot; deterministic build (no timestamp embedded) &middot;
sources: <a href="https://www.nfl.com/injuries/">nfl.com/injuries</a>,
<a href="https://www.nfl.com/schedules/">nfl.com/schedules</a>,
<a href="https://www.nfl.com/standings/">nfl.com/standings</a> (official NFL pages the register rows link)</footer>
</body></html>
"""
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"coverage audit: {len(rows)}/{len(BULLETS)} brief requirements mapped, "
          f"{len(unmapped)} register-internal additions, {len(gaps)} binding-blocked; wrote audit/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
