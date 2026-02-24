"""Command line interface for tudo."""

import argparse
import sys
from pathlib import Path

from .parser import parse_todo_file
from .ui import TudoApp


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
        prog="tudo",
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
    
    args = parser.parse_args()
    
    # Resolve the path
    target_path = Path(args.path).resolve()
    todo_file = find_todo_file(target_path)
    
    # Create sample file if requested and doesn't exist
    if args.create and not todo_file.exists():
        sample_content = """# TODO

## Todo
- Implement user authentication #feature !high
- Write unit tests #testing
- Update documentation #docs

## In Progress
- Design database schema #backend

## Blocked
- Deploy to production #devops !critical (waiting for approval)

## Done
- Initial project setup #setup
- Create repository structure #setup
"""
        todo_file.write_text(sample_content)
        print(f"Created sample TODO.md at {todo_file}")
    
    # Parse the todo file
    board = parse_todo_file(todo_file)
    
    # Launch the TUI app
    app = TudoApp(board, todo_file)
    app.run()


if __name__ == "__main__":
    main()
