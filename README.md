# ModelSieve · 模型筛 / Model Intelligence & Writeback Layer

> **中文**：供应商中立的「模型情报 / 策略顾问层」——不做网关，只做**情报聚合 + 分档推荐 + 写回适配器**。
> 监测全网模型质量/价格漂移，按任务域给三档推荐，可解释、可回退、零配置。你一问，它就聚合多源情报给你推荐。
>
> **EN**: A vendor-neutral model-intelligence / strategy-advisor layer. Not a gateway — only **intelligence aggregation + tiered recommendation + writeback adapters**. Tracks quality/price drift across the model landscape and recommends three tiers per task; explainable, reversible, zero-config. Ask once, it aggregates multi-source intelligence and recommends.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Live Report](https://img.shields.io/badge/daily%20report-Pages-success)](https://modelsieve.github.io/modellens/)

---

## 为什么存在 · Why it exists

**中文**：过去两年有 **199 次前沿模型发布、300+ 可用模型**，同一任务的有效成本差可达 **30×**。但没有任何一个供应商中立的工具告诉你：今天哪个模型在你的任务上**最优质**？哪个**性价比最高**？哪个**最便宜能兜底**？更没有人把答案**写回**你已在用的工作流（Dify / LangGraph / n8n / otari）。

**EN**: In the last two years there were **199 frontier model releases and 300+ usable models**; effective cost for the same task can differ by **30×**. Yet no vendor-neutral tool tells you: which model is **best quality** for your task today? which has the **best value**? which is **cheapest but still works**? And nobody writes the answer back into the workflow you already use (Dify / LangGraph / n8n / otari).

**ModelSieve 只做两件事 · ModelSieve does only two things**: ① 情报层（雷达）· intelligence layer (radar)；② 写回适配器 · writeback adapters。网关/路由的 plumbing 直接骑在 [otari](https://github.com/otari-ai/otari)（Apache-2.0）等开源底座上，我们**不重复造网关** · gateway plumbing rides on open-source bases like otari; we **don't rebuild the gateway**.

---

## 三档推荐 · Three tiers

| 档位 Tier | 含义 Meaning | 典型用途 Typical use |
|-----------|--------------|----------------------|
| `best_quality` | 当前质量上限最高的模型 · highest quality ceiling | 关键任务、对质量要求高的生成 · critical / high-quality generation |
| `best_value` | 质量/价格 性价比最优 · best quality-per-dollar | 日常主力、规模化调用 · daily workhorse, scale calls |
| `cheapest` | 价格最低、能兜底 · lowest cost, still works | 高容错、批量、内部 · tolerant / batch / internal |

---

## 架构 · Architecture

```
OpenRouter /api/v1/models  ──▶  radar/snapshot.py (统一每日入口)  ──▶  site/daily-radar-live.{html,md,json}
                                        │  ├─ 解析 + 三档分层                                      │
                                        │  ├─ quality_aa.py (AA 真实质量分, 启发式兜底)             ▼
                                        │  └─ 缓存快照 data/snapshots/日期.json        adapters/<target>_writeback_adapter.py
                                        │                                                    │
                              radar/diff.py (跨日漂移对比) ◀── 快照历史                        ▼
                                                                          Dify / LangGraph / n8n / otari  model-config
```

- **情报层（开源）· Intelligence (OSS)**：`radar/snapshot.py` 拉取实时价格与（可选）真实质量分，输出三档并缓存快照；`radar/diff.py` 做跨日漂移对比。
- **写回层（开源）· Writeback (OSS)**：`adapters/{dify,langgraph,n8n,otari}` 把三档映射成各平台 model-config，默认 dry-run，可 `--apply` 实跑。
- **托管报告（免费）· Hosted report (free)**：GitHub Actions 每日生成 → GitHub Pages 自动更新（CI 已写好，发布待你执行 `launch/LAUNCH.md`）。
- **推荐技能（开源）· Recommendation skill (OSS)**：`skill/modellens/` —— 你一问，它聚合多源情报（OpenRouter/AA/LMArena/社区）分档推荐，详见下方「按需推荐技能」。

---

## 按需推荐技能 · On-demand recommendation skill

**中文**：`skill/modellens/` 是一个 WorkBuddy 技能。你只要问"推荐个模型 / 哪个性价比最高 / 不考虑钱用哪个"，它就自动去各平台、论坛、权威测试源（价格、Artificial Analysis 智能指数、LMArena 人类偏好、LiveBench、r/LocalLLaMA 等）聚合情报，按档位推荐，并以最易读的形式（表格 + 一句话理由 + 来源链接）呈现。数据源明细见 `skill/modellens/references/sources.md`，输出模板见 `references/output-template.md`。

**EN**: `skill/modellens/` is a WorkBuddy skill. Ask "recommend a model / best value / best regardless of cost" and it auto-aggregates from platforms, forums, and authoritative benchmarks (prices, Artificial Analysis Intelligence Index, LMArena human preference, LiveBench, r/LocalLLaMA…), recommends by tier, and presents in the most readable form (table + one-line rationale + source links). Source details: `skill/modellens/references/sources.md`; output template: `references/output-template.md`.

**安装 · Install**: 把 `skill/modellens/` 复制到你的 `~/.workbuddy/skills/modellens/`（用户级）或项目 `.workbuddy/skills/modellens/`（项目级）即可。

---

## 本地运行 · Local run

```bash
# 1. 生成报告 + 快照（联网；或用 --offline 走缓存，完全离线）
python radar/snapshot.py --json site/daily-radar-live.json --html site/daily-radar-live.html
#    （离线示例）python radar/snapshot.py --offline --html site/daily-radar-live.html

# 2. 跨日漂移对比（默认取 data/snapshots 最近两份）
python radar/diff.py --md data/drift.md

# 3. 写回适配器（dry-run 默认，不调用任何远程 API）
python adapters/dify/dify_writeback_adapter.py --radar data/sample-radar-report.json --tier best_value --app-id DEMO --dry-run
python adapters/langgraph/langgraph_writeback_adapter.py --radar data/sample-radar-report.json --tier best_quality
python adapters/n8n/n8n_writeback_adapter.py --radar data/sample-radar-report.json --tier best_value
python adapters/otari/otari_writeback_adapter.py --radar data/sample-radar-report.json --tier cheapest

# 4. 测试 & 本地预览
python -m pytest tests/ -q
python serve.py   # 打开 http://localhost:8000/

# 5. 任务域细分档位（P2）：每个任务域独立三档 → site/domains.json
python radar/snapshot.py --offline --domains site/domains.json

# 6. 历史漂移可视化（P2）：生成自包含 SVG 趋势图（需 ≥2 份历史快照）
python radar/visualize.py --out site/drift-chart.svg
```

四个写回适配器（`dify` / `langgraph` / `n8n` / `otari`）**均已交付并验证** · all four writeback adapters are delivered and verified.

---

## 质量分说明 · On quality scores

- **中文**：开源版默认使用**启发式质量分层**（基于模型家族/规模的经验估计，**非权威 benchmark**，页面已标注）。接 [Artificial Analysis](https://artificialanalysis.ai/) 真实质量分后，作为 Premium 能力（详见 `docs/quality.md`）。质量分永远可解释、可回退——你随时知道为什么选了某个模型，且能一键改回。
- **EN**: The OSS build defaults to a **heuristic quality tier** (experience-based on family/scale, **not an authoritative benchmark**, labeled on the page). Real scores from [Artificial Analysis](https://artificialanalysis.ai/) become a Premium capability (see `docs/quality.md`). Scores are always explainable and reversible.

---

## 与 otari 的关系 · Relation to otari

**中文**：otari 是 Apache-2.0 的模型路由/网关底座。ModelSieve **不 fork、不竞争**，而是：情报层输出三档 → 通过 otari 的 policy/route 接口写回。我们专注白空间（雷达 + 写回），网关 plumbing 交给成熟开源项目。
**EN**: otari is an Apache-2.0 routing/gateway base. ModelSieve **doesn't fork or compete** — intelligence outputs three tiers → written back via otari's policy/route interface. We focus on the white space (radar + writeback); gateway plumbing goes to mature OSS.

---

## 路线图 · Roadmap

| 阶段 Phase | 内容 Content | 状态 Status |
|------------|--------------|-------------|
| P0 | 开源仓库 + 四写回适配器 + 快照/漂移引擎 + 测试 · repo + adapters + drift engine + tests | ✅ 已交付（本地）delivered (local) |
| P0 | 免费每日报告 (Pages) · free daily report | ⛔ 工程就绪，发布待你（见 `launch/LAUNCH.md`）ready, awaiting you |
| P0 | 按需推荐技能 · on-demand recommendation skill | ✅ 已交付 delivered |
| P1 | 接 Artificial Analysis 真实质量分 · real AA quality | 代码就绪，待 key code ready, needs key |
| P1 | 问卷验证 H1/H2 → 更新 PRD · survey validation | 待人发问卷 awaiting survey |
| P2 | 任务域细分档位 / 漂移可视化 · task-domain tiers / drift viz | ✅ 已交付 delivered |
| P2 | 多工作流写回 / 企业中立 SLA · multi-workflow writeback / SLA | 待 traction awaiting traction |

---

## 贡献 · Contributing

Apache-2.0，欢迎 PR。重点白空间：新适配器、新数据源、质量分校准。· Apache-2.0, PRs welcome. White space: new adapters, new data sources, score calibration.

## 许可证 · License

[Apache-2.0](LICENSE)（权威文本为英文；中文说明见 [LICENSE.zh.md](LICENSE.zh.md)）。内核永远开源、可审计、可 self-host。· Apache-2.0 (authoritative text in English; Chinese summary in [LICENSE.zh.md](LICENSE.zh.md)). Core stays open, auditable, self-hostable.

Copyright (c) 2026 ModelSieve contributors.
