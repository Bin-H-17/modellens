#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 写回适配器（原型 / Prototype）
=================================

把「模型筛每日报告」推荐的模型档位（最优质 / 性价比 / 最划算）
映射成 Dify 应用的模型配置，并通过 Dify Management API 应用（默认 dry-run）。

设计背景（2026-08-06 决策）：
  - 写回适配器是产品的白空间，Dify 为第一落地目标（用户拍板：Dify 优先）。
  - 网关 plumbing 骑 otari（Apache-2.0），本适配器直接写 Dify，不碰网关层。
  - 满足「可选接管」铁律：默认 dry-run，应用前需用户显式给 API Key + App ID，
    且保留回退（先导出旧配置）。

⚠️ 原型声明：apply() 走的是 Dify 公开的 app model-config 端点，结构按官方文档，
   但**尚未在真实 Dify 实例上跑过**。先用 --dry-run 检查产物，再决定实跑。

用法：
  # 1) 先用实时报告生成 JSON：
  python daily_radar_report_live.py --json daily-radar-live.json

  # 2) dry-run：仅生成待应用的 payload，不调用 API
  python dify_writeback_adapter.py \
      --radar daily-radar-live.json \
      --tier best_value \
      --app-id <DIFY_APP_ID> \
      --dry-run

  # 3) 实跑（需 DIFY_API_KEY 环境变量或 --api-key）：
  python dify_writeback_adapter.py \
      --radar daily-radar-live.json --tier best_value \
      --app-id <DIFY_APP_ID> --api-key <KEY>
"""

import argparse
import json
import os
import sys

# ----------------------------------------------------------------------------
# 1. 读雷达报告
# ----------------------------------------------------------------------------
VALID_TIERS = ("best_quality", "best_value", "cheapest")


def load_radar(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    tiers = data.get("tiers", {})
    if not any(tiers.get(t) for t in VALID_TIERS):
        raise ValueError("雷达 JSON 缺少 tiers（best_quality/best_value/cheapest）")
    return data


def pick_model(radar, tier, index=0):
    if tier not in VALID_TIERS:
        raise ValueError(f"tier 必须是 {VALID_TIERS}")
    rows = radar["tiers"].get(tier, [])
    if not rows:
        raise ValueError(f"档位 {tier} 为空")
    if index < 0 or index >= len(rows):
        index = 0
    return rows[index]


# ----------------------------------------------------------------------------
# 2. OpenRouter 模型 ID -> Dify 模型配置
# ----------------------------------------------------------------------------
def to_dify_payload(model_id, provider_mode="openrouter", params=None):
    """
    provider_mode:
      "openrouter" -> provider="openrouter", name=原始 OpenRouter ID（最稳，任意模型可映射）
      "native"     -> 尝试映射到 Dify 原生 provider（anthropic/claude-... 等）
    """
    if provider_mode == "openrouter":
        provider, name = "openrouter", model_id
    else:
        provider, name = _native_map(model_id)

    cfg = {
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": 2048,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }
    if params:
        cfg.update(params)

    return {
        "model": {
            "provider": provider,
            "name": name,
            "mode": "chat",
            "configs": cfg,
        }
    }


def _native_map(model_id):
    """启发式把 OpenRouter ID 映射到 Dify 原生 provider+model。覆盖常见家族。"""
    s = model_id.lower()
    table = [
        ("anthropic/claude", ("anthropic", "claude-3-5-sonnet")),
        ("openai/gpt-5", ("openai", "gpt-5")),
        ("openai/gpt-4", ("openai", "gpt-4o")),
        ("google/gemini", ("google", "gemini-1.5-pro")),
        ("deepseek", ("deepseek", "deepseek-chat")),
        ("meta/llama", ("meta", "llama-3.1-70b-instruct")),
        ("qwen", ("qwen", "qwen-max")),
    ]
    for kw, (prov, mdl) in table:
        if kw in s:
            return prov, mdl
    # 兜底：用 openrouter provider 原样
    return "openrouter", model_id


# ----------------------------------------------------------------------------
# 3. 应用（dry-run / 实跑）
# ----------------------------------------------------------------------------
def dry_run(radar, tier, app_id, provider_mode, params, out_path):
    m = pick_model(radar, tier)
    payload = to_dify_payload(m["id"], provider_mode, params)
    payload["_meta"] = {
        "source_tier": tier,
        "recommended_model_id": m["id"],
        "recommended_model_name": m.get("name"),
        "quality_note": radar.get("quality_note"),
        "app_id": app_id,
        "mode": "DRY-RUN (not applied)",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[dry-run] payload -> {out_path}")
    else:
        print(text)
    print(f"[dry-run] 将把 App {app_id} 的模型设为：{m['name']} ({m['id']})", file=sys.stderr)
    return payload


def apply(radar, tier, app_id, api_key, provider_mode, params, base_url, out_path):
    """实跑：调用 Dify app model-config 端点。需 requests 库。"""
    try:
        import requests
    except ImportError:
        print("ERROR: 实跑需要 requests 库（pip install requests）")
        sys.exit(2)

    m = pick_model(radar, tier)
    payload = to_dify_payload(m["id"], provider_mode, params)
    url = f"{base_url.rstrip('/')}/v1/apps/{app_id}/model-config"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload["model"], timeout=30)
    ok = resp.status_code < 300
    print(f"[apply] HTTP {resp.status_code} -> {url}")
    print(resp.text[:500])
    if ok and out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"[apply] 已记录应用的配置 -> {out_path}")
    return ok


# ----------------------------------------------------------------------------
# 4. CLI
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Dify 写回适配器（原型）")
    ap.add_argument("--radar", required=True, help="雷达报告 JSON（--json 产出）")
    ap.add_argument("--tier", default="best_value", choices=VALID_TIERS)
    ap.add_argument("--index", type=int, default=0, help="档位内第几个模型（默认 0）")
    ap.add_argument("--app-id", required=True, help="Dify App ID")
    ap.add_argument("--provider-mode", default="openrouter", choices=["openrouter", "native"])
    ap.add_argument("--api-key", default=os.environ.get("DIFY_API_KEY", ""))
    ap.add_argument("--base-url", default="https://api.dify.ai")
    ap.add_argument("--out", default="", help="写出 payload 的路径")
    ap.add_argument("--dry-run", action="store_true", help="只生成 payload，不调 API（默认）")
    ap.add_argument("--apply", dest="do_apply", action="store_true", help="实跑（需 api-key）")
    a = ap.parse_args()

    radar = load_radar(a.radar)
    if a.do_apply and not a.api_key:
        print("ERROR: 实跑需要 --api-key 或环境变量 DIFY_API_KEY")
        sys.exit(2)

    if a.do_apply:
        apply(radar, a.tier, a.app_id, a.api_key, a.provider_mode, None, a.base_url, a.out)
    else:
        dry_run(radar, a.tier, a.app_id, a.provider_mode, None, a.out)


if __name__ == "__main__":
    main()
