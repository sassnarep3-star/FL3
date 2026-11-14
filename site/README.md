# FL3 - the published site

This directory is a **build artefact**. `docs/` at the repo root is generated into the same shape by
`python3 scripts/build_site.py`; do not hand-edit either.

- `assets/style.css` - the stylesheet the build copies into `docs/assets/`.
- `.nojekyll` - copied into `docs/` so Jekyll does not strip files.
- `index.html` - a pointer page, kept so a viewer opened at `site/` explains where the real site is.

Publish chain (all four must pass, or there is no deploy):

```bash
python3 scripts/model.py            # derived metrics, calibration, ratings, priced slate
python3 scripts/stats_tables.py     # closed-form thresholds
python3 scripts/make_leaderboard.py # board schema from models/strategy_registry.yaml
python3 scripts/verify.py           # gate G-10 - identity checks over data/
python3 scripts/build_site.py       # renders docs/ from data/ + content/
python3 scripts/check_links.py      # internal links, anchors, orphan pages
```

`build_site.py` runs `verify.py` and `check_links.py` itself, so a single command is enough locally.
GitHub Pages is deployed by `.github/workflows/site.yml`, which additionally fails the build if `docs/`
in the commit does not match what the current `data/` would generate - that is what keeps a hand-patched
page from surviving on the live site.
