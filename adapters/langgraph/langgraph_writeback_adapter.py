#!/usr/bin/env python3
"""LangGraph 写回适配器。

把 ModelSieve 三档推荐映射为 LangGraph / LangChain 可用的 model 配置片段。
雷达 JSON 结构见 radar/daily_radar_report_live.py --json 输出。

用法：
  python langgraph_writeback_adapter.py --radar daily-radar-live.json --tier best_value
  python langgraph_writeback_adapter.py --radar daily-radar-live.json --tier best_value --apply --out lg_config.json
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


def to_langgraph_config(m):
    """生成 LangChain / LangGraph 可用的配置 dict（OpenRouter 兼容 OpenAI 协议）。"""
    return {
        "model": m["id"],
        "model_provider": "openrouter",
        "openai_api_base": "https://openrouter.ai/api/v1",
        "openai_api_key_env": "OPENROUTER_API_KEY",
        "snippet": (
            "from langchain_openai import ChatOpenAI\n"
            f"llm = ChatOpenAI(model={m['id']!r}, "
            "openai_api_base='https://openrouter.ai/api/v1',\n"
            "                 api_key=os.environ['OPENROUTER_API_KEY'])\n"
            "# 在 LangGraph 节点中：builder.add_node('agent', agent_with_llm(llm))"
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radar", required=True, help="雷达 JSON 路径")
    ap.add_argument("--tier", default="best_value", choices=list(TIERS))
    ap.add_argument("--out", default="", help="--apply 时写出的配置文件")
    ap.add_argument("--apply", action="store_true",
                    help="写文件（LangGraph 无远程 API，apply = 落盘配置片段）")
    a = ap.parse_args()

    radar = json.load(open(a.radar, encoding="utf-8"))
    m = pick(radar, a.tier)
    cfg = to_langgraph_config(m)
    payload = {
        "target": "langgraph",
        "tier": a.tier,
        "tier_label": TIERS[a.tier],
        "model": m,
        "config": cfg,
        "integration": "将 config['model'] 写入你的 langgraph 节点 / config.py 或环境变量",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if a.apply and a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"[langgraph] applied -> {a.out}")
    else:
        print(text)
        if not a.apply:
            print("\n(dry-run) 加 --apply --out <file> 落盘配置片段", file=sys.stderr)


if __name__ == "__main__":
    main()
