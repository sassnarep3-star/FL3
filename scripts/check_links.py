#!/usr/bin/env python3
"""Link and registry integrity check for the generated site in docs/.

Fails the build (exit 1) on:
  * an internal href pointing at a file that does not exist in docs/
  * a docs/*.html that is not reachable from index.html (orphan page)
  * an anchor (id=) targeted by an internal link that does not exist on that page

External links are reported but never fail the build: a league page that moves is a finding for the
review queue, not a reason to break a deploy (see content/methodology.md).

Usage: python3 scripts/check_links.py
"""

from __future__ import annotations

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")
HREF = re.compile(r'''href\s*=\s*["']([^"']+)["']''', re.I)
ID_ATTR = re.compile(r'''\bid\s*=\s*["']([^"']+)["']''', re.I)


def main() -> int:
    if not os.path.isdir(DOCS):
        print("check_links: docs/ does not exist - run scripts/build_site.py first")
        return 1
    pages = {f for f in os.listdir(DOCS) if f.endswith(".html")}
    if not pages:
        print("check_links: no pages in docs/")
        return 1
    anchors = {f: {m for m in ID_ATTR.findall(open(os.path.join(DOCS, f), encoding="utf-8").read())}
               for f in pages}
    links = {f: HREF.findall(open(os.path.join(DOCS, f), encoding="utf-8").read()) for f in pages}

    broken, external, reachable = [], set(), {"index.html"}
    for page, hrefs in links.items():
        for href in hrefs:
            if href.startswith(("http://", "https://", "mailto:")):
                external.add(href)
                continue
            if href.startswith("#"):
                target, frag = page, href[1:]
            elif "#" in href:
                target, frag = href.split("#", 1)
            else:
                target, frag = href, None
            target = target.split("?")[0]
            if not target:
                continue
            if target.endswith(".html") or "/" in target:
                path = os.path.normpath(os.path.join(DOCS, target))
                if not os.path.exists(path):
                    broken.append(f"{page} -> {href} (file missing)")
                    continue
                if frag and target in anchors and frag not in anchors[target]:
                    broken.append(f"{page} -> {href} (anchor #{frag} not in {target})")
                    continue
                if target in pages:
                    reachable.add(target)
            else:
                broken.append(f"{page} -> {href} (non-page target)")
    # second pass: reachability from index.html only
    queue, seen = ["index.html"], {"index.html"}
    while queue:
        cur = queue.pop()
        for href in links.get(cur, []):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = href.split("#")[0]
            if target in pages and target not in seen:
                seen.add(target)
                queue.append(target)
    orphans = sorted(pages - seen)
    for o in orphans:
        broken.append(f"{o} is not reachable from index.html")

    print(f"check_links: {len(pages)} pages, {len(external)} distinct external links")
    if broken:
        print(f"CHECK LINKS: FAIL - {len(broken)} problem(s)")
        for b in sorted(set(broken))[:25]:
            print("   ", b)
        return 1
    print("CHECK LINKS: PASS - every internal link and anchor resolves, no orphan pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
