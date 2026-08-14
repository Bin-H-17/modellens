#!/usr/bin/env python3
"""otari 写回适配器。

otari（mozilla-ai/otari，Apache-2.0）是 OpenAI 兼容的自托管 LLM 网关，
模型引用格式为 `provider:model`（如 `anthropic:claude-sonnet-4-6`）。
本适配器把 ModelSieve 三档推荐转换为 otari 可消费的模型 id / config 片段。

用法：
  python otari_writeback_adapter.py --radar daily-radar-live.json --tier best_value
  python otari_writeback_adapter.py --radar daily-radar-live.json --tier best_value --apply --out otari_rec.yaml
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


def to_otari(m, tier):
    # OpenRouter id 是 provider/model，otari 用 provider:model
    otari_id = m["id"].replace("/", ":")
    yaml_snippet = (
        f"# ModelSieve 推荐（tier={TIERS.get(tier, '')}），写入 otari client 的 model 字段\n"
        f"# 或在 config.yml 的 providers 下确认该模型已声明价格后调用\n"
        f"radar_recommendation:\n"
        f"  model: \"{otari_id}\"\n"
    )
    return otari_id, yaml_snippet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radar", required=True)
    ap.add_argument("--tier", default="best_value", choices=list(TIERS))
    ap.add_argument("--out", default="")
    ap.add_argument("--apply", action="store_true",
                    help="写文件（otari 无远程写回 API，apply = 落盘 YAML 片段）")
    a = ap.parse_args()

    radar = json.load(open(a.radar, encoding="utf-8"))
    m = pick(radar, a.tier)
    otari_id, yaml_snippet = to_otari(m, a.tier)
    payload = {
        "target": "otari",
        "tier": a.tier,
        "tier_label": TIERS[a.tier],
        "model": m,
        "otari_model_id": otari_id,
        "yaml_snippet": yaml_snippet,
        "integration": "在 otari client 的 model 字段使用 otari_model_id；或在 config.yml 中为该模型声明 pricing",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if a.apply and a.out:
        # 若后缀为 .yaml/.yml 直接写 YAML 片段，否则写 JSON payload
        if a.out.endswith((".yaml", ".yml")):
            open(a.out, "w", encoding="utf-8").write(yaml_snippet)
        else:
            open(a.out, "w", encoding="utf-8").write(text)
        print(f"[otari] applied -> {a.out}")
    else:
        print(yaml_snippet)
        if not a.apply:
            print("\n(dry-run) 加 --apply --out <file.yaml> 落盘配置片段", file=sys.stderr)


if __name__ == "__main__":
    main()
