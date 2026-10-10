# Contributing / 贡献说明

This is a small personal project. Preserve the deliberately limited scope: one completion per project per day, no cancellation, backdating, timers, pause/resume, accounts, completion rates, or trend charts. iPhone 15 with Safari / Home Screen PWA on iOS 17+ is the primary target. The application UI is Chinese; documentation has Chinese and English entry points.

这是个人日常工具。请保持每天一次完成的规则；不添加补打、取消、计时、暂停、账号、完成率或趋势图。优先支持 iPhone 15，中文界面，中英文文档。

## Development

Use Python 3.12+ and Node.js 22.12+. See [English README](README.en.md) or [中文 README](README.md). Keep README changes synchronized across both languages. Use feature branches and focused pull requests.

Before submitting:

```bash
python -m pytest backend/tests -q
cd frontend
npm ci
npm test
npm run build
```

Run `git diff --check` from the repository root. Include regression tests for persistence, date rules, sync, and restore changes. For UI changes, check 393 × 852 portrait and 852 × 393 landscape, with long project names and keyboard input. Emulator layout checks do not replace iPhone safe-area, Safari, or offline tests.

Never commit credentials, `.env`, databases, backups, personal check-in data, `node_modules`, or `.venv`. Screenshots should contain sample data only. Changes to deployment or restore must describe data safety and migration needs.

No open-source license has been selected. Contact the owner before reuse outside GitHub's normal viewing and forking terms.
