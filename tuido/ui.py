"""TUI UI components for tuido."""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from rich.text import Text

from .models import Task, Board


class TaskCard(Static):
    """A card displaying a single task."""

    DEFAULT_CSS = """
    TaskCard {
        width: 100%;
        height: auto;
        padding: 0 1;
        margin: 0;
        border: solid $surface-lighten-1;
    }
    TaskCard:hover {
        background: $surface-lighten-1;
    }
    TaskCard.selected {
        border: solid $accent;
        background: $surface;
    }
    TaskCard.subtask {
        margin-left: 2;
    }
    """

    def __init__(self, task_obj: Task, is_subtask: bool = False, **kwargs):
        self.task_obj = task_obj
        self.selected = False
        self.is_subtask = is_subtask
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        """Mount and render the task."""
        if self.is_subtask:
            self.add_class("subtask")
        self.update(self.render_task())

    def render_task(self) -> Text:
        """Render task as Rich text."""
        lines = []
        lines.append(self.task_obj.title)

        # Metadata line
        meta_parts = []
        if self.task_obj.priority:
            priority_colors = {
                "P0": "red",
                "P1": "bright_red",
                "P2": "yellow",
                "P3": "green",
                "P4": "dim",
            }
            color = priority_colors.get(self.task_obj.priority.upper(), "white")
            meta_parts.append(f"[{color} bold]!{self.task_obj.priority.upper()}[/{color} bold]")

        if self.task_obj.tags:
            tags_str = " ".join(f"[yellow]#{tag}[/yellow]" for tag in self.task_obj.tags)
            meta_parts.append(tags_str)

        if meta_parts:
            # 子任务的元数据增加缩进
            prefix = "   " if self.is_subtask else ""
            lines.append(prefix + " ".join(meta_parts))

        return Text.from_markup("\n".join(lines))

    def set_selected(self, selected: bool) -> None:
        """Set selected state."""
        self.selected = selected
        if selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")


class ColumnHeader(Static):
    """Header for a kanban column."""

    DEFAULT_CSS = """
    ColumnHeader {
        width: 1fr;
        height: auto;
        padding: 0 1;
        content-align: center middle;
        text-style: bold;
        background: $primary-darken-3;
        color: $text;
    }
    """

    def __init__(self, title: str, **kwargs):
        self.header_title = title
        super().__init__(title, **kwargs)


class KanbanColumn(Vertical):
    """A column in the Kanban board (content only, no header)."""

    DEFAULT_CSS = """
    KanbanColumn {
        width: 1fr;
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    def __init__(self, column: str, **kwargs):
        self.column = column
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield from []

    def add_task(self, task: Task, is_subtask: bool = False) -> TaskCard:
        """Add a task to this column, including its subtasks."""
        card = TaskCard(task, is_subtask=is_subtask)
        self.mount(card)
        
        # 递归添加子任务
        for subtask in task.subtasks:
            self.add_task(subtask, is_subtask=True)
        
        return card

    def clear_tasks(self) -> None:
        """Clear all tasks from this column."""
        self.remove_children()

    def get_task_count(self) -> int:
        """Get the number of tasks in this column."""
        return len(self.children)


class KanbanBoard(Vertical):
    """The main Kanban board widget with header row."""

    DEFAULT_CSS = """
    KanbanBoard {
        width: 100%;
        height: 100%;
    }
    .header-row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    .columns-row {
        width: 100%;
        height: 1fr;
    }
    """

    def __init__(self, board: Board, **kwargs):
        self.board = board
        self.kanban_columns: dict[str, KanbanColumn] = {}
        self._headers: dict[str, ColumnHeader] = {}
        self.selected_task_index = 0
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield TitleBar("TUIDO - TUI based TODO list manage Board")

        # 获取栏目列表
        columns = self.board.get_all_columns()

        # Header row with column titles
        with Horizontal(classes="header-row"):
            for column in columns:
                header = ColumnHeader(column)
                self._headers[column] = header
                yield header

        # Columns row with task content
        with Horizontal(classes="columns-row"):
            for column in columns:
                kanban_column = KanbanColumn(column)
                self.kanban_columns[column] = kanban_column
                yield kanban_column

    def on_mount(self) -> None:
        """Initialize the board with tasks after mounting."""
        self.call_after_refresh(self.refresh_board)

    def refresh_board(self) -> None:
        """Refresh the board display."""
        # 获取当前栏目顺序
        columns = self.board.get_all_columns()

        # 检查是否需要重新创建栏目（栏目数量或顺序变化）
        current_columns = list(self.kanban_columns.keys())
        if current_columns != columns:
            # 需要重新构建UI
            self._rebuild_columns()
            return

        # Clear all columns
        for column in self.kanban_columns.values():
            column.clear_tasks()

        # Add tasks to appropriate columns
        for column, tasks in self.board.columns.items():
            if column in self.kanban_columns:
                for task in tasks:
                    self.kanban_columns[column].add_task(task)

        self.update_selection()

    def _rebuild_columns(self) -> None:
        """Rebuild column widgets when columns change."""
        # 保存当前选中的任务
        selected_task = None
        all_cards = self.get_all_task_cards()
        if all_cards and 0 <= self.selected_task_index < len(all_cards):
            selected_task = all_cards[self.selected_task_index].task_obj

        # 清除现有栏目
        self.kanban_columns.clear()
        self._headers.clear()

        # 重新挂载（通过重新compose）
        # 先移除所有子元素
        for child in list(self.children):
            child.remove()

        # 重新compose
        columns = self.board.get_all_columns()

        # Header row - 先创建并挂载容器
        header_row = Horizontal(classes="header-row")
        self.mount(header_row)
        # 再挂载子组件（容器已挂载到DOM）
        for column in columns:
            header = ColumnHeader(column)
            self._headers[column] = header
            header_row.mount(header)

        # Columns row - 先创建并挂载容器
        columns_row = Horizontal(classes="columns-row")
        self.mount(columns_row)
        # 再挂载子组件（容器已挂载到DOM）
        for column in columns:
            kanban_column = KanbanColumn(column)
            self.kanban_columns[column] = kanban_column
            columns_row.mount(kanban_column)

        # 重新填充任务
        for column, tasks in self.board.columns.items():
            if column in self.kanban_columns:
                for task in tasks:
                    self.kanban_columns[column].add_task(task)

        # 恢复选中状态
        if selected_task:
            all_cards = self.get_all_task_cards()
            for i, card in enumerate(all_cards):
                if card.task_obj == selected_task:
                    self.selected_task_index = i
                    break

        self.update_selection()

    def get_all_task_cards(self) -> list[TaskCard]:
        """Get all task cards across all columns."""
        cards = []
        columns = self.board.get_all_columns()
        for column in columns:
            if column in self.kanban_columns:
                for child in self.kanban_columns[column].children:
                    if isinstance(child, TaskCard):
                        cards.append(child)
        return cards

    def get_visible_columns(self) -> list[str]:
        """Get columns in order."""
        return self.board.get_all_columns()

    def update_selection(self) -> None:
        """Update the visual selection state."""
        all_cards = self.get_all_task_cards()

        # Clear all selections
        for card in all_cards:
            card.set_selected(False)

        # Select current task if any
        if all_cards and 0 <= self.selected_task_index < len(all_cards):
            all_cards[self.selected_task_index].set_selected(True)
            all_cards[self.selected_task_index].scroll_visible()

    def get_selected_task(self) -> tuple[TaskCard | None, str | None]:
        """Get the currently selected task card and its column."""
        all_cards = self.get_all_task_cards()
        if not all_cards or not (0 <= self.selected_task_index < len(all_cards)):
            return None, None

        card = all_cards[self.selected_task_index]
        return card, card.task_obj.column

    def move_task(self, direction: str) -> None:
        """Move task between columns or reorder within column with Shift+Direction."""
        card, current_column = self.get_selected_task()
        if not card or not current_column:
            return

        if direction in ("left", "right"):
            # Check if this is a subtask - subtasks cannot be moved independently
            if card.task_obj.level > 0:
                # Get the app to show notification
                app = self.app
                if app:
                    app.notify("Subtasks cannot be moved independently. They move with their parent task.", severity="warning", timeout=3)
                return

            # Move between columns
            columns = self.get_visible_columns()
            if current_column not in columns:
                return

            current_idx = columns.index(current_column)
            new_column = None

            if direction == "left" and current_idx > 0:
                new_column = columns[current_idx - 1]
            elif direction == "right" and current_idx < len(columns) - 1:
                new_column = columns[current_idx + 1]

            if new_column:
                # Move task to new column in board data
                # Left move: insert at end of left column
                # Right move: insert at start of right column
                insert_at = "end" if direction == "left" else "start"
                self.board.move_task_to_column(card.task_obj, new_column, insert_at)

                # Refresh the entire board
                self.refresh_board()

                # Defer selection update until after DOM refresh
                def update_selection_after_refresh():
                    all_cards = self.get_all_task_cards()
                    for i, c in enumerate(all_cards):
                        if c.task_obj == card.task_obj:
                            self.selected_task_index = i
                            break
                    self.update_selection()

                self.call_after_refresh(update_selection_after_refresh)

        elif direction in ("up", "down"):
            # Reorder within column
            if self.board.reorder_task(card.task_obj, direction):
                # Refresh board to show new order
                self.refresh_board()

                # Defer selection update
                def update_selection_after_refresh():
                    all_cards = self.get_all_task_cards()
                    for i, c in enumerate(all_cards):
                        if c.task_obj == card.task_obj:
                            self.selected_task_index = i
                            break
                    self.update_selection()

                self.call_after_refresh(update_selection_after_refresh)

    def navigate_tasks(self, direction: str) -> None:
        """Navigate between tasks."""
        all_cards = self.get_all_task_cards()
        if not all_cards:
            return

        if direction == "up":
            self.selected_task_index = max(0, self.selected_task_index - 1)
        elif direction == "down":
            self.selected_task_index = min(len(all_cards) - 1, self.selected_task_index + 1)
        elif direction in ("left", "right"):
            self._navigate_horizontal(direction, all_cards)

        self.update_selection()

    def _navigate_horizontal(self, direction: str, all_cards: list[TaskCard]) -> None:
        """Handle left/right navigation between columns."""
        card, current_column = self.get_selected_task()
        if not card or not current_column:
            return

        columns = self.get_visible_columns()
        if current_column not in columns:
            return

        idx = columns.index(current_column)
        offset = -1 if direction == "left" else 1

        # Find next non-empty column (skip empty columns)
        target_column = None
        target_idx = idx + offset
        while 0 <= target_idx < len(columns):
            col = columns[target_idx]
            if col in self.kanban_columns and self.kanban_columns[col].get_task_count() > 0:
                target_column = col
                break
            target_idx += offset

        if target_column is None:
            return

        # Find first task of target column
        for i, c in enumerate(all_cards):
            if c.task_obj.column == target_column:
                self.selected_task_index = i
                break


class TitleBar(Static):
    """Application title bar."""

    DEFAULT_CSS = """
    TitleBar {
        width: 100%;
        content-align: center middle;
        text-style: bold;
    }
    """

    def __init__(self, title: str, **kwargs):
        self.bar_title = title
        super().__init__(title, **kwargs)


class TuidoApp(App):
    """Main TUI application."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "save", "Save"),
        Binding("up", "navigate('up')", "Prev", show=False),
        Binding("down", "navigate('down')", "Next", show=False),
        Binding("left", "navigate('left')", "Left Col", show=False),
        Binding("right", "navigate('right')", "Right Col", show=False),
        Binding("shift+up", "move_task('up')", "Move Up", show=False),
        Binding("shift+down", "move_task('down')", "Move Down", show=False),
        Binding("shift+left", "move_task('left')", "Move Left", show=False),
        Binding("shift+right", "move_task('right')", "Move Right", show=False),
        Binding("h", "navigate('left')", "Left", show=False),
        Binding("j", "navigate('down')", "Down", show=False),
        Binding("k", "navigate('up')", "Up", show=False),
        Binding("l", "navigate('right')", "Right", show=False),
        Binding("shift+k", "move_task('up')", "Move Up", show=False),
        Binding("shift+j", "move_task('down')", "Move Down", show=False),
        Binding("shift+h", "move_task('left')", "Move Left", show=False),
        Binding("shift+l", "move_task('right')", "Move Right", show=False),
        Binding("?", "help", "Help"),
        Binding("t", "change_theme", "Theme"),
    ]

    def __init__(self, board: Board, file_path, **kwargs):
        self.board = board
        self.file_path = file_path
        self._kanban_board = None
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        """Set theme on mount from settings or default."""
        theme = self.board.settings.get("theme", "dracula")
        self.theme = theme

    def compose(self) -> ComposeResult:
        self._kanban_board = KanbanBoard(self.board)
        yield self._kanban_board
        yield Footer()

    def action_navigate(self, direction: str) -> None:
        """Navigate through tasks."""
        if self._kanban_board:
            self._kanban_board.navigate_tasks(direction)

    def action_move_task(self, direction: str) -> None:
        """Move task to adjacent column or reorder."""
        if self._kanban_board:
            self._kanban_board.move_task(direction)

    def action_refresh(self) -> None:
        """Refresh the board."""
        from .parser import parse_todo_file

        self.board = parse_todo_file(self.file_path)
        if self._kanban_board:
            self._kanban_board.board = self.board
            self._kanban_board.refresh_board()
        self.notify("Board refreshed")

    def action_save(self) -> None:
        """Save the board to file."""
        from .parser import save_todo_file

        try:
            save_todo_file(self.file_path, self.board)
            self.notify(f"Saved to {self.file_path}")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    def action_help(self) -> None:
        """Show help dialog."""
        help_text = """
# Keyboard Shortcuts

## Navigation
- ↑/k - Previous task
- ↓/j - Next task
- ←/h - Previous column
- →/l - Next column

## Move Tasks (Between columns)
- Shift+← / Shift+H - Move task to left column
- Shift+→ / Shift+L - Move task to right column

## Reorder Tasks (Within Column / Parent)
- Shift+↑ / Shift+K - Move task up
- Shift+↓ / Shift+J - Move task down
  - Works for both top-level tasks and subtasks

## Actions
- r - Refresh from file
- s - Save to file
- t - Change theme
- q - Quit
- ? - Show this help
"""
        self.notify(help_text, title="Help", timeout=10)

    def action_change_theme(self) -> None:
        """Cycle through available themes."""
        themes = ["dracula", "textual-dark", "nord", "monokai", "solarized-dark"]
        current = self.board.settings.get("theme", "dracula")

        try:
            idx = themes.index(current)
        except ValueError:
            idx = -1

        next_theme = themes[(idx + 1) % len(themes)]
        self.board.settings["theme"] = next_theme
        self.theme = next_theme

        # Auto-save settings
        from .parser import save_todo_file

        try:
            save_todo_file(self.file_path, self.board)
            self.notify(f"Theme changed to: {next_theme}")
        except Exception as e:
            self.notify(f"Theme changed but failed to save: {e}", severity="warning")
