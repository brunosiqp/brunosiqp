"""
Generates github-stats.svg: a "GitHub Stats" card with aggregate numbers for the
token owner (public and private contributions). Only totals are printed or drawn,
never repository names.
"""

from html import escape

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
