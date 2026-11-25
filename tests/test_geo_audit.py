import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geo_audit import audit_html


SAMPLE_PASS_HTML = """<!doctype html>
<html lang="en">
<head>
  <title>Technical SEO & GEO Architecture Guide</title>
  <meta name="description" content="A practical engineering breakdown of Semantic HTML5 landmarks and connected JSON-LD Entity Schema for AI Search." />
  <link rel="canonical" href="https://nguyenthanhthien.com/geo-guide/" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {"@type": "Person", "@id": "https://nguyenthanhthien.com/#person", "name": "Nguyen Thanh Thien"},
      {"@type": "Article", "@id": "https://nguyenthanhthien.com/geo-guide/#article", "author": {"@id": "https://nguyenthanhthien.com/#person"}}
    ]
  }
  </script>
</head>
<body>
  <header><nav><a href="/">Home</a></nav></header>
  <main><article><h1>GEO Architecture</h1><h2>Entity Graph</h2></article></main>
  <footer><p>Footer</p></footer>
</body>
</html>
"""


class TestGeoAudit(unittest.TestCase):
    def test_connected_entity_graph_scores_100(self):
        report = audit_html(SAMPLE_PASS_HTML, "sample.html")
        self.assertEqual(report["score"], 100)
        self.assertIn("Person", report["entity_types"])
        self.assertIn("Article", report["entity_types"])
        self.assertEqual(len(report["entity_ids"]), 2)

    def test_missing_schema_penalizes_score(self):
        report = audit_html("<html><body><h1>Minimal</h1><h3>Skipped</h3></body></html>", "bad.html")
        self.assertLess(report["score"], 50)


if __name__ == "__main__":
    unittest.main()
