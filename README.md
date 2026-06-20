# Daily AI Trends

自动化每日 AI 趋势报告，从 **GitHub** 和 **X/Twitter** 抓取 Top 10 热点。

## 数据源

| 来源 | 内容 | 排序 |
|------|------|------|
| GitHub 仓库 | 最热 AI 仓库 | Star 数降序 |
| GitHub 仓库 | 上升最快 AI 仓库 | 近 30 天活跃，按 Star 增长 |
| X/Twitter | AI/Tech 热门推文 | 互动量（likes+retweets+views） |

## 依赖

- [gh CLI](https://cli.github.com/) — 已认证（GitHub token）
- [twitter-cli](https://github.com/public-clis/twitter-cli) — `uv tool install twitter-cli`
- Python 3.10+

## 认证配置

### GitHub 认证

使用 `gh` CLI，token 存储在：

```
~/.config/gh/hosts.yml
```

**⚠️ 重要：** 如果环境变量 `GITHUB_TOKEN` 存在且无效，会覆盖 `gh` CLI 的本地认证导致 `HTTP 401`。
脚本已自动 `unset GITHUB_TOKEN` 解决此问题。

验证认证状态：
```bash
gh auth status
```

刷新/重新认证：
```bash
gh auth login
# 或刷新 scope
gh auth refresh -h github.com --scopes repo,workflow,read:org
```

### X/Twitter 认证

使用 `twitter-cli`，支持两种认证方式：

1. **环境变量**（推荐，适合无头/服务器环境）：
   ```bash
   export TWITTER_AUTH_TOKEN="your_auth_token"
   export TWITTER_CT0="your_ct0_value"
   ```
   - Token 存储在：`~/.hermes/profiles/coder/home/.bashrc`
   - 获取方式：浏览器登录 x.com → F12 → Application → Cookies → 复制 `auth_token` 和 `ct0`

2. **浏览器 Cookie 自动提取**（适合有浏览器的桌面环境）：
   `twitter-cli` 自动从 Chrome/Firefox 提取 cookie，无需手动配置。

验证认证状态：
```bash
twitter whoami
```

### Cron 环境注意事项

Hermes cron job 运行在独立环境中，**不会自动加载** `.bashrc`。脚本通过以下方式注入凭证：

```bash
source /root/.bashrc 2>/dev/null || true
source /root/.hermes/profiles/coder/home/.bashrc 2>/dev/null || true
unset GITHUB_TOKEN 2>/dev/null || true  # 清除可能冲突的无效 token
```

**⚠️ 不要用 `||` 链式 source**，因为第一个文件存在（即使为空）会导致短路，跳过后面的文件。

## 使用

```bash
# 直接运行
python3 -m src.main

# 或用 Hermes cron 脚本
bash /root/.hermes/profiles/coder/scripts/github_x_daily_no_agent.sh
```

输出保存到 `output/trending-YYYY-MM-DD.md`。

## 定时任务

通过 Hermes cron 运行，每天 08:00 BJT：

```bash
# 查看 job 状态
hermes --profile coder cron list

# 手动触发
hermes --profile coder cron run 666beb6ff8f4
```

Job 配置：
- Job ID: `666beb6ff8f4`
- 脚本: `~/.hermes/profiles/coder/scripts/github_x_daily_no_agent.sh`
- 模式: `no_agent`（直接执行脚本，不经过 LLM）

## 项目结构

```
Github-X-AI-trends-daily/
├── src/
│   ├── __init__.py
│   ├── main.py             # 入口
│   ├── github_trending.py  # GitHub 仓库抓取
│   └── x_trending.py       # X/Twitter 推文抓取（使用 twitter CLI）
├── output/                 # 报告输出（gitignored）
├── .env.example            # 环境变量示例
└── README.md
```

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| GitHub `HTTP 401` | `GITHUB_TOKEN` 环境变量覆盖了 `gh` 本地认证 | `unset GITHUB_TOKEN` 或更新 token |
| X 部分 `获取失败或为空` | `TWITTER_AUTH_TOKEN`/`TWITTER_CT0` 未加载到 cron 环境 | 检查 bashrc source 链，确保 token 文件被加载 |
| `twitter CLI failed: cookie extraction failed` | 无头环境无法从浏览器提取 cookie | 设置环境变量 `TWITTER_AUTH_TOKEN` + `TWITTER_CT0` |
| 脚本 exit code 1 | 某个数据源完全失败 | 已改为优雅降级，部分失败不阻断整体 |
