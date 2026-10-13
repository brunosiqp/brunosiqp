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

# 16px path data from Primer Octicons (MIT License, GitHub Inc.), one icon per row.
ICONS = {
    "contributions": ["M1.5 1.75V13.5h13.75a.75.75 0 0 1 0 1.5H.75a.75.75 0 0 1-.75-.75V1.75a.75.75 0 0 1 1.5 0Zm14.28 2.53-5.25 5.25a.75.75 0 0 1-1.06 0L7 7.06 4.28 9.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.25-3.25a.75.75 0 0 1 1.06 0L10 7.94l4.72-4.72a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042Z"],
    "commits": ["M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z"],
    "pull_requests": ["M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"],
    "issues": ["M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z", "M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"],
    "repositories": ["M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"],
    "stars": ["M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z"],
    "since": ["M4.75 0a.75.75 0 0 1 .75.75V2h5V.75a.75.75 0 0 1 1.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0 1 13.25 16H2.75A1.75 1.75 0 0 1 1 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 0 1 4.75 0ZM2.5 7.5v6.75c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V7.5Zm10.75-4H2.75a.25.25 0 0 0-.25.25V6h11V3.75a.25.25 0 0 0-.25-.25Z"],
}


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
        cursor = repos["pageInfo"]["endCursor"]
        if not repos["pageInfo"]["hasNextPage"] or not cursor:
            break

    contrib = first["contributionsCollection"]
    return {
        "contributions": contrib["contributionCalendar"]["totalContributions"],
        "commits": contrib["totalCommitContributions"],
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
            f'<g class="icon" transform="translate({lx} {ly - 12})" fill="{ACCENT}">'
            + "".join(f'<path d="{d}" />' for d in ICONS.get(key, []))
            + '</g>'
            f'<text x="{lx + 24}" y="{ly}" class="label">{escape(label)}</text>'
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
