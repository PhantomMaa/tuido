"""TUI UI components for tuido."""

from textual.app import App, ComposeResult
from textual.widgets import Footer
from textual.binding import Binding
from tuido.ui_local import KanbanBoard
from tuido.models import Board, FeishuConfig
from tuido.config import save_global_theme


class GlobalViewBoard(KanbanBoard):
    """Read-only Kanban board for global view (no move operations)."""

    def move_task(self, direction: str) -> None:
        """Disable task movement in global view."""
        app = self.app
        if app:
            app.notify("Global view is read-only. Task movement is disabled.", severity="warning", timeout=3)


class GlobalViewApp(App):
    """Read-only TUI application for global task view."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
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

    def __init__(self, board: Board, config: FeishuConfig | None = None, **kwargs):
        self.board = board
        self.config = config
        self._kanban_board = None
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        """Set theme on mount from config, settings or default."""
        # Priority: config.theme > board.settings > default
        if self.config and self.config.theme:
            theme = self.config.theme
        else:
            theme = self.board.settings.get("theme", "dracula")
        self.theme = theme

    def compose(self) -> ComposeResult:
        self._kanban_board = GlobalViewBoard(self.board)
        yield self._kanban_board
        yield Footer()

    def action_navigate(self, direction: str) -> None:
        """Navigate through tasks."""
        if self._kanban_board:
            self._kanban_board.navigate_tasks(direction)

    def action_move_task(self, direction: str) -> None:
        """Disabled in global view."""
        self.notify("Global view is read-only. Task movement is disabled.", severity="warning", timeout=3)

    def action_refresh(self) -> None:
        """Refresh is not supported in global view."""
        self.notify("Refresh not available in global view. Restart to get latest data.", severity="information", timeout=3)

    def action_save(self) -> None:
        """Save is disabled in global view."""
        self.notify("Global view is read-only. Save is disabled.", severity="warning", timeout=3)

    def action_help(self) -> None:
        """Show help dialog."""
        help_text = """
# Global View - Keyboard Shortcuts

## Navigation
- ↑/k - Previous task
- ↓/j - Next task
- ←/h - Previous column
- →/l - Next column

## Move Tasks (Disabled in Global View)
- Shift+← / Shift+H - Move task to left column (disabled)
- Shift+→ / Shift+L - Move task to right column (disabled)
- Shift+↑ / Shift+K - Move task up (disabled)
- Shift+↓ / Shift+J - Move task down (disabled)

## Actions
- t - Change theme
- q - Quit
- ? - Show this help

Note: This is a read-only global view. Tasks cannot be moved or edited.
"""
        self.notify(help_text, title="Global View Help", timeout=10)

    def action_change_theme(self) -> None:
        """Cycle through available themes."""
        themes = ["dracula", "textual-dark", "nord", "monokai", "solarized-dark"]
        # Get current theme from config or board settings
        if self.config and self.config.theme:
            current = self.config.theme
        else:
            current = self.board.settings.get("theme", "dracula")

        try:
            idx = themes.index(current)
        except ValueError:
            idx = -1

        next_theme = themes[(idx + 1) % len(themes)]
        self.board.settings["theme"] = next_theme
        self.theme = next_theme

        # Save to global config
        try:
            save_global_theme(next_theme)
            self.notify(f"Theme changed to: {next_theme}")
        except Exception as e:
            self.notify(f"Theme changed but failed to save: {e}", severity="warning")
