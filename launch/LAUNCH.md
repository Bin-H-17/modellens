# 部署指南 · Deploy Guide

把 ModelSieve 跑起来并发布每日报告的步骤。
Steps to run ModelSieve and publish the daily report.

## 1. 本地运行 · Local run

见 README「本地运行」。最快验证 · See README. Quickest check:

```bash
python radar/snapshot.py --offline --html site/daily-radar-live.html
python serve.py   # http://localhost:8000/
```

## 2. 发布到 GitHub + 每日报告 · Publish to GitHub + daily report

- [ ] 新建 GitHub 仓库（Public）· Create a public repo
- [ ] 推送代码（首次 push 后 Actions 自动跑首次构建）· Push code (Actions runs on first push)
- [ ] 开启 Pages：`Settings → Pages → Source: GitHub Actions`
- [ ] 报告上线 · Report live at `https://<username>.github.io/<repo>/`
- [ ] （可选 · optional）`Settings → Secrets → Actions` 添加 `AA_API_KEY`，升级真实质量分 · add `AA_API_KEY` for real quality scores

## 3. 分发用户问卷 · Distribute survey（可选 · optional）

问卷见 `docs/interview-questionnaire.md`，用于验证需求假设。
The questionnaire in `docs/interview-questionnaire.md` validates demand assumptions.

> 生成报告、部署 Pages 由 GitHub Action 自动完成，无需日常维护。
> Report generation and Pages deployment are automated by GitHub Actions — no daily maintenance needed.
