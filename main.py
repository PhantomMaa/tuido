"""Command line interface for tuido."""

import argparse
from pathlib import Path

from tuido.parser import parse_todo_file
from tuido.ui import TuidoApp
from tuido.cmd_create import run_create_command
from tuido.cmd_push import run_push_command
from tuido.cmd_global_view import run_global_view_command


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
        "--preview",
        action="store_true",
        help="Preview changes without pushing (shows diff between local and remote)",
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

    # Create sample file if requested
    if args.create:
        run_create_command(todo_file)
        return

    # Handle --global-view command
    if args.global_view:
        return run_global_view_command()

    # Check if file exists
    if not todo_file.exists():
        print(f"Error: TODO.md not found at {todo_file}")
        print("Use --create to create a sample file.")
        return

    # Parse the todo file
    board = parse_todo_file(todo_file)

    # Handle --push or --preview command
    if args.push or args.preview:
        return run_push_command(board, todo_file, dry_run=args.preview)

    # Launch the TUI app (default behavior)
    app = TuidoApp(board, todo_file)
    app.run()


if __name__ == "__main__":
    main()
