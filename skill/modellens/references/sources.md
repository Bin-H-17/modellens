# ModelSieve 数据源清单 · Source Catalog

> 双语（中 / EN）。本文件是技能聚合情报的"原料库"——每个源的访问方式、提供什么、局限。
> Bilingual. The raw-material catalog the skill aggregates from: how to access, what it gives, limitations.

---

## 1. OpenRouter · 实时价格与可用性
- **用途 / Use**: 最可靠的实时价格与可用性信号（340+ 模型真实 $/1M、上下文长度、模态）。
- **访问 / Access**: `GET https://openrouter.ai/api/v1/models`（免费、无需 key）。
- **本仓集成 / Repo integration**: `radar/snapshot.py` 直接拉取并解析；`--offline` 走 `data/snapshots/` 缓存。
- **字段 / Fields**: `pricing.prompt` / `pricing.completion`（每 token），`context_length`，`top_provider.max_completion_tokens`，`architecture.modality`，`id`。
- **局限 / Limits**: 仅含在 OpenRouter 上架的模型；价格是路由价，非厂商直供。

## 2. Artificial Analysis · 智能指数 + 速度 + 价格
- **用途 / Use**: 独立测量的 Intelligence Index（综合智能）、输出速度(tokens/s)、价格；按模型大小筛选，性价比比较极佳。
- **访问 / Access**: 官网榜单 `artificialanalysis.ai/leaderboards/models` 公开；API 需免费 key（`x-api-key` 头，`AA_API_KEY`），约 1000 req/day。
- **本仓集成 / Repo**: `radar/quality_aa.py` 调用并落 `artificial_analysis_intelligence_index`；无 key 时启发式兜底。
- **局限 / Limits**: 闭源模型覆盖好，极新或冷门模型可能滞后；指数方法论见其官网 v4.1。

## 3. LMArena (原 Chatbot Arena) · 人类偏好 Elo
- **用途 / Use**: 真实用户盲测 A/B 投票产生的 Elo，最贴近"用起来感觉"，能抓 benchmark 抓不到的真实位移。
- **访问 / Access**: 免费 API + 每日 JSON 快照；`arena-rank` PyPI 包可本地复现排名；`lmarena.ai/leaderboard` 分任务榜（文本/代码/多模态）。
- **局限 / Limits**: 投票者偏英语技术用户，顶部噪声敏感；部分类目票数少、统计不稳；闭源新模型需积满约 1000 票才上榜。

## 4. LiveBench · 抗污染能力榜
- **用途 / Use**: 每月从新论文/新闻出新题，防 benchmark gaming；覆盖数学/代码/推理。
- **访问 / Access**: `livebench.ai` 官网榜单。
- **用法 / Use with**: 与 AA、LMArena 互补——一个模型同时出现在多个榜单 top 才可信。

## 5. SWE-bench Verified / Aider Polyglot · 代码专项
- **用途 / Use**: agentic coding（SWE-bench Verified）与编辑器式多语言编码（Aider Polyglot）的金标准。
- **访问 / Access**: `swebench.com` / Aider 文档；选 coding 模型必看这两个，而非裸 HumanEval。

## 6. r/LocalLLaMA (Reddit) · 社区实测
- **用途 / Use**: 真机量化翻车、Apple Silicon 可用性、诚实的"能本地跑"声明——benchmark 给不了的信息。
- **访问 / Access**: WebSearch「r/LocalLLaMA <模型名>」；看每周 "best models" megathread 与针对硬件的搜索。
- **用法 / Caveat**: 观点化、偶有错，但信息密度最高；作交叉印证，不作唯一依据。

## 7. Hugging Face Trending / Daily Papers / LLM Stats · 新发布追踪
- **用途 / Use**: 24h 内新模型、社群反应、模型发布新闻聚合。
- **访问 / Access**: `huggingface.co/models` Trending、`huggingface.co/papers`、LLM Stats (`llm-stats.com`)。
- **推荐策略 / Pipeline**: LLM Stats 追新发布 → HF Trending 看反应 → AA/LMArena 比数字 → r/LocalLLaMA 看实测。

## 8. Vellum / Onyx · 开源权重聚合
- **用途 / Use**: 仅开源权重的横向比较；Onyx 提供最佳自托管榜单视角。
- **访问 / Access**: `vellum.ai/llm-leaderboard`、`onyx` 项目。

---

## 已退役/慎用的榜 · Retired / use-with-care
- Hugging Face Open LLM Leaderboard（已退役）——开源权重槽位现由 Artificial Analysis Intelligence Index 接替。
- 裸 HumanEval / HellaSwag / 朴素 NIAH：已饱和或被污染，2026 年不要再当头条数字。

## 黄金法则 · Golden rules
1. 厂商自吹的 benchmark = 营销，除非独立榜单 corroborate。
2. 多源交叉：一个模型同时出现在 AA + LMArena + LiveBench 的 top 才可信。
3. 最终在你的 20 条私有 prompt 上实测——这是唯一不可作弊的信号。
