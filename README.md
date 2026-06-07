# Daily AI Trends

自动化每日 AI 趋势报告，从 **GitHub** 和 **X/Twitter** 抓取 Top 10 热点。

## 数据源

| 来源 | 内容 | 排序 |
|------|------|------|
| GitHub 仓库 | 最热 AI 仓库 | Star 数降序 |
| GitHub 仓库 | 上升最快 AI 仓库 | 近 30 天活跃，按 Star |
| X/Twitter | AI/Tech 热门推文 | 互动量（likes+retweets+views） |

## 依赖

- [gh CLI](https://cli.github.com/) — 已认证（GitHub token）
- [twitter-cli](https://github.com/public-clis/twitter-cli) — `uv tool install twitter-cli`
- Python 3.10+
- 环境变量：`TWITTER_AUTH_TOKEN`、`TWITTER_CT0`

## 使用

```bash
# 直接运行
python3 main.py

# 或用封装脚本
bash run.sh
```

输出保存到 `output/trending-YYYY-MM-DD.md`。

## 定时任务

支持 Hermes cron / systemd timer / crontab：

```cron
0 8 * * * cd /path/to/ai-daily-trends && bash run.sh
```

## 项目结构

```
ai-daily-trends/
├── run.sh                  # 封装运行脚本
├── src/
│   ├── __init__.py
│   ├── main.py             # 入口
│   ├── github_trending.py  # GitHub 仓库抓取
│   └── x_trending.py       # X/Twitter 推文抓取
├── output/                 # 报告输出（gitignored）
├── .env.example            # 环境变量示例
└── requirements.txt        # 编译依赖（纯 stdlib）
```