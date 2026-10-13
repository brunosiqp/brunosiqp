"""
Generates github-stats.svg: a "GitHub Stats" card with aggregate numbers for the
token owner (public and private contributions). Only totals are printed or drawn,
never repository names.
"""

import os
import sys
from html import escape

import requests

GRAPHQL_URL = "https://api.github.com/graphql"
OUTPUT = "github-stats.svg"

QUERY = """
query($cursor: String) {
  viewer {
    createdAt
    pullRequests { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
    repositories(ownerAffiliations: OWNER, first: 100, after: $cursor) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
  }
}
"""

# (key in the stats dict, label shown on the card), in display order.
STAT_ROWS = [
    ("contributions", "Contributions (last year)"),
    ("commits", "Commits (last year)"),
    ("pull_requests", "Pull requests"),
    ("issues", "Issues (last year)"),
    ("repositories", "Repositories"),
    ("stars", "Stars earned"),
    ("since", "On GitHub since"),
]

ACCENT = "#58a6ff"


def graphql(token, query, variables=None):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(f"GraphQL error: {body['errors'][0].get('message')}")
    return body["data"]


def fetch_stats(token):
    cursor = None
    stars = 0
    first = None
    while True:
        viewer = graphql(token, QUERY, {"cursor": cursor})["viewer"]
        first = first or viewer
        repos = viewer["repositories"]
        stars += sum(node["stargazerCount"] for node in repos["nodes"])
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]

    contrib = first["contributionsCollection"]
    return {
        "contributions": contrib["contributionCalendar"]["totalContributions"],
        "commits": contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        "pull_requests": first["pullRequests"]["totalCount"],
        "issues": contrib["totalIssueContributions"],
        "repositories": first["repositories"]["totalCount"],
        "stars": stars,
        "since": int(first["createdAt"][:4]),
    }


def fmt_value(value):
    return f"{value:,}"


def build_svg(stats, width=700, title="GitHub Stats"):
    x = 20
    col_width = (width - 2 * x) // 2
    rows_per_col = (len(STAT_ROWS) + 1) // 2
    top = 72
    row_height = 30

    items = []
    for i, (key, label) in enumerate(STAT_ROWS):
        col, row = divmod(i, rows_per_col)
        lx = x + col * (col_width + 20)
        ly = top + row * row_height
        value = str(stats[key]) if key == "since" else fmt_value(stats[key])
        items.append(
            f'<circle cx="{lx + 5}" cy="{ly - 5}" r="5" fill="{ACCENT}" />'
            f'<text x="{lx + 18}" y="{ly}" class="label">{escape(label)}</text>'
            f'<text x="{lx + col_width - 20}" y="{ly}" text-anchor="end" class="value">{escape(value)}</text>'
        )

    height = top + (rows_per_col - 1) * row_height + 28

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .title {{ font: 600 20px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #d0d0d0; }}
    .value {{ font: 700 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
  </style>
  <rect width="100%" height="100%" rx="8" fill="#0d1117" />
  <text x="20" y="35" class="title">{escape(title)}</text>
  {''.join(items)}
</svg>'''


def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set (classic PAT with `repo` and `read:user`).")

    stats = fetch_stats(token)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(build_svg(stats))

    for key, label in STAT_ROWS:
        print(f"{label}: {stats[key]}")


if __name__ == "__main__":
    main()
