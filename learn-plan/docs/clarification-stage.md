# clarification stage

本文件只描述 `/learn-plan` 在 clarification 阶段的执行要求。

## 1. 目标

clarification 的目标不是直接写计划，而是用主题式多轮顾问访谈，把用户的真实目标、当前水平、节奏约束、学习偏好与评估预算收敛成可推进的结构化输入。

它不是一次性问卷。每一轮只聚焦一个主题，直到该主题满足 exit criteria、被明确 deferred，或被记录为 assumption/open question。

## 2. 主题模型

默认主题集合：

- `learning_purpose`：学习目的，例如考试高分、求职、项目落地、兴趣探索。
- `exam_or_job_target`：目标场景，例如考试范围、岗位类型、项目交付物、评价方式。
- `success_criteria`：用户认为“学成”的证据，例如分数、排名、作品、面试通过、能独立完成任务。
- `current_level`：当前水平、自报基础、已有经验；若不可靠，可 deferred 到 diagnostic。
- `constraints`：时间、频率、截止日期、作息与精力约束。
- `teaching_preference`：讲解风格、节奏、抽象/例子偏好。
- `practice_preference`：练习方式、题量、反馈方式；受 runtime 能力限制时要明确告知。
- `materials`：已有资料、教材、真题、课程、项目代码或外部资源条件。
- `assessment_scope`：起始测评预算，最多几轮、每轮最多几题、是否接受分轮追问。
- `non_goals`：当前不学或后置的内容。

## 3. 每轮执行方式

每轮必须：

1. 选定一个 `current_topic_id`。
2. 用一句话说明为什么当前追问这个主题。
3. 以终端自然语言对话继续追问，只问该主题下的 1–3 个开放问题；不要跨主题批量问卷。
4. 禁止使用 `AskUserQuestion` / `UserQuestions` / 选择题控件承载 clarification 访谈；这些控件只适合离散执行决策，不适合顾问式深挖。
5. 主 agent 负责继续顾问式追问和上下文判断；只有需要把较长对话整理成结构化 `clarification` candidate patch 时，才派发子 Agent，子 Agent 不负责继续问用户。
6. 根据用户回答更新该主题：
   - `confirmed_values`
   - `open_questions`
   - `assumptions`
   - `ambiguities`
   - `evidence`
5. 若回答仍模糊，下一轮继续同一主题追问，而不是跳到规划。
6. 若用户暂时答不出，必须记录为 assumption/open question/deferred，不要伪造确定事实。

示例：

- 用户说“我想期末考高分”。这不能直接视为充分目标。
- 应继续围绕 `exam_or_job_target` 或 `success_criteria` 追问：考试范围、题型、近年真题/样卷、目标分数或排名、当前基础。
- 如果用户没有真题，应记录为 open risk，并在 research/diagnostic 中降低确定性。

## 4. 必收集信息

最终至少确认或显式 deferred：

- 学习主题
- 学习目的 / 最终能力目标
- 成功标准
- 当前水平，或明确 deferred 到 diagnostic
- 时间 / 频率约束
- 学习偏好
- 练习偏好
- 希望如何检验掌握
- 起始测评预算：最多几轮、每轮最多几题
- 已有本地资料或外部资料条件
- 非目标

## 5. 强约束

- 必须显式问清：最多接受几轮起始测评、每轮最多接受多少题。
- 默认先按“每轮总题数”理解；只有用户主动在意题型比例时，再细化题型占比。
- 若 `max_assessment_rounds_preference` 或 `questions_per_round_preference` 未确认，必须继续停留在 clarification。
- `current_level` 可以 deferred 到 diagnostic，但必须显式记录，并且 assessment budget 已确认。
- 不要提前生成测评题。
- 不要提前进入正式规划。

## 6. 结构化输出

结构化输出应可写入 `clarification.json`，并至少包含旧兼容字段与新增主题状态：

- `questionnaire`
- `clarification_state`
- `preference_state`
- `consultation_state`

`consultation_state` 至少包含：

- `status`
- `current_topic_id`
- `topic_order`
- `topics[]`
- `thread[]`
- `open_questions`
- `assumptions`

每个 topic 至少包含：

- `id`
- `status`
- `required`
- `exit_criteria`
- `confirmed_values`
- `open_questions`
- `assumptions`
- `ambiguities`
- `evidence`

## 7. 用户可见输出

用户可见输出应包含：

- 当前画像摘要
- 当前聚焦主题
- 为什么追问这个主题
- 当前主题已确认什么
- 当前主题还缺什么
- 下一轮只问当前主题的问题
- 起始测评预算是否已确认
- 当前是中间产物，不是正式计划

## 8. 禁止事项

- 不要一次抛出跨越多个主题的大问卷。
- 不要因为后续还缺 research / diagnostic / approval 字段，就去手动补其他阶段 JSON。
- 不要把用户的自报水平直接当作可靠起点。
- 不要跳过 clarification 直接进入 finalize。
