# 质量分：启发式 vs 真实（Artificial Analysis）

ModelSieve 的三档推荐依赖「质量分」。当前有两档来源：

## 1. 启发式（默认，无需 key）
`radar/daily_radar_report_live.py` 里的 `heuristic_quality()` 按模型家族给 40–98 的经验分：
`opus`/`gpt-5` 高，`flash`/`mini`/`free` 低。**仅为演示用，非权威 benchmark**。
页面会明确标注「质量分为经验性启发式」。

## 2. 真实质量分（Artificial Analysis，推荐用于可交付版）
[Artificial Analysis](https://artificialanalysis.ai/) 提供**免费 API**（1000 req/day），
返回独立评估的 `artificial_analysis_intelligence_index`。

### 获取 key
1. 注册 [Artificial Analysis Insights Platform](https://artificialanalysis.ai/)
2. 生成 API key
3. 本地：`python radar/daily_radar_report_live.py --json out.json --aa-key <KEY>`
4. CI：在仓库 `Settings → Secrets` 添加 `AA_API_KEY`，工作流自动启用（见 `.github/workflows/daily-radar.yml`）

### 匹配逻辑
`radar/quality_aa.py` 把 AA 的 `name`/`slug` 归一化后与 OpenRouter 模型名匹配。
OpenRouter 名称常含 provider 前缀（如 `Anthropic: Claude Opus 4`），脚本会自动去前缀再匹配。
未匹配到的长尾模型**保留启发式兜底**。

### 已知局限
- AA 与启发式量纲接近但非完全一致；混合使用时长尾模型排序可能略偏。
- 后续可对所有模型统一用 AA 的归一化百分位，彻底去掉启发式。

## 3. 为什么不直接用 AA 当唯一来源？
AA 免费档有速率限制（1000 req/day）且需 key。雷达默认**零配置可跑**（启发式），
真实质量分作为「填 key 即升级」的可选层——这与「曝光优先、零运营」定位一致：
开源用户零门槛，想要权威分自己填 key 即可。
