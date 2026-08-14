#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型筛 · 每日快照 / 报告生成器（统一每日入口）
=============================================
- 联网拉取 OpenRouter 实时价格，计算三档推荐，并缓存一份「快照」到 data/snapshots/。
- 快照含完整模型列表 + 三档，供 radar/diff.py 做跨日漂移对比（雷达核心价值）。
- 支持 --offline：用 data/snapshots/latest.json，不联网（用于本地预览 / CI 失败兜底）。
- 支持 --aa-key：用 Artificial Analysis 真实质量分覆盖启发式。

用法：
  python snapshot.py --json site/daily-radar-live.json --html site/daily-radar-live.html --md site/daily-radar-live.md
  python snapshot.py --offline --html site/daily-radar-live.html      # 离线
  python snapshot.py --aa-key <KEY> --json out.json                   # 真实质量分
（不传参则仅打印摘要 + 写快照）
"""
import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_radar_report_live import (  # noqa: E402
    parse, tiers, fetch_models, enrich_with_aa,
    render_html, render_md, dump_json,
)
from domains import tiers_by_domain, summarize  # noqa: E402  (P2-① 任务域细分)

SNAP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "snapshots")
QUALITY_SOURCE_HEUR = "启发式（经验性，非权威 benchmark）"
QUALITY_SOURCE_AA = "Artificial Analysis Intelligence Index（真实独立评估）"


def build(aa_key):
    """联网构建：返回 (rows, bq, bc, bch, qsrc)。"""
    rows = parse(fetch_models())
    qsrc = QUALITY_SOURCE_HEUR
    if aa_key:
        n = enrich_with_aa(rows, aa_key)
        if n > 0:
            qsrc = QUALITY_SOURCE_AA
    bq, bc, bch = tiers(rows)
    return rows, bq, bc, bch, qsrc


def load_offline(snap_dir):
    latest = os.path.join(snap_dir, "latest.json")
    if not os.path.exists(latest):
        return None
    snap = json.load(open(latest, encoding="utf-8"))
    rows = snap["models"]
    bq = snap["tiers"]["best_quality"]
    bc = snap["tiers"]["best_value"]
    bch = snap["tiers"]["cheapest"]
    return rows, bq, bc, bch, snap.get("quality_source", QUALITY_SOURCE_HEUR), snap.get("generated_at")


def save_snapshot(rows, bq, bc, bch, qsrc, now, snap_dir):
    date = now.split(" ")[0]
    models = [{k: r[k] for k in ("id", "name", "in", "out", "avg", "ctx", "q", "mod", "cpp")}
              for r in rows]
    snap = {
        "date": date,
        "generated_at": now,
        "source": "OpenRouter /api/v1/models (live)",
        "quality_source": qsrc,
        "count": len(models),
        "models": models,
        "tiers": dump_json(rows, bq, bc, bch, now)["tiers"],
        "domains": tiers_by_domain(rows),
        "domain_counts": summarize(rows),
    }
    os.makedirs(snap_dir, exist_ok=True)
    path = os.path.join(snap_dir, f"{date}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    shutil.copyfile(path, os.path.join(snap_dir, "latest.json"))
    return path


def main():
    ap = argparse.ArgumentParser(description="模型筛每日快照/报告生成器")
    ap.add_argument("--html", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--aa-key", default="",
                    help="Artificial Analysis API key；提供则用真实质量分覆盖启发式")
    ap.add_argument("--offline", action="store_true",
                    help="用 data/snapshots/latest.json，不联网")
    ap.add_argument("--snap-dir", default=SNAP_DIR)
    ap.add_argument("--domains", default="",
                    help="额外输出「任务域细分档位」JSON 到该路径")
    a = ap.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if a.offline:
        off = load_offline(a.snap_dir)
        if not off:
            print("NO_OFFLINE_SNAPSHOT: 先联网跑一次 snapshot.py 生成快照", file=sys.stderr)
            sys.exit(1)
        rows, bq, bc, bch, qsrc, now = off
        print(f"[offline] 用快照（{len(rows)} 模型，质量分={qsrc}）")
    else:
        try:
            rows, bq, bc, bch, qsrc = build(a.aa_key)
        except Exception as e:
            print("FETCH_ERROR", repr(e), file=sys.stderr)
            # 兜底：若已有快照则离线继续，否则失败
            off = load_offline(a.snap_dir)
            if off:
                rows, bq, bc, bch, qsrc, now = off
                print("[fallback] 联网失败，改用离线快照", file=sys.stderr)
            else:
                sys.exit(1)
        sp = save_snapshot(rows, bq, bc, bch, qsrc, now, a.snap_dir)
        print("SNAPSHOT ->", sp)

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

    if a.domains:
        dom = {"generated_at": now, "domain_counts": summarize(rows),
               "domains": tiers_by_domain(rows)}
        open(a.domains, "w", encoding="utf-8").write(
            json.dumps(dom, ensure_ascii=False, indent=2))
        print("DOMAINS ->", a.domains)

    print("\n【最优质】", [r["name"] for r in bq[:3]])
    print("【性价比】", [r["name"] for r in bc[:3]])
    print("【最划算】", [r["name"] for r in bch[:3]])
    print("质量分来源:", qsrc)
    dc = summarize(rows)
    print("【任务域覆盖】", {k: dc[k] for k in
          ("coding", "reasoning", "long-context", "multimodal", "general")})
    for d in ("coding", "reasoning", "long-context", "multimodal", "general"):
        top = tiers_by_domain(rows)[d]["best_value"][:1]
        if top:
            print(f"  [{d}] 性价比首选: {top[0]['name']}  (${top[0]['avg']}/MTok)")


if __name__ == "__main__":
    main()
