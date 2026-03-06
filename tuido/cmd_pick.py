"""Pick command for tuido - pick the top task and move to next column."""

from pathlib import Path
import click
from tuido.parser import parse_todo_file, save_todo_file


def run_pick_command(todo_file: Path) -> int:
    """Pick the top task from a column and move it to the next column.

    Args:
        todo_file: Path to TODO.md file
        from_column: Column to pick from (default: first column)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Check file exists
    if not todo_file.exists():
        click.echo(f"Error: TODO.md not found at {todo_file}", err=True)
        click.echo("Use 'tuido create' to create a sample file.", err=True)
        return 1

    # Parse the board
    board = parse_todo_file(todo_file)

    # Get all columns in order
    columns = board.get_all_columns()
    if not columns:
        click.echo("Error: No columns found in TODO.md", err=True)
        return 1

    # First column by default
    source_column = columns[0]

    # Get tasks from source column
    tasks = board.get_tasks_by_column(source_column)
    if not tasks:
        click.echo(f"No tasks found in '{source_column}' column")
        return 0

    # Get the top task (first task)
    task = tasks[0]

    # Determine target column (next column)
    source_idx = columns.index(source_column)
    if source_idx >= len(columns) - 1:
        click.echo(f"Error: Cannot move task - '{source_column}' is the last column", err=True)
        return 1

    target_column = columns[source_idx + 1]

    # Move task to target column
    if not board.move_task_to_column(task, target_column):
        click.echo(f"Error: Failed to move task to '{target_column}'", err=True)
        return 1

    # Save the board
    save_todo_file(todo_file, board)

    # Print the picked task
    click.echo(task.title)

    return 0
