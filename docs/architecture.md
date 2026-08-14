# 架构说明（Architecture）

模型筛是一个**供应商中立的模型情报 / 策略顾问层**，不碰网关 plumbing，护城河在「情报层 + 写回适配器」。

## 数据流向

```
┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────┐
│ OpenRouter API  │───▶│ radar/snapshot.py│───▶│ data/snapshots/日期.json│
│ (/api/v1/models)│    │ 解析+三档分层     │    │ (完整模型+三档缓存)    │
└─────────────────┘    └──────────────────┘    └───────────┬───────────┘
                              │  ┌──────────────────────┐    │
                              └─▶│ radar/quality_aa.py  │◀───┤ Artificial Analysis API
                                 │ (真实质量分, 优雅降级) │    │ (可选, 需 key)
                                 └──────────────────────┘    └────────────────────┘
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 ▼                            ▼                            ▼
        radar/diff.py (漂移)        报告渲染 (HTML/MD/JSON)        adapters/* (写回)
        跨日对比→换模型建议          site/daily-radar-live.*       Dify/LangGraph/n8n/otari
```

## 模块职责

| 模块 | 职责 |
|------|------|
| `radar/daily_radar_report_live.py` | 核心：拉 OpenRouter → 解析 → 三档分层（最优质/性价比/最划算）→ 渲染 |
| `radar/quality_aa.py` | 接 Artificial Analysis 真实 Intelligence Index；无 key 时启发式兜底 |
| `radar/snapshot.py` | **每日入口**：生成报告 + 缓存快照（含完整模型列表，供漂移对比）；支持 `--offline` / `--aa-key` |
| `radar/diff.py` | 两个快照对比：新增/退市/价格漂移/档位变动/换模型建议 |
| `radar/domains.py` | **任务域细分**（P2）：按名称/模态/上下文把模型分到 coding/reasoning/long-context/multimodal/general，各域独立算三档 |
| `radar/visualize.py` | **历史漂移可视化**（P2）：读快照历史生成自包含 SVG 价格趋势图（需 ≥2 份快照，否则提示累积） |
| `radar/daily_radar_report_seed.py` | 离线种子版（内置示例数据，无需联网，适合 demo） |
| `adapters/{dify,langgraph,n8n,otari}` | 把三档推荐映射为目标平台的模型配置；**默认 dry-run**，显式 `--apply` 才落盘/调 API |
| `data/sample-radar-report.json` | 真实雷达格式样例，使报告/适配器/测试完全离线可跑 |
| `data/snapshots/` | 每日快照（CI 累积 → 漂移可比） |
| `pages/index.html` + `site/` | 落地页与生成的报告 |

## 设计铁律

1. **可选接管**：写回适配器默认 dry-run，用户显式授权（API Key + App ID）才 apply；保留回退（先导出旧配置）。
2. **零网关**：不造网关，骑 otari 等开源底座。
3. **优雅降级**：真实质量分拿不到时退回启发式，并在页面明确标注来源。
4. **离线可用**：`--offline` 走缓存；样例数据保证无网也能演示与测试。

## 质量分来源说明

- 默认：基于模型家族的**经验性启发式分层**（0-100，非权威 benchmark），仅用于演示。
- 提供 Artificial Analysis key 后：`artificial_analysis_intelligence_index` 真实独立评估覆盖启发式。
- 页面 / JSON 的 `quality_source` 字段会如实标注当前用的是哪种。
