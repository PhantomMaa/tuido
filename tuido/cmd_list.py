"""List command for tuido."""

from tuido.models import Board, Task


def run_list_command(board: Board, status: str | None = None) -> None:
    """List tasks, optionally filtered by status.

    Args:
        board: The parsed board containing tasks.
        status: Optional status/column to filter by (e.g., "In Progress").
    """
    # Filter tasks by status if specified
    if status:
        tasks = board.columns.get(status, [])
        if not tasks:
            print(f"No tasks found with status: {status}")
            return
        print(f"## {status}\n")
        for task in tasks:
            print_task(task)
    else:
        # List all tasks grouped by column
        for column, tasks in board.columns.items():
            if tasks:
                print(f"## {column}\n")
                for task in tasks:
                    print_task(task)
                print()


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
