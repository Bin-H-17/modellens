#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型筛 · 历史漂移可视化（P2 深化护城河 · 分支②）
================================================
把 data/snapshots/*.json 的历史数据画成自包含 SVG 趋势图——
每条线是一个模型的价格（avg $/MTok）随时间的变化，一眼看懂涨跌。

特点：
  - 纯 Python 生成 SVG，零外部依赖，离线可直接在浏览器/编辑器打开。
  - 价格跨度大（免费 ~ 几十 $），纵轴用对数刻度更易读。
  - 默认挑选「最新快照的三档模型」画 8 条线；可用 --max-models 调整。
  - --selftest：用合成数据验证 SVG 生成逻辑，不落盘、不污染仓库。

用法：
  python visualize.py                       # 读 data/snapshots -> site/drift-chart.svg
  python visualize.py --out /tmp/x.svg      # 指定输出
  python visualize.py --selftest            # 合成数据自测
"""
import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP_DIR = os.path.join(ROOT, "data", "snapshots")
SITE_DIR = os.path.join(ROOT, "site")
PALETTE = ["#4f8cff", "#ff6b6b", "#37d39b", "#ffb454", "#b07cff",
           "#ff7ad9", "#3fd0d6", "#9aa7ff"]


def load_snapshots(snap_dir):
    if not os.path.isdir(snap_dir):
        return []
    snaps = []
    for f in os.listdir(snap_dir):
        if not f.endswith(".json") or f == "latest.json":
            continue
        try:
            snaps.append(json.load(open(os.path.join(snap_dir, f), encoding="utf-8")))
        except Exception:
            continue
    snaps.sort(key=lambda x: x.get("date", ""))
    return snaps


def pick_models(snaps, max_n=8):
    if not snaps:
        return []
    latest = snaps[-1]
    ids, names = [], {}
    for tier in ("best_quality", "best_value", "cheapest"):
        for r in latest.get("tiers", {}).get(tier, []):
            if r["id"] not in ids:
                ids.append(r["id"])
                names[r["id"]] = r.get("name", r["id"])
    return ids[:max_n], names


def build_series(snaps, ids):
    series = {i: [] for i in ids}
    for s in snaps:
        date = s.get("date", "")
        models = {m["id"]: m for m in s.get("models", [])}
        for i in ids:
            if i in models:
                avg = models[i].get("avg") or 0
                series[i].append((date, avg))
    return series


def _fmt(v):
    if v <= 0:
        return "free"
    if v < 1:
        return f"${v:.2f}"
    return f"${v:.1f}"


def render_svg(series, names, title="ModelSieve · 价格漂移趋势（avg $/MTok，对数刻度）"):
    dates = sorted({d for s in series.values() for d, _ in s})
    if not dates:
        return ""
    n = len(dates)
    W, H = 920, 460
    pad_l, pad_r, pad_t, pad_b = 64, 200, 40, 48
    plot_w, plot_h = W - pad_l - pad_r, H - pad_t - pad_b

    # y 范围（对数）
    allv = [v for s in series.values() for _, v in s if v > 0]
    if not allv:
        allv = [0.01, 1]
    lo, hi = min(allv), max(allv)
    lo = max(lo, 1e-4)
    log_lo, log_hi = math.log10(lo), math.log10(hi)
    if log_hi - log_lo < 1e-6:
        log_hi = log_lo + 1

    def x_of(idx):
        return pad_l + (plot_w * idx / max(1, n - 1)) if n > 1 else pad_l + plot_w / 2

    def y_of(v):
        if v <= 0:
            v = 1e-4
        lv = math.log10(max(v, 1e-4))
        return pad_t + plot_h * (1 - (lv - log_lo) / (log_hi - log_lo))

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    parts.append(f'<rect width="{W}" height="{H}" fill="#0b1020"/>')
    parts.append(f'<text x="{pad_l}" y="22" fill="#e6edf7" font-size="15" '
                 f'font-weight="600">{title}</text>')

    # y 网格 + 刻度（5 档对数）
    for k in range(6):
        lv = log_lo + (log_hi - log_lo) * k / 5
        y = y_of(10 ** lv)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l+plot_w}" y2="{y:.1f}" '
                     f'stroke="#1c2742" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" fill="#7e8aa3" font-size="10" '
                     f'text-anchor="end">{_fmt(10**lv)}</text>')

    # x 轴日期标签（最多标 6 个）
    step = max(1, math.ceil(n / 6))
    for idx in range(0, n, step):
        x = x_of(idx)
        parts.append(f'<text x="{x:.1f}" y="{H-pad_b+18}" fill="#7e8aa3" font-size="10" '
                     f'text-anchor="middle">{dates[idx][5:]}</text>')

    # 折线
    for i, mid in enumerate(series):
        pts = series[mid]
        if not pts:
            continue
        color = PALETTE[i % len(PALETTE)]
        d = " ".join(f"{x_of(dates.index(d)):.1f},{y_of(v):.1f}" for d, v in pts)
        parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" '
                     f'stroke-width="2" stroke-linejoin="round"/>')
        for d, v in pts:
            parts.append(f'<circle cx="{x_of(dates.index(d)):.1f}" cy="{y_of(v):.1f}" '
                         f'r="2.5" fill="{color}"/>')

    # 图例
    ly = pad_t + 6
    for i, mid in enumerate(series):
        color = PALETTE[i % len(PALETTE)]
        y = ly + i * 20
        parts.append(f'<rect x="{pad_l+plot_w+16}" y="{y-9}" width="11" height="11" '
                     f'rx="2" fill="{color}"/>')
        nm = (names.get(mid, mid))[:34]
        parts.append(f'<text x="{pad_l+plot_w+34}" y="{y+1}" fill="#cdd6e6" '
                     f'font-size="11">{nm}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def mock_snapshots():
    base = [
        ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", 9.0),
        ("openai/gpt-4o", "GPT-4o", 6.25),
        ("deepseek/deepseek-chat", "DeepSeek Chat", 0.6),
        ("qwen/qwen3-max", "Qwen3 Max", 0.3),
        ("google/gemini-2.0-flash", "Gemini 2.0 Flash", 0.1),
    ]
    snaps = []
    for di, d in enumerate(("2026-08-05", "2026-08-10", "2026-08-14")):
        models = []
        for mid, nm, p in base:
            drift = 1 + 0.12 * di * (0.5 if "deepseek" in mid else 1)
            models.append({"id": mid, "name": nm, "avg": round(p * drift, 4)})
        snaps.append({"date": d, "models": models,
                      "tiers": {"best_quality": [{"id": base[0][0], "name": base[0][1]}],
                                "best_value": [{"id": base[3][0], "name": base[3][1]}],
                                "cheapest": [{"id": base[4][0], "name": base[4][1]}]}})
    return snaps


def main():
    ap = argparse.ArgumentParser(description="模型筛历史漂移可视化")
    ap.add_argument("--snap-dir", default=SNAP_DIR)
    ap.add_argument("--out", default=os.path.join(SITE_DIR, "drift-chart.svg"))
    ap.add_argument("--max-models", type=int, default=8)
    ap.add_argument("--selftest", action="store_true",
                    help="用合成数据验证 SVG 生成逻辑（不落盘）")
    a = ap.parse_args()

    if a.selftest:
        snaps = mock_snapshots()
        print(f"[selftest] 合成 {len(snaps)} 份快照")
    else:
        snaps = load_snapshots(a.snap_dir)

    if len(snaps) < 2:
        print(f"NEED_MORE_SNAPSHOTS: 至少 2 份历史快照才能画图（当前 {len(snaps)}）。"
              f"\n  联网跑 snapshot.py 累积几日后，本图会自动有数据。", file=sys.stderr)
        sys.exit(2)

    ids, names = pick_models(snaps, a.max_models)
    series = build_series(snaps, ids)
    svg = render_svg(series, names)
    out_dir = os.path.dirname(a.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG -> {a.out}  （{len(ids)} 条线，{len(snaps)} 个时间点）")


if __name__ == "__main__":
    main()
