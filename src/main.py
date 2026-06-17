#!/usr/bin/env python3
"""Main runner: GitHub hottest + rising AI repos, X AI/tech trending top 10."""

import subprocess
import sys
import os
from datetime import datetime, timezone, timedelta
from src import github_trending
from src import x_trending


def header(text: str) -> str:
    return f"\n━━━ {text} ━━━"


def main():
    tz = timezone(timedelta(hours=8))  # Beijing time
    today = datetime.now(tz).strftime("%Y-%m-%d")
    since = datetime.now(tz).strftime("%Y-%m-%d")

    lines = [f"📆 **每日 AI 趋势报告 — {today}**\n"]

    # ── GitHub Hottest ──
    lines.append(header("GitHub 最热 AI 仓库 Top 10"))
    hottest = github_trending.hottest_top10()
    if hottest:
        for i, r in enumerate(hottest, 1):
            lines.append(f"\n**{i}.** {github_trending.format_repo(r)}")
    else:
        lines.append("\n⚠️ 获取失败或为空")

    # ── GitHub Rising ──
    lines.append(header("GitHub AI 项目增长最快 Top 10"))
    rising = github_trending.rising_top10()
    if rising:
        for i, r in enumerate(rising, 1):
            lines.append(f"\n**{i}.** {github_trending.format_rising_repo(r)}")
    else:
        lines.append("\n⚠️ 获取失败或为空")

    # ── X Trending ──
    lines.append(header("X AI/Tech Trending Top 10"))
    tweets = x_trending.fetch_top10(since)
    if tweets:
        for i, t in enumerate(tweets, 1):
            lines.append(f"\n**{i}.** {x_trending.format_tweet(t)}")
    else:
        lines.append("\n⚠️ 获取失败或为空")

    lines.append(f"\n\n---\n🤖 _自动生成 · 每天 08:00 BJT_")

    report = "\n".join(lines)
    print(report, flush=True)

    # Write to file too
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"trending-{today}.md")
    with open(path, "w") as f:
        f.write(report)
    print(f"\n📝 已保存: {path}")


if __name__ == "__main__":
    main()