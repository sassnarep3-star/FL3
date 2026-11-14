#!/usr/bin/env python3
"""Offline checks for local navigation and sourced table rows."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_HOSTS = {"nfl.com", "operations.nfl.com", "media.nfl.com", "itl.nist.gov"}

class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.table_depth = 0
        self.in_tbody = False
        self.in_row = False
        self.row_links = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if self.in_tbody and self.in_row:
                self.row_links.append(attrs["href"])
        if tag == "table":
            self.table_depth += 1
        elif tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_links = []

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            self.rows.append(list(self.row_links))
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False
        elif tag == "table":
            self.table_depth = max(0, self.table_depth - 1)

errors = []
html_files = sorted([ROOT / "index.html", * (ROOT / "pages").glob("*.html")])
for path in html_files:
    parser = AuditParser()
    parser.feed(path.read_text(encoding="utf-8"))
    for href in parser.links:
        if href.startswith(("https://", "http://", "mailto:", "tel:", "#")):
            continue
        target = unquote(href.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        local = (path.parent / target).resolve()
        if not local.is_file():
            errors.append(f"{path.relative_to(ROOT)}: broken local link {href}")
    for number, links in enumerate(parser.rows, 1):
        if not links:
            errors.append(f"{path.relative_to(ROOT)}: tbody row {number} has no source link")
            continue
        official = False
        for href in links:
            host = urlparse(href).hostname or ""
            if host in OFFICIAL_HOSTS or any(host.endswith("." + domain) for domain in OFFICIAL_HOSTS):
                official = True
        if not official:
            errors.append(f"{path.relative_to(ROOT)}: tbody row {number} has no approved official-domain link")

if errors:
    print("Site validation failed:")
    print("\n".join(f"- {error}" for error in errors))
    raise SystemExit(1)

row_count = 0
for path in html_files:
    parser = AuditParser(); parser.feed(path.read_text(encoding="utf-8")); row_count += len(parser.rows)
print(f"Site validation passed: {len(html_files)} HTML pages; all local links resolve; {row_count} table body rows have official-domain source links.")
