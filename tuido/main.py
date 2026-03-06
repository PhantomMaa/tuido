"""Command line interface for tuido using Click."""

import sys
from pathlib import Path

import click
from loguru import logger
from tuido.cmd_add import run_add_command
from tuido.cmd_create import run_create_command
from tuido.cmd_tui import run_tui_command
from tuido.cmd_list import run_list_command, run_list_command_remote
from tuido.cmd_pick import run_pick_command
from tuido.cmd_pull import run_pull_command
from tuido.cmd_push import run_push_command, run_push_command_remote
from tuido.parser import parse_todo_file
from tuido import util


path_option = click.option(
    "--path",
    required=False,
    default=".",
    type=click.Path(exists=False, path_type=Path),
    help="Path to TODO.md or directory",
)


@click.group()
@click.version_option(version="0.1.0", prog_name="tuido")
def cli():
    """A TUI Kanban board for TODO.md file."""


@cli.command(name="tui")
@path_option
@click.option(
    "--remote",
    is_flag=True,
    help="Open remote global view from Feishu table instead of local TODO.md",
)
def tui_command(path: Path, remote: bool) -> int:
    """Open TUI Kanban board."""
    return run_tui_command(path, remote)


@cli.command(name="list")
@path_option
@click.option(
    "--status",
    type=str,
    help="Filter tasks by status (column name, e.g., 'Active')",
)
@click.option(
    "--tag",
    type=str,
    help="Filter tasks by tag (e.g., 'feature')",
)
@click.option(
    "--priority",
    type=str,
    help="Filter tasks by priority (e.g., 'P0', 'P1')",
)
@click.option(
    "--remote",
    is_flag=True,
    help="List tasks from remote Feishu table instead of local TODO.md",
)
def list_command(path: Path, status: str, tag: str, priority: str, remote: bool) -> int:
    """List tasks from TODO.md."""
    if remote:
        # List tasks from remote
        return run_list_command_remote(status=status, tag=tag, priority=priority)

    todo_file = util.find_todo_file(path.resolve())
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    board = parse_todo_file(todo_file)
    run_list_command(board, status=status, tag=tag, priority=priority)
    return 0


@cli.command(name="pick")
@path_option
def pick_command(path: Path) -> int:
    """Pick the top task from a column and move to next column."""
    todo_file = util.find_todo_file(path.resolve())
    return run_pick_command(todo_file)


@cli.command(name="push")
@path_option
@click.option(
    "--remote",
    is_flag=True,
    help="Push all tasks from global view (/tmp/TODO_global.md) to Feishu",
)
def push_command(path: Path, remote: bool) -> int:
    """Push tasks to Feishu table (requires remote config in TODO.md)."""
    if remote:
        # Push from global view
        return run_push_command_remote()

    todo_file = util.find_todo_file(path.resolve())
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    board = parse_todo_file(todo_file)
    return run_push_command(board, todo_file)


@cli.command(name="pull")
@path_option
def pull_command(path: Path) -> int:
    """Pull tasks from Feishu table (requires remote config in TODO.md)."""
    todo_file = util.find_todo_file(path.resolve())
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    board = parse_todo_file(todo_file)
    return run_pull_command(board, todo_file)


@cli.command(name="add")
@click.argument("content", required=True)
@click.option(
    "--path",
    "target_path",
    required=True,
    type=click.Path(exists=False, path_type=Path),
    help="Path to TODO.md or directory",
)
def add_command(content: str, target_path: Path) -> int:
    """Add a new task to TODO.md.

    The content can include tags (#tag) and priority (!P0-4).
    Examples:
        tuido add "Fix login bug #bug !P0"
        tuido add "Update documentation #docs"
    """
    todo_file = util.find_todo_file(target_path.resolve())

    # If file doesn't exist, create it first
    if not todo_file.exists():
        click.echo(f"TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file first.", err=True)
        return 1

    return run_add_command(todo_file, content=content)


@cli.command(name="create")
@path_option
def create_command(path: Path):
    """Create a sample TODO.md if it doesn't exist."""
    todo_file = util.find_todo_file(path.resolve())
    run_create_command(todo_file)


def main():
    """Main entry point."""
    # Remove default logger handler and add one with WARNING level to suppress INFO logs
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="WARNING")

    # Run CLI and exit with the returned exit code
    # Click commands return int exit codes which are propagated here
    sys.exit(cli())


if __name__ == "__main__":
    main()
