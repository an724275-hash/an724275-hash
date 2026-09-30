"""Build local SVG profile cards from public GitHub repository metadata."""

from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


USERNAME = "an724275-hash"
BASE = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
COLORS = ("#f5c542", "#77c6b3", "#8eb6e8", "#d7a2d8", "#e7a77e", "#84929c")


def fetch_json(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-profile-stats"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(f"{BASE}{path}", headers=headers), timeout=20) as response:
        return json.load(response)


def public_repos():
    repos = []
    for page in range(1, 11):
        batch = fetch_json(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        if not isinstance(batch, list):
            raise ValueError("GitHub returned an unexpected repository list")
        repos.extend(batch)
        if len(batch) < 100:
            break
    return [repo for repo in repos if not repo.get("fork") and not repo.get("archived")
            and not repo.get("private") and repo.get("name") != USERNAME]


def aggregate(repos, language_loader):
    languages = Counter()
    stars = 0
    for repo in repos:
        stars += repo.get("stargazers_count", 0)
        for language, size in language_loader(repo).items():
            if isinstance(size, int) and size > 0:
                languages[language] += size
    return {"repositories": len(repos), "stars": stars, "languages": languages}


def start_svg(title, subtitle):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="430" height="220" viewBox="0 0 430 220" role="img">',
        '<rect x="1" y="1" width="428" height="218" rx="12" fill="#151b23" stroke="#38424a"/>',
        f'<text x="24" y="42" fill="#f3f4f6" font-family="Arial,sans-serif" font-size="19" font-weight="700">{escape(title)}</text>',
        f'<text x="24" y="64" fill="#b7c2cc" font-family="Arial,sans-serif" font-size="11">{escape(subtitle)}</text>',
    ]


def finish_svg(parts):
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def languages_svg(stats, date):
    parts = start_svg("Языки в репозиториях", f"GitHub API · {date} · объём кода")
    total = sum(stats["languages"].values())
    if not total:
        parts.append('<text x="24" y="115" fill="#b7c2cc" font-family="Arial,sans-serif" font-size="14">Пока нет данных о языках.</text>')
        return finish_svg(parts)
    top = stats["languages"].most_common(5)
    rest = total - sum(size for _, size in top)
    if rest:
        top.append(("Другое", rest))
    x = 24.0
    for index, (_, size) in enumerate(top):
        width = 382 * size / total
        parts.append(f'<rect x="{x:.2f}" y="84" width="{width:.2f}" height="13" fill="{COLORS[index]}"/>')
        x += width
    for index, (name, size) in enumerate(top):
        column = index % 2
        row = index // 2
        x = 24 + column * 194
        y = 122 + row * 27
        label = f"{name[:18]} {size / total * 100:.1f}%"
        parts.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{COLORS[index]}"/>')
        parts.append(f'<text x="{x + 18}" y="{y}" fill="#e3e8ed" font-family="Arial,sans-serif" font-size="12">{escape(label)}</text>')
    return finish_svg(parts)


def overview_svg(stats, date):
    parts = start_svg("Публичный код", f"GitHub API · {date} · без форков и архивов")
    values = [
        (stats["repositories"], "репозиториев"),
        (stats["stars"], "звёзд на проектах"),
        (len(stats["languages"]), "языков в коде"),
    ]
    for index, (value, caption) in enumerate(values):
        x = 24 + index * 132
        parts.append(f'<text x="{x}" y="133" fill="#f5c542" font-family="Arial,sans-serif" font-size="36" font-weight="700">{value}</text>')
        parts.append(f'<text x="{x}" y="158" fill="#dce3e8" font-family="Arial,sans-serif" font-size="12">{escape(caption)}</text>')
    parts.append('<text x="24" y="194" fill="#b7c2cc" font-family="Arial,sans-serif" font-size="11">Исходные данные: публичные репозитории профиля</text>')
    return finish_svg(parts)


def main():
    repos = public_repos()
    stats = aggregate(repos, lambda repo: fetch_json(f"/repos/{USERNAME}/{repo['name']}/languages"))
    date = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "languages.svg").write_text(languages_svg(stats, date), encoding="utf-8")
    (ASSETS / "overview.svg").write_text(overview_svg(stats, date), encoding="utf-8")
    print(f"Updated cards from {stats['repositories']} public repositories")


if __name__ == "__main__":
    main()
