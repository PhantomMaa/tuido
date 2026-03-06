"""Global view command implementation for tuido."""

from pathlib import Path

import click

from tuido import util
from tuido.feishu import fetch_tasks
from tuido.config import load_global_config
from tuido.parser import parse_todo_file, save_todo_file
from tuido.models import Board
from tuido.ui import TuidoApp


# Global temp file path for global view
GLOBAL_VIEW_TEMP_FILE = Path("/tmp/TODO_global.md")


def fetch_remote_to_tmp_file() -> int:
    """Run the global view command.

    Fetches tasks from Feishu and saves them to a temporary file.
    """
    global_config = load_global_config()

    # Check required config values
    if not global_config.remote.is_valid():
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        missing = global_config.remote.get_missing_fields()
        for field in missing:
            print(f"Error: remote.{field} not found in {config_path}")
        return 1

    # Fetch tasks from Feishu
    try:
        print("Fetching global tasks from Feishu...")
        records = fetch_tasks(
            global_config.remote.feishu_api_endpoint,
            global_config.remote.feishu_bot_app_id,
            global_config.remote.feishu_bot_app_secret,
            global_config.remote.feishu_table_app_token,
            global_config.remote.feishu_table_id,
            global_config.remote.feishu_table_view_id,
        )
        print(f"Fetched {len(records)} tasks from Feishu.")

        # Convert to Board
        board = Board.from_feishu_records(records)

        # Apply theme from config if available
        if global_config.theme:
            board.settings["theme"] = global_config.theme
            board.settings["remote"] = global_config.remote.model_dump()

        # Save to temp file
        save_todo_file(GLOBAL_VIEW_TEMP_FILE, board)
        print(f"Global view saved to {GLOBAL_VIEW_TEMP_FILE}")
        return 0
    except Exception as e:
        print(f"Error fetching global tasks: {e}")
        return 1


def run_tui_command(path: Path, remote: bool):
    file_path = path
    if remote:
        exit_code = fetch_remote_to_tmp_file()
        if exit_code != 0:
            raise SystemExit(exit_code)

        file_path = Path(GLOBAL_VIEW_TEMP_FILE)

    todo_file = util.find_todo_file(file_path)
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        raise SystemExit(1)

    board = parse_todo_file(todo_file)
    app = TuidoApp(board, todo_file, global_mode=remote)
    app.run()
