import os
import sys
import unittest
from unittest import mock
from xml.dom import minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import github_stats  # noqa: E402

SAMPLE = {
    "contributions": 207,
    "commits": 176,
    "pull_requests": 34,
    "issues": 14,
    "repositories": 42,
    "stars": 3,
    "since": 2024,
}


class BuildSvgTests(unittest.TestCase):
    def test_build_svg_is_valid_xml(self):
        doc = minidom.parseString(github_stats.build_svg(SAMPLE))
        self.assertEqual(doc.documentElement.getAttribute("width"), "700")

    def test_build_svg_shows_every_label_and_value(self):
        svg = github_stats.build_svg(SAMPLE)
        for _, label in github_stats.STAT_ROWS:
            self.assertIn(label, svg)
        self.assertIn(">207<", svg)
        self.assertIn(">2024<", svg)
        self.assertIn(">3<", svg)

    def test_fmt_value_thousands(self):
        self.assertEqual(github_stats.fmt_value(12345), "12,345")
        self.assertEqual(github_stats.fmt_value(0), "0")

    def test_since_not_comma_formatted(self):
        self.assertNotIn("2,024", github_stats.build_svg(SAMPLE))

    def test_escapes_text(self):
        rows = [("contributions", "A<B")]
        with mock.patch.object(github_stats, "STAT_ROWS", rows):
            svg = github_stats.build_svg(SAMPLE)
        self.assertIn("A&lt;B", svg)
        minidom.parseString(svg)


if __name__ == "__main__":
    unittest.main()
