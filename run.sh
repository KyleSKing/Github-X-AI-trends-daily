#!/usr/bin/env bash
set -euo pipefail

# Daily AI Trends — runner script
# Requires: gh CLI, twitter-cli (uv tool), Python 3.10+
# Env vars: TWITTER_AUTH_TOKEN, TWITTER_CT0 (loaded from ~/.bashrc)

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=== Daily AI Trends ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo

# Load Twitter credentials
source ~/.bashrc 2>/dev/null || true

# Verify dependencies
echo "🔍 Checking gh CLI..."
gh auth status 2>&1 | head -2 || { echo "❌ gh CLI not authenticated"; exit 1; }

echo "🔍 Checking twitter CLI..."
twitter whoami 2>&1 | grep -q "ok: true" || { echo "❌ twitter CLI not authenticated"; exit 1; }

echo "🚀 Fetching trends..."
python3 src/main.py