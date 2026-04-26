# Phase 2：起点检测

本文件定义 `/learn-plan` Phase 2 的执行要求。此阶段可选，但跳过时必须记录风险。

## 1. 目标

做最小但可信的起点验证，判断用户距离目标水平还差多少，而不是只信用户自报。

## 2. 进入条件

- Phase 1 的综合报告已完成且用户认可
- 测评预算已在 Phase 1 确认（轮数、题量）
- 用户未明确跳过

若用户坚持跳过：
- 必须在最终 learn-plan.md 中标记"起点基于自报，未经诊断验证"
- 后续 /learn-today 可能根据实际表现动态调整起点

## 3. 设计诊断题

根据 Phase 1 报告中的"目标能力"来设计诊断题，而不是无差别出题。

每道题至少绑定：
- 对应的能力/知识点
- 预期看到的信号（什么表现说明掌握得好/不好）
- 评分标准（正确、部分正确、不知道、错误）

## 4. 交付方式（执行步骤）

必须通过网页 session 交付，不复用旧 workflow engine 的中间态文件。

### 4.1 执行步骤

**Step A：生成诊断题 artifact**
- 派发子 Agent A 出题：根据 Phase 1 报告中的目标能力，生成题目。输出为 `question-artifact.json`
- 派发子 Agent B 审题：独立审查题目质量（答案正确性、干扰项迷惑性、覆盖度、表述清晰度）。输出为 `question-review.json`
- 审题失败 → 修改 → 重审，直到通过

**Step B：准备 plan_path**
- 如果 learn-plan.md 已存在（Phase 3 后）：直接使用
- 如果尚未进入 Phase 3（仅 Phase 2 诊断）：创建一个临时最小 Markdown 文件，包含 topic 名称即可，仅用于让 session_orchestrator 有一个合法的 `--plan-path` 参数

**Step C：启动 session**
```bash
python3 "$HOME/.claude/skills/learn-plan/learn-plan/session_orchestrator.py" \
  --session-type test \
  --test-mode general \
  --plan-path "<临时或正式 learn-plan.md 路径>" \
  --session-dir "<root>/sessions/YYYY-MM-DD-diagnostic" \
  --topic "<学习主题>" \
  --question-artifact-json "<question-artifact.json路径>" \
  --question-review-json "<question-review.json路径>"
```

**Step D**：启动服务并打开浏览器。若 8080 端口被占用，先探测占用进程告知用户。

### 4.2 禁止事项

- **禁止创建 `.learn-workflow/` 中间态文件**：diagnostic.json、workflow_state.json 等旧 workflow engine 的中间产物一律不需要
- **禁止创建 diagnostic blueprint**：题目由外部 Agent 注入，不需要 blueprint
- **禁止手动拼写 `questions.json`**：必须通过 session_orchestrator.py 组装
- **禁止在终端逐题文本测评**来替代网页 session

## 5. 诊断结论

用户完成网页作答后，分析 progress.json，形成诊断结论：

- 每个诊断能力维度的掌握证据与缺口
- 推荐起点（从哪个阶段/章节开始）
- 当前与目标的差距估计
- 置信度（高/中/低，基于证据充分性）
- 若开放题未评完，标注"待评阅/证据不足"

## 6. 多轮诊断

若 follow_up_needed 且未达到 max_rounds：
- 继续启动下一轮诊断
- 下一轮应聚焦上一轮暴露的薄弱维度

若已达到 max_rounds：
- 基于已有证据给出结论
- 标注因预算限制未覆盖的维度

## 7. 用户可见输出

- 诊断 session 路径与浏览器地址
- 作答完成后：诊断摘要（当前水平、与目标的差距、薄弱项、推荐起点）
- 如果跳过诊断：明确说明"起点基于自报"
- 当前是中间产物，不是正式计划

## 8. 禁止事项

- 不要在终端文本问答替代网页 session
- 不要把诊断结论写成"测试通过/未通过"——这是起点判断，不是阶段测试
- 不要伪造未评阅的开放题结果
