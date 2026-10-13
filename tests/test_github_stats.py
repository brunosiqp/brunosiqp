import os
import sys
import tempfile
import unittest
from unittest import mock
from xml.dom import minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import github_stats  # noqa: E402

SAMPLE = {
    "contributions": 207,
    "commits": 176,
    "pull_requests": 7,
    "issues": 14,
    "pull_requests_total": 34,
    "repositories": 42,
    "stars": 3,
    "since": 2024,
    "calendar": [
        [{"date": "2026-09-27", "count": 0}, {"date": "2026-09-28", "count": 5},
         {"date": "2026-09-29", "count": 10}],
        [{"date": "2026-10-04", "count": 1}],
    ],
}

CALENDAR_WEEKS = [
    {"contributionDays": [{"date": d["date"], "contributionCount": d["count"]} for d in week]}
    for week in SAMPLE["calendar"]
]


class BuildSvgTests(unittest.TestCase):
    def test_build_svg_is_valid_xml(self):
        doc = minidom.parseString(github_stats.build_svg(SAMPLE))
        self.assertEqual(doc.documentElement.getAttribute("width"), "830")

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

    def test_level_for_buckets_counts(self):
        self.assertEqual(github_stats.level_for(0, 10), 0)
        self.assertEqual(github_stats.level_for(1, 10), 1)
        self.assertEqual(github_stats.level_for(5, 10), 2)
        self.assertEqual(github_stats.level_for(10, 10), 4)
        self.assertEqual(github_stats.level_for(0, 0), 0)

    def test_build_svg_draws_one_cell_per_day(self):
        svg = github_stats.build_svg(SAMPLE)
        self.assertEqual(svg.count('class="day"'), 4)

    def test_build_svg_labels_months(self):
        svg = github_stats.build_svg(SAMPLE)
        self.assertIn(">Oct<", svg)

    def test_build_svg_hides_partial_first_month(self):
        svg = github_stats.build_svg(SAMPLE)
        self.assertNotIn(">Sep<", svg)

    def test_build_svg_draws_icon_per_row(self):
        svg = github_stats.build_svg(SAMPLE)
        self.assertEqual(svg.count('class="icon"'), len(github_stats.STAT_ROWS))


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
                    "totalCommitContributions": 176,
                    "restrictedContributionsCount": 6,
                    "totalIssueContributions": 14,
                    "totalPullRequestContributions": 7,
                    "contributionCalendar": {"totalContributions": 207, "weeks": CALENDAR_WEEKS},
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

    def test_commits_exclude_restricted_contributions(self):
        with mock.patch.object(github_stats.requests, "post",
                               return_value=fake_response(viewer_page([3], False, None))):
            self.assertEqual(github_stats.fetch_stats("t")["commits"], 176)

    def test_fetch_stats_stops_when_cursor_missing(self):
        pages = [fake_response(viewer_page([3], True, None))]
        with mock.patch.object(github_stats.requests, "post", side_effect=pages) as post:
            self.assertEqual(github_stats.fetch_stats("t")["stars"], 3)
        self.assertEqual(post.call_count, 1)

    def run_main_against_sentinel(self, env, **post_kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "github-stats.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write("previous card")
            with (mock.patch.dict(os.environ, env, clear=True),
                  mock.patch.object(github_stats, "OUTPUT", path),
                  mock.patch.object(github_stats.requests, "post", **post_kwargs)):
                with self.assertRaises((SystemExit, RuntimeError)):
                    github_stats.main()
            with open(path, encoding="utf-8") as f:
                return f.read()

    def test_main_keeps_svg_on_graphql_error(self):
        content = self.run_main_against_sentinel(
            {"GH_TOKEN": "t"}, return_value=fake_response({"errors": [{"message": "x"}]}))
        self.assertEqual(content, "previous card")

    def test_main_keeps_svg_without_token(self):
        self.assertEqual(self.run_main_against_sentinel({}), "previous card")

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
