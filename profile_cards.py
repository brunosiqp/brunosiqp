"""
Generates the static SVG cards of the profile README (featured projects, "What I do"
and education) in the same visual style as github-stats.svg.

Run it after editing the content below; the cards are committed to assets/.
"""

import os
import sys
from html import escape

from github_stats import ICONS
from tech_icons import TECH_ICONS

FONT = "'Segoe UI', Ubuntu, Sans-Serif"
CARD_WIDTH = 410
FULL_WIDTH = 830
ACCENT = "#58a6ff"

# 16px path data from Primer Octicons (MIT License, GitHub Inc.).
OCTICONS = {
    "repo": ICONS["repositories"][0],
    "zap": "M9.504.43a1.516 1.516 0 0 1 2.437 1.713L10.415 5.5h2.123c1.57 0 2.346 1.909 1.22 3.004l-7.34 7.142a1.249 1.249 0 0 1-.871.354h-.302a1.25 1.25 0 0 1-1.157-1.723L5.633 10.5H3.462c-1.57 0-2.346-1.909-1.22-3.004L9.503.429Zm1.047 1.074L3.286 8.571A.25.25 0 0 0 3.462 9H6.75a.75.75 0 0 1 .694 1.034l-1.713 4.188 6.982-6.793A.25.25 0 0 0 12.538 7H9.25a.75.75 0 0 1-.683-1.06l2.008-4.418.003-.006a.036.036 0 0 0-.004-.009l-.006-.006-.008-.001c-.003 0-.006.002-.009.004Z",
    "workflow": "M0 1.75C0 .784.784 0 1.75 0h3.5C6.216 0 7 .784 7 1.75v3.5A1.75 1.75 0 0 1 5.25 7H4v4a1 1 0 0 0 1 1h4v-1.25C9 9.784 9.784 9 10.75 9h3.5c.966 0 1.75.784 1.75 1.75v3.5A1.75 1.75 0 0 1 14.25 16h-3.5A1.75 1.75 0 0 1 9 14.25v-.75H5A2.5 2.5 0 0 1 2.5 11V7h-.75A1.75 1.75 0 0 1 0 5.25Zm1.75-.25a.25.25 0 0 0-.25.25v3.5c0 .138.112.25.25.25h3.5a.25.25 0 0 0 .25-.25v-3.5a.25.25 0 0 0-.25-.25Zm9 9a.25.25 0 0 0-.25.25v3.5c0 .138.112.25.25.25h3.5a.25.25 0 0 0 .25-.25v-3.5a.25.25 0 0 0-.25-.25Z",
    "people": "M2 5.5a3.5 3.5 0 1 1 5.898 2.549 5.508 5.508 0 0 1 3.034 4.084.75.75 0 1 1-1.482.235 4 4 0 0 0-7.9 0 .75.75 0 0 1-1.482-.236A5.507 5.507 0 0 1 3.102 8.05 3.493 3.493 0 0 1 2 5.5ZM11 4a3.001 3.001 0 0 1 2.22 5.018 5.01 5.01 0 0 1 2.56 3.012.749.749 0 0 1-.885.954.752.752 0 0 1-.549-.514 3.507 3.507 0 0 0-2.522-2.372.75.75 0 0 1-.574-.73v-.352a.75.75 0 0 1 .416-.672A1.5 1.5 0 0 0 11 5.5.75.75 0 0 1 11 4Zm-5.5-.5a2 2 0 1 0-.001 3.999A2 2 0 0 0 5.5 3.5Z",
    "graph": ICONS["contributions"][0],
    "sparkle": "M7.53 1.282a.5.5 0 0 1 .94 0l.478 1.306a7.492 7.492 0 0 0 4.464 4.464l1.305.478a.5.5 0 0 1 0 .94l-1.305.478a7.492 7.492 0 0 0-4.464 4.464l-.478 1.305a.5.5 0 0 1-.94 0l-.478-1.305a7.492 7.492 0 0 0-4.464-4.464L1.282 8.47a.5.5 0 0 1 0-.94l1.306-.478a7.492 7.492 0 0 0 4.464-4.464Z",
    "verified": "m9.585.52.929.68c.153.112.331.186.518.215l1.138.175a2.678 2.678 0 0 1 2.24 2.24l.174 1.139c.029.187.103.365.215.518l.68.928a2.677 2.677 0 0 1 0 3.17l-.68.928a1.174 1.174 0 0 0-.215.518l-.175 1.138a2.678 2.678 0 0 1-2.241 2.241l-1.138.175a1.17 1.17 0 0 0-.518.215l-.928.68a2.677 2.677 0 0 1-3.17 0l-.928-.68a1.174 1.174 0 0 0-.518-.215L3.83 14.41a2.678 2.678 0 0 1-2.24-2.24l-.175-1.138a1.17 1.17 0 0 0-.215-.518l-.68-.928a2.677 2.677 0 0 1 0-3.17l.68-.928c.112-.153.186-.331.215-.518l.175-1.14a2.678 2.678 0 0 1 2.24-2.24l1.139-.175c.187-.029.365-.103.518-.215l.928-.68a2.677 2.677 0 0 1 3.17 0ZM7.303 1.728l-.927.68a2.67 2.67 0 0 1-1.18.489l-1.137.174a1.179 1.179 0 0 0-.987.987l-.174 1.136a2.677 2.677 0 0 1-.489 1.18l-.68.928a1.18 1.18 0 0 0 0 1.394l.68.927c.256.348.424.753.489 1.18l.174 1.137c.078.509.478.909.987.987l1.136.174a2.67 2.67 0 0 1 1.18.489l.928.68c.414.305.979.305 1.394 0l.927-.68a2.67 2.67 0 0 1 1.18-.489l1.137-.174a1.18 1.18 0 0 0 .987-.987l.174-1.136a2.67 2.67 0 0 1 .489-1.18l.68-.928a1.176 1.176 0 0 0 0-1.394l-.68-.927a2.686 2.686 0 0 1-.489-1.18l-.174-1.137a1.179 1.179 0 0 0-.987-.987l-1.136-.174a2.677 2.677 0 0 1-1.18-.489l-.928-.68a1.176 1.176 0 0 0-1.394 0ZM11.28 6.78l-3.75 3.75a.75.75 0 0 1-1.06 0L4.72 8.78a.75.75 0 0 1 1.06-1.06l1.22 1.22 3.22-3.22a.75.75 0 0 1 1.06 1.06Z",
    "book": "M0 1.75A.75.75 0 0 1 .75 1h4.253c1.227 0 2.317.59 3 1.501A3.743 3.743 0 0 1 11.006 1h4.245a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75h-4.507a2.25 2.25 0 0 0-1.591.659l-.622.621a.75.75 0 0 1-1.06 0l-.622-.621A2.25 2.25 0 0 0 5.258 13H.75a.75.75 0 0 1-.75-.75Zm7.251 10.324.004-5.073-.002-2.253A2.25 2.25 0 0 0 5.003 2.5H1.5v9h3.757a3.75 3.75 0 0 1 1.994.574ZM8.755 4.75l-.004 7.322a3.752 3.752 0 0 1 1.992-.572H14.5v-9h-3.495a2.25 2.25 0 0 0-2.25 2.25Z",
    "mortar-board":"M7.693 1.066a.747.747 0 0 1 .614 0l7.25 3.25a.75.75 0 0 1 0 1.368L13 6.831v2.794c0 1.024-.81 1.749-1.66 2.173-.893.447-2.075.702-3.34.702-.278 0-.55-.012-.816-.036a.75.75 0 0 1 .133-1.494c.22.02.45.03.683.03 1.082 0 2.025-.221 2.67-.543.69-.345.83-.682.83-.832V7.503L8.307 8.934a.747.747 0 0 1-.614 0L4 7.28v1.663c.296.105.575.275.812.512.438.438.688 1.059.688 1.796v3a.75.75 0 0 1-.75.75h-3a.75.75 0 0 1-.75-.75v-3c0-.737.25-1.358.688-1.796.237-.237.516-.407.812-.512V6.606L.443 5.684a.75.75 0 0 1 0-1.368ZM2.583 5 8 7.428 13.416 5 8 2.572ZM2.5 11.25v2.25H4v-2.25c0-.388-.125-.611-.25-.735a.697.697 0 0 0-.5-.203.707.707 0 0 0-.5.203c-.125.124-.25.347-.25.735Z",
}

PROJECTS = [
    {
        "name": "envy-converter",
        "description": "Windows app that converts PDF to DOCX and other formats without corrupting the files.",
        "stack": [("C#", "#178600"), ("WPF", "#512BD4")],
        "license": "MIT",
    },
    {
        "name": "MegaQG-Vivo",
        "description": "Batch automation of NFCom and NFSe fiscal operations, with a report exporter.",
        "stack": [("Python", "#3572A5")],
        "license": None,
    },
    {
        "name": "LongNameJanitor",
        "description": "Windows service that watches folders and deletes or moves files with long names, with a live web dashboard.",
        "stack": [("C#", "#178600"), ("Windows Service", "#0078D4")],
        "license": "MIT",
    },
    {
        "name": "PDA",
        "description": "Automation panel: fiscal alerts, monitors, help desk indicators and support tools in a single app.",
        "stack": [("Python", "#3572A5"), ("Tkinter", "#8b949e")],
        "license": None,
    },
    {
        "name": "github-lang-stats",
        "description": "Generates the languages card from all public and private repositories, using GitHub Linguist.",
        "stack": [("Python", "#3572A5"), ("GitHub Actions", "#2088FF")],
        "license": "MIT",
    },
    {
        "name": "docker-n8n-project",
        "description": "Workflow automation lab with n8n and Docker Compose.",
        "stack": [("Docker", "#2496ED"), ("n8n", "#EA4B71")],
        "license": "MIT",
    },
]

WHAT_I_DO = [
    ("Automation", "zap",
     "Python automations and Windows services that integrate REST APIs, web services and "
     "databases, processing large volumes of data with logging and error handling."),
    ("Processes & administration", "workflow",
     "I create, document and manage operational processes end to end, from mapping and "
     "implementation to monitoring and continuous improvement."),
    ("Team coordination", "people",
     "I run alignments, trainings and feedback sessions, and coordinate the team on using "
     "the automations and handling day-to-day cases."),
    ("Dashboards", "graph",
     "Dashboards and monitoring panels with indicators and alerts that support day-to-day "
     "decisions."),
    ("AI assistant (Invi)", "sparkle",
     "I built Invi, the company's internal AI assistant: our automations log every run "
     "as structured, LGPD-sanitized data that feeds it and turns into real actions for the team."),
]

LEARNING = "Currently learning"

TECH_STACK = [
    ("Languages", [("Python", "python"), ("C#", "csharp"), ("PowerShell", "powershell"),
                   ("JavaScript", "javascript"), ("TypeScript", "typescript"), ("HTML", "html"), ("CSS", "css")]),
    ("AI & agents", [("Anthropic API", "anthropic"), ("Claude Code", "claude"), ("AI Agents", "agents"), ("LLM Automation", "llm")]),
    ("Data", [("SQL Server", "sqlserver"), ("Oracle", "oracle"), ("Excel Automation", "excel"),
              ("Power BI", "powerbi")]),
    ("Cloud", [("Azure", "azure"), ("Amazon S3", "s3")]),
    ("Integration & automation", [("REST APIs", "rest"), ("Webhooks", "webhooks"),
                                  ("GitHub Actions", "githubactions")]),
    ("Security", [("LGPD", "lgpd"), ("Cloudflare Zero Trust", "cloudflare"), ("Information Security", "infosec")]),
    ("Infra & tools", [("Linux", "linux"), ("Windows Server / IIS", "windows"), ("Docker", "docker"), ("Kubernetes", "kubernetes"), ("Minikube", "minikube"),
                       ("Git", "git"), ("Godot", "godot")]),
    (LEARNING, [("MCP", "mcp"), ("LMM (Multimodal AI)", "lmm"), ("Hermes Agent", "hermes"), ("Ollama", "ollama"),
                ("n8n", "n8n")]),
]

EDUCATION = [
    ("Postgraduate in Applied AI Engineering", "UNIDPS", "2026 – 2027", "In progress"),
    ("Postgraduate in Data Science & Artificial Intelligence", "SENAI", "2026 – 2027", "In progress"),
    ("Technologist in Systems Analysis and Development", "UNIASSELVI", "2024 – 2026", "Completed"),
]

# Set "enabled" to False to hide an entry without deleting it. Dates are "Mon YYYY".
CERTIFICATIONS = [
    {"title": "Python Fundamentals for Data Analysis, Data Science and Machine Learning",
     "issuer": "Data Science Academy", "date": "Mar 2026", "credential_id": None,
     "credential_url": None, "skills": ["Python", "Data Analysis", "Data Science", "Machine Learning"],
     "enabled": True},
    {"title": "Microsoft Generative Artificial Intelligence", "issuer": "ProWay", "date": "Sep 2024",
     "credential_id": None, "credential_url": None,
     "skills": ["Generative AI", "Artificial Intelligence", "Machine Learning"], "enabled": True},
    {"title": "UX (User Experience)", "issuer": "FIAP", "date": "Sep 2024", "credential_id": None,
     "credential_url": None, "skills": ["User Experience (UX)", "Web Design"], "enabled": True},
    {"title": "Entrepreneurship in Digital Social Media", "issuer": "IFF – Instituto Federal Fluminense",
     "date": "Oct 2020", "credential_id": None, "credential_url": None,
     "skills": ["Entrepreneurship", "Digital Marketing"], "enabled": True},
    {"title": "Microsoft Applied Skills: Build a generative AI chat app with the Microsoft Foundry SDK",
     "issuer": "Microsoft", "date": "Nov 2026", "credential_id": None, "credential_url": None,
     "skills": ["Microsoft Foundry", "Azure OpenAI", "Responses API", "Python", "Chat History"],
     "enabled": True, "badge": "Microsoft Applied Skills"},
]

MICROSOFT_LEARN = [
    {"title": "Develop an AI app with the Microsoft Foundry SDK", "issuer": "Microsoft Learn",
     "date": "Nov 2026", "duration": "55 min", "enabled": True},
    {"title": "Tooling, MCP, and Agent Execution Environments", "issuer": "Microsoft Learn",
     "date": "Nov 2026", "duration": "1 h 20 min", "enabled": True},
    {"title": "Designing Agent Architecture and SDLC Integration", "issuer": "Microsoft Learn",
     "date": "Nov 2026", "duration": "45 min", "enabled": True},
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STATUS_COLORS = {"In progress": "#D29922", "Completed": "#3fb950"}

STYLE = f"""  <style>
    .title {{ font: 600 16px {FONT}; fill: {ACCENT}; }}
    .heading {{ font: 600 15px {FONT}; fill: #ffffff; }}
    .text {{ font: 400 13px {FONT}; fill: #8b949e; }}
    .chip {{ font: 600 13px {FONT}; fill: #e6edf3; }}
    .pill {{ font: 600 11px {FONT}; }}
    .heading-learning {{ font: 600 15px {FONT}; fill: #D29922; }}
    .chip-learning {{ fill: #D29922; fill-opacity: 0.08; stroke: #D29922; stroke-opacity: 0.7; stroke-dasharray: 4 3; }}
  </style>"""


def wrap(text, width, max_lines=None):
    lines = []
    for word in text.split():
        if lines and len(lines[-1]) + 1 + len(word) <= width:
            lines[-1] += " " + word
        else:
            lines.append(word)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1].rstrip() + "…"
    return lines


def icon(name, x, y, color=ACCENT):
    return f'<path transform="translate({x} {y})" fill="{color}" d="{OCTICONS[name]}" />'


def frame(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f"{STYLE}\n"
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="#0d1117" stroke="#30363d" />\n'
        f"  {body}\n</svg>\n"
    )


def pill(text, right_x, y, color):
    width = 7 * len(text) + 18
    x = right_x - width
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="22" rx="11" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-opacity="0.6" />'
        f'<text x="{x + width / 2:.1f}" y="{y + 15}" text-anchor="middle" class="pill" fill="{color}">{escape(text)}</text>'
    )


def project_card(project):
    height = 150
    license_text = project["license"] or "All rights reserved"
    license_color = "#3fb950" if project["license"] else "#8b949e"
    parts = [
        icon("repo", 20, 22),
        f'<text x="44" y="35" class="title">{escape(project["name"])}</text>',
        pill(license_text, CARD_WIDTH - 18, 18, license_color),
    ]
    for i, line in enumerate(wrap(project["description"], 54, max_lines=3)):
        parts.append(f'<text x="20" y="{66 + i * 19}" class="text">{escape(line)}</text>')
    x = 20
    for label, color in project["stack"]:
        parts.append(f'<circle cx="{x + 6}" cy="{height - 24}" r="6" fill="{color}" />'
                     f'<text x="{x + 18}" y="{height - 20}" class="chip">{escape(label)}</text>')
        x += 18 + 7 * len(label) + 18
    return frame(CARD_WIDTH, height, "".join(parts))


def what_i_do_card():
    pad, gap, tile_h = 20, 16, 128
    tile_w = (FULL_WIDTH - 2 * pad - gap) / 2
    rows = (len(WHAT_I_DO) + 1) // 2
    parts = []
    for i, (title, icon_name, text) in enumerate(WHAT_I_DO):
        row, col = divmod(i, 2)
        tx = pad + col * (tile_w + gap)
        ty = pad + row * (tile_h + gap)
        width = FULL_WIDTH - 2 * pad if i == len(WHAT_I_DO) - 1 and len(WHAT_I_DO) % 2 else tile_w
        parts.append(
            f'<rect x="{tx:.0f}" y="{ty}" width="{width:.0f}" height="{tile_h}" rx="10" fill="#161b22" stroke="#30363d" />'
            + f'<circle cx="{tx + 32:.0f}" cy="{ty + 32}" r="16" fill="{ACCENT}" fill-opacity="0.12" />'
            + icon(icon_name, round(tx + 24), ty + 24)
            + f'<text x="{tx + 58:.0f}" y="{ty + 37}" class="heading">{escape(title)}</text>'
        )
        for j, line in enumerate(wrap(text, 56 if width == tile_w else 118, max_lines=4)):
            parts.append(f'<text x="{tx + 20:.0f}" y="{ty + 72 + j * 19}" class="text">{escape(line)}</text>')
    height = 2 * pad + rows * tile_h + (rows - 1) * gap
    return frame(FULL_WIDTH, height, "".join(parts))


def education_card():
    pad, row_h = 28, 72
    height = 2 * pad + len(EDUCATION) * row_h - 16
    line_x = pad + 16
    parts = [f'<line x1="{line_x}" y1="{pad + 16}" x2="{line_x}" y2="{height - pad - 24}" stroke="#30363d" stroke-width="2" />']
    for i, (program, school, period, status) in enumerate(EDUCATION):
        y = pad + i * row_h
        color = STATUS_COLORS[status]
        parts.append(
            f'<circle cx="{line_x}" cy="{y + 16}" r="16" fill="#161b22" stroke="{color}" />'
            + icon("mortar-board", line_x - 8, y + 8, color)
            + f'<text x="{line_x + 32}" y="{y + 14}" class="heading">{escape(program)}</text>'
            + f'<text x="{line_x + 32}" y="{y + 36}" class="text">{escape(school)} · {escape(period)}</text>'
            + pill(status, FULL_WIDTH - pad, y + 2, color)
        )
    return frame(FULL_WIDTH, height, "".join(parts))


def date_key(date):
    try:
        month, year = (date or "").split()
        return int(year), MONTHS.index(month) + 1
    except ValueError:
        return 0, 0


def enabled_sorted(entries):
    return sorted((e for e in entries if e.get("enabled")), key=lambda e: date_key(e.get("date")), reverse=True)


def accessible_frame(width, height, title, desc, body):
    svg = frame(width, height, body).replace("  </style>", f"    .tag {{ font: 500 11px {FONT}; fill: #8b949e; }}\n  </style>", 1)
    head, rest = svg.split("\n", 1)
    head = head.replace("<svg ", '<svg role="img" aria-labelledby="t d" ', 1)
    return f'{head}\n  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n{rest}'


def tags(labels, x, y):
    parts = []
    for label in labels:
        width = 6.3 * len(label) + 16
        parts.append(f'<rect x="{x:.0f}" y="{y}" width="{width:.0f}" height="20" rx="10" fill="#161b22" stroke="#30363d" />'
                     f'<text x="{x + width / 2:.0f}" y="{y + 14}" text-anchor="middle" class="tag">{escape(label)}</text>')
        x += width + 6
    return "".join(parts)


def timeline_rows(rows, pad=28, top=28):
    """rows: (icon, color, title_lines, meta, tags, pills). Same timeline look as the education card."""
    line_x = pad + 16
    parts, centers, y = [], [], top
    for icon_name, color, title_lines, meta, labels, pills in rows:
        centers.append(y + 16)
        parts.append(f'<circle cx="{line_x}" cy="{y + 16}" r="16" fill="#161b22" stroke="{color}" />'
                     + icon(icon_name, line_x - 8, y + 8, color))
        for i, line in enumerate(title_lines):
            parts.append(f'<text x="{line_x + 32}" y="{y + 14 + i * 20}" class="heading">{escape(line)}</text>')
        meta_y = y + 36 + (len(title_lines) - 1) * 20
        parts.append(f'<text x="{line_x + 32}" y="{meta_y}" class="text">{escape(meta)}</text>')
        for i, (text, pill_color) in enumerate(pills):
            parts.append(pill(text, FULL_WIDTH - pad, y + 2 + i * 28, pill_color))
        bottom = meta_y + 6
        if labels:
            parts.append(tags(labels, line_x + 32, bottom + 4))
            bottom += 24
        y = max(bottom, y + len(pills) * 28) + 24
    if len(centers) > 1:
        parts.insert(0, f'<line x1="{line_x}" y1="{centers[0]}" x2="{line_x}" y2="{centers[-1]}" stroke="#30363d" stroke-width="2" />')
    return "".join(parts), y - 24 + pad


def certifications_card(entries=None):
    entries = enabled_sorted(CERTIFICATIONS if entries is None else entries)
    rows = []
    for e in entries:
        credential = e.get("credential_id") and f"Credential ID {e['credential_id']}"
        meta = " · ".join(filter(None, [e["issuer"], credential]))
        pills = [(e["date"], ACCENT)] if e.get("date") else []
        if e.get("badge"):
            pills.append((e["badge"], "#a371f7"))
        color = "#a371f7" if e.get("badge") else "#3fb950"
        rows.append(("verified", color, wrap(e["title"], 72, max_lines=2), meta, e.get("skills", []), pills))
    body, height = timeline_rows(rows)
    desc = "; ".join(f"{e['title']}, {e['issuer']} ({e.get('date') or 'date pending'})" for e in entries)
    return accessible_frame(FULL_WIDTH, height, "Certifications", desc, body)


def microsoft_learn_card(entries=None):
    entries = enabled_sorted(MICROSOFT_LEARN if entries is None else entries)
    pad = 28
    header = (icon("book", pad + 8, pad - 2)
              + f'<text x="{pad + 32}" y="{pad + 11}" class="title">Completed modules</text>'
              + f'<text x="{FULL_WIDTH - pad}" y="{pad + 11}" text-anchor="end" class="text">Microsoft Learn training, not certifications</text>')
    rows = [("book", ACCENT, [e["title"]], f"{e['issuer']} · {e['date']} · {e['duration']}", [], [("Completed", "#3fb950")])
            for e in entries]
    body, height = timeline_rows(rows, pad, top=pad + 36)
    desc = "Completed Microsoft Learn modules: " + "; ".join(f"{e['title']} ({e['duration']}, {e['date']})" for e in entries)
    return accessible_frame(FULL_WIDTH, height, "Microsoft Learn: completed modules", desc, header + body)


def tech_chip(name, key, x, y, learning=False):
    size, color, path = TECH_ICONS[key]
    width = chip_width(name)
    box = 'class="chip-learning"' if learning else 'fill="#161b22" stroke="#30363d"'
    return (
        f'<rect x="{x:.0f}" y="{y}" width="{width:.0f}" height="34" rx="8" {box} />'
        f'<path transform="translate({x + 12:.0f} {y + 8}) scale({18 / size:.4f})" fill="{color}" d="{path}" />'
        f'<text x="{x + 38:.0f}" y="{y + 22}" class="chip">{escape(name)}</text>'
    )


def chip_width(name):
    return 38 + 7.4 * len(name) + 14


def tech_stack_card():
    pad, label_w, gap, row_gap = 20, 214, 10, 14
    chips_x = pad + label_w
    max_x = FULL_WIDTH - pad
    parts = []
    y = pad
    for i, (category, tools) in enumerate(TECH_STACK):
        if i:
            parts.append(f'<line x1="{pad}" y1="{y - row_gap / 2:.0f}" x2="{max_x}" y2="{y - row_gap / 2:.0f}" stroke="#21262d" />')
        x, line_y = chips_x, y
        for name, key in tools:
            if x + chip_width(name) > max_x:
                x, line_y = chips_x, line_y + 34 + gap
            parts.append(tech_chip(name, key, x, line_y, learning=category == LEARNING))
            x += chip_width(name) + gap
        row_bottom = line_y + 34
        heading = "heading-learning" if category == LEARNING else "heading"
        parts.append(f'<text x="{pad + 4}" y="{(y + row_bottom) / 2 + 5:.0f}" class="{heading}">{escape(category)}</text>')
        y = row_bottom + row_gap
    height = y - row_gap + pad
    return frame(FULL_WIDTH, height, "".join(parts))


def card_file(project):
    return f"assets/projects/{project['name'].lower()}.svg"


def write_all(root="."):
    files = {card_file(p): project_card(p) for p in PROJECTS}
    files["assets/what-i-do.svg"] = what_i_do_card()
    files["assets/education.svg"] = education_card()
    files["assets/tech-stack.svg"] = tech_stack_card()
    files["assets/certifications.svg"] = certifications_card()
    files["assets/microsoft-learn.svg"] = microsoft_learn_card()
    for rel, svg in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
    return list(files)


if __name__ == "__main__":
    for rel in write_all(os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]):
        print(rel)
