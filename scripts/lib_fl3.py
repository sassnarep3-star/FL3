"""Shared helpers for the FL3 pipeline.

Everything here is pure standard library so the site can be rebuilt in a bare
GitHub Actions runner (ubuntu-latest) with no install step.

Conventions used across the repo:
  * a data row is only "published" if it carries source_id + accessed_utc
  * `verified`   -> read directly from a source in data/sources.csv
  * `derived`    -> computed by these scripts from verified rows (no new facts)
  * `blank`      -> deliberately empty because no official source confirms it
"""

from __future__ import annotations

import csv
import os
from statistics import mean, stdev

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")


def read_rows(name):
    """Read data/<name> as a list of dicts, keeping empty strings as ''."""
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def write_rows(name, rows, fieldnames=None):
    path = os.path.join(DATA, name)
    if not rows:
        rows = []
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    return path


def num(value, default=None):
    """Float or default. Blank stays blank - never coerced into 0."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def close(a, b, tol=0.061):
    """Compare a published 1-dp stat against a recomputed value.

    Tolerance is 0.061 rather than 0.05 because the published figure is itself
    rounded to one decimal place and we do not know the league's rounding rule at
    the .x5 boundary (half-up vs half-even). Anything beyond that is a real
    mismatch. Rows inside 0.05..0.061 are surfaced as warnings, not failures.
    """
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def borderline(a, b, warn=0.05, tol=0.061):
    """True when a value passes only because of the rounding-tolerance slack."""
    if a is None or b is None:
        return False
    return warn < abs(a - b) <= tol


def sd(values):
    """Sample SD (n-1) - the ingested sample is a sample, not the population."""
    values = [v for v in values if v is not None]
    return stdev(values) if len(values) > 1 else None


def summary(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0, "mean": None, "sd": None, "min": None, "max": None}
    return {
        "n": len(values),
        "mean": mean(values),
        "sd": sd(values) or 0.0,
        "min": min(values),
        "max": max(values),
    }
