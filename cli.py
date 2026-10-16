#!/usr/bin/env python3
"""Check local Markdown links, images and heading anchors. External HTTP links are reported as skipped; no network requests are made."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def headings(path):
    seen, anchors = {}, set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{1,6}\s+", line):
            title = re.sub(r"^#{1,6}\s+", "", line).strip().rstrip("#").strip().lower()
            slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
            n = seen.get(slug, 0)
            anchors.add(slug if n == 0 else f"{slug}-{n}")
            seen[slug] = n + 1
    return anchors


def check(path):
    issues, skipped = [], 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for match in re.finditer(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", line):
            dest = match.group(1).strip("<>")
            parts = urlsplit(dest)
            if parts.scheme or parts.netloc:
                skipped += 1
                continue
            target = path.parent / unquote(parts.path) if parts.path else path
            reason = None
            if not target.exists():
                reason = "missing target"
            elif parts.fragment and target.is_file() and target.suffix.lower() in (".md", ".markdown"):
                if unquote(parts.fragment) not in headings(target):
                    reason = "missing heading anchor"
            if reason:
                issues.append({"line": line_no, "target": dest, "reason": reason})
    return {"file": str(path), "issues": issues, "external_links_skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        report = check(args.file)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"Input error: {exc}\n")
    print(json.dumps(report, indent=2))
    return bool(report["issues"])


if __name__ == "__main__":
    raise SystemExit(main())
