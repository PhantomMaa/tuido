"""Command line interface for tuido using Click."""

from pathlib import Path

import click
from tuido.cmd_add import run_add_command
from tuido.cmd_create import run_create_command
from tuido.cmd_global_view import run_global_view_command
from tuido.cmd_list import run_list_command, run_list_command_remote
from tuido.cmd_pick import run_pick_command
from tuido.cmd_pull import run_pull_command
from tuido.cmd_push import run_push_command
from tuido.parser import parse_todo_file
from tuido.ui import TuidoApp
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


def _open_tui(path: Path) -> None:
    """Open the TUI with the given path."""
    todo_file = util.find_todo_file(path)

    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        raise SystemExit(1)

    board = parse_todo_file(todo_file)
    app = TuidoApp(board, todo_file)
    app.run()


@cli.command(name="open")
@path_option
@click.option(
    "--remote",
    is_flag=True,
    help="Open remote global view from Feishu table instead of local TODO.md",
)
def open_command(path, remote):
    """Open TUI Kanban board."""
    if remote:
        # Open global view from remote
        run_global_view_command(push=False)
    else:
        _open_tui(path.resolve())


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
def list_command(path, status, tag, priority, remote):
    """List tasks from TODO.md."""
    if remote:
        # List tasks from remote
        exit_code = run_list_command_remote(status=status, tag=tag, priority=priority)
        raise SystemExit(exit_code)

    todo_file = util.find_todo_file(path.resolve())

    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        raise SystemExit(1)

    board = parse_todo_file(todo_file)
    run_list_command(board, status=status, tag=tag, priority=priority)


@cli.command(name="pick")
@path_option
def pick_command(path):
    """Pick the top task from a column and move to next column."""
    todo_file = util.find_todo_file(path.resolve())
    exit_code = run_pick_command(todo_file)
    raise SystemExit(exit_code)


@cli.command(name="push")
@path_option
def push_command(path):
    """Push tasks to Feishu table (requires remote config in TODO.md)."""
    todo_file = util.find_todo_file(path.resolve())

    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        raise SystemExit(1)

    board = parse_todo_file(todo_file)
    exit_code = run_push_command(board, todo_file)
    raise SystemExit(exit_code)


@cli.command(name="pull")
@path_option
def pull_command(path):
    """Pull tasks from Feishu table (requires remote config in TODO.md)."""
    todo_file = util.find_todo_file(path.resolve())

    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        raise SystemExit(1)

    board = parse_todo_file(todo_file)
    exit_code = run_pull_command(board, todo_file)
    raise SystemExit(exit_code)


@cli.command(name="add")
@click.argument("content", required=True)
@click.option(
    "--path",
    "target_path",
    required=True,
    type=click.Path(exists=False, path_type=Path),
    help="Path to TODO.md or directory",
)
def add_command(content, target_path):
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
        raise SystemExit(1)

    exit_code = run_add_command(todo_file, content=content)
    raise SystemExit(exit_code)


@cli.command(name="create")
@path_option
def create_command(path):
    """Create a sample TODO.md if it doesn't exist."""
    todo_file = util.find_todo_file(path.resolve())
    run_create_command(todo_file)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
