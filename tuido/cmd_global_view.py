"""Global view command implementation for tuido."""

from pathlib import Path

from tuido.feishu import fetch_global_tasks
from tuido.config import load_global_config
from tuido.models import Board
from tuido.parser import save_todo_file


# Global temp file path for global view
GLOBAL_VIEW_TEMP_FILE = Path("/tmp/TODO_global.md")


def run_global_view_command() -> Path | None:
    """Run the global view command.

    Fetches tasks from Feishu and saves them to a temporary file.

    Returns:
        Path to the temporary file if successful, None otherwise
    """
    config = load_global_config()

    # Check required config values
    if not config.is_valid():
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        missing = config.get_missing_fields()
        for field in missing:
            print(f"Error: feishu.{field} not found in {config_path}")
        return None

    # Fetch tasks from Feishu
    try:
        print("Fetching global tasks from Feishu...")
        records = fetch_global_tasks(
            config.api_endpoint,
            config.bot_app_id,
            config.bot_app_secret,
            config.table_app_token,
            config.table_id,
            config.table_view_id,
        )
        print(f"Fetched {len(records)} tasks from Feishu.")

        # Convert to Board
        board = Board.from_feishu_records(records)

        # Apply theme from config if available
        if config.theme:
            board.settings["theme"] = config.theme

        # Save to temp file
        save_todo_file(GLOBAL_VIEW_TEMP_FILE, board)
        print(f"Global view saved to {GLOBAL_VIEW_TEMP_FILE}")

        return GLOBAL_VIEW_TEMP_FILE

    except Exception as e:
        print(f"Error fetching global tasks: {e}")
        return None
