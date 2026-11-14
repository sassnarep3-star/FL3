# FL3 — NFL Lines Research Desk

A static, source-first research dashboard for NFL line modeling and decision review. It intentionally publishes **no picks, current player/injury claims, odds, backtest statistics, correlation values, or performance results**: this repository began with no underlying data, no odds history, and no model. Unknown values remain blank and are listed on **Flagged for Review**.

## Site sections

- **Executive summary** — project state, what is known, and what blocks a decision.
- **Strategy lab** — proposed single-game, player-prop, combo, parlay, and availability-signal research paths.
- **Validation gates** — pre-registration, point-in-time integrity, chronological holdouts, calibration, dependence, and replication requirements.
- **Availability & depth** — official-source injury / inactive workflow and limits around backup-string claims.
- **Decision questions** — information to establish before choosing a product or model direction.
- **Official sources** — verified NFL and NIST primary-source entry points.
- **Flagged for Review** — source irregularities and missing evidence.

## Run locally

Serve the repository root with any static web server, for example:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000`. The dashboard uses plain HTML, CSS, and a small search helper; there is no package install or runtime API.

## GitHub Pages

The workflow in `.github/workflows/pages.yml` deploys the root of the repository to GitHub Pages on pushes to `main` and can be run manually. In repository settings, configure **Pages → Build and deployment → Source: GitHub Actions**. PRs can be previewed by serving the static files locally; no secrets are required.

## Evidence and limitations

- Every NFL data/method table row links to the relevant official NFL or NIST source. Links are for manual review and may be dynamic; source pages must be archived with a retrieval timestamp and query before using them in research.
- The NFL injury-report route observed during this review had a path/title/body week mismatch. It is recorded as a flag and not used for any player-level value.
- NFL official stats and injury pages are source entry points, not proof of historical completeness, public bulk access, or reuse rights. Confirm terms and coverage before ingestion.
- Correlation is not inferred from narratives. Parlay legs require joint-outcome evidence and uncertainty analysis.
- “Luck-free” performance cannot be promised. Validation can only evaluate repeatability with carefully controlled, out-of-sample evidence.
- This prototype is not wagering, legal, or financial advice and does not offer prizes or betting recommendations.

See [`COORDINATION.md`](COORDINATION.md) for the task claim, verification log, and integration status.
