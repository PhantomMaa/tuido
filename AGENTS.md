# Tuido - Terminal Kanban for TODO.md

Python 3.12+, Textual TUI, Click CLI, Feishu sync.

## Commands
```
uv sync
pip install -e .
tuido tui # open board (default: current dir)
tuido create / add / list / push / pull
```

## Critical Traps

### TaskCard属性必须用 `task_obj`，不能用 `task`
`task` 与 Textual `Static` 的内置属性冲突，会导致 `AttributeError: property has no setter`。

### 异步DOM：刷新后用 `call_after_refresh()` 更新选中状态
```python
self.refresh_board()
self.call_after_refresh(self.update_selection)
```

### CLI退出码约定
- 命令函数签名 `-> int`，返回 0/1
- 禁止在命令函数中直接 `raise SystemExit`
- 统一由 `main()` 中 `sys.exit(cli())` 退出
- 错误信息用 `click.echo(..., err=True)` 输出到 stderr

## Data Format
TODO.md 的 `## 标题` 自动成为看板列（动态，无需改代码）。

元数据语法：`#tag` `!P0-P4` `~YYYY-MM-DDTHH:MM`（移动任务时自动更新）

## Global Config
`~/.config/tuido/config.yaml` — Feishu credentials（bot_app_id/secret + table tokens）
