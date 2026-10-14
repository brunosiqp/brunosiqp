"""
Generates github-stats.svg: a "GitHub Activity" card with aggregate numbers for the
token owner. Commits are counted straight from every owned repository (public and
private), because GitHub's contribution calendar hides private work unless the
profile setting "Private contributions" is on. Only totals are printed or drawn,
never repository names.
"""

import math
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from html import escape

import requests

API = "https://api.github.com"
GRAPHQL_URL = f"{API}/graphql"
OUTPUT = "github-stats.svg"

QUERY = """
query($cursor: String) {
  viewer {
    login
    createdAt
    pullRequests { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100, after: $cursor) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { nameWithOwner isFork isEmpty stargazerCount }
    }
  }
}
"""

# Brazil has no daylight saving time since 2019, so a fixed offset is enough.
LOCAL_TZ = timezone(timedelta(hours=-3))

# Commits made by workflows under the owner's identity; not real work.
AUTOMATED_PREFIXES = (
    "chore: atualiza estatísticas",
    "chore: update GitHub stats",
    "chore: update language stats",
)

# (key in the stats dict, label shown on the card), in display order.
STAT_ROWS = [
    ("contributions", "Contributions"),
    ("commits", "Commits"),
    ("pull_requests", "Pull requests"),
    ("issues", "Issues"),
    ("repositories", "Repositories"),
    ("pull_requests_total", "Pull requests (all time)"),
    ("stars", "Stars"),
    ("since", "On GitHub since"),
]

ACCENT = "#58a6ff"
HEAT_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

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
ICONS["pull_requests_total"] = ICONS["pull_requests"]


def with_retries(send, attempts=4):
    """Retries dropped connections (flaky proxies, GitHub hiccups) with a short backoff."""
    for attempt in range(attempts):
        try:
            return send()
        except requests.ConnectionError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)


def graphql(token, query, variables=None):
    resp = with_retries(lambda: requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"bearer {token}"},
        timeout=30,
    ))
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(f"GraphQL error: {body['errors'][0].get('message')}")
    return body["data"]


def rest_pages(token, url, params=None):
    """Yields every item of a paginated REST list (or search) endpoint."""
    headers = {"Authorization": f"bearer {token}", "Accept": "application/vnd.github+json"}
    while url:
        resp = with_retries(lambda: requests.get(url, params=params, headers=headers, timeout=30))
        if resp.status_code == 409:  # empty repository
            return
        resp.raise_for_status()
        body = resp.json()
        yield from body["items"] if isinstance(body, dict) else body
        url = resp.links.get("next", {}).get("url")
        params = None  # the next link already carries the query string


def local_date(timestamp):
    moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return moment.astimezone(LOCAL_TZ).date().isoformat()


def is_automated(message):
    return message.startswith(AUTOMATED_PREFIXES)


def commit_dates(token, login, repo, since):
    """Local dates of the user's own commits on the default branch of `repo`."""
    return [
        local_date(item["commit"]["author"]["date"])
        for item in rest_pages(token, f"{API}/repos/{repo}/commits",
                               {"author": login, "since": since, "per_page": 100})
        if (item.get("author") or {}).get("login") == login
        and not is_automated(item["commit"]["message"])
    ]


def search_dates(token, query):
    """Local creation dates of the issues or pull requests matched by a search query."""
    return [
        local_date(item["created_at"])
        for item in rest_pages(token, f"{API}/search/issues", {"q": query, "per_page": 100})
    ]


def build_calendar(dates, today):
    """53 weeks ending today, Sunday first, in the shape build_heatmap draws."""
    counts = {}
    for day in dates:
        counts[day] = counts.get(day, 0) + 1
    start = today - timedelta(weeks=52)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    weeks = []
    day = start
    while day <= today:
        if not weeks or len(weeks[-1]) == 7:
            weeks.append([])
        weeks[-1].append({"date": day.isoformat(), "count": counts.get(day.isoformat(), 0)})
        day += timedelta(days=1)
    return weeks


def fetch_stats(token, today=None):
    today = today or datetime.now(LOCAL_TZ).date()
    year_ago = today - timedelta(days=365)
    since = f"{year_ago.isoformat()}T00:00:00Z"

    cursor = None
    repos = []
    first = None
    while True:
        viewer = graphql(token, QUERY, {"cursor": cursor})["viewer"]
        first = first or viewer
        page = viewer["repositories"]
        repos.extend(page["nodes"])
        cursor = page["pageInfo"]["endCursor"]
        if not page["pageInfo"]["hasNextPage"] or not cursor:
            break

    login = first["login"]
    commits = []
    for repo in repos:
        if not repo["isFork"] and not repo["isEmpty"]:
            commits += commit_dates(token, login, repo["nameWithOwner"], since)
    prs = search_dates(token, f"author:{login} type:pr created:>={year_ago.isoformat()}")
    issues = search_dates(token, f"author:{login} type:issue created:>={year_ago.isoformat()}")

    year_start = year_ago.isoformat()
    commits = [d for d in commits if d >= year_start]
    activity = commits + prs + issues
    return {
        "contributions": len(activity),
        "commits": len(commits),
        "pull_requests": len(prs),
        "issues": len(issues),
        "pull_requests_total": first["pullRequests"]["totalCount"],
        "repositories": first["repositories"]["totalCount"],
        "stars": sum(repo["stargazerCount"] for repo in repos),
        "since": int(first["createdAt"][:4]),
        "calendar": build_calendar(activity, today),
    }


def fmt_value(value):
    return f"{value:,}"


def quartiles(counts):
    """Cut points between the 4 color levels, taken from the active days only (like GitHub)."""
    active = sorted(c for c in counts if c > 0)
    if not active:
        return [0, 0, 0]
    return [active[max(0, math.ceil(len(active) * k / 4) - 1)] for k in (1, 2, 3)]


def level_for(count, cuts):
    if count <= 0:
        return 0
    return 1 + sum(count > cut for cut in cuts)


def build_heatmap(calendar, x, y):
    """Contribution grid like the GitHub profile: one column per week, Sunday on top."""
    step = 14
    cuts = quartiles([day["count"] for week in calendar for day in week])
    cells = []
    changes = []
    for w, week in enumerate(calendar):
        month = date.fromisoformat(week[0]["date"]).month
        if not changes or changes[-1][1] != month:
            changes.append((w, month))
    if len(changes) > 1 and changes[1][0] - changes[0][0] < 3:
        changes.pop(0)
    months = [
        f'<text x="{x + w * step}" y="{y - 8}" class="muted">{MONTHS[month - 1]}</text>'
        for w, month in changes
    ]
    for w, week in enumerate(calendar):
        cx = x + w * step
        for day in week:
            row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
            color = HEAT_COLORS[level_for(day["count"], cuts)]
            cells.append(
                f'<rect class="day" x="{cx}" y="{y + row * step}" width="11" height="11" rx="2" fill="{color}" />'
            )
    weekdays = "".join(
        f'<text x="{x - 30}" y="{y + row * step + 10}" class="muted">{name}</text>'
        for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    return "".join(months) + weekdays + "".join(cells)


def build_svg(stats, width=830, title="GitHub Activity"):
    pad = 28
    tiles = STAT_ROWS[:4]
    extras = STAT_ROWS[4:]
    gap = 14
    tile_w = (width - 2 * pad - gap * (len(tiles) - 1)) / max(len(tiles), 1)
    tile_y, tile_h = 84, 84

    def value_of(key):
        return str(stats[key]) if key == "since" else fmt_value(stats[key])

    def icon(key, ix, iy):
        paths = "".join(f'<path d="{d}" />' for d in ICONS.get(key, []))
        return f'<g class="icon" transform="translate({ix:.0f} {iy:.0f})" fill="{ACCENT}">{paths}</g>'

    parts = []
    for i, (key, label) in enumerate(tiles):
        tx = pad + i * (tile_w + gap)
        parts.append(
            f'<rect x="{tx:.0f}" y="{tile_y}" width="{tile_w:.0f}" height="{tile_h}" rx="10" class="tile" />'
            + icon(key, tx + 16, tile_y + 16)
            + f'<text x="{tx + 40:.0f}" y="{tile_y + 29}" class="muted">{escape(label)}</text>'
            f'<text x="{tx + 16:.0f}" y="{tile_y + 68}" class="big">{escape(value_of(key))}</text>'
        )

    extra_y = tile_y + tile_h + 34
    # Estimated text widths (13px Segoe UI) so the items spread evenly across the row.
    widths = [24 + 7 * len(label) + 8 + 8 * len(value_of(key)) for key, label in extras]
    spacing = (width - 2 * pad - sum(widths)) / max(len(extras) - 1, 1)
    ex = pad
    for (key, label), item_width in zip(extras, widths):
        parts.append(
            icon(key, ex, extra_y - 12)
            + f'<text x="{ex + 24:.0f}" y="{extra_y}"><tspan class="label">{escape(label)}</tspan>'
            f'<tspan dx="8" class="value">{escape(value_of(key))}</tspan></text>'
        )
        ex += item_width + spacing

    calendar = stats.get("calendar", [])
    heat_y = extra_y + 52
    parts.append(build_heatmap(calendar, pad + 30, heat_y))

    legend_y = heat_y + 7 * 14 + 14
    legend_x = width - pad - 5 * 14 - 34
    parts.append(f'<text x="{legend_x - 34}" y="{legend_y + 10}" class="muted">Less</text>')
    parts.extend(
        f'<rect x="{legend_x + i * 14}" y="{legend_y}" width="11" height="11" rx="2" fill="{c}" />'
        for i, c in enumerate(HEAT_COLORS)
    )
    parts.append(f'<text x="{legend_x + 5 * 14 + 4}" y="{legend_y + 10}" class="muted">More</text>')
    height = legend_y + 32

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .title {{ font: 600 20px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .subtitle {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
    .muted {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
    .label {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
    .value {{ font: 700 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .big {{ font: 700 28px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .tile {{ fill: #161b22; stroke: #30363d; }}
  </style>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="#0d1117" stroke="#30363d" />
  <text x="{pad}" y="44" class="title">{escape(title)}</text>
  <text x="{pad}" y="66" class="subtitle">Last 12 months · public and private repositories</text>
  {''.join(parts)}
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
