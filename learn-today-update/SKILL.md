---
name: learn-today-update
description: 基于当日 session 的 progress.json 汇总学习结果，并回写到 learn-plan.md
---

# learn-today-update

这是“完成今日学习后更新计划”的独立 skill 入口。

## 用途

读取当日 session 的 `progress.json`，汇总本次学习结果，并将结果回写到 `learn-plan.md` 的学习记录区块。

## 执行规则

1. 确认要汇总的 session 目录。
2. 优先读取当前目录下的 `learn-plan.md`，不要把 `PROJECT.md` 当默认状态源。
3. 主 agent 负责编排与事实核对；若需要语义总结，应使用 subagent 生成 summary artifact，再交给 CLI 验证和回写。
4. 必须复用：

```bash
python3 "$HOME/.claude/skills/learn-plan/learn_today_update.py" --session-dir "<session目录>" --plan-path "<learn-plan.md路径>" --semantic-summary-json "<semantic-summary.json>"
```

5. 汇总至少包含：
   - 主题
   - 总题数
   - 已练习题数
   - 正确/通过题数
   - 高频错误点
   - 下次复习重点
   - 下次新学习建议

6. 终端只输出简短摘要，不展开长报告。
