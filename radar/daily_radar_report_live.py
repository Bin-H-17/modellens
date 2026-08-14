#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型筛 · 每日最佳模型配置（实时数据版 / Phase 1）
=================================================
数据源：OpenRouter 公开 API (https://openrouter.ai/api/v1/models) —— 实时价格 + 上下文长度。
质量分：默认基于模型家族的【经验性启发式分层】；若提供 --aa-key，则用
        Artificial Analysis 真实 Intelligence Index 覆盖（详见 radar/quality_aa.py）。

用法：
  python daily_radar_report_live.py --html daily-radar-live.html --md daily-radar-live.md --json daily-radar-live.json
  python daily_radar_report_live.py --json out.json --aa-key <AA_API_KEY>   # 接真实质量分
  （不传参则仅打印摘要）
"""
import argparse, json, sys, urllib.request
from datetime import datetime, timezone
from quality_aa import enrich_with_aa

API = "https://openrouter.ai/api/v1/models"
QUALITY_SOURCE = "启发式（经验性，非权威 benchmark）"

# ---- 经验性质量分层（0-100，启发式，非 benchmark）----
def heuristic_quality(mid: str) -> int:
    s = mid.lower()
    q = 70
    if "opus" in s: q = 95
    elif "gpt-5" in s or "gpt5" in s: q = 92
    elif "sonnet" in s: q = 88
    elif "gemini-3" in s or "gemini-2.5" in s: q = 86
    elif "deepseek-v4" in s or "deepseek-chat" in s: q = 85
    elif "deepseek" in s: q = 84
    elif "qwen3.8" in s or "qwen3-max" in s: q = 84
    elif "qwen3.7" in s: q = 80
    elif "claude" in s: q = 82
    elif "qwen" in s: q = 75
    elif "gemini" in s: q = 78
    elif "llama-4" in s or "llama4" in s: q = 80
    elif "ling" in s: q = 78
    elif "gpt-4" in s: q = 80
    if "r1" in s or "reasoning" in s: q = max(q, 90)
    if "flash" in s: q -= 10
    if "mini" in s: q -= 12
    if "nano" in s or "lite" in s: q -= 18
    if ":free" in s or "-free" in s: q = min(q, 68)
    return max(40, min(98, q))

def fetch_models():
    req = urllib.request.Request(API, headers={"User-Agent": "ModelSieve/1.0"})
    raw = urllib.request.urlopen(req, timeout=25).read()
    return json.loads(raw)["data"]

def parse(models):
    out = []
    for m in models:
        p = m.get("pricing") or {}
        try:
            inp = float(p.get("prompt", 0)) * 1_000_000
            outp = float(p.get("completion", 0)) * 1_000_000
        except Exception:
            continue
        mid = m.get("id", "")
        ctx = m.get("context_length") or 0
        q = heuristic_quality(mid)
        avg = (inp + outp) / 2
        arch = m.get("architecture") or {}
        mod = (arch.get("modality") or (m.get("modalities") or ["text"]))
        mod = mod[0] if isinstance(mod, list) and mod else (mod or "text")
        out.append({
            "id": mid,
            "name": (m.get("name") or mid),
            "in": inp, "out": outp, "avg": avg,
            "ctx": ctx, "q": q, "mod": str(mod).lower(),
            "cpp": q / avg if avg > 0 else (q if avg == 0 else 0),  # 性价比指数
        })
    return out

def is_real_model(mid):
    s = mid.lower()
    for kw in ("router", "fusion", "merge", "auto-router", "/dev/", "load-balance", "cache"):
        if kw in s:
            return False
    return True

def tiers(rows):
    rows = [r for r in rows if is_real_model(r["id"]) and r.get("mod", "").split("->")[-1] == "text"]
    by_q = sorted(rows, key=lambda r: r["q"], reverse=True)
    # 最优质：质量最高（不限价）
    best_quality = by_q[:5]
    # 性价比日常：质量/均价 最高，排除免费档与极贵档(avg>20)
    candidates = [r for r in rows if r["avg"] > 0 and r["avg"] <= 20]
    by_cpp = sorted(candidates, key=lambda r: r["cpp"], reverse=True)
    best_cpp = by_cpp[:5]
    # 最划算小批量：在质量>=70 前提下价格最低
    cheap_ok = [r for r in rows if r["q"] >= 70]
    by_price = sorted(cheap_ok, key=lambda r: r["avg"])
    best_cheap = by_price[:6]
    return best_quality, best_cpp, best_cheap

def render_html(rows, bq, bc, bch, now):
    qsrc = QUALITY_SOURCE
    def row(r):
        price = "FREE" if r["avg"] == 0 else f"${r['avg']:.3f}/MTok(avg)"
        return f"<tr><td>{r['name']}</td><td>{r['id']}</td><td>{r['q']}</td><td>{price}</td><td>{r['ctx']:,}</td></tr>"
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>模型筛 · 每日最佳模型配置（实时）</title>
<style>body{{font-family:-apple-system,Segoe UI,Roboto,'PingFang SC',sans-serif;max-width:980px;margin:32px auto;padding:0 20px;color:#1a1a1a;}}
h1{{font-size:24px}}h2{{font-size:18px;margin-top:32px;border-left:4px solid #2b6cb0;padding-left:10px}}
table{{border-collapse:collapse;width:100%;margin-top:10px;font-size:14px}}th,td{{border:1px solid #e2e8f0;padding:8px 10px;text-align:left}}
th{{background:#f7fafc}}tr:nth-child(even){{background:#fbfdff}}
.note{{background:#fffbeb;border:1px solid #fde68a;padding:12px 14px;border-radius:8px;font-size:13px;color:#92400e;margin:14px 0}}
.meta{{color:#718096;font-size:13px}}.tag{{display:inline-block;background:#ebf4ff;color:#2b6cb0;border-radius:6px;padding:2px 8px;font-size:12px;margin-right:6px}}</style>
</head><body>
<h1>📡 模型筛 · 每日最佳模型配置（实时版）</h1>
<p class="meta">生成时间：{now} ｜ 数据源：OpenRouter /api/v1/models（实时价格·{len(rows)} 个模型）｜ 质量分来源：{qsrc}</p>
<div class="note">⚠️ <b>质量分层说明</b>：当前质量分来源为「{qsrc}」。若页面标注为启发式，则仅用于演示；提供 Artificial Analysis API key 后即为真实独立评估的可交付版。价格均为每百万 token（输入/输出均价）。</div>

<h2><span class="tag">档位一</span>最优质模型（只看质量，不限成本）</h2>
<table><tr><th>名称</th><th>ID</th><th>质量分</th><th>价格</th><th>上下文</th></tr>{''.join(row(r) for r in bq)}</table>

<h2><span class="tag">档位二</span>性价比日常模型（质量/成本最优平衡）</h2>
<table><tr><th>名称</th><th>ID</th><th>质量分</th><th>价格</th><th>上下文</th></tr>{''.join(row(r) for r in bc)}</table>

<h2><span class="tag">档位三</span>最划算小/批量任务模型（质量≥70 前提下最便宜）</h2>
<table><tr><th>名称</th><th>ID</th><th>质量分</th><th>价格</th><th>上下文</th></tr>{''.join(row(r) for r in bch)}</table>

<p class="meta">本页为实时数据原型，验证「每日早起报告」是否有用。不做任何自动配置改写。</p>
</body></html>"""

def render_md(rows, bq, bc, bch, now):
    qsrc = QUALITY_SOURCE
    def block(title, rs):
        lines = [f"### {title}", "| 名称 | ID | 质量分 | 价格(avg/MTok) | 上下文 |", "|---|---|---|---|---|"]
        for r in rs:
            price = "FREE" if r["avg"] == 0 else f"${r['avg']:.3f}"
            lines.append(f"| {r['name']} | {r['id']} | {r['q']} | {price} | {r['ctx']:,} |")
        return "\n".join(lines) + "\n"
    return (f"# 📡 模型筛 · 每日最佳模型配置（实时版）\n\n生成时间：{now} ｜ 数据源：OpenRouter（{len(rows)} 模型）｜ 质量分来源：{qsrc}\n\n"
            + f"⚠️ 质量分来源：{qsrc}。提供 Artificial Analysis key 后为真实评估。\n\n"
            + block("档位一 · 最优质（不限成本）", bq)
            + block("档位二 · 性价比日常", bc)
            + block("档位三 · 最划算小/批量", bch))

def dump_json(rows, bq, bc, bch, now):
    def slim(rs):
        return [{"id": r["id"], "name": r["name"], "q": r["q"],
                 "avg": round(r["avg"], 4), "ctx": r["ctx"]} for r in rs]
    return {
        "generated_at": now,
        "source": "OpenRouter /api/v1/models (live)",
        "quality_source": QUALITY_SOURCE,
        "tiers": {
            "best_quality": slim(bq),
            "best_value": slim(bc),
            "cheapest": slim(bch),
        },
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--aa-key", default="",
                    help="Artificial Analysis API key；提供则用真实质量分覆盖启发式")
    a = ap.parse_args()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        rows = parse(fetch_models())
        print(f"[OK] 拉取真实模型 {len(rows)} 个")
    except Exception as e:
        print("FETCH_ERROR", repr(e)); sys.exit(1)

    if a.aa_key:
        n = enrich_with_aa(rows, a.aa_key)
        if n > 0:
            global QUALITY_SOURCE
            QUALITY_SOURCE = "Artificial Analysis Intelligence Index（真实独立评估）"

    bq, bc, bch = tiers(rows)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(
            json.dumps(dump_json(rows, bq, bc, bch, now), ensure_ascii=False, indent=2))
        print("JSON ->", a.json)
    if a.html:
        open(a.html, "w", encoding="utf-8").write(render_html(rows, bq, bc, bch, now))
        print("HTML ->", a.html)
    if a.md:
        open(a.md, "w", encoding="utf-8").write(render_md(rows, bq, bc, bch, now))
        print("MD ->", a.md)
    # 控制台摘要
    print("\n【最优质】", [r["name"] for r in bq[:3]])
    print("【性价比】", [r["name"] for r in bc[:3]])
    print("【最划算】", [r["name"] for r in bch[:3]])
    print("质量分来源:", QUALITY_SOURCE)

if __name__ == "__main__":
    main()
