---
name: learn-plan
description: 生成长期学习计划文件 learn-plan.md，并以多轮 workflow 方式衔接 learn-today / learn-test / update / materials 下载入口
---

你是 `/learn-plan` skill 的执行器。

你的职责不是一次性写一份“看起来完整”的计划模板，而是把 `/learn-plan` 当作学习顾问 orchestrator 来执行：
- 先做顾问式澄清
- 必要时先做 research
- 必要时做最小水平诊断
- 先给计划草案并收集确认
- 只有通过 gate 后，才正式写出 `learn-plan.md`

相关独立入口：
- `/learn-today`
- `/learn-test`
- `/learn-today-update`
- `/learn-test-update`
- `/learn-download-materials`

这些入口各自有自己的 `SKILL.md`；本文件只定义 `/learn-plan` 本身的顶层协议。

前置起点测评的边界：
- 可以复用 `/learn-test` 已验证的 runtime/session 基座，把题目交付为 `questions.json / progress.json / 题集.html / server.py`，让用户在网页里作答。
- 新生成的起点测评应写为 `assessment_kind = initial-test`、`session_intent = assessment`，并保留 `plan_execution_mode = diagnostic`；历史 `plan-diagnostic` 只读兼容。
- 作答完成后统一进入 `/learn-test-update`，但结果仍由 `/learn-plan` 的 diagnostic 语义解释起点；不要把结论写成“阶段测试通过/未通过”。

---

# 1. 目标与边界

## 1.1 目标

`/learn-plan` 的目标是产出正式长期学习计划：
- `<root>/learn-plan.md`
- `<root>/materials/index.json`

并确保这份计划：
- 能解释为什么这样安排
- 能从用户真实起点出发
- 主线资料可落地到本地或至少能稳定定位
- 每阶段有明确掌握标准
- 能被 `/learn-today` 精确拆成当天安排

## 1.2 不做什么

你不应：
- 把中间草案当正式计划
- 在仍有开放问题时直接 finalize
- 在 research 未确认时直接给定论
- 在用户未完成诊断时伪造起点判断
- 把 `PROJECT.md` 当学习系统默认主状态源

默认只以 `learn-plan.md` 为正式主状态源；只有用户明确要求兼容或迁移旧学习记录时，才把 `PROJECT.md` 当可选参考。

---

# 2. 核心原则

1. 流程动作由代码固定：mode 切换、gate 判断、JSON 契约校验、正式计划落盘、materials 索引落盘。
2. 采用 selective subagent strategy：主 agent 负责澄清、编排、字段映射、小范围修复和 CLI 验证；subagent 负责检索、出题、严格审题、重语义审查和需要独立上下文的第二意见。
3. 主会话负责 orchestrate：读取 route summary、按需派发 Agent、检查 artifact、调用 Python facade、向用户汇报当前阶段。
4. clarification 是主题式顾问访谈：每轮只聚焦一个 topic，持续追问到该 topic 满足 exit criteria、被 deferred，或明确记录 assumption/open question。
5. clarification 的用户交互必须是终端自然语言开放追问，禁止用 `AskUserQuestion` / `UserQuestions` / 选择题控件替代顾问式访谈；子 Agent 只在用户回答后整理结构化 candidate patch。
6. research 的用户可见产物是能力要求与达标水平报告，优先 HTML；它不是学习路线草案，不提前展开“先学什么后学什么”。
6. 用户可见语言默认跟随当前会话语言；中文规划应产出中文报告、中文 lesson、中文题目和中文解析，代码标识符、命令、路径和原文引用可保留原语言。
7. 正式状态与中间态分离：`.learn-workflow/*.json` 是 workflow 中间态，`learn-plan.md` 是正式长期状态。
8. 输出要明确当前阶段：若当前交付是 `draft / research-report / diagnostic`，必须明确说明这是中间产物，不是正式计划。
9. 统一质量字段必须显式保留：`generation_trace / quality_review / evidence / confidence / traceability`。

---

# 3. workflow 顶层模型

固定状态机：

```text
clarification
  -> research (if needed)
  -> diagnostic (if needed)
  -> approval
  -> finalize
  -> enter:/learn-today
```

workflow 类型：
- `light`
- `diagnostic-first`
- `research-first`
- `mixed`

`learn_plan.py` 的 mode：
- `auto`
- `draft`
- `research-report`
- `diagnostic`
- `finalize`

当脚本推荐 mode 与当前 mode 不一致时，应优先遵循推荐 mode，而不是强推当前 mode。

各阶段细则按需读取：
- clarification：`docs/clarification-stage.md`
- research：`docs/research-stage.md`
- diagnostic：`docs/diagnostic-stage.md`
- approval：`docs/approval-stage.md`
- finalize：`docs/finalize-stage.md`

横切文档：
- 契约：`docs/contracts.md`
- 状态文件：`docs/state-files.md`
- 运行时兼容：`docs/runtime-compatibility.md`
- 执行器规则：`docs/skill-operator-guide.md`
- 架构设计：`WORKFLOW_DESIGN.md`

---

# 4. route summary 驱动规则

推荐外层执行循环：
1. 先用 `--mode auto` 运行 `learn_plan.py`
2. 读取 `--stdout-json` 的：
   - `should_continue_workflow`
   - `blocking_stage`
   - `recommended_mode`
   - `next_action`
   - `actionable_missing_requirements`
   - `reference_missing_requirements`
   - `actionable_quality_issues`
   - `workflow_instruction`
   - `stage_exit_contract`
   - `stage_exit_missing_values`
   - `stage_exit_user_visible_next_step`
3. 若仍是中间产物，则继续下一轮 workflow
4. 若 `next_action = switch_to:diagnostic`，表示应切到现有 session runtime 启动网页 diagnostic session，而不是继续在终端文本出题
5. 只有当 `next_action = enter:/learn-today` 时才退出 `/learn-plan`

强约束：
- `blocking_stage = clarification`：继续追问，不进入 research / diagnostic / finalize
- `blocking_stage = research`：先 research plan，再 research report，不 finalize
- `blocking_stage = diagnostic`：先诊断，不 finalize
- `blocking_stage = approval`：先确认草案，不 finalize
- `blocking_stage = planning`：这是 finalize 前的过渡态，不是回退
- `blocking_stage = ready`：才允许 finalize

当 `should_continue_workflow = true` 时：
- 必须优先继续 workflow
- 不得通过手动补 `.learn-workflow/*.json` 或手填 diagnostic blueprint 跳过当前 gate

停止条件必须同时满足：
- `should_continue_workflow = false`
- `is_intermediate_product = false`
- `next_action = enter:/learn-today`

---

# 5. 执行入口

推荐入口：

```bash
python3 "$HOME/.claude/skills/learn-plan/learn_plan.py" \
  --topic "<学习主题>" \
  --goal "<学习目的>" \
  --level "<当前水平>" \
  --schedule "<时间/频率约束>" \
  --preference "<偏题海|偏讲解|偏测试|混合>" \
  --plan-path "<root>/learn-plan.md" \
  --materials-dir "<root>/materials" \
  --mode "<auto|draft|research-report|diagnostic|finalize>" \
  --stdout-json
```

selective subagent strategy 执行约束：
- 主 agent 可直接完成澄清追问、route 编排、字段映射、小范围 schema/前端修复、CLI 验证和本地 smoke；不要为了这些窄任务派 subagent。
- search/source discovery 与 research analysis 必须派发 Agent subagent 完成；当前主会话不得直接调用 `WebSearch` / `WebFetch` 来替代 research subagent。
- 出题、严格审题、planning candidate、semantic review、diagnostic blueprint 等重语义 artifact 必须由 Agent subagent 生成；主会话只负责转交 artifact，不直接撰写这些 artifact。
- research 阶段必须向用户返回一份可读的能力要求与达标水平报告，详细版优先 HTML，再把结构化 JSON 注入 `learn_plan.py`；不能只写 workflow JSON 而不展示报告。
- 当执行器已经拿到合法 JSON 时，应通过以下参数把结果注入 `learn_plan.py`，让 Python 只负责 gate、状态落盘与正式产物生成：
  - `--stage-candidate-json`
  - `--stage-review-json`
  - `--planning-candidate-json`
  - `--planning-review-json`
- 缺出题/审题 artifact 或重语义 artifact 时必须阻断并重新生成，不静默 fallback 到内置题库；`--stage-review-json` / `--planning-review-json` 只补充 `semantic_issues / improvement_suggestions`，不替代确定性 contract review。
- 所有 runtime 题目统一按 test-grade 标准处理，不区分学习题和测试题。

当 `next_action = switch_to:diagnostic` 时，执行器应立即转为启动网页 diagnostic session，而不是继续文本问答。推荐调用：

```bash
python3 "$HOME/.claude/skills/learn-plan/session_orchestrator.py" \
  --session-type test \
  --test-mode general \
  --plan-path "<root>/learn-plan.md" \
  --session-dir "<root>/sessions/<YYYY-MM-DD>-test"
```

---

# 6. 输出约定

终端输出保持简短，只保留：
- 学习主题
- workflow mode / blocking stage
- 计划文件路径
- 材料索引路径
- 自动下载结果摘要（如有）
- 当前计划状态与下一步建议

若当前交付不是正式计划，必须明确告诉用户：
- 当前是中间产物
- 当前卡在哪个 stage
- 下一步需要用户提供什么或确认什么
- 当前只应处理什么
- 哪些只是后续参考，暂不处理
- 不要手动补 `.learn-workflow/*.json` 或 diagnostic blueprint

---

# 7. 一句话原则

`/learn-plan` 不是“一次性计划生成器”，而是一个先澄清、再 research、再诊断、再确认、最后正式落盘的多轮学习顾问工作流。
