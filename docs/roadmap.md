# 路线图（Roadmap）

> 阶段划分基于「曝光优先、零运营精力」约束。
> 标 ⛔ 的需人介入（已暂停 push，待用户执行 `launch/LAUNCH.md`）。

## Phase 0 · 情报内核（✅ 已完成，本地）
- [x] 实时报告生成器（OpenRouter 价格 + 三档分层）
- [x] 真实质量分接入（Artificial Analysis，优雅降级）
- [x] 四个写回适配器（Dify / LangGraph / n8n / otari），默认 dry-run
- [x] 样例数据 + 离线模式 + 测试套件
- [x] 本地预览（serve.py）

## Phase 1 · 每日自动雷达（⛔ 发布待用户，工程已就绪）
- [x] `snapshot.py` 每日缓存快照
- [x] `diff.py` 跨日漂移对比
- [x] GitHub Actions 每日生成 → Pages（CI 已写好，未激活）
- [ ] ⛔ 用户建仓 + push + 开 Pages（按 LAUNCH.md 阶段一）
- [ ] ⛔ 填 `AA_API_KEY` secret（升级真实质量分）

## Phase 2 · 验证需求（⛔ 待人发问卷）
- [ ] ⛔ 问卷分发（H1：是否每日看报告；H2：是否愿写回）— `docs/interview-questionnaire.md` + `launch/distribution.md`
- [ ] 回收后更新 PRD 优先级（`docs/strategy/mvp-prd.md`）

## Phase 3 · 深化护城河（可自主推进）
- [x] 任务域细分档位（`radar/domains.py`）：coding / reasoning / long-context / multimodal / general 各自独立三档（启发式分桶；真实能力以 LMArena / AA 分任务榜为准，见技能）
- [x] 历史漂移可视化（`radar/visualize.py`）：自包含 SVG 价格趋势图（需 ≥2 份历史快照，否则提示累积）
- [ ] LangGraph / n8n / otari「真实 apply」路径（如 otari 有 config API 可补实写）
- [ ] 多快照聚合看板（价格/质量随时间的中位数与极值）

## Phase 4 · 变现（仅当 traction + 精力具备）
- [ ] 真实质量分作为 Premium（开源版保持启发式）
- [ ] 多工作流写回 / 企业中立 SLA
- [ ] 托管写回服务（免自托管，面向非技术用户）

## 明确不做（Non-goals）
- 不自研网关
- 不做 API 转售抽成
- 不做需每日运营的托管付费服务
