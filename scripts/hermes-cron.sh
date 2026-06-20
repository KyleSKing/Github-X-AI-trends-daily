#!/usr/bin/env bash
# ============================================================
# Hermes Cron Script: github-x-daily-report-no-llm
# Job ID: 666beb6ff8f4
# Schedule: 0 8 * * * (每天 08:00 BJT)
# Mode: no_agent (直接执行脚本，不经过 LLM)
# ============================================================
# 部署位置: ~/.hermes/profiles/coder/scripts/github_x_daily_no_agent.sh
# 项目仓库: https://github.com/KyleSKing/Github-X-AI-trends-daily
# ============================================================
set -euo pipefail

PROJECT="/root/projects/Github-X-AI-trends-daily"
TZ_NAME="Asia/Shanghai"
export PATH="/root/.hermes/profiles/coder/home/.local/bin:/root/.hermes/profiles/coder/home/.local/share/pnpm:/usr/local/lib/hermes-agent/venv/bin:/usr/local/lib/hermes-agent/node_modules/.bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:${PATH:-}"
TODAY="$(TZ="$TZ_NAME" date +%F)"
REPORT="$PROJECT/output/trending-$TODAY.md"

cd "$PROJECT"

# ============================================================
# 认证注入（cron 环境不会自动加载 .bashrc）
# ============================================================
# ⚠️ 不要用 || 链式 source — 第一个文件存在会短路后续文件
# TWITTER_AUTH_TOKEN / TWITTER_CT0 在 ~/.hermes/profiles/coder/home/.bashrc
# gh CLI token 在 ~/.config/gh/hosts.yml（gh auth 自动读取）
# 清除 GITHUB_TOKEN 环境变量避免覆盖 gh CLI 本地认证
set +u
source /root/.bashrc 2>/dev/null || true
source /root/.hermes/profiles/coder/home/.bashrc 2>/dev/null || true
unset GITHUB_TOKEN 2>/dev/null || true
set -u

# Dependency/auth checks go to stderr so cron no_agent delivers only the report on stdout.
echo "🔍 Checking gh CLI..." >&2
gh auth status >/dev/null

# Check Twitter only if credentials exist; don't fail the whole job if just generating report
if [[ -n "${TWITTER_AUTH_TOKEN:-}" ]] || [[ -n "${TWITTER_CT0:-}" ]]; then
  echo "🔍 Checking twitter CLI... (optional, for posting to X)" >&2
  TW_STATUS="$(twitter whoami 2>&1 || true)"
  if ! grep -q "ok: true" <<<"$TW_STATUS"; then
    echo "⚠️ twitter CLI not fully authenticated, will skip posting to X but continue generating report" >&2
  fi
else
  echo "⚠️ Twitter credentials not found (TWITTER_AUTH_TOKEN/TWITTER_CT0), will skip posting to X but continue generating report" >&2
fi

echo "🚀 Generating Github-X report for $TODAY...">&2
python3 -m src.main >&2

if [[ ! -f "$REPORT" ]]; then
  REPORT="$(ls -1t "$PROJECT"/output/trending-*.md 2>/dev/null | head -1 || true)"
fi

if [[ -z "${REPORT:-}" || ! -f "$REPORT" ]]; then
  echo "❌ No report file found" >&2
  exit 1
fi

cat "$REPORT"
