"""Global view command implementation for tuido."""

from pathlib import Path

from tuido.cmd_push import run_push_command
from tuido.feishu import fetch_tasks
from tuido.config import load_global_config
from tuido.models import Board
from tuido.parser import parse_todo_file, save_todo_file
from tuido.ui import TuidoApp


# Global temp file path for global view
GLOBAL_VIEW_TEMP_FILE = Path("/tmp/TODO_global.md")


def run_global_view_command(push: bool = False) -> None:
    """Run the global view command.

    Fetches tasks from Feishu and saves them to a temporary file.

    Returns:
        Path to the temporary file if successful, None otherwise
    """
    if push:
        board = parse_todo_file(GLOBAL_VIEW_TEMP_FILE)
        ## For global view, --push will update all projects in the Feishu table
        run_push_command(board, GLOBAL_VIEW_TEMP_FILE, is_global_view=True)
        return

    config = load_global_config()

    # Check required config values
    if not config.remote.is_valid():
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        missing = config.remote.get_missing_fields()
        for field in missing:
            print(f"Error: remote.{field} not found in {config_path}")
        return None

    # Fetch tasks from Feishu
    try:
        print("Fetching global tasks from Feishu...")
        records = fetch_tasks(
            config.remote.feishu_api_endpoint,
            config.remote.feishu_bot_app_id,
            config.remote.feishu_bot_app_secret,
            config.remote.feishu_table_app_token,
            config.remote.feishu_table_id,
            config.remote.feishu_table_view_id,
        )
        print(f"Fetched {len(records)} tasks from Feishu.")

        # Convert to Board
        board = Board.from_feishu_records(records)

        # Apply theme from config if available
        if config.theme:
            board.settings["theme"] = config.theme
            board.settings["remote"] = config.remote.model_dump()

        # Save to temp file
        save_todo_file(GLOBAL_VIEW_TEMP_FILE, board)
        print(f"Global view saved to {GLOBAL_VIEW_TEMP_FILE}")

        app = TuidoApp(board, GLOBAL_VIEW_TEMP_FILE, is_global_view=True)
        app.run()

    except Exception as e:
        print(f"Error fetching global tasks: {e}")
        return None
