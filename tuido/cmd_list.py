"""List command for tuido."""

from tuido.models import Board, Task


def run_list_command(
    board: Board, 
    status: str | None = None, 
    tag: str | None = None,
    priority: str | None = None,
) -> None:
    """List tasks, optionally filtered by status, tag, or priority.

    Args:
        board: The parsed board containing tasks.
        status: Optional status/column to filter by (e.g., "In Progress").
        tag: Optional tag to filter by (e.g., "feature").
        priority: Optional priority to filter by (e.g., "P0", "P1").
    """
    # Collect all tasks from board
    all_tasks: list[Task] = []
    
    def collect_tasks(task_list: list[Task]):
        """Recursively collect tasks including subtasks."""
        for task in task_list:
            all_tasks.append(task)
            if task.subtasks:
                collect_tasks(task.subtasks)
    
    for column_tasks in board.columns.values():
        collect_tasks(column_tasks)
    
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
