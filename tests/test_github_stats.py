import io
import os
import sys
import tempfile
import unittest
from datetime import date
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

    def test_quartiles_of_active_days(self):
        self.assertEqual(github_stats.quartiles([0, 1, 2, 3, 4, 5, 6, 7, 8]), [2, 4, 6])
        self.assertEqual(github_stats.quartiles([0, 0]), [0, 0, 0])

    def test_level_for_uses_quartiles(self):
        cuts = [2, 4, 6]
        self.assertEqual(github_stats.level_for(0, cuts), 0)
        self.assertEqual(github_stats.level_for(1, cuts), 1)
        self.assertEqual(github_stats.level_for(3, cuts), 2)
        self.assertEqual(github_stats.level_for(6, cuts), 3)
        self.assertEqual(github_stats.level_for(50, cuts), 4)

    def test_one_busy_day_does_not_darken_the_rest(self):
        counts = [1] * 20 + [2] * 20 + [3] * 20 + [100]
        cuts = github_stats.quartiles(counts)
        self.assertGreaterEqual(github_stats.level_for(3, cuts), 3)

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


def fake_response(payload, next_url=None):
    resp = mock.Mock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    resp.links = {"next": {"url": next_url}} if next_url else {}
    return resp


def commit(sha_date, message="feat: work", login="brunosiqp"):
    return {"author": {"login": login}, "commit": {"message": message, "author": {"date": sha_date}}}


VIEWER = {
    "viewer": {
        "login": "brunosiqp",
        "createdAt": "2024-05-01T19:20:26Z",
        "pullRequests": {"totalCount": 34},
        "repositories": {
            "totalCount": 42,
            "pageInfo": {"hasNextPage": False, "endCursor": None},
            "nodes": [
                {"nameWithOwner": "brunosiqp/a", "isFork": False, "isEmpty": False, "stargazerCount": 2},
                {"nameWithOwner": "brunosiqp/b", "isFork": False, "isEmpty": False, "stargazerCount": 1},
                {"nameWithOwner": "brunosiqp/fork", "isFork": True, "isEmpty": False, "stargazerCount": 0},
                {"nameWithOwner": "brunosiqp/empty", "isFork": False, "isEmpty": True, "stargazerCount": 0},
            ],
        },
    }
}


class HelperTests(unittest.TestCase):
    def test_local_date_converts_utc_to_brasilia(self):
        self.assertEqual(github_stats.local_date("2026-05-03T01:30:00Z"), "2026-05-02")
        self.assertEqual(github_stats.local_date("2026-05-03T12:00:00Z"), "2026-05-03")

    def test_is_automated_matches_bot_commits(self):
        self.assertTrue(github_stats.is_automated("chore: atualiza estatísticas de linguagens"))
        self.assertTrue(github_stats.is_automated("chore: update GitHub stats"))
        self.assertTrue(github_stats.is_automated("chore: update language stats"))
        self.assertFalse(github_stats.is_automated("feat: add runner"))

    def test_build_calendar_covers_53_weeks_ending_today(self):
        today = date(2026, 10, 14)  # a Wednesday
        weeks = github_stats.build_calendar(["2026-10-14", "2026-10-14", "2026-10-12"], today)
        self.assertEqual(len(weeks), 53)
        self.assertEqual(weeks[-1][-1], {"date": "2026-10-14", "count": 2})
        self.assertEqual(weeks[-1][1], {"date": "2026-10-12", "count": 1})
        self.assertEqual(date.fromisoformat(weeks[0][0]["date"]).weekday(), 6)  # Sunday
        self.assertTrue(all(len(w) == 7 for w in weeks[:-1]))

    def test_build_calendar_ignores_dates_outside_range(self):
        weeks = github_stats.build_calendar(["2020-01-01", "2030-01-01"], date(2026, 10, 14))
        self.assertEqual(sum(d["count"] for w in weeks for d in w), 0)

    def test_rest_pages_follows_next_links(self):
        pages = [fake_response([1, 2], next_url="https://api.github.com/x?page=2"),
                 fake_response([3])]
        with mock.patch.object(github_stats.requests, "get", side_effect=pages) as get:
            self.assertEqual(list(github_stats.rest_pages("t", "https://api.github.com/x")), [1, 2, 3])
        self.assertEqual(get.call_args_list[1].args[0], "https://api.github.com/x?page=2")

    def test_rest_pages_retries_dropped_connection(self):
        attempts = [github_stats.requests.ConnectionError("eof"), fake_response([1])]
        with (mock.patch.object(github_stats.requests, "get", side_effect=attempts),
              mock.patch.object(github_stats.time, "sleep")):
            self.assertEqual(list(github_stats.rest_pages("t", "https://api.github.com/x")), [1])

    def test_rest_pages_gives_up_after_retries(self):
        error = github_stats.requests.ConnectionError("eof")
        with (mock.patch.object(github_stats.requests, "get", side_effect=[error] * 5),
              mock.patch.object(github_stats.time, "sleep")):
            with self.assertRaises(github_stats.requests.ConnectionError):
                list(github_stats.rest_pages("t", "https://api.github.com/x"))

    def test_with_retries_retries_timeouts(self):
        calls = [github_stats.requests.Timeout("slow"), "ok"]
        def send():
            item = calls.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        with mock.patch.object(github_stats.time, "sleep"):
            self.assertEqual(github_stats.with_retries(send), "ok")

    def test_with_retries_retries_server_errors(self):
        responses = [mock.Mock(status_code=502, headers={}), mock.Mock(status_code=200, headers={})]
        with mock.patch.object(github_stats.time, "sleep"):
            self.assertEqual(github_stats.with_retries(lambda: responses.pop(0)).status_code, 200)

    def test_rest_pages_reads_items_from_search(self):
        with mock.patch.object(github_stats.requests, "get",
                               return_value=fake_response({"total_count": 1, "items": [{"id": 9}]})):
            self.assertEqual(list(github_stats.rest_pages("t", "https://api.github.com/search/issues")),
                             [{"id": 9}])

    def test_rest_pages_skips_empty_repository(self):
        resp = mock.Mock(status_code=409, links={})
        with mock.patch.object(github_stats.requests, "get", return_value=resp):
            self.assertEqual(list(github_stats.rest_pages("t", "https://api.github.com/x")), [])

    def test_commit_dates_keeps_only_own_manual_commits(self):
        items = [commit("2026-10-14T12:00:00Z"),
                 commit("2026-10-13T12:00:00Z", "chore: update GitHub stats"),
                 commit("2026-10-12T12:00:00Z", login="someone-else")]
        with mock.patch.object(github_stats, "rest_pages", return_value=iter(items)):
            dates = github_stats.commit_dates("t", "brunosiqp", "brunosiqp/a", "2025-10-14T00:00:00Z")
        self.assertEqual(dates, ["2026-10-14"])


class FetchStatsTests(unittest.TestCase):
    def test_graphql_raises_on_errors(self):
        with mock.patch.object(github_stats.requests, "post",
                               return_value=fake_response({"errors": [{"message": "x"}]})):
            with self.assertRaises(RuntimeError):
                github_stats.graphql("t", "{ viewer { login } }")

    def test_fetch_stats_counts_commits_prs_and_issues_from_owned_repos(self):
        def fake_commits(token, login, repo, since):
            return {"brunosiqp/a": ["2026-10-14", "2026-10-13"], "brunosiqp/b": ["2026-10-14"]}[repo]

        def fake_search(token, query):
            if "type:pr" in query and "created:" in query:
                return ["2026-10-10"]
            if "type:issue" in query:
                return ["2026-10-11", "2026-10-12"]
            raise AssertionError(query)

        with mock.patch.object(github_stats, "graphql", return_value=VIEWER["viewer"] and VIEWER), \
                mock.patch.object(github_stats, "commit_dates", side_effect=fake_commits) as commits, \
                mock.patch.object(github_stats, "search_dates", side_effect=fake_search):
            stats = github_stats.fetch_stats("t", today=date(2026, 10, 14))

        self.assertEqual([c.args[2] for c in commits.call_args_list], ["brunosiqp/a", "brunosiqp/b"])
        self.assertEqual(stats["commits"], 3)
        self.assertEqual(stats["pull_requests"], 1)
        self.assertEqual(stats["issues"], 2)
        self.assertEqual(stats["contributions"], 6)
        self.assertEqual(stats["pull_requests_total"], 34)
        self.assertEqual(stats["repositories"], 42)
        self.assertEqual(stats["stars"], 3)
        self.assertEqual(stats["since"], 2024)
        self.assertEqual(sum(d["count"] for w in stats["calendar"] for d in w), 6)

    def test_fetch_stats_skips_failing_repo_without_leaking_its_name(self):
        def fake_commits(token, login, repo, since):
            if repo == "brunosiqp/b":
                raise github_stats.requests.HTTPError(
                    "404 Client Error: Not Found for url: https://api.github.com/repos/brunosiqp/b/commits")
            return ["2026-10-14"]

        with (mock.patch.object(github_stats, "graphql", return_value=VIEWER),
              mock.patch.object(github_stats, "commit_dates", side_effect=fake_commits),
              mock.patch.object(github_stats, "search_dates", return_value=[]),
              mock.patch("sys.stdout", new_callable=io.StringIO) as out):
            stats = github_stats.fetch_stats("t", today=date(2026, 10, 14))
        self.assertEqual(stats["commits"], 1)
        self.assertEqual(stats["skipped_repositories"], 1)
        self.assertNotIn("brunosiqp/b", out.getvalue())

    def test_total_matches_the_heatmap_window(self):
        old = "2025-10-18"  # exactly 365 days ago: inside a "year", but before the first drawn Sunday
        with (mock.patch.object(github_stats, "graphql", return_value=VIEWER),
              mock.patch.object(github_stats, "commit_dates", return_value=[old, "2026-10-14"]),
              mock.patch.object(github_stats, "search_dates", return_value=[])):
            stats = github_stats.fetch_stats("t", today=date(2026, 10, 18))  # a Sunday
        drawn = sum(d["count"] for w in stats["calendar"] for d in w)
        self.assertEqual(stats["contributions"], drawn)

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


if __name__ == "__main__":
    unittest.main()
