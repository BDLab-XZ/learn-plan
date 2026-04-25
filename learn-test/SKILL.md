---
name: learn-test
description: 基于学习进度生成并启动测试 session，复用 learn-plan 目录下的 session_orchestrator.py 与 session_bootstrap.py
---

# learn-test

这是“开始阶段测试”的独立 skill 入口。

## 用途

基于 `learn-plan.md`、历史 session 与最近薄弱项，生成或继续测试 session，并自动启动本地服务、打开浏览器。

## 测试模式

支持：
- `general`
- `weakness-focused`
- `mixed`

## 执行规则

1. 确认学习根目录、测试模式与 session 保存路径（默认 `./sessions/YYYY-MM-DD-test/`）。
2. 读取 `learn-plan.md`、必要时读取 `PROJECT.md`。
3. 若测试 session 已通过完整性校验（`题集.html`、`questions.json`、`progress.json`、`server.py` 存在，且 `questions.json` / `progress.json` 结构有效），直接继续。
4. 否则先按 selective subagent strategy 让主 agent 编排必要的检索、出题、严格审题和语义审查 subagent，题目必须是 test-grade。拿到可验证 artifact 后复用：

```bash
python3 "$HOME/.claude/skills/learn-plan/session_orchestrator.py" --session-dir "<session目录>" --topic "<学习主题>" --plan-path "<learn-plan.md路径>" --session-type test --test-mode "<general|weakness-focused|mixed>" --lesson-artifact-json "<lesson-artifact.json>" --question-artifact-json "<question-artifact.json>" --question-review-json "<question-review.json>"
```

若缺出题/审题 artifact，必须阻断并补齐；CLI 验证只消费 artifact，不代替出题和审题。

5. 若已有 `questions.json` 但缺运行时文件，也可调用：

```bash
python3 "$HOME/.claude/skills/learn-plan/session_bootstrap.py" --session-dir "<session目录>" --questions "<questions.json路径>" --session-type test --test-mode "<general|weakness-focused|mixed>"
```

6. 执行后至少校验：
   - `questions.json`
   - `progress.json`
   - `题集.html`
   - `server.py`
7. 必须启动服务并打开浏览器。
8. 终端只做简短输出：
   - session 目录
   - 关键文件路径
   - 测试模式
   - 浏览器地址
   - 手动停服命令
