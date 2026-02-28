"""Global view command implementation for tuido."""

from pathlib import Path

from tuido.feishu import fetch_global_tasks
from tuido.config import load_global_config
from tuido.models import Board
from tuido.ui_global_view import GlobalViewApp


def run_global_view_command() -> int:
    """Run the global view command.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = load_global_config()

    # Check required config values
    if not config.is_valid():
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        missing = config.get_missing_fields()
        for field in missing:
            print(f"Error: feishu.{field} not found in {config_path}")
        return 1

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

        # Launch the global view TUI
        app = GlobalViewApp(board, config=config)
        app.run()
        return 0

    except Exception as e:
        print(f"Error fetching global tasks: {e}")
        return 1
