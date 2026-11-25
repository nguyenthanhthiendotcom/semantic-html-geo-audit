#!/usr/bin/env python3
"""Zero-dependency Semantic HTML5 & AEO/GEO Audit CLI."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from html.parser import HTMLParser
from typing import Any


LANDMARKS = {"header", "nav", "main", "article", "section", "aside", "footer"}


class SemanticHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._in_ldjson = False
        self._ldjson_buf: list[str] = []
        self.meta_description = ""
        self.canonical = ""
        self.headings: list[tuple[int, str]] = []
        self._current_h: int | None = None
        self._h_buf: list[str] = []
        self.landmarks: set[str] = set()
        self.jsonld_raw: list[str] = []
        self.microdata_types: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()

        if t in LANDMARKS:
            self.landmarks.add(t)

        if "itemtype" in attr_map and attr_map["itemtype"]:
            self.microdata_types.add(attr_map["itemtype"])

        if t == "title":
            self._in_title = True
        elif t == "meta" and attr_map.get("name", "").lower() == "description":
            self.meta_description = attr_map.get("content", "").strip()
        elif t == "link" and "canonical" in attr_map.get("rel", "").lower().split():
            self.canonical = attr_map.get("href", "").strip()
        elif t in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_h = int(t[1])
            self._h_buf = []
        elif t == "script" and attr_map.get("type", "").lower() == "application/ld+json":
            self._in_ldjson = True
            self._ldjson_buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "title":
            self._in_title = False
        elif t in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._current_h is not None:
            text = " ".join("".join(self._h_buf).split())
            self.headings.append((self._current_h, text))
            self._current_h = None
        elif t == "script" and self._in_ldjson:
            self._in_ldjson = False
            self.jsonld_raw.append("".join(self._ldjson_buf).strip())

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._current_h is not None:
            self._h_buf.append(data)
        if self._in_ldjson:
            self._ldjson_buf.append(data)


def load_html(target: str) -> str:
    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(target, headers={"User-Agent": "semantic-html-geo-audit/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def audit_html(html: str, target: str) -> dict[str, Any]:
    parser = SemanticHTMLParser()
    parser.feed(html)

    checks: list[dict[str, Any]] = []
    score = 0

    # 1. Title
    title = " ".join(parser.title.split())
    if 10 <= len(title) <= 70:
        score += 15
        checks.append({"status": "PASS", "rule": f"Title optimal ({len(title)} chars)"})
    elif title:
        score += 8
        checks.append({"status": "WARN", "rule": f"Title length suboptimal ({len(title)} chars)"})
    else:
        checks.append({"status": "FAIL", "rule": "Missing <title> tag"})

    # 2. Meta description
    desc_len = len(parser.meta_description)
    if 50 <= desc_len <= 165:
        score += 15
        checks.append({"status": "PASS", "rule": f"Meta description optimal ({desc_len} chars)"})
    elif desc_len > 0:
        score += 8
        checks.append({"status": "WARN", "rule": f"Meta description length suboptimal ({desc_len} chars)"})
    else:
        checks.append({"status": "FAIL", "rule": "Missing meta description"})

    # 3. Canonical
    if parser.canonical:
        score += 10
        checks.append({"status": "PASS", "rule": f"Canonical URL defined ({parser.canonical})"})
    else:
        checks.append({"status": "FAIL", "rule": "Missing rel=canonical link"})

    # 4. H1 count
    h1s = [h for lvl, h in parser.headings if lvl == 1]
    if len(h1s) == 1:
        score += 15
        checks.append({"status": "PASS", "rule": "Exactly 1 <h1> found"})
    else:
        checks.append({"status": "FAIL", "rule": f"Expected 1 <h1>, found {len(h1s)}"})

    # 5. Heading hierarchy
    skipped = []
    prev = 0
    for lvl, _ in parser.headings:
        if prev and lvl > prev + 1:
            skipped.append(f"h{prev}->h{lvl}")
        prev = lvl
    if not skipped and parser.headings:
        score += 15
        checks.append({"status": "PASS", "rule": "Heading hierarchy valid (no skipped levels)"})
    else:
        checks.append({"status": "WARN", "rule": f"Heading hierarchy issues: {skipped or 'no headings'}"})

    # 6. Semantic landmarks
    core = {"main", "header", "footer"}
    if core.issubset(parser.landmarks):
        score += 15
        checks.append({"status": "PASS", "rule": f"Semantic landmarks found: {', '.join(sorted(parser.landmarks))}"})
    else:
        missing = sorted(core - parser.landmarks)
        checks.append({"status": "WARN", "rule": f"Missing core landmarks: {', '.join(missing)}"})

    # 7. JSON-LD presence
    valid_blocks = 0
    for raw in parser.jsonld_raw:
        try:
            json.loads(raw)
            valid_blocks += 1
        except json.JSONDecodeError:
            pass
    if valid_blocks > 0:
        score += 15
        checks.append({"status": "PASS", "rule": f"Valid JSON-LD blocks found: {valid_blocks}"})
    else:
        checks.append({"status": "FAIL", "rule": "No valid JSON-LD structured data found"})

    return {
        "target": target,
        "score": score,
        "checks": checks,
        "landmarks": sorted(parser.landmarks),
        "microdata_types": sorted(parser.microdata_types),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Semantic HTML5 & AEO/GEO readiness.")
    ap.add_argument("target", help="Live URL (https://...) or local HTML file path")
    ap.add_argument("--json", action="store_true", help="Output JSON report")
    args = ap.parse_args()

    html = load_html(args.target)
    report = audit_html(html, args.target)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=== Semantic HTML5 & GEO Audit ===")
        print(f"Target: {report['target']}")
        print(f"Score : {report['score']} / 100
")
        for c in report["checks"]:
            print(f"[{c['status']}] {c['rule']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
