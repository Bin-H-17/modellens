# ModelSieve 输出模板 · Output Template

> 技能每次推荐都严格套用此模板，保证"最方便读取"。
> The skill always renders recommendations in this readable template.

---

## 一句话总结 · TL;DR
（根据用户问题，用 1–2 句话给结论。例如：*不考虑钱，闭源首选 Claude Opus 5；性价比首选 Qwen3-Max；最便宜兜底选 DeepSeek-V4-Flash。*）

## 推荐表 · Recommendations

### 🥇 最优质 / Best Quality（不考虑钱）
| 模型 | 一句话理由 | 价格($/1M) | 质量信号 | 来源 |
|------|-----------|-----------|----------|------|
| `anthropic/claude-opus-5` | AA 智能指数与 LMArena 双高，agentic 最强 | $15 / $75 | AA 57 · LMArena #1 | [AA](url) · [LMArena](url) |
| ... | ... | ... | ... | ... |

### 💰 性价比最高 / Best Value
| 模型 | 一句话理由 | 价格($/1M) | 性价比指数 | 来源 |
|------|-----------|-----------|-----------|------|
| `qwen/qwen3-max` | 质量接近前沿、价格仅零头 | $0.3 / $0.9 | 高 | [OpenRouter](url) · [AA](url) |
| ... | ... | ... | ... | ... |

### 🪙 最便宜兜底 / Cheapest
| 模型 | 一句话理由 | 价格($/1M) | 上下文 | 来源 |
|------|-----------|-----------|--------|------|
| `deepseek/deepseek-v4-flash` | 能打且近乎免费 | $0.05 / $0.15 | 128K | [OpenRouter](url) |

## 数据说明 · Data notes
- 价格时间：<UTC 时间>；来源：OpenRouter 实时 / Artificial Analysis / LMArena。
- 质量分：<真实分 AA/LMArena> 或 <启发式，非权威，已标注>。
- 任务域：<若用户指定 coding/reasoning/...，写明过滤依据>。

## ⚠️ 免责提醒 · Caveat
- 榜单有偏差，建议用你的 **20 条私有 prompt** 再做一次实测（唯一不可作弊的信号）。
- ModelSieve 是顾问，不是接管；写回工作流需你显式确认。
- 模型更替极快，本推荐仅供参考，请以各源最新数据为准。
