"""Command line interface for tuido."""

import argparse
from pathlib import Path

from .parser import parse_todo_file
from .ui import TuidoApp, GlobalViewApp
from .feishu import FeishuTable, fetch_global_tasks
from .models import Board, FeishuTask
from .envs import bot_app_id, bot_app_secret, global_view_table_app_token, global_view_table_id, global_view_table_view_id


def find_todo_file(path: Path) -> Path:
    """Find TODO.md file in the given path."""
    if path.is_dir():
        # Look for TODO.md or TODO.md in the directory
        for filename in ["TODO.md", "TODO.MD", "todo.md", "Todo.md"]:
            todo_file = path / filename
            if todo_file.exists():
                return todo_file
        # Default to TODO.md if not found
        return path / "TODO.md"
    else:
        return path


def push_to_feishu(board: Board, project_name: str) -> bool:
    """Push tasks to Feishu table.

    Args:
        board: The Board object containing tasks
        project_name: Project name to identify tasks in Feishu

    Returns:
        True if successful, False otherwise
    """
    # Get Feishu config from board settings
    settings = board.settings
    remote_config = settings.get("remote", {})

    table_app_token = remote_config.get("feishu_table_app_token")
    table_id = remote_config.get("feishu_table_id")
    table_view_id = remote_config.get("feishu_table_view_id")

    if not table_app_token or not table_id or not table_view_id:
        print("Error: Feishu table configuration not found in TODO.md front matter.")
        print("Please add the following to your TODO.md:")
        print(
            """---
remote:
  feishu_table_app_token: your_app_token
  feishu_table_id: your_table_id
  feishu_table_view_id: your_table_view_id
---"""
        )
        return False

    # Collect all tasks
    tasks: list[FeishuTask] = []

    def collect_tasks(column_name: str, task_list: list, parent_title: str = ""):
        """Recursively collect tasks and their subtasks."""
        for task in task_list:
            # Build full title with parent prefix if exists
            if parent_title:
                full_title = f"{parent_title} > {task.title}"
            else:
                full_title = task.title

            feishu_task = FeishuTask(
                task=full_title,
                project=project_name,
                status=column_name,
                tags=task.tags,
                priority=task.priority or "",
            )
            tasks.append(feishu_task)

            # Recursively collect subtasks
            if task.subtasks:
                collect_tasks(column_name, task.subtasks, full_title)

    # Iterate through all columns and collect tasks
    for column_name, task_list in board.columns.items():
        collect_tasks(column_name, task_list)

    if not tasks:
        print("No tasks found to push.")
        return True

    # Convert to Feishu records format
    # Note: Tags should be an array for MultiSelect field type
    records = []
    for task in tasks:
        fields = {
            "Task": task.task,
            "Project": task.project,
            "Status": task.status,
            "Tags": task.tags,
            "Priority": task.priority,
        }
        record = {"fields": fields}
        records.append(record)

    # Initialize Feishu bot and push
    try:
        bot = FeishuTable(bot_app_id, bot_app_secret, table_app_token, table_id, table_view_id)
        success = bot.batch_create(records)

        if success:
            print(f"Successfully pushed {len(records)} tasks to Feishu table.")
            return True
        else:
            print("Failed to push tasks to Feishu table.")
            return False
    except Exception as e:
        print(f"Error pushing to Feishu: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="tuido",
        description="A TUI Kanban board for TODO.md files",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to TODO.md file or directory containing it (default: .)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create a sample TODO.md if it doesn't exist",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push tasks to Feishu table (requires remote config in TODO.md)",
    )
    parser.add_argument(
        "--global-view",
        action="store_true",
        dest="global_view",
        help="Show global view of all projects from Feishu table (requires GLOBAL_VIEW_* env vars)",
    )
    args = parser.parse_args()

    # Resolve the path
    target_path = Path(args.path).resolve()
    todo_file = find_todo_file(target_path)

    # Create sample file if requested and doesn't exist
    if args.create and not todo_file.exists():
        sample_content = """# TUIDO
---
theme: textual-dark
---

## Todo
- Implement user authentication #feature !P1
- Write unit tests #testing
  - backend tests #testing
  - frontend tests #testing
- Update documentation #docs

## In Progress
- Design database schema #backend

## Blocked
- Deploy to production #devops !P0

## Done
- Initial project setup #setup
- Create repository structure #setup
"""
        todo_file.write_text(sample_content)
        print(f"Created sample TODO.md at {todo_file}")
        return

    # Handle --global-view command
    if args.global_view:
        # Check required env vars
        if not global_view_table_app_token:
            print("Error: GLOBAL_VIEW_TABLE_APP_TOKEN environment variable not set.")
            print("Please set it in your .env file.")
            return 1
        if not global_view_table_id:
            print("Error: GLOBAL_VIEW_TABLE_ID environment variable not set.")
            print("Please set it in your .env file.")
            return 1
        if not global_view_table_view_id:
            print("Error: GLOBAL_VIEW_TABLE_VIEW_ID environment variable not set.")
            print("Please set it in your .env file.")
            return 1

        # Fetch tasks from Feishu
        try:
            print("Fetching global tasks from Feishu...")
            records = fetch_global_tasks(
                bot_app_id,
                bot_app_secret,
                global_view_table_app_token,
                global_view_table_id,
                global_view_table_view_id,
            )
            print(f"Fetched {len(records)} tasks from Feishu.")

            # Convert to Board
            board = Board.from_feishu_records(records)

            # Launch the global view TUI
            app = GlobalViewApp(board)
            app.run()
            return 0

        except Exception as e:
            print(f"Error fetching global tasks: {e}")
            return 1

    # Check if file exists
    if not todo_file.exists():
        print(f"Error: TODO.md not found at {todo_file}")
        print("Use --create to create a sample file.")
        return

    # Parse the todo file
    board = parse_todo_file(todo_file)

    # Handle --push command
    if args.push:
        # Determine project name
        project_name: str
        # Use parent directory name as project name
        if todo_file.is_dir():
            project_name = todo_file.name
        else:
            project_name = todo_file.parent.name

        success = push_to_feishu(board, project_name)
        return 0 if success else 1

    # Launch the TUI app (default behavior)
    app = TuidoApp(board, todo_file)
    app.run()


if __name__ == "__main__":
    main()
