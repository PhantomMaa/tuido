# TUIDO - 终端看板工具

基于终端的 Kanban 看板 TUI，用于管理 TODO.md 文件。

## 项目概览

- **语言**: Python 3.12+
- **框架**: Textual (TUI 框架)
- **入口**: `tuido [path] [--create]`
- **配置**: `pyproject.toml` (setuptools 打包)

## 架构

```
tuido/
├── __init__.py      # 包版本
├── __main__.py      # CLI 入口 (argparse)
├── models.py        # 数据模型: Task, Board, TaskStatus
├── parser.py        # TODO.md 读写逻辑
└── ui.py            # Textual TUI 实现
```

## 数据格式 (TODO.md)

任务状态由章节标题决定，而非前缀：

```markdown
## Todo
- 任务描述 #标签 !优先级 @负责人

## In Progress
- 另一个任务 #功能 !高 @开发

## Blocked
- 被阻塞的任务

## Done
- 已完成的任务
```

### 元数据语法
- `#标签` - 标签 (如 #功能, #缺陷)
- `!优先级` - 优先级 (如 !高, !低)
- `@负责人` - 负责人 (如 @开发, @设计)

## 核心类

### models.py
- `TaskStatus` 枚举: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`
- `Task`: 标题、状态、标签列表、优先级、负责人、行号
- `Board`: 任务列表、按状态获取任务、移动任务、重排序任务

### ui.py
- `TaskCard`: 单个任务组件 (**重要: 使用 `task_obj`, 不要用 `task`**)
- `KanbanColumn`: 列容器，包含标题和任务列表
- `KanbanBoard`: 主应用，处理导航、按键绑定、看板渲染

## 键盘快捷键

### 导航 (Vim 风格)
- `h/j/k/l` 或 `←/↓/↑/→` - 移动光标
- `q` 或 `Ctrl+C` - 退出

### 任务操作
- `Shift+←/H` - 左移 (改变状态)
- `Shift+→/L` - 右移 (改变状态)
- `Shift+↑/K` - 上移 (同列内调整顺序)
- `Shift+↓/J` - 下移 (同列内调整顺序)

### 视图
- `b` - 切换 Blocked 列显示/隐藏

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

### 添加新状态列
1. 在 `TaskStatus` 枚举中添加
2. 更新 `ui.py` 中的 `STATUS_ORDER`
3. 更新 `parse_todo_file()` 的章节检测
4. 更新 `save_todo_file()` 的章节写入

## 测试

手动运行：
```bash
pip install -e .
tuido test_todo.md --create  # 创建示例文件
tuido test_todo.md           # 打开看板
```

## 依赖

- `textual` - TUI 框架
- `rich` - 终端格式化 (textual 自带)

开发安装：
```bash
pip install -e .
```
