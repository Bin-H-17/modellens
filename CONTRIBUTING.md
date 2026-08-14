# Contributing · 贡献指南

感谢你有兴趣为 ModelSieve 做贡献 · Thanks for your interest in contributing.

## 开发环境 · Dev setup

```bash
git clone <repo>
cd modellens
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest tests/ -q
```

## 跑通本地报告 · Run locally

```bash
python radar/snapshot.py --offline --html site/daily-radar-live.html
python serve.py   # http://localhost:8000/
```

## 提交规范 · Commit conventions

- 用清晰的中文或英文 commit message，说明"做了什么 + 为什么"。
- 小步提交，一次 PR 聚焦一件事。
- 新增功能请补测试（`tests/`），确保 `pytest` 全绿。

## 代码风格 · Code style

- Python 3.10+，优先用标准库；新依赖需说明必要性。
- 函数加简短 docstring；注释解释"为什么"而非"是什么"。
- 写回适配器**默认 dry-run**，不得在默认路径调用任何远程写接口。

## 报告问题 · Reporting issues

用 GitHub Issues；安全漏洞请走 `SECURITY.md` 的流程，不要在 Issue 公开。

## 许可证 · License

提交即表示你同意以 Apache-2.0 许可发布贡献。
By submitting, you agree your contributions are licensed under Apache-2.0.
