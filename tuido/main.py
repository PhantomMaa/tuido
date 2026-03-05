"""Command line interface for tuido."""

import argparse
from pathlib import Path

from tuido.ui import TuidoApp
from tuido.parser import parse_todo_file
from tuido.cmd_create import run_create_command
from tuido.cmd_push import run_push_command
from tuido.cmd_pull import run_pull_command
from tuido.cmd_global_view import run_global_view_command
from tuido.cmd_list import run_list_command
from tuido import util


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="tuido",
        description="A TUI Kanban board for TODO.md files",
    )

    # Global flags
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

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command: tuido list [--status]
    list_parser = subparsers.add_parser(
        "list",
        help="List tasks from TODO.md",
        description="List all tasks or filter by status, tags, priority, etc.",
    )
    list_parser.add_argument(
        "--status",
        type=str,
        help="Filter tasks by status (column name, e.g., 'In Progress')",
    )
    list_parser.add_argument(
        "--tag",
        type=str,
        help="Filter tasks by tag (e.g., 'feature')",
    )
    list_parser.add_argument(
        "--priority",
        type=str,
        help="Filter tasks by priority (e.g., 'P0', 'P1')",
    )

    # push command: tuido push
    subparsers.add_parser(
        "push",
        help="Push tasks to Feishu table (requires remote config in TODO.md)",
        description="Push local tasks to Feishu table.",
    )

    # pull command: tuido pull
    subparsers.add_parser(
        "pull",
        help="Pull tasks from Feishu table (requires remote config in TODO.md)",
        description="Pull remote tasks from Feishu table and update local TODO.md.",
    )

    # global-view command: tuido global-view
    subparsers.add_parser(
        "global-view",
        help="Show global view of all projects from Feishu table",
        description="Fetch all tasks from Feishu and display in TUI (read-only).",
    )

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Resolve the path
    target_path = Path(".").resolve()
    todo_file = util.find_todo_file(target_path)

    # Handle --create flag
    if args.create:
        run_create_command(todo_file)
        return

    # Handle subcommands
    if args.command == "global-view":
        # global-view 不需要本地文件，直接执行
        run_global_view_command()
        return

    # Check if file exists for other commands
    if not todo_file.exists():
        print(f"Error: TODO.md not found at {todo_file}")
        print("Use --create to create a sample file.")
        return

    # Parse the todo file for commands that need it
    if args.command not in ("list", "push", "pull"):
        print(f"Error: Unknown command '{args.command}'")
        return

    board = parse_todo_file(todo_file)
    if args.command == "list":
        # list 子命令
        run_list_command(board, status=args.status, tag=args.tag, priority=args.priority)
        return

    if args.command == "push":
        # push 子命令
        exit_code = run_push_command(board, todo_file)
        return exit_code

    if args.command == "pull":
        # pull 子命令
        exit_code = run_pull_command(board, todo_file)
        return exit_code

    # No subcommand: launch the TUI app (default behavior)
    if not todo_file.exists():
        print(f"Error: TODO.md not found at {todo_file}")
        print("Use --create to create a sample file.")
        return

    board = parse_todo_file(todo_file)
    app = TuidoApp(board, todo_file)
    app.run()


if __name__ == "__main__":
    main()
