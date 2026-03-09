---
name: dev-task
description: 领取开发任务并按要求完成开发的技能。在 github 中新建 Issue 编写方案，用户确认方案后，再做具体的分支开发，以及提交 PR。当用户安排给你开发任务时，使用此技能。
---

# Dev Task Skill

- 使用 `tuido` 命令管理开发任务列表
- 使用 `gh` 命令来操作 github
- 使用 `kimi` code agent 来做具体的开发工作

## 源码仓库所在路径
- `code-repos`: 存放的是远程仓库为 github 的源码项目（可使用 gh 命令操作 github）

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
  tuido list --status "Todo" --tag "bugfix" --priority "P1"
  ```

### `gh`
我已经设置好 gh 命令的登录状态，可以直接使用 gh 命令来操作 github。

### `kimi`
我已经设置好 kimi agent，可以直接调用 `kimi` 来进行代码相关的操作。

具体用法：
```bash
# 使用 kimi，开启 `yolo` 免确认模式，传入 prompt 实现一个功能
cd code-repos/{project} && kimi --yolo --prompt "请帮我实现一个函数，功能是 xxx，要求 xxx"
```

## 操作流程
2. 在 github 中新建 Issue，编写方案，然后将 Issue 发送给用户，等待用户确认
3. 确认方案后，创建分支进行开发
4. 提交 PR，等待用户审核和合并
