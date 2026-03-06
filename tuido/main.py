"""Command line interface for tuido using Click."""

from pathlib import Path

import click

from tuido.cmd_create import run_create_command
from tuido.cmd_global_view import run_global_view_command
from tuido.cmd_list import run_list_command
from tuido.cmd_pull import run_pull_command
from tuido.cmd_push import run_push_command
from tuido.parser import parse_todo_file
from tuido.ui import TuidoApp
from tuido import util


# Shared path argument
path_argument = click.argument(
    "path",
    required=False,
    default=".",
    type=click.Path(exists=False, path_type=Path),
)


class TuidoGroup(click.Group):
    """Custom group that treats unknown commands as paths for TUI opening."""

    def get_command(self, ctx, cmd_name):
        # First try to get the command normally
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd

        # If cmd_name looks like a path (starts with . or / or ~), treat as 'open'
        # Return None to let Click handle the error, but we'll intercept in main()
        return None

    def resolve_command(self, ctx, args):
        # Check if first arg is a path rather than a command
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            # Check if it looks like a path
            first_arg = args[0]
            if first_arg in (".", "./", "../") or first_arg.startswith(("/", "~", ".")):
                # Treat as open command with path
                return super().resolve_command(ctx, ["open"] + args)
        return super().resolve_command(ctx, args)


@click.group(cls=TuidoGroup, invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="tuido")
@click.option(
    "--path",
    "target_path",
    default=".",
    type=click.Path(exists=False, path_type=Path),
    help="Path to TODO.md or directory (default: current directory)",
)
@click.pass_context
def cli(ctx, target_path):
    """A TUI Kanban board for TODO.md files.
    \b
    Examples:
        tuido .              # Open TUI with current directory's TODO.md
        tuido create         # Create a sample TODO.md
        tuido list           # List all tasks
        tuido push           # Push tasks to Feishu
        tuido pull           # Pull tasks from Feishu
        tuido global-view    # Show global view from Feishu
    """
    # If no subcommand is invoked, open TUI
    if ctx.invoked_subcommand is None:
        _open_tui(target_path.resolve())


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
@path_argument
def open_command(path):
    """Open TUI Kanban board (default behavior)."""
    _open_tui(path.resolve())


@cli.command(name="list")
@path_argument
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
def list_command(path, status, tag, priority):
    """List tasks from TODO.md."""
    todo_file = util.find_todo_file(path.resolve())

    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        raise SystemExit(1)

    board = parse_todo_file(todo_file)
    run_list_command(board, status=status, tag=tag, priority=priority)


@cli.command(name="push")
@path_argument
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
@path_argument
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


@cli.command(name="global-view")
@click.option(
    "--push",
    "push_flag",
    is_flag=True,
    help="Push global view tasks to Feishu table",
)
def global_view_command(push_flag):
    """Show global view of all projects from Feishu table."""
    run_global_view_command(push=push_flag)


@cli.command(name="create")
@path_argument
def create_command(path):
    """Create a sample TODO.md if it doesn't exist."""
    todo_file = util.find_todo_file(path.resolve())
    run_create_command(todo_file)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
