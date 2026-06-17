#!/usr/bin/env python3
"""Fetch GitHub AI trends.

Hottest is sorted by total stars. Rising is sorted by local star growth
between scheduled runs, with a no-LLM candidate pool focused on AI tools,
agents, IDE/plugin projects, courses, books, and learning repositories.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
STAR_HISTORY_PATH = DATA_DIR / "github-star-history.json"
MIN_RISING_STARS = 100

GH_FIELDS = (
    "fullName,name,owner,url,description,stargazersCount,forksCount,"
    "updatedAt,createdAt,language,isFork,isArchived"
)

RISING_QUERIES = [
    # Keep this list compact: GitHub search has strict rate limits.
    # These buckets cover tools/agents/IDEs/plugins plus courses/books/resources.
    "AI agent",
    "LLM tool",
    "AI IDE",
    "AI coding assistant",
    "vscode AI",
    "MCP server",
    "AI skill",
    "AI course",
    "LLM course",
    "AI book",
    "machine learning course",
    "awesome AI",
]

POSITIVE_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "large language model", "agent",
    "mcp", "ide", "vscode", "cursor", "plugin", "extension", "skill",
    "tool", "toolkit", "workflow", "coding", "developer", "code", "prompt",
    "course", "book", "tutorial", "awesome", "roadmap", "learning",
    "machine learning", "deep learning", "rag", "copilot", "assistant",
]

NEGATIVE_KEYWORDS = [
    "crypto", "blockchain", "airdrop", "nft", "casino", "betting", "porn",
    "onlyfans", "job board", "hiring", "resume", "interview questions only",
]

TYPE_RULES = [
    ("MCP", ["mcp", "model context protocol"]),
    ("IDE", ["ide", "cursor", "neovim", "nvim", "vscode", "jetbrains"]),
    ("Plugin", ["plugin", "extension", "addon"]),
    ("Skill", ["skill", "skills"]),
    ("Agent", ["agent", "agents", "copilot", "assistant"]),
    ("Course", ["course", "courses", "curriculum", "bootcamp"]),
    ("Book", ["book", "books", "handbook"]),
    ("Tutorial", ["tutorial", "guide", "learn", "learning"]),
    ("Awesome", ["awesome", "curated"]),
    ("Roadmap", ["roadmap"]),
    ("Tool", ["tool", "toolkit", "workflow", "prompt", "rag", "llm", "ai"]),
]


def repo_text(repo: dict) -> str:
    return " ".join([
        str(repo.get("fullName") or ""),
        str(repo.get("name") or ""),
        str(repo.get("description") or ""),
        str(repo.get("language") or ""),
    ]).lower()


def run_gh(args: list[str], limit_seconds: int = 60) -> list[dict]:
    cmd = ["gh", "search", "repos"] + args + ["--json", GH_FIELDS]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=limit_seconds)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "rate limit" in stderr.lower():
            # Stop the caller early; repeated search calls worsen secondary limits.
            raise RuntimeError(stderr)
        print(f"gh CLI error for {' '.join(args)}: {stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"gh CLI JSON error: {exc}", file=sys.stderr)
        return []


def hottest_top10() -> list[dict]:
    """AI repos sorted by total stars."""
    return run_gh(["AI", "--sort", "stars", "--limit", "10"])


def load_star_history() -> dict:
    if not STAR_HISTORY_PATH.exists():
        return {}
    try:
        with STAR_HISTORY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_star_history(repos: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    history = load_star_history()
    for repo in repos:
        key = repo_key(repo)
        if not key:
            continue
        history[key] = {
            "stars": int(repo.get("stargazersCount") or 0),
            "seen_at": now,
            "url": repo.get("url"),
            "description": repo.get("description"),
        }
    tmp = STAR_HISTORY_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(STAR_HISTORY_PATH)


def repo_key(repo: dict) -> str:
    full_name = repo.get("fullName")
    if full_name:
        return str(full_name)
    owner = (repo.get("owner") or {}).get("login")
    name = repo.get("name")
    return f"{owner}/{name}" if owner and name else ""


def is_relevant_repo(repo: dict) -> bool:
    if repo.get("isFork") or repo.get("isArchived"):
        return False
    if int(repo.get("stargazersCount") or 0) < MIN_RISING_STARS:
        return False
    text = repo_text(repo)
    if any(k in text for k in NEGATIVE_KEYWORDS):
        return False
    return any(k in text for k in POSITIVE_KEYWORDS)


def collect_rising_candidates() -> list[dict]:
    """Collect a deterministic no-LLM candidate pool.

    We keep calls modest to avoid GitHub secondary rate limits. Star-heavy
    searches catch popular projects in each category; local star deltas decide
    the final ranking.
    """
    by_name: dict[str, dict] = {}
    for query in RISING_QUERIES:
        repos = run_gh([query, "--sort", "stars", "--limit", "15"])
        for repo in repos:
            key = repo_key(repo)
            if key and is_relevant_repo(repo):
                by_name[key] = repo
    return list(by_name.values())


def rising_top10() -> list[dict]:
    """AI projects sorted by star growth since the previous local snapshot."""
    history = load_star_history()
    candidates = collect_rising_candidates()

    for repo in candidates:
        key = repo_key(repo)
        current_stars = int(repo.get("stargazersCount") or 0)
        old_stars = history.get(key, {}).get("stars") if key else None
        if isinstance(old_stars, int):
            repo["starDelta"] = max(0, current_stars - old_stars)
            repo["previousStars"] = old_stars
        else:
            repo["starDelta"] = None
            repo["previousStars"] = None
        repo["repoType"] = classify_repo(repo)

    save_star_history(candidates)

    with_delta = [r for r in candidates if r.get("starDelta") is not None]
    if with_delta:
        with_delta.sort(
            key=lambda r: (
                int(r.get("starDelta") or 0),
                int(r.get("stargazersCount") or 0),
            ),
            reverse=True,
        )
        return with_delta[:10]

    # First run: establish baseline, then show a high-signal fallback list.
    candidates.sort(
        key=lambda r: (int(r.get("stargazersCount") or 0), str(r.get("updatedAt") or "")),
        reverse=True,
    )
    return candidates[:10]


def classify_repo(repo: dict) -> str:
    text = repo_text(repo)
    for label, keywords in TYPE_RULES:
        if any(k in text for k in keywords):
            return label
    return "Project"


def format_repo(r: dict) -> str:
    forks = int(r.get("forksCount") or 0)
    return (
        f"**#{int(r['stargazersCount']):,} ⭐ | {forks:,} 🍴 | @{r['owner']['login']}/{r['name']}**\n"
        f"> {(r.get('description') or '无描述')[:120]}\n"
        f"🔗 {r['url']}\n"
        f"📅 {r['updatedAt'][:10]}"
    )


def format_rising_repo(r: dict) -> str:
    delta = r.get("starDelta")
    delta_text = "baseline" if delta is None else f"+{int(delta):,} ⭐ / 24h"
    repo_type = r.get("repoType") or classify_repo(r)
    return (
        f"**{delta_text} | {int(r['stargazersCount']):,} ⭐ | [{repo_type}] @{r['owner']['login']}/{r['name']}**\n"
        f"> {(r.get('description') or '无描述')[:120]}\n"
        f"🔗 {r['url']}\n"
        f"📅 {r['updatedAt'][:10]}"
    )
