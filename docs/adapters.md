# 写回适配器（Adapters）

ModelSieve 的情报层产出三档推荐（JSON），写回层把它映射到各平台的 model-config。
所有适配器统一接口：

```bash
python adapters/<target>/<target>_writeback_adapter.py \
    --radar daily-radar-live.json \
    --tier {best_quality|best_value|cheapest} \
    --out payload.json          # 写出配置文件
    [--apply]                   # Dify=真实 API 写回；其余=落盘配置片段
```

`--tier` 默认 `best_value`（日常性价比档）。

## 已交付

### Dify（`adapters/dify/`）✅
真实写回：调用 Dify API 修改 App 的 model 配置。
需环境变量 `DIFY_BASE_URL`、`DIFY_API_KEY`，以及 `--app-id`。
`--apply` 才会真正改写；默认 dry-run 只生成 payload。

### LangGraph（`adapters/langgraph/`）
生成 LangChain `ChatOpenAI` 配置片段（OpenRouter 兼容 OpenAI 协议）。
无远程 API，`--apply --out` 落盘 `config.json`（含可粘贴的 Python snippet）。

### n8n（`adapters/n8n/`）
生成 n8n HTTP Request 节点 JSON，指向 OpenRouter chat completions 并设定 `model`。
粘贴进 n8n 工作流即可。`--apply --out` 落盘节点 JSON。

### otari（`adapters/otari/`）
otari（mozilla-ai/otari，Apache-2.0）模型格式为 `provider:model`。
适配器把 OpenRouter `id` 的 `/` 转成 `:`，输出可直接用于 otari client / config.yml。
`--apply --out xxx.yaml` 落盘 YAML 片段。

## 扩展新适配器
照葫芦画瓢：读雷达 JSON → `tiers[tier][0]` 取首选模型 → 映射为目标平台 config →
默认 dry-run 打印，可选 `--apply` 落盘或调 API。统一放在 `adapters/<target>/`。
