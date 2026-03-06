"""List command for tuido."""

from pathlib import Path

from tuido.config import load_global_config
from tuido.feishu import fetch_tasks
from tuido.models import Board, Task


def run_list_command_remote(
    status: str | None = None,
    tag: str | None = None,
    priority: str | None = None,
) -> int:
    """List tasks from remote Feishu table.

    Args:
        status: Optional status/column to filter by (e.g., "Active").
        tag: Optional tag to filter by (e.g., "feature").
        priority: Optional priority to filter by (e.g., "P0", "P1").

    Returns:
        Exit code (0 for success, 1 for error).
    """
    config = load_global_config()

    # Check required config values
    if not config.remote.is_valid():
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        missing = config.remote.get_missing_fields()
        for field in missing:
            print(f"Error: remote.{field} not found in {config_path}")
        return 1

    # Fetch tasks from Feishu
    try:
        records = fetch_tasks(
            config.remote.feishu_api_endpoint,
            config.remote.feishu_bot_app_id,
            config.remote.feishu_bot_app_secret,
            config.remote.feishu_table_app_token,
            config.remote.feishu_table_id,
            config.remote.feishu_table_view_id,
        )

        # Convert to Board
        board = Board.from_feishu_records(records)

        # Run list command with the fetched board
        run_list_command(board, status=status, tag=tag, priority=priority)
        return 0

    except Exception as e:
        print(f"Error fetching tasks from Feishu: {e}")
        return 1


def run_list_command(
    board: Board,
    status: str | None = None,
    tag: str | None = None,
    priority: str | None = None,
) -> None:
    """List tasks, optionally filtered by status, tag, or priority.

    Args:
        board: The parsed board containing tasks.
        status: Optional status/column to filter by (e.g., "Active").
        tag: Optional tag to filter by (e.g., "feature").
        priority: Optional priority to filter by (e.g., "P0", "P1").
    """
    # Collect all tasks from board
    all_tasks: list[Task] = []

    for column_tasks in board.columns.values():
        all_tasks.extend(column_tasks)

    # Apply filters
    filtered_tasks = all_tasks

    if status:
        filtered_tasks = [t for t in filtered_tasks if t.column == status]

    if tag:
        filtered_tasks = [t for t in filtered_tasks if tag in t.tags]

    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority]

    # Display results
    if not filtered_tasks:
        filters = []
        if status:
            filters.append(f"status='{status}'")
        if tag:
            filters.append(f"tag='{tag}'")
        if priority:
            filters.append(f"priority='{priority}'")
        filter_str = ", ".join(filters) if filters else "any tasks"
        print(f"No tasks found matching {filter_str}")
        return

    # Group by column for display
    tasks_by_column: dict[str, list[Task]] = {}
    for task in filtered_tasks:
        col = task.column
        if col not in tasks_by_column:
            tasks_by_column[col] = []
        tasks_by_column[col].append(task)

    # Print tasks grouped by column
    first_column = True
    for column, tasks in tasks_by_column.items():
        if not first_column:
            print()
        first_column = False
        print(f"## {column}")
        for task in tasks:
            print_task(task)


def print_task(task: Task) -> None:
    """Print a single task with its details."""
    line = f"- {task.title}"

    if task.project:
        line += f" [{task.project}]"

    if task.tags:
        line += " " + " ".join(f"#{tag}" for tag in task.tags)

    if task.priority:
        line += f" !{task.priority}"

    if task.updated_at:
        line += f" ~{task.updated_at}"

    print(line)
