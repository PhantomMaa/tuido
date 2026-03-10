"""Command line interface for tuido using Click."""

import sys
from pathlib import Path

import click
from loguru import logger
from tuido.cmd_add import run_add_command, run_add_command_remote
from tuido.cmd_create import run_create_command
from tuido.cmd_tui import run_tui_command
from tuido.cmd_list import run_list_command, run_list_command_remote
from tuido.cmd_pull import run_pull_command
from tuido.cmd_push import run_push_command, run_push_command_remote
from tuido.parser import parse_todo_file
from tuido import util


@click.group(invoke_without_command=False)
@click.version_option(version="0.1.0", prog_name="tuido")
@click.option(
    "--path",
    required=False,
    default=".",
    type=click.Path(exists=False, path_type=Path),
    help="Path to TODO.md or directory",
)
@click.option(
    "--remote",
    is_flag=True,
    help="Use remote Feishu table (only for tui/list/push/add commands)",
)
@click.pass_context
def cli(ctx: click.Context, path: Path, remote: bool):
    """A TUI Kanban board for TODO.md file."""
    # Store global options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["path"] = path
    ctx.obj["remote"] = remote


@cli.command(name="tui")
@click.pass_context
def tui_command(ctx: click.Context) -> int:
    """Open TUI Kanban board."""
    path = ctx.obj["path"]
    remote = ctx.obj["remote"]
    return run_tui_command(path, remote)


@cli.command(name="list")
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
@click.pass_context
def list_command(ctx: click.Context, status: str, tag: str, priority: str) -> int:
    """List tasks from TODO.md."""
    path = ctx.obj["path"]
    remote = ctx.obj["remote"]
    
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


@cli.command(name="push")
@click.pass_context
def push_command(ctx: click.Context) -> int:
    """Push tasks to Feishu table (requires remote config in TODO.md)."""
    path = ctx.obj["path"]
    remote = ctx.obj["remote"]
    
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
@click.pass_context
def pull_command(ctx: click.Context) -> int:
    """Pull tasks from Feishu table (requires remote config in TODO.md)."""
    path = ctx.obj["path"]
    remote = ctx.obj["remote"]
    
    if remote:
        click.echo("Error: --remote is not supported for pull command", err=True)
        ctx.exit(1)

    todo_file = util.find_todo_file(path.resolve())
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    board = parse_todo_file(todo_file)
    return run_pull_command(board, todo_file)

    todo_file = util.find_todo_file(path.resolve())
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    board = parse_todo_file(todo_file)
    return run_pull_command(board, todo_file)


@cli.command(name="add")
@click.argument("content", required=True)
@click.pass_context
def add_command(ctx: click.Context, content: str) -> int:
    """Add a new task to TODO.md or Feishu.

    If TODO.md exists locally, the task will be added to it.
    Use --remote to add directly to Feishu table.

    The content can include tags (#tag) and priority (!P0-4).
    Examples:
        tuido add 'Fix login bug #bug !P0'
        tuido add 'Update documentation #docs'
        tuido add 'New feature #enhancement !P1' --remote
    """
    path = ctx.obj["path"]
    remote = ctx.obj["remote"]
    
    if remote:
        # Add task to remote
        return run_add_command_remote(content)

    todo_file = util.find_todo_file(path.resolve())
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    return run_add_command(todo_file, content)


@cli.command(name="create")
@click.pass_context
def create_command(ctx: click.Context) -> int:
    """Create a sample TODO.md if it doesn't exist."""
    path = ctx.obj["path"]
    remote = ctx.obj["remote"]
    
    if remote:
        click.echo("Error: --remote is not supported for create command", err=True)
        ctx.exit(1)
    
    todo_file = util.find_todo_file(path.resolve())
    result = run_create_command(todo_file)
    return result if result is not None else 0


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
