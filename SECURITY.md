# Security Policy · 安全策略

## 报告漏洞 · Reporting a vulnerability

如果你发现安全漏洞，**请不要在 GitHub Issue 公开**，请通过以下方式私密报告：
If you find a security vulnerability, **do not open a public issue**. Report privately via:

- GitHub Security Advisory：仓库 `Security → Report a vulnerability`
- 或邮件联系维护者（见仓库 profile）

请在 90 天内不要公开披露，给维护者修复时间。
Please allow up to 90 days for a fix before public disclosure.

## 支持版本 · Supported versions

| 版本 | 支持安全更新 |
|------|--------------|
| 0.1.x | ✅ |

## 安全设计说明 · Security design notes

- **写回适配器默认 dry-run**：不会在用户未显式授权（`--apply` + 凭证）时修改任何远程配置。
  Writeback adapters are dry-run by default; no remote config is changed without explicit `--apply` + credentials.
- **零凭据硬编码**：所有 API key 通过环境变量传入（`AA_API_KEY` / `DIFY_API_KEY`），不落盘、不入库。
  No credentials are hardcoded; all keys come from environment variables.
- **只读外部 API**：雷达仅 `GET` OpenRouter / Artificial Analysis 公开端点，不发送用户数据。
  The radar only reads public endpoints; it does not send user data anywhere.
