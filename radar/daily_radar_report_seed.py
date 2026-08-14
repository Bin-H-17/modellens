#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型筛 · 每日最佳模型配置报告生成器 (PoC)
================================================
读取模型数据集（默认内嵌种子数据，可替换为实时抓取），
按任务域与三档（性价比日常 / 最优质 / 最划算小批量）产出可解释的配置建议报告。

用法:
    python daily_radar_report.py                      # 输出 markdown 到 stdout
    python daily_radar_report.py --html out.html       # 生成 HTML 文件
    python daily_radar_report.py --md out.md           # 生成 Markdown 文件
    python daily_radar_report.py --json models.json    # 用外部数据集

说明:
    - 这是 v0「每日雷达报告」的可运行雏形（只读、零网关、零风险）。
    - 种子数据来自研究硬数据(tokencost/benchlm/OpenRouter×a16z) + Artificial Analysis 实时信号，
      部分价格为估算，接入实时抓取后自动校正。
    - v1 在用户授权 API 后可把推荐「一键应用」到网关 policy / Dify·Coze 插件（可选接管）。
"""

import argparse
import json
import datetime
import html
import os

# ---- 种子数据集（标注来源/置信）----
SEED_MODELS = [
    {
        "id": "gpt-5", "name": "GPT-5", "provider": "OpenAI", "quality": 88,
        "price_in": 5.0, "price_out": 20.0, "context": 400000, "speed": 1.0,
        "tasks": {"coding": 85, "reasoning": 90, "translation": 82, "summarization": 84, "longctx": 80},
        "conf": "hard(数析报告)"
    },
    {
        "id": "claude-opus-5", "name": "Claude Opus 5", "provider": "Anthropic", "quality": 92,
        "price_in": 15.0, "price_out": 75.0, "context": 400000, "speed": 0.9,
        "tasks": {"coding": 90, "reasoning": 91, "translation": 93, "summarization": 92, "longctx": 82},
        "conf": "est(AA: agentic leader)"
    },
    {
        "id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "Google", "quality": 87,
        "price_in": 1.25, "price_out": 10.0, "context": 1000000, "speed": 1.1,
        "tasks": {"coding": 84, "reasoning": 86, "translation": 88, "summarization": 87, "longctx": 95},
        "conf": "hard(数析报告)"
    },
    {
        "id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "provider": "DeepSeek", "quality": 50,
        "price_in": 0.12, "price_out": 0.40, "context": 256000, "speed": 1.6,
        "tasks": {"coding": 55, "reasoning": 52, "translation": 58, "summarization": 60, "longctx": 55},
        "conf": "hard(AA index=50)"
    },
    {
        "id": "deepseek-r1", "name": "DeepSeek R1", "provider": "DeepSeek", "quality": 80,
        "price_in": 0.55, "price_out": 2.19, "context": 256000, "speed": 0.8,
        "tasks": {"coding": 82, "reasoning": 88, "translation": 70, "summarization": 76, "longctx": 70},
        "conf": "hard(数析报告)"
    },
    {
        "id": "qwen3.8-max", "name": "Qwen3.8 Max", "provider": "Alibaba", "quality": 85,
        "price_in": 0.80, "price_out": 2.50, "context": 256000, "speed": 1.2,
        "tasks": {"coding": 83, "reasoning": 84, "translation": 90, "summarization": 86, "longctx": 75},
        "conf": "est(AA 新评测)"
    },
    {
        "id": "llama-4", "name": "Llama 4", "provider": "Meta", "quality": 78,
        "price_in": 0.10, "price_out": 0.30, "context": 10000000, "speed": 1.3,
        "tasks": {"coding": 74, "reasoning": 72, "translation": 80, "summarization": 82, "longctx": 90},
        "conf": "hard(数析:10M ctx)"
    },
    {
        "id": "mistral-large", "name": "Mistral Large", "provider": "Mistral", "quality": 80,
        "price_in": 2.0, "price_out": 6.0, "context": 256000, "speed": 1.0,
        "tasks": {"coding": 78, "reasoning": 79, "translation": 82, "summarization": 80, "longctx": 70},
        "conf": "est"
    },
]

TASKS = ["coding", "reasoning", "translation", "summarization", "longctx"]
TASK_CN = {"coding": "编码", "reasoning": "推理", "translation": "翻译", "summarization": "摘要", "longctx": "长文本"}


def value_score(m):
    """性价比指数 = 质量 / 有效输出成本（输出价近似）"""
    return m["quality"] / max(m["price_out"], 0.01)


def daily_economy_score(m):
    """日常性价比档：质量>=75 才有资格参与"""
    return value_score(m) if m["quality"] >= 75 else -1


def premium_score(m):
    return m["quality"]


def batch_score(m):
    """最划算小/批量：质量>=60 时取最低输出价"""
    return m["price_out"] if m["quality"] >= 60 else 1e9


def pick(models, scorer, reverse=True):
    best = None
    bs = None
    for m in models:
        s = scorer(m)
        if bs is None or (s > bs if reverse else s < bs):
            bs = s
            best = m
    return best


def explain(m, tier):
    if tier == "economy":
        return f"性价比指数 {value_score(m):.1f}（质量 {m['quality']} / 输出价 ${m['price_out']}/M），兼顾质量与成本的最佳平衡。"
    if tier == "premium":
        return f"质量分 {m['quality']} 全池最高，输出价 ${m['price_out']}/M，不计成本优先质量。"
    if tier == "batch":
        return f"输出价仅 ${m['price_out']}/M，质量 {m['quality']} 足以覆盖小/批量任务，批量最划算。"
    return ""


def compute(models, date):
    return {
        "date": date,
        "count": len(models),
        "economy": pick(models, daily_economy_score),
        "premium": pick(models, premium_score),
        "batch": pick(models, batch_score, reverse=False),
        "tasks": {t: max(models, key=lambda m: (m["tasks"][t], value_score(m))) for t in TASKS},
    }


def render_md(r):
    m, p, b = r["economy"], r["premium"], r["batch"]
    L = []
    L.append("# 📡 模型筛 · 每日最佳配置报告")
    L.append(f"> 日期：{r['date']} ｜ 监控模型：{r['count']} ｜ 形态：情报层（只读建议；授权 API 后可一键应用）")
    L.append("")
    L.append("## 一、三档总推荐")
    L.append(f"- **日常性价比（每天主力）**：`{m['name']}`（{m['provider']}）— {explain(m, 'economy')}")
    L.append(f"- **最优质（只看质量）**：`{p['name']}`（{p['provider']}）— {explain(p, 'premium')}")
    L.append(f"- **最划算小/批量**：`{b['name']}`（{b['provider']}）— {explain(b, 'batch')}")
    L.append("")
    L.append("## 二、分任务域推荐")
    for t in TASKS:
        best = r["tasks"][t]
        L.append(f"- **{TASK_CN[t]}**：`{best['name']}`（质量 {best['tasks'][t]}）— {explain(best, 'economy')}")
    L.append("")
    L.append("## 三、使用建议")
    L.append("- 未授权 API：照此在 Dify / Coze / LangGraph 里手动设置即可。")
    L.append("- 已授权 + 开启接管：可在网关 policy / 插件里一键应用本配置，并随模型涨跌持续更新。")
    L.append("- 每条推荐都附带可解释理由；任何应用都可一键回退上一版。")
    L.append("")
    L.append("---")
    L.append("*数据来源：研究硬数据(tokencost/benchlm/OpenRouter×a16z) + Artificial Analysis 实时信号；部分价格为估算，接入实时抓取后自动校正。*")
    return "\n".join(L)


CSS = """
:root{--bg:#0f1220;--card:#1a1f35;--acc:#6c8cff;--txt:#e8ebf5;--mut:#9aa3c0}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--txt);padding:24px}
header{margin-bottom:20px}
h1{margin:0 0 6px;font-size:22px}
header p{color:var(--mut);margin:0;font-size:13px}
.tiers{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px}
.card{background:var(--card);border:1px solid #2a3050;border-radius:14px;padding:16px}
.tier{font-size:12px;color:var(--acc);font-weight:600;letter-spacing:.5px}
.model{font-size:18px;font-weight:700;margin:8px 0 6px}
.prov{font-size:12px;color:var(--mut);font-weight:400}
.desc{font-size:13px;color:#c7cdec;line-height:1.6}
section h2{font-size:16px;margin:8px 0 12px}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:10px 12px;font-size:13px;border-bottom:1px solid #2a3050}
th{color:var(--mut);font-weight:600}
code{background:#0c0f1c;padding:2px 6px;border-radius:6px;color:#9fd0ff}
footer{margin-top:22px;color:var(--mut);font-size:12px;line-height:1.7}
@media(max-width:720px){.tiers{grid-template-columns:1fr}}
"""


def render_html(r):
    m, p, b = r["economy"], r["premium"], r["batch"]

    def card(title, model, desc):
        return (
            f'<div class="card"><div class="tier">{title}</div>'
            f'<div class="model">{html.escape(model["name"])} <span class="prov">{html.escape(model["provider"])}</span></div>'
            f'<div class="desc">{html.escape(desc)}</div></div>'
        )

    tiers = (
        card("日常性价比 · 每天主力", m, explain(m, "economy"))
        + card("最优质 · 只看质量", p, explain(p, "premium"))
        + card("最划算 · 小/批量", b, explain(b, "batch"))
    )
    rows = ""
    for t in TASKS:
        best = r["tasks"][t]
        rows += (
            f"<tr><td>{TASK_CN[t]}</td><td><code>{html.escape(best['name'])}</code></td>"
            f"<td>{best['tasks'][t]}</td><td>{html.escape(explain(best, 'economy'))}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>模型筛 · 每日报告</title>
<style>{CSS}</style>
</head>
<body>
<header><h1>📡 模型筛 · 每日最佳配置</h1>
<p>日期 {r['date']} ｜ 监控 {r['count']} 个模型 ｜ 情报层（只读建议）</p></header>
<section class="tiers">{tiers}</section>
<section><h2>分任务域推荐</h2>
<table><thead><tr><th>任务</th><th>推荐模型</th><th>质量</th><th>理由</th></tr></thead>
<tbody>{rows}</tbody></table></section>
<footer>未授权 API：照此手动设置即可；授权后可一键应用并随涨跌更新。每条推荐可解释、可回退。</footer>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser(description="模型筛 · 每日最佳模型配置报告生成器 (PoC)")
    ap.add_argument("--json", help="外部模型数据集 JSON 路径")
    ap.add_argument("--html", help="输出 HTML 文件路径")
    ap.add_argument("--md", help="输出 Markdown 文件路径")
    args = ap.parse_args()

    models = SEED_MODELS
    if args.json and os.path.exists(args.json):
        with open(args.json, encoding="utf-8") as f:
            models = json.load(f)

    date = datetime.date.today().isoformat()
    r = compute(models, date)
    md = render_md(r)

    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_html(r))
    if not args.md and not args.html:
        print(md)


if __name__ == "__main__":
    main()
