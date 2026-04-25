---
name: learn-plan
description: 生成长期学习计划文件 learn-plan.md，并以多轮 workflow 方式衔接 learn-today / learn-test / update / materials 下载入口
---

# /learn-plan root entry

这是本机 Claude Code 的 `/learn-plan` skill 入口 shim。

实际实现位于：

```text
$HOME/.claude/skills/learn-plan/learn-plan/SKILL.md
```

执行 `/learn-plan` 时必须先读取并遵循该文件；所有实现脚本、文档、模板、测试与前端资源也都以：

```text
$HOME/.claude/skills/learn-plan/learn-plan
```

作为 skill 根目录。

不要把当前目录下的仓库顶层当作学习系统运行根；它只是发布仓库的多 skill 容器。
