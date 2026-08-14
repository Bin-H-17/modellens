#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型筛 · 任务域细分档位（P2 深化护城河 · 分支①）
================================================
现在的三档（最优质 / 性价比 / 最便宜）是「混在所有模型上」的通用推荐。
但「最优质」在写代码、长文本摘要、多模态理解里答案完全不同。
本模块按模型元信息（名称 / 模态 / 上下文长度）启发式分桶到任务域，
对每个域独立算三档，让推荐更精准。

任务域（按优先级匹配，命中即归桶）：
  - multimodal   多模态（vision / image / audio / video / omni）
  - long-context 长上下文（ctx >= 128k）
  - coding       编码（名称含 code/coder/swe 等）
  - reasoning    推理（名称含 reason/think/r1/o1/qwq 等）
  - general      通用（兜底）

注意：分桶是「启发式」，基于公开元信息，非权威能力评测。
真实能力仍应以 LMArena / Artificial Analysis 分任务榜为准（见 skill/modellens）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_radar_report_live import tiers  # noqa: E402

DOMAINS = ("coding", "reasoning", "long-context", "multimodal", "general")

# 名称关键词（小写匹配）
_K_MULTIMODAL = ("vision", "image", "omni", "multimodal", "tts", "audio",
                 "whisper", "dall", "flux", "sora", "video")
_K_CODING = ("code", "coder", "swe", "deepcoder", "codestral", "codex")
_K_REASON = ("reason", "think", "qwq", "deepseek-r", "r1", "o1", "o3", "o4")


def domain_of(m):
    """返回单个模型的任务域字符串。"""
    name = (m.get("name") or m.get("id") or "").lower()
    mod = (m.get("mod") or "").lower()
    ctx = m.get("ctx") or 0

    # 1) 多模态优先：模态字段或名称显式多模态
    if any(k in mod for k in ("image", "audio", "video")) or \
       any(k in name for k in _K_MULTIMODAL):
        return "multimodal"

    # 2) 长上下文：上下文 >= 128k 视为长上下文专用能力
    if ctx and ctx >= 128000:
        return "long-context"

    # 3) 编码
    if any(k in name for k in _K_CODING):
        return "coding"

    # 4) 推理
    if any(k in name for k in _K_REASON):
        return "reasoning"

    return "general"


def _slim(rs, n=3):
    return [{"id": r["id"], "name": r["name"], "q": r["q"],
             "avg": round(r["avg"], 4), "ctx": r["ctx"]} for r in rs[:n]]


def tiers_by_domain(rows, top=3):
    """对每个任务域独立算三档推荐。

    返回 {domain: {"best_quality":[...], "best_value":[...], "cheapest":[...]}}。
    空域返回空列表，调用方可据此跳过。
    """
    out = {}
    for dom in DOMAINS:
        sub = [r for r in rows if domain_of(r) == dom]
        if not sub:
            out[dom] = {"best_quality": [], "best_value": [], "cheapest": []}
            continue
        bq, bc, bch = tiers(sub)
        out[dom] = {
            "best_quality": _slim(bq, top),
            "best_value": _slim(bc, top),
            "cheapest": _slim(bch, top),
        }
    return out


def summarize(rows):
    """返回各域模型计数，便于报告里展示覆盖度。"""
    cnt = {d: 0 for d in DOMAINS}
    for r in rows:
        cnt[domain_of(r)] += 1
    return cnt


if __name__ == "__main__":
    # 自测：用一份样例验证分桶不崩
    sample = [
        {"id": "openai/gpt-4o", "name": "OpenAI: GPT-4o", "ctx": 128000,
         "in": 2.5, "out": 10, "avg": 6.25, "q": 88, "cpp": round(88/6.25, 2),
         "mod": "text->image,text->text"},
        {"id": "deepseek/deepseek-r1", "name": "DeepSeek: R1", "ctx": 64000,
         "in": 0.5, "out": 2, "avg": 1.25, "q": 90, "cpp": round(90/1.25, 2),
         "mod": "text->text"},
        {"id": "qwen/qwen2.5-coder-32b", "name": "Qwen: Coder 32B", "ctx": 32768,
         "in": 0.1, "out": 0.1, "avg": 0.1, "q": 70, "cpp": round(70/0.1, 2),
         "mod": "text->text"},
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude: 3.5 Sonnet", "ctx": 200000,
         "in": 3, "out": 15, "avg": 9, "q": 92, "cpp": round(92/9, 2),
         "mod": "text->text"},
    ]
    print("分桶:", {m["name"]: domain_of(m) for m in sample})
    print("计数:", summarize(sample))
    print("分域三档:", tiers_by_domain(sample))
