#!/usr/bin/env python3
"""Generates assets/stats.svg from live public GitHub data (no API token required
for public data, but GITHUB_TOKEN is used when available to raise the rate limit)."""
import json
import os
import urllib.request
from datetime import datetime, timezone

USERNAME = "zexuguo"
API = "https://api.github.com"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKEN = os.environ.get("GITHUB_TOKEN", "")


def fetch(path):
    req = urllib.request.Request(f"{API}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "zexuguo-profile-stats")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    user = fetch(f"/users/{USERNAME}")
    repos = fetch(f"/users/{USERNAME}/repos?per_page=100&type=owner")

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    lang_bytes = {}
    for r in repos:
        try:
            langs = fetch(f"/repos/{USERNAME}/{r['name']}/languages")
        except Exception:
            langs = {}
        for lang, n in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + n

    top_langs = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:5]
    total_lang_bytes = sum(n for _, n in top_langs) or 1

    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    days_active = (datetime.now(timezone.utc) - created).days

    stats = [
        ("REPOSITORIOS", user.get("public_repos", 0)),
        ("ESTRELLAS", total_stars),
        ("FORKS", total_forks),
        ("SEGUIDORES", user.get("followers", 0)),
        ("DIAS_ACTIVO", days_active),
    ]

    font_path = os.path.join(HERE, "assets", "_font.b64")
    with open(font_path) as f:
        font_b64 = f.read().strip()

    W, H = 800, 230
    PAD = 26
    svg = []
    svg.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">')
    svg.append(f'''<defs><style>
      @font-face {{ font-family:"STMono"; src:url(data:font/ttf;base64,{font_b64}) format("truetype"); }}
    </style></defs>''')
    svg.append(f'''<style>
      .card {{ fill:#000000; stroke:rgba(255,255,255,0.16); stroke-width:1; }}
      .label {{ fill:rgba(255,255,255,0.55); font:11px "STMono",monospace; letter-spacing:2px; }}
      .rule {{ stroke:rgba(255,255,255,0.14); stroke-width:1; }}
      .stat-k {{ fill:rgba(255,255,255,0.55); font:11px "STMono",monospace; letter-spacing:1.5px; }}
      .stat-v {{ fill:#ffffff; font:26px "STMono",monospace; }}
      .bar-bg {{ fill:rgba(255,255,255,0.12); }}
      .bar-fg {{ fill:#ffffff; }}
      .lang {{ fill:#ffffff; font:12px "STMono",monospace; }}
      .pct {{ fill:rgba(255,255,255,0.5); font:11px "STMono",monospace; }}
      .cursor {{ animation: blink 1.1s steps(2, jump-none) infinite; fill:#ffffff; }}
      @keyframes blink {{ 50% {{ opacity:0; }} }}
    </style>''')
    svg.append(f'<rect class="card" x="1" y="1" width="{W-2}" height="{H-2}" rx="10"/>')
    svg.append(f'<text class="label" x="{PAD}" y="{PAD-4}">ZG // LIVE_STATS</text>')
    svg.append(f'<line class="rule" x1="{PAD}" y1="30" x2="{W-PAD}" y2="30"/>')

    col_w = (W - PAD * 2) / len(stats)
    for i, (k, v) in enumerate(stats):
        x = PAD + i * col_w
        svg.append(f'<text class="stat-k" x="{x:.1f}" y="58">{k}</text>')
        svg.append(f'<text class="stat-v" x="{x:.1f}" y="88">{v}</text>')

    svg.append(f'<line class="rule" x1="{PAD}" y1="112" x2="{W-PAD}" y2="112"/>')
    svg.append(f'<text class="label" x="{PAD}" y="132">TOP_LANGUAGES</text>')

    bar_x = PAD
    bar_y0 = 146
    bar_w = W - PAD * 2
    bar_h = 10
    row_h = 26
    for i, (lang, n) in enumerate(top_langs):
        pct = n / total_lang_bytes * 100
        y = bar_y0 + i * row_h
        svg.append(f'<text class="lang" x="{bar_x}" y="{y-2:.1f}">{lang}</text>')
        svg.append(f'<text class="pct" x="{bar_x+bar_w:.1f}" y="{y-2:.1f}" text-anchor="end">{pct:.1f}%</text>')
        svg.append(f'<rect class="bar-bg" x="{bar_x}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h}" rx="2"/>')
        fw = max(3, bar_w * pct / 100)
        svg.append(f'<rect class="bar-fg" x="{bar_x}" y="{y:.1f}" width="{fw:.1f}" height="{bar_h}" rx="2"/>')

    if not top_langs:
        svg.append(f'<text class="lang" x="{bar_x}" y="{bar_y0+10}">sin datos suficientes todavia</text>')

    svg.append(f'<rect class="cursor" x="{PAD+2}" y="{H-18}" width="6" height="10"/>')
    svg.append("</svg>")

    out_path = os.path.join(HERE, "assets", "stats.svg")
    with open(out_path, "w") as f:
        f.write("\n".join(svg))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
