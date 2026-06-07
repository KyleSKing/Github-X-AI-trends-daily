#!/usr/bin/env python3
"""Fetch GitHub trending AI repos: hottest (by stars) and fastest-rising (recently active)."""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta


def run_gh(args: list[str]) -> list[dict]:
    cmd = ["gh", "search", "repos"] + args + [
        "--json", "name,owner,url,description,stargazersCount,forkCount,updatedAt,createdAt,primaryLanguage"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"gh CLI error: {result.stderr}", file=sys.stderr)
        return []
    return json.loads(result.stdout)


def hottest_top10() -> list[dict]:
    """AI repos sorted by stars."""
    repos = run_gh([
        "AI OR artificial-intelligence OR machine-learning OR deep-learning OR LLM OR large-language-model",
        "--sort", "stars",
        "--limit", "10"
    ])
    return repos


def rising_top10() -> list[dict]:
    """Recently active AI repos with high stars."""
    repos = run_gh([
        "AI OR artificial-intelligence OR machine-learning OR deep-learning OR LLM",
        "--sort", "updated",
        "--limit", "30"
    ])
    # Filter repos updated or created in the last 30 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    filtered = []
    for r in repos:
        updated = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
        created = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
        if updated >= cutoff or created >= cutoff:
            filtered.append(r)
    # Sort by stars descending
    filtered.sort(key=lambda x: x["stargazersCount"], reverse=True)
    return filtered[:10]


def format_repo(r: dict) -> str:
    lang = r.get("primaryLanguage") or ""
    return (
        f"**#{r['stargazersCount']:,} ⭐ | {r['forkCount']:,} 🍴 | @{r['owner']['login']}/{r['name']}**\n"
        f"> {(r['description'] or '无描述')[:120]}\n"
        f"🔗 {r['url']}\n"
        f"📅 {r['updatedAt'][:10]}"
    )