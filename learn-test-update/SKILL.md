---
name: learn-test-update
description: 基于测试 session 的 progress.json 更新当前水平判断与后续学习建议，并回写到 learn-plan.md
---

# learn-test-update

这是“测试完成后更新计划”的独立 skill 入口。

## 用途

读取测试 session 的 `progress.json`，分析测试结果，并更新 `learn-plan.md` 中的当前水平判断、薄弱项和后续学习建议。

## 执行规则

1. 确认测试 session 目录。
2. 优先读取当前目录下的 `learn-plan.md`，不要把 `PROJECT.md` 当默认状态源。
3. 主 agent 负责编排与事实核对；若需要语义审查，应使用 subagent 生成 review artifact，再交给 CLI 验证和回写。
4. 必须复用：

```bash
python3 "$HOME/.claude/skills/learn-plan/learn_test_update.py" --session-dir "<session目录>" --plan-path "<learn-plan.md路径>" --semantic-review-json "<semantic-review.json>"
```

5. 输出至少覆盖：
   - 本次测试覆盖范围
   - 总体表现
   - 薄弱项
   - 是否应回退复习
   - 是否可以进入下一阶段

6. 终端只输出简短摘要。
