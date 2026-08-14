---
name: modellens
description: >-
  按需聚合多源大模型情报（实时价格 / 质量指数 / 社区实测），按"最优质 / 性价比最高 /
  不考虑钱 / 最便宜兜底"分档推荐，并以最易读的形式呈现。当用户问"推荐个模型""哪个模型性价比
  最高""不考虑钱用哪个""便宜又能打的模型"时触发。Triggers on requests like "recommend a model",
  "best value LLM", "best quality regardless of cost", "cheapest model that works".
---

# ModelSieve · 模型筛

> 供应商中立的「模型情报 / 策略顾问层」。不做网关，只做**情报聚合 + 分档推荐 + 易读呈现**。
> Vendor-neutral model-intelligence layer. Not a gateway — only aggregation, tiered recommendation, readable output.

## 何时使用 · When to use

- 用户要**选型建议**："给我推荐个模型""写代码用哪个""性价比最高的""不考虑钱用最好的"。
- 用户要**横向对比**："Claude 和 GPT 哪个值""这个价位有没有更好的"。
- 用户要**价格/质量情报**："现在哪个模型最便宜""最新发布有哪些值得看"。
- 用户要**把推荐落到工作流**（可选）：配合 `adapters/` 把三档写回 Dify / LangGraph / n8n / otari。

## 核心定位 · Positioning

- **白空间**：情报层 + 写回适配器。网关/路由（OmniRoute、LiteLLM、otari）已是红海，我们不重复造。
- **可解释、可回退**：每个推荐都给出来源链接与一句话理由；用户随时知道"为什么选它"，且能改回。
- **永远标注权威性**：实时价格来自 OpenRouter（可靠）；质量分优先用 Artificial Analysis / LMArena，
  否则明确标注"启发式/社区信号，非权威 benchmark"。

## 数据源矩阵 · Source matrix

| 维度 | 权威源 | 访问方式 | 提供什么 | 备注 |
|------|--------|----------|----------|------|
| 实时价格 / 可用性 | **OpenRouter** `/api/v1/models` | 免费、无需 key；本仓 `radar/snapshot.py` 直接拉 | 340+ 模型真实 $/1M、上下文、模态 | 最可靠的价格信号 |
| 质量指数 | **Artificial Analysis** Intelligence Index | 官网榜单公开；API 需免费 key（`AA_API_KEY`） | 综合智能指数、速度(tokens/s)、价格 | 本仓 `radar/quality_aa.py` 已集成，无 key 时启发式兜底 |
| 人类偏好 | **LMArena** (原 Chatbot Arena) | 免费 API + 每日 JSON 快照；`arena-rank` PyPI 可复现 | Elo 人类偏好分（最贴近"用起来感觉"） | 分任务榜（文本/代码/多模态） |
| 抗污染能力榜 | **LiveBench** (livebench.ai) | 官网；月度刷新题 | 数学/代码/推理，防 benchmark gaming | 与 AA/LMArena 互补 |
| 代码专项 | **SWE-bench Verified** / **Aider Polyglot** | 官网榜单 | agentic  coding / 编辑器式编码 | 选 coding 模型看这两个 |
| 社区实测 | **r/LocalLLaMA** (Reddit) | WebSearch / WebFetch | 量化翻车、真机可用性、Apple Silicon 等 | 信号噪声比最高的论坛 |
| 新发布追踪 | **Hugging Face Trending** / **Daily Papers** / **LLM Stats** | WebSearch | 24h 内新模型、社群反应 | 追新发布用 |
| 开源权重聚合 | **Vellum** / **Onyx** open-weight leaderboard | 官网 | 仅开源权重的横向比较 | 自托管视角 |

> 完整访问细节见 `references/sources.md`（双语）。

## 工作流程 · Workflow

**1. 解析意图 · Classify intent**
- `best_quality` / `不考虑钱` → 质量上限最高（AA Intelligence Index + LMArena Elo 双高）。
- `best_value` / `性价比最高` → 质量/价格 最优（用实时价格算性价比指数）。
- `cheapest` / `最便宜兜底` → 价格最低且能完成任务。
- 若用户指定任务域（coding / reasoning / long-context / vision），叠加任务榜过滤。

**2. 拉取实时数据 · Gather（按需，优先实时）**
- 价格/可用性：**直接运行** `python radar/snapshot.py`（联网拉 OpenRouter；或 `--offline` 走缓存）。
- 质量分：优先 Artificial Analysis（有 key 时 `radar/quality_aa.py` 自动用真实分）；否则 WebFetch LMArena / AA 榜单。
- 社区/新发布：WebSearch「r/LocalLLaMA <模型>」或「<模型> benchmark 2026」。
- 能用结构化 API 就别只靠网页摘要；多源交叉验证，避免单一厂商自吹。

**3. 排名 · Rank**
- 质量档：AA Intelligence Index 降序为主，LMArena Elo 作交叉印证。
- 性价比档：`性价比指数 = 质量分 / 平均价格`，取 top。
- 便宜档：实时 $/1M 升序，剔除明显玩具模型（上下文<8K 或已退市）。
- 每个入选模型附**一句话理由 + 来源链接**。

**4. 呈现 · Present**
- 严格使用 `references/output-template.md` 的易读模板（表格 + 一句话总结 + 免责声明）。
- 默认输出 Markdown 表格；若用户要"看"而非"读"，可用 Visualizer 渲染对比卡片。
- **永远附**：① 数据时间/来源；② "建议在你的真实任务上再做 20 条私有评测" 的提醒。

## 边界与免责 · Caveats

- 质量分若非来自 AA/LMArena，必须明确写"启发式/社区信号，非权威"。
- 榜单有偏差（LMArena 偏英语技术用户、闭源新模型覆盖稀疏）——交叉印证，不盲信单一源。
- 我们不替用户做"全自动接管"；推荐是顾问，最终决策与写回需用户显式确认。

## 与仓库其他部分的关系 · Repo map

- `radar/snapshot.py`：每日入口，拉价格+三档+缓存快照。
- `radar/diff.py`：跨日漂移对比（价格波动/退市/换模型建议）。
- `radar/quality_aa.py`：Artificial Analysis 真实质量分接入。
- `adapters/{dify,langgraph,n8n,otari}`：把三档写回用户工作流（默认 dry-run）。
- 更多设计细节见 `docs/architecture.md` 与 `docs/roadmap.md`。
