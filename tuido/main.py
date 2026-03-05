"""Command line interface for tuido."""

import argparse
from pathlib import Path

from tuido.parser import parse_todo_file
from tuido.ui import TuidoApp
from tuido.cmd_create import run_create_command
from tuido.cmd_push import run_push_command
from tuido.cmd_pull import run_pull_command
from tuido.cmd_global_view import run_global_view_command
from tuido.cmd_list import run_list_command
from tuido import util


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="tuido",
        description="A TUI Kanban board for TODO.md files",
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
        "--pull",
        action="store_true",
        help="Pull tasks from Feishu table (requires remote config in TODO.md)",
    )
    parser.add_argument(
        "--global-view",
        action="store_true",
        dest="global_view",
        help="Show global view of all projects from Feishu table (requires GLOBAL_VIEW_* env vars)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List tasks (use --status to filter by status)",
    )
    parser.add_argument(
        "--status",
        type=str,
        help="Filter tasks by status (column name, e.g., 'In Progress')",
    )
    args = parser.parse_args()

    # Handle --global-view command
    if args.global_view:
        run_global_view_command(args.push)
        return

    # Resolve the path
    target_path = Path(".").resolve()
    todo_file = util.find_todo_file(target_path)

    # Create sample file if requested
    if args.create:
        run_create_command(todo_file)
        return

    # Check if file exists
    if not todo_file.exists():
        print(f"Error: TODO.md not found at {todo_file}")
        print("Use --create to create a sample file.")
        return

    # Parse the todo file
    board = parse_todo_file(todo_file)

    # Handle --push command
    if args.push:
        return run_push_command(board, todo_file)

    # Handle --pull command
    if args.pull:
        return run_pull_command(board, todo_file)

    # Handle --list command
    if args.list:
        return run_list_command(board, args.status)

    # Launch the TUI app (default behavior)
    app = TuidoApp(board, todo_file)
    app.run()


if __name__ == "__main__":
    main()
