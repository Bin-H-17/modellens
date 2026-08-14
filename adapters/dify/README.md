# Dify 写回适配器（原型）

把「模型筛每日报告」推荐的模型档位，映射成 Dify 应用的模型配置并应用。

> 状态：原型（未在生产 Dify 实跑过）。默认 `--dry-run`，请先检查产物再决定实跑。

## 它解决什么
产品的白空间是「**写回适配器**」——把推荐的模型配置自动落回用户已有的工具。
Dify 是第一个落地目标（用户决策：Dify 优先）。网关 plumbing 骑 otari（Apache-2.0），本适配器不碰网关层。

## 前置
1. 先用实时报告生成 JSON：
   ```bash
   python daily_radar_report_live.py --json daily-radar-live.json
   ```
2. 安装请求库（仅实跑需要）：`pip install requests`

## 使用
```bash
# dry-run：仅生成 payload，不调 API
python dify_writeback_adapter.py \
    --radar ../daily-radar-live.json \
    --tier best_value \
    --app-id <DIFY_APP_ID> \
    --out dify_writeback_payload.json

# 实跑：需 DIFY_API_KEY（环境变量或 --api-key）
python dify_writeback_adapter.py \
    --radar ../daily-radar-live.json --tier best_value \
    --app-id <DIFY_APP_ID> --api-key <KEY> --apply
```

## 档位说明
- `best_quality` 最优质（只看质量，不限成本）
- `best_value`   性价比日常（质量/成本最优平衡）← 默认
- `cheapest`     最划算小/批量（质量≥70 前提下最便宜）

## Provider 映射
- `--provider-mode openrouter`（默认）：Dify 用 openrouter provider，name=原始 OpenRouter ID，**任意模型可映射，最稳**。
- `--provider-mode native`：尝试映射到 Dify 原生 provider（anthropic/claude-... 等），覆盖常见家族，兜底仍用 openrouter。

## 重要限制（已知）
- **基础 Chat App**：走 `POST /v1/apps/{app_id}/model-config`，可整体改默认模型。
- **Workflow App**：模型是「LLM 节点」级的，没有单一 app 级端点。本适配器对 workflow 仅产出 payload，**需你在 Dify Studio 手动贴到对应 LLM 节点**（或后续扩展为按 node ID 更新）。
- **回退**：应用前请先在 Dify 导出当前 App 配置，以便一键回退（满足「可选接管 + 回退」铁律）。
- **质量分**：来自启发式，非权威 benchmark；接 artificialanalysis 真实分后替换。

## 下一步
- [ ] 在真实 Dify 基础 Chat App 上验证 model-config 端点
- [ ] 扩展 workflow 按 node ID 写回
- [ ] LangGraph / otari 写回适配器（同模式复用）
