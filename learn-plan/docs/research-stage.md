# research stage

本文件只描述 `/learn-plan` 在 research 阶段的执行要求。

## 1. 目标

research 的目标是先回答“为了达成用户真实目标，需要掌握到什么水平、哪些能力、通常如何被验证”，而不是直接写学习路线。

## 2. 何时进入

以下情况通常必须进入 research：
- 目标涉及岗位 / 求职 / 职业标准
- 需要外部能力标准或市场要求
- 材料取舍不明确
- 主题跨多栈，不能只靠 family 模板

## 3. 固定顺序

必须按下面顺序执行：
1. 先给 research plan 并确认
2. 当前主会话派发 Agent subagent 做 search/source discovery 与能力要求分析；主会话不得直接调用 WebSearch/WebFetch 替代
3. Agent subagent 返回 search_context、source evidence、research analysis report 与 `user_facing_report.html`
4. 主会话先向用户展示 HTML 能力要求与达标水平报告，再把结构化 candidate 注入 `learn_plan.py`
5. 再给 diagnostic scope 预览

## 4. 报告核心结构

报告开头先给极简核心分析：
- `goal_target_band`
- `required_level_definition`
- `must_master_core`
- `evidence_expectations`
- `research_brief`

详细版优先写为 HTML，并同步保存到结构化字段 `research_report.user_facing_report`。

然后再展开：
- 达成目标需要哪些能力
- 常见验证方式
- 哪些内容当前不是重点
- 为什么这么划分
- 依据哪些来源 / 证据
- 这些结论如何影响后续测试与规划

## 5. diagnostic scope 约束

若用户此前选择了要测试，则 research 阶段必须同时产出 machine-consumable 的 `diagnostic_scope`，至少说明：
- 接下来测什么
- 为什么这么安排
- 看哪些信号
- 暂不重点测什么

不要只给用户看一段解释，却不把 scope 真正传给后续 diagnostic/runtime。

## 6. 输出

用户可见输出应包含：
- HTML 能力要求与达标水平报告路径或摘要，报告由 Agent subagent 的 research analysis report 同源生成
- 目标达标带、required level definition、能力集合、主线/支撑/后置能力、可观察行为、量化指标、材料取舍依据
- source evidence 与 open risks
- diagnostic scope 预览
- 是否需要用户继续补充检索或确认

用户可见语言必须遵守 `language_policy.user_facing_language`；中文会话默认中文解释，英文来源、代码标识符、命令和原文引用可保留原语言。

结构化输出应可写入 `research.json`，并与用户可见报告保持同源。

## 7. 禁止事项

- 不要把 research 写成学习路线或小型计划。
- 不要提前展开“先学什么后学什么”。
- 不要用纯文本长报告替代 HTML 详细报告，除非 HTML 渲染失败并已明确记录。
- 不要忽略 `diagnostic_scope`，让 runtime 回退默认题库。
- 不要手动补 diagnostic blueprint 来替代 research 的真实产出。
