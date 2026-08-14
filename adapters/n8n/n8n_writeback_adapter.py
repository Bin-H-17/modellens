#!/usr/bin/env python3
"""n8n 写回适配器。

把 ModelSieve 三档推荐映射为 n8n 可调用的 OpenRouter HTTP Request 节点 JSON。
可直接粘贴进 n8n 工作流的 "HTTP Request" 节点（或作为 Set 节点的 model 字段来源）。

用法：
  python n8n_writeback_adapter.py --radar daily-radar-live.json --tier best_value
  python n8n_writeback_adapter.py --radar daily-radar-live.json --tier best_value --apply --out n8n_node.json
"""
import argparse
import json
import sys

TIERS = {"best_quality": "最优质", "best_value": "最划算", "cheapest": "最便宜"}


def pick(radar, tier):
    t = radar.get("tiers", {}).get(tier)
    if not t:
        sys.exit(f"[err] tier {tier} 无数据，请重新生成雷达 JSON")
    return t[0]


def to_n8n_node(m):
    """生成 n8n HTTP Request 节点参数（调用 OpenRouter chat completions）。"""
    return {
        "parameters": {
            "method": "POST",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Authorization", "value": "=Bearer {{$env.OPENROUTER_API_KEY}}"},
                    {"name": "Content-Type", "value": "application/json"},
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": json.dumps({
                "model": m["id"],
                "messages": [{"role": "={{$json.role}}", "content": "={{$json.content}}"}],
            }, ensure_ascii=False),
            "options": {},
        },
        "name": f"ModelSieve → OpenRouter ({m['id']})",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [0, 0],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radar", required=True)
    ap.add_argument("--tier", default="best_value", choices=list(TIERS))
    ap.add_argument("--out", default="")
    ap.add_argument("--apply", action="store_true",
                    help="写文件（n8n 无远程写回 API，apply = 落盘节点 JSON）")
    a = ap.parse_args()

    radar = json.load(open(a.radar, encoding="utf-8"))
    m = pick(radar, a.tier)
    node = to_n8n_node(m)
    payload = {
        "target": "n8n",
        "tier": a.tier,
        "tier_label": TIERS[a.tier],
        "model": m,
        "node": node,
        "integration": "在 n8n 工作流中添加 HTTP Request 节点，粘贴本 JSON 的 parameters；或用作 Set 节点的 model 表达式",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if a.apply and a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"[n8n] applied -> {a.out}")
    else:
        print(text)
        if not a.apply:
            print("\n(dry-run) 加 --apply --out <file> 落盘节点 JSON", file=sys.stderr)


if __name__ == "__main__":
    main()
