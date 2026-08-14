# Changelog

本项目遵循语义化版本 · This project follows Semantic Versioning.

## [0.1.0] - 2026-08-14

### Added
- 雷达生成器：实时拉取 OpenRouter 全量模型价格，输出三档推荐（最优质 / 性价比 / 最划算）。
  Radar generator: live OpenRouter prices → three-tier recommendation (best quality / best value / cheapest).
- 任务域细分档位：coding / reasoning / long-context / multimodal / general 各域独立三档。
  Task-domain tiers: per-domain three-tier ranking.
- 历史漂移监控：每日快照缓存 + 跨日对比（新增/退市/价格漂移/换模型建议）+ SVG 趋势可视化。
  Drift monitoring: daily snapshots + cross-day diff + SVG trend chart.
- 四个写回适配器：Dify / LangGraph / n8n / otari，默认 dry-run，显式 `--apply` 才落盘。
  Four writeback adapters, dry-run by default.
- Artificial Analysis 真实质量分接入，无 key 时启发式优雅降级。
  Real quality scores from Artificial Analysis with graceful fallback.
- GitHub Actions 每日生成报告 → GitHub Pages。
  Daily report via GitHub Actions → Pages.
- 按需推荐技能（`skill/modellens`）：聚合多源情报，按需分档推荐。
  On-demand recommendation skill.
- 离线自包含样例 + pytest 套件。
  Offline sample data + pytest suite.

### Notes
- 质量分默认为启发式（非权威 benchmark），页面已标注；接入 AA key 后为真实评估。
  Quality scores are heuristic by default (labeled on page); real when AA key provided.
