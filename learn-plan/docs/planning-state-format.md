# learn-plan.md planning state 格式规范

`plan_source.py` 的 `parse_learning_profile_section()` 从 `学习画像` 章节解析 planning state。格式必须精确匹配以下前缀，否则状态回退为 fallback。

---

## 1. 必需格式

planning state 必须位于 `## 学习画像` 章节下，格式如下：

```markdown
## 学习画像

- planning state：
  - 澄清状态：confirmed
  - deepsearch 状态：completed
  - 诊断状态：completed
  - 当前轮次：2/2
  - 每轮题量：8
  - 是否需要下一轮：false
  - 偏好确认状态：confirmed
  - 计划状态：confirmed

- 学习主题：Python 数据科学与大模型应用开发工程能力
- 目标：6 个月内强化 Python 工程能力...
- 背景：本科市场营销...
```

## 2. 前缀映射表

以下是 parser 查找的精确前缀。**冒号必须是中文全角冒号 `：`**，前缀文字必须完全一致：

| 前缀 | 解析的目标字段 | 有效值示例 |
|---|---|---|
| `澄清状态：` | `planning_state.clarification_status` | `confirmed`, `captured` |
| `deepsearch 状态：` | `planning_state.deepsearch_status` | `completed`, `approved-running` |
| `诊断状态：` | `planning_state.diagnostic_status` | `completed`, `confirmed` |
| `当前轮次：` 或 `诊断轮次：` | `planning_state.diagnostic_round_index` | `2/2`, `1` |
| `最多轮次：` | `planning_state.diagnostic_max_rounds` | `2`, `3` |
| `每轮题量：` | `planning_state.questions_per_round` | `8`, `10` |
| `是否需要下一轮：` | `planning_state.diagnostic_follow_up_needed` | `true`, `false`, `否` |
| `偏好确认状态：` | `planning_state.preference_status` | `confirmed`, `not-started` |
| `计划状态：` | `planning_state.plan_status` | `confirmed`, `approved` |

## 3. 执行 gate 判断逻辑

`resolve_plan_execution_mode()` 检查这些状态决定能否进入 normal 学习：

| gate | 状态要求 | 不满足时的行为 |
|---|---|---|
| 澄清 gate | `clarification_status` 为 `confirmed` 或 `captured` | session 被重定向为 clarification 模式 |
| 研究 gate | `deepsearch_status` 不为 `needed-pending-plan` 或 `approved-running` | session 重定向为 research 模式 |
| 诊断 gate | `diagnostic_status` 不为 `in-progress`、`not-started`、`follow-up-needed` | session 重定向为 diagnostic 模式 |
| 计划 gate | `plan_status` 为 `confirmed`、`approved` 等可执行状态 | session 重定向为 prestudy 模式 |

## 4. 常见错误

| 错误 | 后果 |
|---|---|
| 用英文冒号 `:` 代替中文冒号 `：` | 前缀匹配失败，回退 fallback |
| `- planning state` 写为嵌套列表的标题 | parser 找不到前缀行 |
| planning state 不在 `学习画像` 章节下 | parser 读不到该段 |
| 状态值拼写错误（如 `confirmd` 而非 `confirmed`） | gate 判断为未完成 |
| `当前轮次：2/2` 写成 `当前轮次：2` | round_index 解析为 2，但 max_rounds 可能为 None |
| `是否需要下一轮：否` 而非 `false` | `_parse_optional_bool()` 能识别中文，但 boolean 更可靠 |

## 5. 完整模板

```markdown
## 学习画像

- planning state：
  - 澄清状态：confirmed
  - deepsearch 状态：completed
  - 诊断状态：completed
  - 当前轮次：2/2
  - 每轮题量：8
  - 是否需要下一轮：false
  - 偏好确认状态：confirmed
  - 计划状态：confirmed

- 学习主题：Python 数据科学与大模型应用开发工程能力
- 目标：6 个月内强化 Python 工程能力...
- 背景：本科市场营销；一年数据分析经验...
```

## 6. 用户模型和诊断摘要（可选）

同一 `学习画像` 章节下的额外区块：

```markdown
- 用户模型：
  - 画像：<一句话描述>
  - 约束：<时间/频率限制>
  - 偏好：<学习偏好>
  - 已知优势：<已掌握的内容>
  - 已知薄弱点：<待补强的内容>

- 目标层级：
  - 主线目标：<最终目标>
  - 支撑能力：<需要掌握的能力列表>

- 学习风格与练习方式：
  - 学习风格：<风格描述>
  - 练习方式：<练习偏好>
  - 交付偏好：<教学风格偏好>

- 诊断摘要：
  - 诊断维度：<维度列表>
  - 观察到的优势：<优势>
  - 观察到的薄弱点：<薄弱点>
  - 推荐起步层级：<起点建议>
```

这些区块的解析规则同样使用中文冒号前缀匹配，详细信息见 `plan_source.py:parse_learning_profile_section()`。
