# TUIDO - 终端看板工具

基于终端的 Kanban 看板 TUI，用于管理 TODO.md 文件。

## 项目概览

- **语言**: Python 3.12+
- **框架**: Textual (TUI 框架)
- **入口**: `tuido [path] [--create] [--push]`
- **配置**: `pyproject.toml` (setuptools 打包)

## 架构

```
tuido/
├── __init__.py      # 包版本
├── cli.py           # CLI 入口 (argparse)
├── models.py        # 数据模型: Task, Board, FeishuTask
├── parser.py        # TODO.md 读写逻辑
├── ui.py            # Textual TUI 实现
├── feishu.py        # 飞书 API 封装
└── envs.py          # 环境变量加载
```

## 数据格式 (TODO.md)

**栏目(Column)是动态的，由二级标题决定**。TODO.md 中的每个 `## ` 标题成为一个看板列，按文件中出现的顺序展示。

### Front Matter 配置

TODO.md 支持 YAML front matter 格式配置，放在文件开头：

```markdown
---
theme: textual-dark
remote:
  feishu_table_app_token: xxx
  feishu_table_id: yyy
---
```

支持的配置项：
- `theme`: TUI 主题
- `remote.feishu_table_app_token`: 飞书多维表格 app token
- `remote.feishu_table_id`: 飞书多维表格 ID

```markdown
## Todo
- 任务描述 #标签 !优先级

## In Progress
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

### 层级任务（子任务）
通过缩进（2个空格）表示子任务层级关系，支持多级嵌套：

```markdown
## Todo
- 父任务 !P1
  - 子任务 1
  - 子任务 2
    - 孙子任务
- 另一个父任务
```

**规则：**
- 每 2 个空格表示一级缩进
- 子任务跟随父任务一起移动（左右移动栏目时）
- TUI 中子任务显示为缩进样式，带有 `└─` 前缀

## 核心类

### models.py
- `Task`: 标题、**column(栏目名称)**、标签列表、优先级、行号
  - `column`: 字符串，对应 TODO.md 中的二级标题
  - `level`: 层级深度（0为父任务，1+为子任务）
  - `parent`: 父任务引用（Task 或 None）
  - `subtasks`: 子任务列表（list[Task]）
- `Board`: 任务列表、**栏目顺序列表(columns)**、按栏目获取任务、重排序任务
  - `columns` 只存储顶级任务（level=0），子任务通过 `task.subtasks` 访问

### ui.py
- `TaskCard`: 单个任务组件 (**重要: 使用 `task_obj`, 不要用 `task`**)
- `KanbanColumn`: 列容器，包含标题和任务列表
- `KanbanBoard`: 主应用，处理导航、按键绑定、看板渲染

## 键盘快捷键

### 导航 (Vim 风格)
- `h/j/k/l` 或 `←/↓/↑/→` - 移动光标
- `q` 或 `Ctrl+C` - 退出

### 任务操作
- `Shift+←/H` - 左移 (移到上一栏目)
- `Shift+→/L` - 右移 (移到下一栏目)
- `Shift+↑/K` - 上移 (同列内调整顺序)
- `Shift+↓/J` - 下移 (同列内调整顺序)

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
1. 在 `KanbanBoard.BINDINGS` 添加绑定
2. 用 `@on(Key)` 装饰器实现处理方法
3. 如需更新 UI，调用 `refresh_board()`
4. 刷新后需更新选中状态时，使用 `call_after_refresh()`

### 修改任务显示
1. 更新 `TaskCard.render()` 方法
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

使用 `--global-view` 命令查看所有项目的任务：

```bash
# 查看全局任务列表（从飞书读取）
tuido --global-view
```

**特性：**
- 只读视图，不支持编辑和移动任务
- 任务标题显示格式：`[项目名] 任务名`
- 按状态自动分栏（Todo, In Progress, Review, Blocked, Done）

## 飞书同步

使用 `--push` 命令将任务同步到飞书多维表格：

```bash
# 推送当前目录 TODO.md 的任务到飞书
tuido --push

# 指定项目名（默认使用目录名）
tuido --push --project "MyProject"

# 推送指定路径的 TODO.md
tuido /path/to/project --push
```

**要求**：
2. TODO.md 的 front matter 中配置了 `remote.feishu_table_app_token` 和 `remote.feishu_table_id`

飞书表格字段映射：
- `Task`: 任务标题（带子任务层级）
- `Project`: 项目名称
- `Status`: 任务状态（栏目名称）
- `Tags`: 标签（逗号分隔）
- `Priority`: 优先级

## 测试

手动运行：
```bash
pip install -e .
tuido test_todo.md --create  # 创建示例文件
tuido test_todo.md           # 打开看板
tuido --push                 # 推送到飞书
```

## 依赖

- `textual` - TUI 框架
- `rich` - 终端格式化 (textual 自带)

开发安装：
```bash
pip install -e .
```
