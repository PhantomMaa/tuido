import re
from pathlib import Path
from .models import Task, TaskStatus, Board


def parse_task_content(content: str) -> dict:
    """Parse task content to extract metadata."""
    result = {
        "title": content,
        "tags": [],
        "priority": None,
    }

    # Extract tags (e.g., #bug, #feature)
    tag_pattern = r"#(\w+)"
    tags = re.findall(tag_pattern, content)
    result["tags"] = tags
    result["title"] = re.sub(tag_pattern, "", content).strip()

    # Extract priority (e.g., !high, !medium, !low)
    priority_pattern = r"!((?:high|medium|low|critical))"
    priority_match = re.search(priority_pattern, content, re.IGNORECASE)
    if priority_match:
        result["priority"] = priority_match.group(1).lower()
        result["title"] = re.sub(
            priority_pattern, "", result["title"], flags=re.IGNORECASE
        ).strip()

    return result


def parse_front_matter(lines: list[str]) -> tuple[dict, int]:
    """Parse YAML front matter from the beginning of file.
    
    Standard format:
        ---
        key: value
        ---
        # Title
        content...
    
    Returns (settings_dict, line_index_to_continue_parsing)
    """
    settings = {}
    
    if len(lines) < 2:
        return settings, 0
    
    # File must start with '---'
    if lines[0].strip() != '---':
        return settings, 0
    
    # Find closing '---'
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    
    if end_idx == -1:
        return settings, 0
    
    # Parse settings content between --- markers
    for i in range(1, end_idx):
        line = lines[i].strip()
        if not line or line.startswith('#'):
            continue
        
        # Parse key: value format
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            settings[key] = value
    
    return settings, end_idx + 1


def parse_todo_file(file_path: Path) -> Board:
    """Parse a TODO.md file and return a Board."""
    board = Board(title="TODO Board")

    if not file_path.exists():
        return board

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse front matter settings
    settings, start_idx = parse_front_matter(lines)
    board.settings = settings

    current_status = TaskStatus.TODO

    for line_num, line in enumerate(lines[start_idx:], start_idx + 1):
        stripped = line.strip()

        if not stripped:
            continue

        # Check for section headers
        lower_line = stripped.lower()
        if any(
            header in lower_line
            for header in ["# todo", "# to do", "# to-do", "## todo"]
        ):
            current_status = TaskStatus.TODO
            continue
        elif any(
            header in lower_line
            for header in [
                "# in progress",
                "# in-progress",
                "# doing",
                "## in progress",
            ]
        ):
            current_status = TaskStatus.IN_PROGRESS
            continue
        elif any(
            header in lower_line for header in ["# done", "# completed", "## done"]
        ):
            current_status = TaskStatus.DONE
            continue
        elif any(
            header in lower_line for header in ["# blocked", "# waiting", "## blocked"]
        ):
            current_status = TaskStatus.BLOCKED
            continue

        # Only parse lines starting with '- '
        if stripped.startswith("- "):
            content = stripped[2:].strip()
            metadata = parse_task_content(content)

            task = Task(
                title=metadata["title"],
                status=current_status,
                tags=metadata["tags"],
                priority=metadata["priority"],
                line_number=line_num,
                raw_text=line.rstrip(),
            )
            board.tasks.append(task)

    return board


def save_todo_file(file_path: Path, board: Board) -> None:
    """Save board back to TODO.md file."""
    # Group tasks by status
    todo_tasks = board.get_tasks_by_status(TaskStatus.TODO)
    in_progress_tasks = board.get_tasks_by_status(TaskStatus.IN_PROGRESS)
    blocked_tasks = board.get_tasks_by_status(TaskStatus.BLOCKED)
    done_tasks = board.get_tasks_by_status(TaskStatus.DONE)

    lines = []
    
    # Write front matter settings at the beginning
    if board.settings:
        lines.append("---\n")
        for key, value in board.settings.items():
            lines.append(f"{key}: {value}\n")
        lines.append("---\n")
        lines.append("\n")
    
    lines.append("# TODO\n")
    lines.append("\n")

    def format_task(task: Task) -> str:
        """Format a task as markdown."""
        content = task.title
        if task.tags:
            content += " " + " ".join(f"#{tag}" for tag in task.tags)
        if task.priority:
            content += f" !{task.priority}"
        return f"- {content}"

    # Write sections
    if todo_tasks:
        lines.append("## Todo\n")
        for task in todo_tasks:
            lines.append(format_task(task) + "\n")
        lines.append("\n")

    if in_progress_tasks:
        lines.append("## In Progress\n")
        for task in in_progress_tasks:
            lines.append(format_task(task) + "\n")
        lines.append("\n")

    if blocked_tasks:
        lines.append("## Blocked\n")
        for task in blocked_tasks:
            lines.append(format_task(task) + "\n")
        lines.append("\n")

    if done_tasks:
        lines.append("## Done\n")
        for task in done_tasks:
            lines.append(format_task(task) + "\n")
        lines.append("\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
