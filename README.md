# Semantic HTML5 & AEO/GEO Audit CLI

A zero-dependency Python CLI tool that audits live URLs or local HTML files for **Semantic HTML5 landmarks**, **Heading hierarchy**, **Meta hygiene**, and **JSON-LD / Entity Schema readiness** for Search & AI Engines (AEO/GEO).

## Why Use This?
Before optimizing content for AI Overviews, ChatGPT, or Perplexity, pages must pass structural fundamentals:
- Single unambiguous `<h1>` with no skipped heading levels (`h1 -> h3`).
- Core Semantic HTML5 landmarks (`<main>`, `<article>`, `<header>`, `<nav>`, `<footer>`).
- Valid canonical link, title, and meta description length.
- Valid JSON-LD structured data with connected `@graph` and `@id` entity references.

## Usage

```bash
# Audit a live URL
python3 geo_audit.py https://nguyenthanhthien.com/

# Audit a local HTML file
python3 geo_audit.py ./sample.html --json
```

## Example Output

```text
=== Semantic HTML5 & GEO Audit ===
Target: sample.html
Score : 95 / 100

[PASS] Title present (48 chars)
[PASS] Meta description present (142 chars)
[PASS] Canonical URL defined
[PASS] Exactly 1 <h1> found
[PASS] Heading hierarchy valid (no skipped levels)
[PASS] Semantic landmarks found: header, nav, main, article, footer
[PASS] JSON-LD blocks: 1 valid (types: Person, WebSite, Article)
```

**Author:** Nguyễn Thành Thiên — [nguyenthanhthien.com](https://nguyenthanhthien.com/)
