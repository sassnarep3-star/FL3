# Source registry

Every `source_id` referenced anywhere in `data/` must exist here, and the build fails if a row cites one
that does not. Status values: `read` (opened this session through the source URL), `search-snippet`
(official page content seen through a search index - usable as a pointer, not as a published value),
`not-read` / `not-acquired` (registered, deliberately not used yet).

:::table sources.csv | 19 registered sources; 9 read, 1 snippet-level, 9 pending | source_id,publisher,name,url,class,status,used_for,notes

## Reading the class column

| Class | Weight in this repo |
|---|---|
| `official-league` | the only class a published data value may come from today |
| `official-club` | official for that club's own facts (roster, depth chart, stadium) |
| `official-government` | official for weather and any regulatory fact |
| `secondary` | can raise a question, cannot fill a cell |
| `commercial-market` | the only realistic route to odds; requires a licence, and no value from it is in the repo yet |

## Why three sources are `not-read`

`SRC-012` (flexible-scheduling procedures) and `SRC-013` (tie-breaking procedures) are linked from pages
that were read but not opened; they matter for rest-day and end-of-season-motivation features, not for
today's numbers. `SRC-016` is the odds vendor: it is registered **because it is the blocking gap**, not
because anything was obtained from it. `SRC-015` (NWS) and `SRC-017` (club pages) are the same category -
the fetcher knows where to go, and until it does, the site shows blanks.

## Link hygiene

Every URL here was reached through the fetcher this session or is registered as pending; the deploy runs
`scripts/check_links.py`, which fails on a broken internal link and reports (without failing on) external
links that return an error - external pages move, and a stale league URL is a finding for the
[review page](flagged.html), not a reason to break a build.
