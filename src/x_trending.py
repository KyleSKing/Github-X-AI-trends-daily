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


def _get_twitter_env() -> dict[str, str]:
    """Extract TWITTER_AUTH_TOKEN and TWITTER_CT0 from bashrc."""
    result = subprocess.run(
        ["bash", "-c", "source ~/.bashrc 2>/dev/null; "
         'echo "AUTH=$TWITTER_AUTH_TOKEN"; echo "CT0=$TWITTER_CT0"'],
        capture_output=True, text=True, timeout=10
    )
    env = {}
    for line in result.stdout.strip().split("\n"):
        if line.startswith("AUTH="):
            env["TWITTER_AUTH_TOKEN"] = line[5:]
        elif line.startswith("CT0="):
            env["TWITTER_CT0"] = line[4:]
    if not env.get("TWITTER_AUTH_TOKEN") or not env.get("TWITTER_CT0"):
        print("ERROR: TWITTER_AUTH_TOKEN or TWITTER_CT0 not found in env", file=sys.stderr)
        sys.exit(1)
    return env


def search_twitter(query: str, since: str) -> list[dict]:
    tw_env = _get_twitter_env()
    cmd = [
        "twitter", "search", query,
        "--type", "top", "--lang", "en",
        "--min-likes", "50",
        "--since", since,
        "--exclude", "retweets",
        "--full-text", "--json",
        "-n", "20"
    ]
    merged_env = {**os.environ, **tw_env}
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90, env=merged_env)
    if result.returncode != 0:
        print(f"ERROR: twitter CLI failed: {result.stderr[:200]}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        if not data.get("ok"):
            print(f"ERROR: twitter auth failed: {data.get('error', {})}", file=sys.stderr)
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