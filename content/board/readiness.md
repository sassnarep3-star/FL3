# Requirement readiness register

This is the decision table requested for the landing page: one row for every distinct requirement in the brief, showing what the checked-in repository demonstrates, what is still missing, the gate that blocks use, and the condition or number that would clear it. The landing page links here under **Requirement readiness**.

## Status semantics

- **BLOCKED** — a required input or policy is missing, so the dependent output must not be trusted or published.
- **PARTIAL** — related artifacts exist, but coverage, provenance, temporal validity, or verification is incomplete.
- **NOT STARTED / DESIGN ONLY** — the repository contains no demonstrated operational result; any stated clearance condition is a proposed gate.
- **IMPLEMENTED HERE** — the register or policy is present in this build. This label does not imply the underlying NFL data feed is complete.
- **REVIEW REQUIRED / REJECT SHORTCUT** — a known conflict or invalid inference needs explicit treatment.
- **NOT REPRODUCED** — a claim was checked against the official source and the claimed condition was not found; the flag stays open until the claim's origin is traced.

The status is an audit of checked-in artifacts, not a live test of upstream NFL pages. The official-source column links an applicable NFL, club, or government input where one is registered. A link is not proof of data capture. If no applicable official source is registered, the citation cell remains blank and the row explains the source gap. This matters especially for sportsbook prices, model-validation methodology, rewards, and operational policy: those are not NFL-published facts.

The clearance metrics are proposed engineering/evaluation gates, not empirical findings or guarantees of profitability. Read the linked **Questions & gaps**, **Suggestions**, **Validation gates**, and **Flagged for review** pages before choosing an implementation path. No backtest, ROI or strategy ranking should be treated as validated while its blockers remain open.

## Register

The table below is generated from `data/requirements_readiness.csv`. The source of truth for any factual input remains the official URL linked on the row; internal related-page links are provided for repository evidence and review context.
