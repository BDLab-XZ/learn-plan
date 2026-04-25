# diagnostic stage

本文件只描述 `/learn-plan` 在 diagnostic 阶段的执行要求。

## 1. 目标

diagnostic 的目标是做最小但可信的起点验证，判断用户距离目标水平还差多少，而不是只信用户自报。

## 2. 前置条件

进入 diagnostic 前必须已经确认：
- 最多接受几轮测试
- 每轮最多接受多少题
- 若用户主动在意，再细化题型比例

若预算未确认，必须回到 clarification。

## 3. 交付方式

起点测评必须通过网页 session 交付，复用现有 test runtime：
- `questions.json`
- `progress.json`
- `题集.html`
- `server.py`

调用方式保持测试链路：
- `session_orchestrator.py --session-type test --test-mode general`
- runtime 根据 `plan_execution_mode=diagnostic` 自动写入 `assessment_kind = initial-test` 与 `session_intent = assessment`

## 4. 执行规则

- 当 route summary 给出 `blocking_stage = diagnostic` 或 `next_action = switch_to:diagnostic` 时，不要在终端直接出题。
- 应立即走网页 session。
- 只有用户完成网页作答后，才读取 `progress.json` 并形成诊断结论。
- 若 `follow_up_needed = true` 且未达到 `max_rounds`，继续停留在 diagnostic，并启动下一轮。

## 5. 批改要求

批改时至少给出：
- capability / expected signals / rubric
- 证据
- 缺口
- recommended entry level
- confidence

若开放题未评完，只能输出“待评阅 / 证据不足”，不能伪造通过或失败。

## 6. 输出

用户可见输出应包含：
- session 路径
- 浏览器地址
- 停服命令
- 作答说明
- 作答完成后的诊断摘要

结构化输出应可写入 `diagnostic.json`。

## 7. 禁止事项

- 不要在终端逐题文本测评来替代网页 session。
- 不要手动补 `diagnostic.json` 或 diagnostic blueprint 试图绕过 gate。
- 不要把起点测评结论写成普通 `stage-test` 的通过/未通过。
