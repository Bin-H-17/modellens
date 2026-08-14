#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""适配器 + 快照 / 漂移引擎的冒烟测试（pytest）。

全部使用 modellens/data/sample-radar-report.json（真实雷达格式样例），
完全离线、无需任何远程 API 或网络。
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "data", "sample-radar-report.json")
ADAPTERS = os.path.join(ROOT, "adapters")


def _run(script, *args):
    cmd = [sys.executable, script, "--radar", SAMPLE, *args]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p


def test_sample_exists():
    assert os.path.exists(SAMPLE), "缺少样例雷达 JSON：data/sample-radar-report.json"


def test_dify_dry_run():
    p = _run(os.path.join(ADAPTERS, "dify", "dify_writeback_adapter.py"),
             "--tier", "best_value", "--app-id", "DEMO", "--dry-run")
    assert p.returncode == 0, p.stderr
    payload = json.loads(p.stdout)
    assert payload["model"]["provider"] in ("openrouter", "anthropic", "openai", "google",
                                            "deepseek", "meta", "qwen")
    assert payload["model"]["mode"] == "chat"


def test_langgraph():
    p = _run(os.path.join(ADAPTERS, "langgraph", "langgraph_writeback_adapter.py"),
             "--tier", "best_quality")
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["target"] == "langgraph"
    assert "snippet" in out["config"]


def test_n8n():
    p = _run(os.path.join(ADAPTERS, "n8n", "n8n_writeback_adapter.py"),
             "--tier", "best_value")
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["target"] == "n8n"
    assert out["node"]["type"] == "n8n-nodes-base.httpRequest"


def test_otari():
    p = _run(os.path.join(ADAPTERS, "otari", "otari_writeback_adapter.py"),
             "--tier", "cheapest")
    assert p.returncode == 0, p.stderr
    # otari dry-run 默认打印 YAML 片段
    assert "radar_recommendation" in p.stdout or "model:" in p.stdout


def test_snapshot_offline():
    """离线模式需要 data/snapshots/latest.json；若已生成则验证，否则跳过。"""
    latest = os.path.join(ROOT, "data", "snapshots", "latest.json")
    if not os.path.exists(latest):
        import pytest
        pytest.skip("尚未生成离线快照（先联网跑一次 snapshot.py）")
    out_json = os.path.join(ROOT, "data", "_test_snapshot.json")
    p = subprocess.run(
        [sys.executable, os.path.join(ROOT, "radar", "snapshot.py"),
         "--offline", "--json", out_json],
        capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    data = json.loads(open(out_json, encoding="utf-8").read())
    assert "tiers" in data and data["tiers"]["best_value"]
    os.remove(out_json)
