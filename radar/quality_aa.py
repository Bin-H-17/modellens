#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量分接入层 · Artificial Analysis 真实 Intelligence Index。

免费 API（需 key，1000 req/day）：
  GET https://artificialanalysis.ai/api/v2/data/llms/models
  Header: x-api-key: <your_key>
返回每个模型的 artificial_analysis_intelligence_index（真实独立评估）。

本模块把 AA 的质量分按模型名归一化匹配，覆盖 OpenRouter 雷达行的启发式 q。
未匹配到的长尾模型保留启发式作为兜底。
"""
import json
import re
import sys
import urllib.request

AA_API = "https://artificialanalysis.ai/api/v2/data/llms/models"


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def fetch_aa(api_key):
    req = urllib.request.Request(
        AA_API, headers={"x-api-key": api_key, "User-Agent": "ModelSieve/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("data", [])


def build_aa_map(aa_models):
    m = {}
    for md in aa_models:
        idx = (md.get("evaluations") or {}).get("artificial_analysis_intelligence_index")
        if idx is None:
            continue
        m[_norm(md.get("name"))] = idx
        if md.get("slug"):
            m[_norm(md.get("slug"))] = idx
    return m


def _match_candidates(or_name, or_id):
    cands = []
    if or_name:
        cands.append(or_name)
        if ":" in or_name:  # OpenRouter 常写 "Anthropic: Claude Opus 4"
            cands.append(or_name.split(":", 1)[1].strip())
    if or_id:
        cands.append(or_id.split("/")[-1].replace("-", " "))
    return cands


def enrich_with_aa(rows, api_key):
    """用 AA 真实质量分覆盖 rows 的 q。返回匹配数量；失败则保留启发式。"""
    if not api_key:
        return 0
    try:
        aa = fetch_aa(api_key)
    except Exception as e:  # 网络/鉴权失败 → 优雅降级
        print("[AA] fetch failed, 保留启发式:", repr(e), file=sys.stderr)
        return 0
    am = build_aa_map(aa)
    n = 0
    for r in rows:
        for cand in _match_candidates(r.get("name"), r.get("id")):
            k = _norm(cand)
            if k in am:
                r["q"] = am[k]
                n += 1
                break
    print(f"[AA] 匹配 {n}/{len(rows)} 个模型真实质量分", file=sys.stderr)
    return n
