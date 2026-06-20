#!/usr/bin/env python3
"""Fetch X/Twitter trending AI/tech posts — top 10 by engagement in the last 24h."""

import json
import os
import subprocess
import sys
from datetime import datetime


SEARCH_QUERY = (
    '"AI" OR "artificial intelligence" OR "LLM" OR "AGI" '
    'OR "machine learning" OR "tech" OR "robotics" OR "model"'
)


def search_twitter(query: str, since: str) -> list[dict]:
    """Search X/Twitter using system-authenticated twitter CLI (no env vars needed)."""
    cmd = [
        "twitter", "search", query,
        "--type", "top", "--lang", "en",
        "--min-likes", "50",
        "--since", since,
        "--exclude", "retweets",
        "--full-text", "--json",
        "-n", "20"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if result.returncode != 0:
        print(f"ERROR: twitter CLI failed: {result.stderr[:200]}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        if not data.get("ok"):
            print(f"ERROR: twitter search failed: {data.get('error', {})}", file=sys.stderr)
            return []
        return data.get("data", [])
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse: {e}", file=sys.stderr)
        print(f"Raw: {result.stdout[:300]}", file=sys.stderr)
        return []


def fetch_top10(since: str) -> list[dict]:
    """Fetch top 10 AI/tech tweets by engagement."""
    tweets = search_twitter(SEARCH_QUERY, since)
    filtered = []
    for t in tweets:
        m = t.get("metrics", {})
        eng = m.get("likes", 0) + m.get("retweets", 0) + m.get("views", 0)
        text = t.get("text", "")
        if eng > 200 and len(text) > 80:
            t["_engagement"] = eng
            filtered.append(t)
    filtered.sort(key=lambda x: x["_engagement"], reverse=True)
    return filtered[:10]


def format_tweet(t: dict) -> str:
    a = t["author"]
    m = t["metrics"]
    text = t["text"][:120].replace("\n", " ")
    tweet_id = t["id"]
    screen_name = a["screenName"]
    link = f"https://x.com/{screen_name}/status/{tweet_id}"
    return (
        f"🔥 **{m['likes']:,} 👍 | {m.get('retweets', 0):,} 🔄 | {m.get('views', 0):,} 👁 | @{screen_name}**\n"
        f"> {text}\n"
        f"🔗 {link}\n"
        f"📅 {t.get('createdAtLocal', t.get('createdAt', '')[:10])}"
    )