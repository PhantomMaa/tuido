# Tuido 📝

一个基于 TODO.md 文件的 TUI（终端用户界面）看板工具。

## 特性

- 📋 解析简单列表语法的 TODO.md 文件
- 📊 **动态列** - 基于 markdown 标题自动生成（`## 标题`）
- 🎨 多种主题（Dracula、Nord、Monokai、Solarized 等）
- ⌨️ Vim 风格快捷键（h/j/k/l）
- ↔️ 使用 Shift+方向键在列之间移动任务
- 🔃 在列内重新排序任务（包括子任务）
- 🏷️ 支持标签（#标签）、优先级（!P0/!P1/!P2/!P3/!P4）、时间戳（~YYYY-MM-DDTHH:MM）
- 💾 自动保存更改到 TODO.md
- 🌏 **全局视图** - 从飞书表格查看所有项目的任务
- 🔄 **双向同步** - 推送到和拉取自飞书表格
- 📁 **层级任务** - 支持带缩进的子任务

## 安装

```bash
# 克隆或下载仓库
cd tuido

# 以可编辑模式安装
pip install -e .
```

## 使用方法

```bash
# 打开当前目录 TODO.md 的 TUI 看板（默认）
tuido tui
tuido tui --path .

# 创建示例 TODO.md 文件
tuido create
tuido create --path /path/to/project

# 列出任务（可选过滤）
tuido list
tuido list --status "Active"
tuido list --tag feature
tuido list --priority P1

# 添加新任务
tuido add "修复 bug #bug !P0"
tuido add "更新文档 #docs" --path /path/to/project

# 选取顶部任务并移动到下一列
tuido pick
tuido pick --path /path/to/project

# 推送任务到飞书表格
tuido push
tuidu push --path /path/to/project

# 从飞书表格拉取任务
tuido pull
tuido pull --path /path/to/project

# 从飞书表格打开远程全局视图
tuido tui --remote

# 从远程飞书表格列出任务
tuido list --remote
```

**注意：** 大多数命令的 `--path` 参数是可选的，默认为当前目录（`.`）。

## 键盘快捷键

### 导航（Vim 风格）
- `↑` / `k` - 上一个任务
- `↓` / `j` - 下一个任务
- `←` / `h` - 上一列
- `→` / `l` - 下一列

### 移动任务（列之间）
- `Shift+↑` / `Shift+K` - 向上移动（在列内排序）
- `Shift+↓` / `Shift+J` - 向下移动（在列内排序）
- `Shift+←` / `Shift+H` - 移动到左列
- `Shift+→` / `Shift+L` - 移动到右列

### 操作
- `a` - 添加新任务
- `d` - 删除任务
- `e` - 编辑任务
- `r` - 从文件刷新
- `s` - 保存到文件
- `t` - 切换主题
- `q` / `Ctrl+C` - 退出
- `?` - 显示帮助

## TODO.md 格式

```markdown
---
theme: dracula
---

# TODO

## Todo
- 待办任务 #feature !P1 ~2026-02-28T10:30
- 另一个任务 #bug ~2026-02-28T09:00

## Active
- 正在进行中 ~2026-02-28T14:00
  - 子任务 1 #backend
  - 子任务 2 #frontend

## Done
- 已完成任务 ~2026-02-27T16:30
```

### 动态列

列会根据 TODO.md 中的 `## ` 标题自动创建。你可以定义任何需要的列：

- `## Todo` - 待办任务
- `## Active` - 进行中的任务
- `## Done` - 已完成的任务

列的顺序按照它们在文件中的出现顺序。

### 任务语法

- `- ` - 任务前缀（必需）
- `#tag` - 标签（如 #feature、#bug、#docs）
- `!P0` / `!P1` / `!P2` / `!P3` / `!P4` - 优先级（P0 最高，P4 最低）
- `~YYYY-MM-DDTHH:MM` - 最后更新时间（如 ~2026-02-28T14:30）

任务状态由它所属的栏目（`## Todo`、`## Active` 等）决定。

### 行内样式

任务标题支持 TUI 中的 Markdown 风格行内格式：

- `**粗体**` 或 `__粗体__` - **粗体文本**
- `` `代码` `` - `代码文本`（青色）
- `~~删除线~~` - ~~删除线文本~~

示例：
```markdown
- 实现 **粗体** 和 `代码` 支持 !P1 #ui
- ~~已弃用的功能~~ 将在 v2.0 中移除
- **重要：** 运行前检查 `config.yaml`
```

**注意：** 当你在 TUI 中移动或重新排序任务时，时间戳会自动更新，并与飞书的 `时间戳` 字段同步。

### 子任务（层级任务）

使用 2 空格缩进创建子任务：

```markdown
## Todo
- 父任务 !P1
  - 子任务 1
  - 子任务 2
    - 孙子任务
```

**规则：**
- 2 空格 = 1 级缩进
- 移动到其他列时，子任务跟随父任务一起移动
- 子任务可以在同一父任务内独立重新排序

## 配置

### Front Matter（TODO.md）

在 TODO.md 开头添加配置：

```markdown
---
theme: nord
remote:
  feishu_api_endpoint: https://open.feishu.cn/open-apis
  feishu_table_app_token: 你的_app_token
  feishu_table_id: 你的_table_id
  feishu_table_view_id: 你的_view_id
---
```

### 全局配置（~/.config/tuido/config.yaml）

要集成飞书，创建配置文件：

```yaml
theme: dracula
remote:
  feishu_api_endpoint: https://open.feishu.cn/open-apis
  feishu_table_app_token: 你的_table_app_token
  feishu_table_id: 你的_table_id
  feishu_table_view_id: 你的_view_id
  feishu_bot_app_id: 你的_bot_app_id
  feishu_bot_app_secret: 你的_bot_app_secret
```

## 全局视图

在单一界面中查看所有项目的任务：

```bash
# 从飞书表格显示全局视图
tuido tui --remote
```

**配置：**

使用你的飞书凭据创建 `~/.config/tuido/config.yaml`（见上文）。

全局视图显示所有项目的任务，按状态列（Todo、Active、Review、Done）组织。

## 飞书同步

### 推送到飞书

将本地任务推送到飞书表格：

```bash
tuido push
```

功能：
- 比较本地任务和远程记录
- 推送前显示差异预览
- 创建新任务，更新已修改的任务
- 删除孤立的远程记录

### 从飞书拉取

从飞书拉取远程任务到本地：

```bash
tuido pull
```

功能：
- 为当前项目从飞书获取任务
- 应用前显示差异预览
- 添加新任务，更新已修改的任务
- 删除本地已远程删除的任务
- 自动保存到 TODO.md

## 环境要求

- Python 3.12+
- textual
- rich
- requests
- pyyaml
- loguru
