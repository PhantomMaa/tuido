# TUIDO - 终端看板工具

基于终端的 Kanban 看板 TUI，用于管理 TODO.md 文件。

## 项目概览

- **语言**: Python 3.12+
- **框架**: Textual (TUI 框架)
- **入口**: `tuido [open|create|add|pick|list|push|pull|global-view] [options]`
- **路径参数**: `--path` 可选，默认为当前目录 `.`
- **配置**: `pyproject.toml` (hatchling 打包)

## 架构

```
tuido/
├── __init__.py           # 包版本
├── main.py               # CLI 入口 (Click)，包含 TuidoGroup 类处理路径解析
├── models.py             # 数据模型: Task, Board, FeishuTask, RemoteConfig, GlobalConfig
├── parser.py             # TODO.md 读写逻辑，front matter 解析
├── ui.py                 # TUI 实现 (本地和全局视图共用)
├── cmd_list.py           # list 命令实现
├── cmd_add.py            # add 命令实现
├── cmd_pick.py           # pick 命令实现
├── util.py               # 工具函数
├── feishu.py             # 飞书 API 封装
├── config.py             # 全局配置加载/保存 (~/.config/tuido/config.yaml)
├── cmd_create.py         # create 命令实现
├── cmd_push.py           # push 命令实现
├── cmd_pull.py           # pull 命令实现
└── cmd_global_view.py    # global-view 命令实现
```

## 数据格式 (TODO.md)

**栏目(Column)是动态的，由二级标题决定**。TODO.md 中的每个 `## ` 标题成为一个看板列，按文件中出现的顺序展示。

### Front Matter 配置

TODO.md 支持 YAML front matter 格式配置，放在文件开头：

```markdown
---
theme: atom-one-dark
remote:
  feishu_api_endpoint: https://open.feishu.cn/open-apis
  feishu_table_app_token: xxx
  feishu_table_id: yyy
  feishu_table_view_id: zzz
  feishu_bot_app_id: aaa
  feishu_bot_app_secret: bbb
---
```

```markdown
## Todo
- 任务描述 #标签 !优先级

## Active
- 进行中的任务 #功能 !P1

## Review
- 待审核的任务

## Done
- 已完成的任务
```

### 动态栏目
- 栏目由 `## 标题` 自动读取，无需修改代码
- 可在文件中定义任意数量的栏目
- 栏目顺序遵循文件中的出现顺序

### 元数据语法
- `#标签` - 标签 (如 #功能, #缺陷)
- `!优先级` - 优先级 (如 !P0, !P1, !P2, !P3, !P4，P0 最高)
- `~YYYY-MM-DDTHH:MM` - 时间戳 (如 ~2026-02-28T14:30，自动更新)

### 行内样式
任务标题支持 Markdown 风格的行内格式，在 TUI 中会渲染为对应样式：

- `**加粗**` 或 `__加粗__` → **加粗文本**
- `` `代码` `` → `代码文本` (青色)
- `~~删除线~~` → ~~删除线文本~~

示例：
```markdown
- 实现 **加粗** 和 `代码` 样式支持 !P1 #ui
- ~~废弃功能~~ 将在 v2.0 中移除
- **重要:** 运行前检查 `config.yaml`
```

## 核心类

### models.py
- `Task`: 标题、**column(栏目名称)**、标签列表、优先级、项目名称、更新时间
  - `column`: 字符串，对应 TODO.md 中的二级标题
  - `project`: 项目名称（用于全局视图）
  - `updated_at`: 最后更新时间，格式 `YYYY-MM-DDTHH:MM`
- `Board`: 标题、栏目有序字典(columns)、设置字典、任务操作方法
- `FeishuTask`: 用于飞书同步的扁平化任务模型
- `RemoteConfig`: 飞书远程配置模型，从 YAML 加载
- `GlobalConfig`: 全局配置模型，包含主题和远程配置

### ui.py
- `TaskCard`: 单个任务组件 (**重要: 使用 `task_obj`, 不要用 `task`**)
- `ColumnHeader`: 栏目标题组件
- `KanbanColumn`: 列容器，包含任务列表
- `KanbanBoard`: 本地看板主组件，处理导航、按键绑定、看板渲染
- `TitleBar`: 应用标题栏
- `AddTaskScreen`: 添加/编辑任务的模态对话框
- `TuidoApp`: 主应用，支持本地模式和全局视图模式

## 键盘快捷键

### 导航 (Vim 风格)
- `h/j/k/l` 或 `←/↓/↑/→` - 移动光标
- `q` 或 `Ctrl+C` - 退出

### 任务操作
- `Shift+←/H` - 左移 (移到上一栏目)
- `Shift+→/L` - 右移 (移到下一栏目)
- `Shift+↑/K` - 上移 (同列内调整顺序)
- `Shift+↓/J` - 下移 (同列内调整顺序)

### 任务编辑
- `a` - 添加新任务
- `d` - 删除任务
- `e` - 编辑任务

### 其他操作
- `r` - 从文件刷新
- `s` - 保存到文件
- `t` - 切换主题
- `?` - 显示帮助

## 关键约定

### 1. TaskCard 属性命名
**必须使用 `task_obj`，不能用 `task`**

```python
# 错误 - 会导致 AttributeError: property has no setter
@dataclass
class TaskCard(Static):
    task: Task  # 与 Textual 的 Static.task 属性冲突

# 正确
@dataclass
class TaskCard(Static):
    task_obj: Task  # 避免命名冲突
```

### 2. 异步 DOM 操作
调用 `refresh_board()` 后，使用 `call_after_refresh()` 更新选中状态：

```python
def move_task(self, direction: str) -> None:
    self.refresh_board()
    
    def update_selection_after_refresh():
        # 此时 DOM 已就绪
        self.update_selection()
    
    self.call_after_refresh(update_selection_after_refresh)
```

### 3. 当前状态验证
使用索引前，先验证状态是否存在于可见列：

```python
# 错误 - 可能引发 ValueError
if current_status:
    current_idx = columns.index(current_status)  # 危险!

# 正确
if current_status in columns:
    current_idx = columns.index(current_status)  # 安全
```

## 常见任务

### 添加新快捷键
1. 在 `TuidoApp.BINDINGS` 添加绑定
2. 实现对应的 `action_*` 方法
3. 如需更新 UI，调用 `refresh_board()`
4. 刷新后需更新选中状态时，使用 `call_after_refresh()`

### 修改任务显示
1. 更新 `TaskCard.render_task()` 方法
2. 用特殊字符测试标题/标签/负责人
3. 确保 Rich 标记已正确转义

### 添加新栏目
直接在 TODO.md 中添加新的二级标题即可，无需修改代码：

```markdown
## 新栏目
- 新任务
```

刷新看板后，新栏目会自动显示。

## 全局视图

使用 `global-view` 命令查看所有项目的任务：

```bash
# 查看全局任务列表（从飞书读取）
tuido global-view

# 推送全局视图到飞书
tuido global-view --push
```

**配置要求：**

全局视图需要配置 `~/.config/tuido/config.yaml`：

```yaml
theme: atom-one-dark
remote:
  feishu_api_endpoint: https://open.feishu.cn/open-apis
  feishu_table_app_token: your_table_app_token
  feishu_table_id: your_table_id
  feishu_table_view_id: your_table_view_id
  feishu_bot_app_id: your_bot_app_id
  feishu_bot_app_secret: your_bot_app_secret
```

**实现方式：**
全局视图模式首先从飞书获取所有任务，生成临时文件 `/tmp/TODO_global.md`，然后使用与本地模式相同的 TUI (`TuidoApp`) 进行展示。

**特性：**
- 任务标题显示格式：`[项目名] 任务名`
- 按状态自动分栏（Todo, Active, Review, Done 及自定义栏目）
- 主题切换会自动保存到全局配置
- 支持 `--push` 参数推送任务到飞书

## 飞书同步

### 推送本地任务到飞书

使用 `push` 子命令将任务同步到飞书多维表格：

```bash
# 推送当前目录 TODO.md 的任务到飞书（--path 默认为 .）
tuido push
tuido push --path /path/to/project
```

**要求**：
1. `~/.config/tuido/config.yaml` 中配置了 `remote.feishu_bot_app_id` 和 `remote.feishu_bot_app_secret`
2. TODO.md 的 front matter 中配置了 `remote.feishu_api_endpoint`, `remote.feishu_table_app_token`, `remote.feishu_table_id`, `remote.feishu_table_view_id`

### 从飞书拉取任务到本地

使用 `pull` 命令将飞书多维表格中的任务同步到本地：

```bash
# 拉取飞书任务到当前目录 TODO.md（--path 默认为 .）
tuido pull
tuido pull --path /path/to/project
```

**特性：**
- 对比本地和远程任务，显示差异预览
- 支持新增、修改、删除任务的同步
- 自动保存到 TODO.md 文件

飞书表格字段映射：
- `Task`: 任务标题（带子任务层级）
- `Project`: 项目名称
- `Status`: 任务状态（栏目名称）
- `Tags`: 标签（逗号分隔）
- `Priority`: 优先级
- `Timestamp`: 时间戳

## 测试

手动运行：
```bash
pip install -e .
tuido open                      # 打开看板（--path 默认为 .）
tuido create                    # 创建示例文件
tuido add "Fix bug #bug !P0"    # 添加任务
tuido pick                      # 选取首任务并移到下一栏
tuido list                      # 列出所有任务
tuido push                      # 推送到飞书
tuido pull                      # 从飞书拉取
tuido global-view               # 全局视图
tuido global-view --push        # 推送全局视图到飞书
```

## 依赖

- `textual` - TUI 框架
- `rich` - 终端格式化 (textual 自带)
- `pydantic` - 数据模型验证
- `requests` - HTTP 请求
- `pyyaml` - YAML 解析

开发安装：
```bash
pip install -e .
```
