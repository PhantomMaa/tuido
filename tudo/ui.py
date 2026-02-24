"""TUI UI components for tudo."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from rich.text import Text

from .models import Task, TaskStatus, Board


class TaskCard(Static):
    """A card displaying a single task."""

    DEFAULT_CSS = """
    TaskCard {
        width: 100%;
        height: auto;
        padding: 0 1;
        margin: 0;
        border: solid $primary-darken-2;
        background: $surface-darken-1;
    }
    TaskCard:hover {
        background: $surface-lighten-1;
    }
    TaskCard.selected {
        border: solid $success;
        background: $surface-lighten-2;
    }
    """

    def __init__(self, task_obj: Task, **kwargs):
        self.task_obj = task_obj
        self.selected = False
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        """Mount and render the task."""
        self.update(self.render_task())

    def render_task(self) -> Text:
        """Render task as Rich text."""
        lines = []

        # Title
        title = self.task_obj.title
        if self.task_obj.status == TaskStatus.DONE:
            title = f"[strike]{title}[/strike]"
        lines.append(f"[bold]{title}[/bold]")

        # Metadata line
        meta_parts = []
        if self.task_obj.priority:
            priority_colors = {
                "high": "red",
                "critical": "red",
                "medium": "yellow",
                "low": "green",
            }
            color = priority_colors.get(self.task_obj.priority, "white")
            meta_parts.append(f"[{color} bold]!{self.task_obj.priority}[/{color} bold]")

        if self.task_obj.tags:
            tags_str = " ".join(
                f"[yellow]#{tag}[/yellow]" for tag in self.task_obj.tags
            )
            meta_parts.append(tags_str)

        if meta_parts:
            lines.append(" ".join(meta_parts))

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
        border: solid $primary-darken-2;
        padding: 0 1;
        overflow-y: auto;
    }
    KanbanColumn:focus-within {
        border: solid $primary;
    }
    """

    def __init__(self, status: TaskStatus, **kwargs):
        self.status = status
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield from []

    def add_task(self, task: Task) -> TaskCard:
        """Add a task to this column."""
        card = TaskCard(task)
        self.mount(card)
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
    }
    .columns-row {
        width: 100%;
        height: 1fr;
    }
    """

    def __init__(self, board: Board, **kwargs):
        self.board = board
        self.columns: dict[TaskStatus, KanbanColumn] = {}
        self._headers: dict[TaskStatus, ColumnHeader] = {}
        self.selected_task_index = 0
        self._column_order = [
            TaskStatus.TODO,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.DONE,
        ]
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        # Header row with column titles
        with Horizontal(classes="header-row"):
            for status in self._column_order:
                title = status.value.replace("_", " ").title()
                header = ColumnHeader(title)
                self._headers[status] = header
                yield header

        # Columns row with task content
        with Horizontal(classes="columns-row"):
            for status in self._column_order:
                column = KanbanColumn(status)
                self.columns[status] = column
                yield column

    def on_mount(self) -> None:
        """Initialize the board with tasks after mounting."""
        self.call_after_refresh(self.refresh_board)

    def refresh_board(self) -> None:
        """Refresh the board display."""
        # Clear all columns
        for column in self.columns.values():
            column.clear_tasks()

        # Add tasks to appropriate columns
        for task in self.board.tasks:
            if task.status in self.columns:
                self.columns[task.status].add_task(task)

        self.update_selection()

    def get_all_task_cards(self) -> list[TaskCard]:
        """Get all task cards across all columns."""
        cards = []
        for status in self._column_order:
            if status in self.columns:
                for child in self.columns[status].children:
                    if isinstance(child, TaskCard):
                        cards.append(child)
        return cards

    def get_visible_columns(self) -> list[TaskStatus]:
        """Get columns in order."""
        return [s for s in self._column_order if s in self.columns]

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

    def get_selected_task(self) -> tuple[TaskCard | None, TaskStatus | None]:
        """Get the currently selected task card and its status."""
        all_cards = self.get_all_task_cards()
        if not all_cards or not (0 <= self.selected_task_index < len(all_cards)):
            return None, None

        card = all_cards[self.selected_task_index]
        return card, card.task_obj.status

    def move_task(self, direction: str) -> None:
        """Move task between columns or reorder within column with Shift+Direction."""
        card, current_status = self.get_selected_task()
        if not card or not current_status:
            return

        if direction in ("left", "right"):
            # Move between columns
            columns = self.get_visible_columns()
            if current_status not in columns:
                return

            current_idx = columns.index(current_status)
            new_status = None

            if direction == "left" and current_idx > 0:
                new_status = columns[current_idx - 1]
            elif direction == "right" and current_idx < len(columns) - 1:
                new_status = columns[current_idx + 1]

            if new_status:
                # Update task status
                card.task_obj.status = new_status

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
            self.selected_task_index = min(
                len(all_cards) - 1, self.selected_task_index + 1
            )
        elif direction in ("left", "right"):
            self._navigate_horizontal(direction, all_cards)

        self.update_selection()

    def _navigate_horizontal(self, direction: str, all_cards: list[TaskCard]) -> None:
        """Handle left/right navigation between columns."""
        card, current_status = self.get_selected_task()
        if not card or not current_status:
            return

        columns = self.get_visible_columns()
        if current_status not in columns:
            return

        idx = columns.index(current_status)
        offset = -1 if direction == "left" else 1
        target_idx = idx + offset

        if not (0 <= target_idx < len(columns)):
            return

        target_status = columns[target_idx]
        if self.columns[target_status].get_task_count() == 0:
            return

        # Find first task of target column
        for i, c in enumerate(all_cards):
            if c.task_obj.status == target_status:
                self.selected_task_index = i
                break


class TudoApp(App):
    """Main TUI application."""

    CSS = """
    Screen {
        align: center middle;
    }
    TudoApp {
        background: $surface-darken-1;
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
    ]

    def __init__(self, board: Board, file_path, **kwargs):
        self.board = board
        self.file_path = file_path
        self._kanban_board = None
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        # 直接显示看板，没有额外的标题栏
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

## Move Tasks (Change Status)
- Shift+← / Shift+H - Move task left (Todo → In Progress → Blocked → Done)
- Shift+→ / Shift+L - Move task right

## Reorder Tasks (Within Column)
- Shift+↑ / Shift+K - Move task up
- Shift+↓ / Shift+J - Move task down

## Actions
- r - Refresh from file
- s - Save to file
- q - Quit
- ? - Show this help
"""
        self.notify(help_text, title="Help", timeout=10)
