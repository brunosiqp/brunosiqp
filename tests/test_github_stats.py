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


def fake_response(payload):
    resp = mock.Mock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def viewer_page(stars, has_next, cursor):
    return {
        "data": {
            "viewer": {
                "createdAt": "2024-05-01T19:20:26Z",
                "pullRequests": {"totalCount": 34},
                "contributionsCollection": {
                    "totalCommitContributions": 170,
                    "restrictedContributionsCount": 6,
                    "totalIssueContributions": 14,
                    "contributionCalendar": {"totalContributions": 207},
                },
                "repositories": {
                    "totalCount": 42,
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                    "nodes": [{"stargazerCount": s} for s in stars],
                },
            }
        }
    }


class FetchStatsTests(unittest.TestCase):
    def test_graphql_raises_on_errors(self):
        with mock.patch.object(github_stats.requests, "post",
                               return_value=fake_response({"errors": [{"message": "x"}]})):
            with self.assertRaises(RuntimeError):
                github_stats.graphql("t", "{ viewer { login } }")

    def test_fetch_stats_maps_fields(self):
        with mock.patch.object(github_stats.requests, "post",
                               return_value=fake_response(viewer_page([2, 1, 0], False, None))):
            self.assertEqual(github_stats.fetch_stats("t"), SAMPLE)

    def test_fetch_stats_paginates_stars(self):
        pages = [fake_response(viewer_page([2], True, "CUR1")),
                 fake_response(viewer_page([1], False, None))]
        with mock.patch.object(github_stats.requests, "post", side_effect=pages) as post:
            stats = github_stats.fetch_stats("t")
        self.assertEqual(stats["stars"], 3)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args_list[1].kwargs["json"]["variables"]["cursor"], "CUR1")

    def test_main_without_token_exits(self):
        env = {k: v for k, v in os.environ.items() if k != "GH_TOKEN"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(github_stats, "OUTPUT", "should-not-exist.svg"):
            with self.assertRaises(SystemExit) as ctx:
                github_stats.main()
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertFalse(os.path.exists("should-not-exist.svg"))


if __name__ == "__main__":
    unittest.main()
