---
name: dev-task
description: 开发任务管理。到本地代码仓库，使用 `tuido` 命令领取和查看开发任务（读取自项目下 TODO.md）。在 github 中新建 Issue 编写方案，确认方案后，再做具体的分支开发，以及提交 PR。
---

# Dev Task Skill

- 每个源码仓库中使用 `tuido` 命令管理开发任务。任务信息存储在项目根目录的 `TODO.md` 文件中。
- 使用 `gh` 命令来操作 github。
- 使用 `kimi` code agent 来做具体的开发工作。

## 源码仓库所在路径
- `code-repos`: 存放的是远程仓库为 github 的源码项目
- `code-repos-byte`: 存放的是远程仓库为 codebase 的源码项目

## 可用命令

### `tuido`
- 添加任务 (tuido add)。添加新任务到 TODO.md 的第一个栏目（通常是 Todo）。
  **语法:**
  ```bash
  tuido add "任务描述 #标签 !优先级"
  ```

- 列出任务 (tuido list)。列出 TODO.md 中的所有任务，支持按状态、标签、优先级筛选。
  **语法:**
  ```bash
  tuido list
  tuido list --status "Todo"
  ```

- 选取任务 (tuido pick)。选取第一个栏目的第一个任务，并将其移动到下一个栏目。
  **语法:**
  ```bash
  tuido pick
  ```

### `gh`
我已经设置好 gh 命令的登录状态，可以直接使用 gh 命令来操作 github。

### `kimi`
我已经设置好 kimi agent，可以直接调用 `kimi` 来进行代码相关的操作。
具体用法：
```bash
kimi --yolo --prompt "请帮我实现一个函数，功能是 xxx，要求 xxx"
```

## 操作流程
1. 如果用户没有明确指定任务，使用 `tuido pick` 选取一个开发任务
2. 在 github 中新建 Issue，编写方案
3. 确认方案后，创建分支进行开发
4. 提交 PR，等待用户审核和合并
