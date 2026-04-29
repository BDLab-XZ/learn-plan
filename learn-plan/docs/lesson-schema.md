# 课件 JSON Schema（Agent 生成课件必读）

`lesson-artifact.json` 必须通过 `lesson_builder.py` 的 `build_lesson_review()` 校验。本文件描述 runtime metadata；正式课件正文写入 `lesson-html.json`，按 /long-output-html 格式渲染。

---

## 1. 顶层结构

```json
{
  "lesson": {
    "title": "Python 变量与对象引用",
    "current_stage": "阶段 1",
    "study_mode": "复习+推进",
    "why_today": "理解变量引用机制是避免 Python 常见 bug 的基础。",
    "materials_used": [ /* 材料引用 */ ],
    "today_focus": { /* 今日知识点 */ },
    "project_driven_explanation": { /* 可选：项目驱动元数据 */ },
    "review_suggestions": { /* 复习建议与内容回看元数据 */ },
    "case_courseware": { /* 可选/旧版兼容：不再作为正式课件正文 */ },
    "source_trace": { "basis": "agent-generated" }
  }
}
```

---

## 1.1 lesson-html.json 正文框架

正式课件正文不在 `lesson-artifact.json` 中承载，而是由子 Agent 生成 `/long-output-html` 兼容的 `lesson-html.json`。正文应覆盖三段教学框架：

1. **往期复习**：复习上期学习内容、掌握情况、错题/薄弱点，并说明与本期的衔接。
2. **本期知识点讲解**：围绕本期核心问题讲解，可自由使用段落、列表、表格、代码块、案例、反例和逐步推理。
3. **本期内容回看**：列出材料来源与回看重点，尽量精确到材料名、章节、页码、段落、section 或 locator；缺失精确定位时必须说明，禁止编造。

`case_courseware` 仅保留为旧版兼容字段，不再是主路径必填课件结构。

---

## 2. materials_used

```json
[
  {
    "material_title": "Python编程：从入门到实践（第3版）",
    "locator": "第2章 变量和简单数据类型",
    "segment_id": "py-crash-course-ch2",
    "match_reason": "讲解变量赋值和引用语义的基础章节",
    "source_status": "agent-selected"
  }
]
```

| 字段 | 是否必需 | 说明 |
|---|---|---|
| `material_title` | 必需 | 材料名称 |
| `locator` | **强制** | 章节/页码/小节定位。缺少触发 `material-locator-missing` |
| `segment_id` | 可选 | 材料 segment ID |
| `match_reason` | 可选 | 为什么选这份材料 |
| `source_status` | 可选 | 来源状态 |

**注意**：在 `execution_mode: "normal"` 模式下，`materials_used` 为空触发 `materials-used-missing`。每个 item 必须有 `locator`。

---

## 3. today_focus

```json
{
  "summary": "今天核心学习变量引用语义：Python 变量是对象的标签，赋值不会复制对象。",
  "focus_points": [
    {
      "point": "变量名绑定对象引用",
      "why_it_matters": "这是理解 list/dict 可变性、函数传参、copy/deepcopy 的前提",
      "mastery_check": "能解释 a=[1,2]; b=a; b.append(3) 后 a 的值及原因",
      "source_segment_ids": ["py-crash-course-ch2"],
      "related_tasks": ["task-1"]
    }
  ]
}
```

| 字段 | 校验规则 |
|---|---|
| `focus_points` | 非空数组，缺少触发 `today-focus-missing` |
| `focus_points[].point` | 必填 |
| `focus_points[].why_it_matters` | 至少一个 item 必须非空；全部为空触发 `why-it-matters-weak` |
| `focus_points[].mastery_check` | 至少一个 item 必须非空；全部为空触发 `mastery-check-weak` |
| `focus_points[].source_segment_ids` | 最多 4 个 |
| `focus_points[].related_tasks` | 最多 4 个 |

---

## 4. project_driven_explanation

```json
{
  "summary": "通过一个数据清洗任务，展示变量引用如何导致意外副作用。",
  "tasks": [
    {
      "task_name": "复现变量引用 Bug",
      "real_context": "你在清洗调查数据时发现修改副本后原数据也被改了",
      "blocker": "不清楚为什么 b = a 后修改 b 会影响 a",
      "why_now": "这是 Python 新手最常见的困惑之一",
      "knowledge_points": ["变量引用语义", "可变对象 vs 不可变对象"],
      "explanation": "Python 中赋值操作不复制对象，而是创建新的引用...",
      "how_to_apply": "使用 .copy() 或 copy.deepcopy() 来创建独立副本",
      "extension": "函数参数传递也遵循同样的引用语义",
      "source_segment_ids": ["py-crash-course-ch2"],
      "source_status": "agent-generated"
    }
  ]
}
```

| 字段 | 校验规则 |
|---|---|
| `tasks` | 非空数组，缺少触发 `project-driven-explanation-missing` |
| `tasks[].task_name` | 必填 |
| `tasks[].real_context` | 至少一个 item 必须非空；全部为空触发 `real-context-missing` |
| `tasks[].blocker` | 至少一个 item 必须非空；全部为空触发 `project-blocker-weak` |
| `tasks[].knowledge_points` | 至少一个 item 必须非空；全部为空触发 `project-knowledge-link-weak` |
| `tasks[].why_now` | 不能是模板填充文字（如"为什么今天现在引入这些知识"） |

---

## 5. review_suggestions

```json
{
  "summary": "今日复习重点",
  "today_review": ["用自己的话解释变量引用和对象复制之间的区别"],
  "progress_review": ["回顾之前学过的 list 操作，检查是否有引用相关的误解"],
  "next_actions": ["下次学习 copy 模块和 deepcopy"]
}
```

| 字段 | 校验规则 |
|---|---|
| `today_review` | 非空数组，缺少触发 `review-today-missing` |
| `progress_review` | 在 `execution_mode: "normal"` 下非空，缺少触发 `review-progress-missing` |
| `next_actions` | 建议下一步行动 |

---

## 6. case_courseware（可选 / 旧版兼容）

```json
{
  "case_courseware": {
    "knowledge_preview_flashcards": [
      {
        "term": "变量引用",
        "explanation": "变量名指向内存中的对象，而非存储对象本身",
        "mastery_check": "判断：b = a 总是创建副本？（答案：错误）"
      }
    ],
    "case_background": {
      "situation": "你接手了一个数据清洗脚本，修改筛选后的列表时发现原数据也被污染了...",
      "problem_to_solve": "如何创建数据的独立副本进行操作？"
    },
    "guided_story_practice": [
      {
        "scene": "你打开 colleague 的 Jupyter notebook",
        "challenge": "为什么只修改了 filtered_data 却影响到了 raw_data？",
        "teaching_move": "引入 Python 变量引用模型，展示内存图",
        "resolution": "使用 .copy() 方法创建浅拷贝，理解它和赋值的区别"
      },
      {
        "scene": "你又发现 copy() 对嵌套列表无效",
        "challenge": "修改副本中的子列表还是影响了原数据",
        "teaching_move": "引入浅拷贝 vs 深拷贝的概念",
        "resolution": "使用 copy.deepcopy() 处理嵌套结构"
      }
    ],
    "review_sources": [
      {
        "material_title": "Python官方文档",
        "locator": "Data Model - Objects, values and types",
        "locator_detail": "第 3 段，'Every object has an identity, a type and a value'",
        "key_excerpt": "An object's identity never changes once it has been created",
        "review_focus": "理解对象标识（id()）和值的关系"
      }
    ],
    "exercise_policy": {
      "embedded_questions": false
    }
  }
}
```

### case_courseware 校验规则

| 字段 | 校验规则 |
|---|---|
| `case_courseware` | 可选旧版兼容字段；新课件正文以 `lesson-html.json` 为准 |
| `knowledge_preview_flashcards` | 非空数组；每个 card 的 `mastery_check` 非空（否则 `flashcard-mastery-check-missing`） |
| `case_background.situation` | **≥10 字符**；不够触发 `case-background-hollow` |
| `case_background.problem_to_solve` | **≥6 字符**；不够触发 `case-background-hollow` |
| `guided_story_practice` | 非空数组；每步必须含 `scene`、`challenge`、`teaching_move`、`resolution` 全部非空（否则 `guided-practice-hollow`） |
| `review_sources` | 非空数组；每项含 `material_title`(≥2字符)、`locator`(≥2字符)、`review_focus`(≥2字符)。**新增**：`locator_detail`（页码/段落级定位）和 `key_excerpt`（原文关键句摘录）为强烈推荐字段 |
| `exercise_policy.embedded_questions` | **必须为 `false`**；为 true 触发 `embedded-practice-questions` |

---

## 7. 禁止用语（fluff filter）

以下中文短语不能出现在 `why_today`、`coach_explanation`、`today_focus.summary`、`project_driven_explanation.summary`、`review_suggestions.summary`、`focus_points[].why_it_matters`、`project_tasks[].real_context`、`project_tasks[].why_now` 中：

| 触发词 | 错误码 |
|---|---|
| `"你可以考虑"` | `fluff-tone-detected` |
| `"建议如下"` | `fluff-tone-detected` |
| `"下面给出建议"` | `fluff-tone-detected` |
| `"建议结构"` | `fluff-tone-detected` |

**替代写法**：直接给出具体内容，不使用"建议""可以考虑"等委婉表达。

---

## 8. 生成后自查清单

**结构完整性：**
- [ ] materials_used 非空（normal 模式），每项有 locator
- [ ] today_focus.focus_points 非空，至少一个有 why_it_matters 和 mastery_check
- [ ] project_driven_explanation.tasks 非空，至少一个有 real_context 和 blocker
- [ ] review_suggestions.today_review 非空
- [ ] review_suggestions.progress_review 非空（normal 模式）
- [ ] lesson-html.json 覆盖往期复习、本期知识点讲解、本期内容回看，并在内容回看中提供精确来源
- [ ] case_background.situation ≥ 10 字符，problem_to_solve ≥ 6 字符
- [ ] guided_story_practice 每步含 scene/challenge/teaching_move/resolution
- [ ] exercise_policy.embedded_questions = false
- [ ] 无 fluff 触发词

**叙事质量：**
- [ ] 案例背景有具体人物（有名字/角色）和真实场景（有时间/地点/具体情境），非"一个开发者""某个项目"等套话
- [ ] 叙事连贯，章节间有自然过渡，非卡片堆砌
- [ ] guided_story_practice 的每一步都推进故事，而非孤立的知识点展示
- [ ] 正文是连贯段落而非 bullet list
