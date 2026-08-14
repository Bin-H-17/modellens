#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型筛 · 快照漂移对比（雷达核心价值）
=====================================
对比两个日期的快照，输出：
  - 新增模型 / 退市模型
  - 价格漂移（均价变动 ≥5%）
  - 档位变动（哪些模型进入/离开三档）
  - 换模型建议（性价比档榜首是否变化）

用法：
  python diff.py                                  # 默认取 data/snapshots 中最近两份
  python diff.py --old s1.json --new s2.json
  python diff.py --old s1.json --new s2.json --md drift.md --json drift.json
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

SNAP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "snapshots")
TIER_LABELS = {"best_quality": "最优质", "best_value": "性价比", "cheapest": "最划算"}


def load(path):
    return json.load(open(path, encoding="utf-8"))


def latest_two(snap_dir):
    files = [f for f in os.listdir(snap_dir) if f.endswith(".json") and f != "latest.json"]
    files.sort()
    if len(files) < 2:
        return None
    return os.path.join(snap_dir, files[-2]), os.path.join(snap_dir, files[-1])


def diff(old, new):
    om = {m["id"]: m for m in old["models"]}
    nm = {m["id"]: m for m in new["models"]}
    added = [nm[i] for i in nm if i not in om]
    removed = [om[i] for i in om if i not in nm]

    price_drift = []
    for mid in set(om) & set(nm):
        oa, na = om[mid]["avg"], nm[mid]["avg"]
        if oa == 0 and na == 0:
            continue
        if oa == 0:
            price_drift.append({"id": mid, "name": nm[mid]["name"], "old_avg": 0,
                                "new_avg": round(na, 4), "change_pct": None,
                                "kind": "free->priced"})
            continue
        ch = (na - oa) / oa * 100
        if abs(ch) >= 5:
            price_drift.append({"id": mid, "name": nm[mid]["name"],
                                "old_avg": round(oa, 4), "new_avg": round(na, 4),
                                "change_pct": round(ch, 1), "kind": "drift"})

    tier_changes = {}
    for t in TIER_LABELS:
        oi = {m["id"] for m in old["tiers"][t]}
        ni = {m["id"] for m in new["tiers"][t]}
        entered = [i for i in ni - oi]
        left = [i for i in oi - ni]
        if entered or left:
            tier_changes[t] = {"label": TIER_LABELS[t], "entered": entered, "left": left}

    swap = None
    if old["tiers"]["best_value"] and new["tiers"]["best_value"]:
        if old["tiers"]["best_value"][0]["id"] != new["tiers"]["best_value"][0]["id"]:
            swap = {"from": old["tiers"]["best_value"][0], "to": new["tiers"]["best_value"][0]}

    return {
        "old_date": old["date"],
        "new_date": new["date"],
        "old_count": old["count"],
        "new_count": new["count"],
        "added": added,
        "removed": removed,
        "price_drift": price_drift,
        "tier_changes": tier_changes,
        "swap_suggestion": swap,
    }


def render_md(d):
    L = []
    L.append(f"# 📡 模型筛 · 模型漂移报告（{d['old_date']} → {d['new_date']}）\n")
    L.append(f"模型总数：{d['old_count']} → {d['new_count']}（新增 {len(d['added'])} / 退市 {len(d['removed'])}）\n")

    if d["swap_suggestion"]:
        f, t = d["swap_suggestion"]["from"], d["swap_suggestion"]["to"]
        L.append(f"## 🔁 换模型建议（性价比档榜首变动）\n- 旧：`{f['name']}`（`{f['id']}`）\n- 新：**`{t['name']}`（`{t['id']}`）**\n- 建议评估后切换到新榜首。\n")
    else:
        L.append("## 🔁 换模型建议\n性价比档榜首未变。\n")

    if d["added"]:
        L.append("## ➕ 新增模型\n" + "\n".join(f"- {m['name']}（`{m['id']}`）" for m in d["added"]) + "\n")
    if d["removed"]:
        L.append("## ➖ 退市模型\n" + "\n".join(f"- {m['name']}（`{m['id']}`）" for m in d["removed"]) + "\n")

    if d["price_drift"]:
        L.append("## 💸 价格漂移（≥5%）\n| 模型 | 旧均价 | 新均价 | 变动 |")
        L.append("|---|---|---|---|")
        for p in d["price_drift"]:
            if p["kind"] == "free->priced":
                L.append(f"| {p['name']} | FREE | ${p['new_avg']:.3f} | 转收费 |")
            else:
                L.append(f"| {p['name']} | ${p['old_avg']:.3f} | ${p['new_avg']:.3f} | {p['change_pct']:+.1f}% |")
        L.append("")
    else:
        L.append("## 💸 价格漂移\n无显著价格变动（≥5%）。\n")

    if d["tier_changes"]:
        L.append("## 🏷️ 档位变动\n")
        for t, v in d["tier_changes"].items():
            L.append(f"- **{v['label']}**：进入 {v['entered'] or '—'} ｜ 离开 {v['left'] or '—'}")
        L.append("")
    else:
        L.append("## 🏷️ 档位变动\n三档成员未变。\n")

    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="模型筛快照漂移对比")
    ap.add_argument("--old", default="")
    ap.add_argument("--new", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--snap-dir", default=SNAP_DIR)
    a = ap.parse_args()

    if a.old and a.new:
        op, np_ = a.old, a.new
    else:
        pair = latest_two(a.snap_dir)
        if not pair:
            print("NEED_TWO_SNAPSHOTS: data/snapshots 至少需要两份（先联网跑 snapshot.py 多次）",
                  file=sys.stderr)
            sys.exit(1)
        op, np_ = pair

    d = diff(load(op), load(np_))
    if a.json:
        open(a.json, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
        print("DIFF JSON ->", a.json)
    md = render_md(d)
    if a.md:
        open(a.md, "w", encoding="utf-8").write(md)
        print("DIFF MD ->", a.md)
    print(md)


if __name__ == "__main__":
    main()
