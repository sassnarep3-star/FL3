"""check_depth_links.py - static link and markup check for depth/.

No network access is required: internal hrefs are resolved against the files on
disk, and every external href must belong to a domain in the allow-list.

Exits non-zero on any failure so it can gate the deploy.
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "depth"

ALLOWED_DOMAINS = {
    "www.nfl.com", "nfl.com", "www.ourlads.com", "ourlads.com",
    "site.api.espn.com", "site.web.api.espn.com", "www.espn.com",
    "github.com", "sassnarep3-star.github.io",
}

fails = []
pages = sorted(DOCS.glob("*.html"))
if not pages:
    print("no pages found in docs/")
    sys.exit(1)

TAG = re.compile(r"<(a|img|link|script)\b([^>]*)>", re.I)
ATTR = re.compile(r'(href|src)\s*=\s*"([^"]*)"', re.I)

internal, external = 0, 0
for p in pages:
    text = p.read_text()
    for m in TAG.finditer(text):
        for am in ATTR.finditer(m.group(2)):
            url = am.group(2).strip()
            if not url or url.startswith("#"):
                continue
            if url.startswith("mailto:") or url.startswith("javascript:"):
                continue
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                external += 1
                if parsed.netloc not in ALLOWED_DOMAINS:
                    fails.append("%s: external link to non-allowlisted domain %r" % (p.name, parsed.netloc))
                continue
            internal += 1
            target = (p.parent / parsed.path).resolve()
            if not target.exists():
                fails.append("%s: internal link %r does not resolve" % (p.name, url))

    # structural checks
    if text.count("<html") != 1 or text.count("</html>") != 1:
        fails.append("%s: unbalanced <html> tag" % p.name)
    if "<title>" not in text:
        fails.append("%s: missing <title>" % p.name)
    if 'name="viewport"' not in text:
        fails.append("%s: missing viewport meta" % p.name)
    if "Flagged for Review" not in text and p.name != "flagged.html":
        fails.append("%s: does not link/mention the Flagged for Review page" % p.name)
    if text.count("<table") != text.count("</table>"):
        fails.append("%s: unbalanced <table> tags" % p.name)
    if text.count("<tbody>") != text.count("</tbody>"):
        fails.append("%s: unbalanced <tbody> tags" % p.name)
    # every data page must show the as-of date somewhere
    if "2026-11-14" not in text:
        fails.append("%s: does not display the as-of date" % p.name)

print("pages checked: %d" % len(pages))
print("internal links resolved: %d" % internal)
print("external links checked against allow-list: %d" % external)
if fails:
    print("\nFAILURES:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("\nOK: no broken internal links, no non-allowlisted external domains, markup balanced")
