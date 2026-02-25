import re
from pathlib import Path
from .models import Task, Board


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
    """Parse a TODO.md file and return a Board.
    
    栏目(Category)从二级标题(##)读取，按文件中的顺序展示。
    """
    board = Board(title="TODO Board")

    if not file_path.exists():
        # 默认栏目
        board.categories = ["Todo", "In Progress", "Done"]
        return board

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse front matter settings
    settings, start_idx = parse_front_matter(lines)
    board.settings = settings

    current_category = None
    categories_order = []

    for line_num, line in enumerate(lines[start_idx:], start_idx + 1):
        stripped = line.strip()

        if not stripped:
            continue

        # Check for section headers (二级标题 ##)
        if stripped.startswith("## "):
            category_name = stripped[3:].strip()
            current_category = category_name
            if category_name not in categories_order:
                categories_order.append(category_name)
            continue

        # Only parse lines starting with '- '
        if stripped.startswith("- "):
            # 如果没有当前栏目，使用默认值
            if current_category is None:
                current_category = "Todo"
                if current_category not in categories_order:
                    categories_order.append(current_category)
            
            content = stripped[2:].strip()
            metadata = parse_task_content(content)

            task = Task(
                title=metadata["title"],
                category=current_category,
                tags=metadata["tags"],
                priority=metadata["priority"],
                line_number=line_num,
                raw_text=line.rstrip(),
            )
            board.tasks.append(task)

    # 设置栏目顺序（保留有任务和没有任务的栏目）
    board.categories = categories_order if categories_order else ["Todo", "In Progress", "Done"]
    
    return board


def save_todo_file(file_path: Path, board: Board) -> None:
    """Save board back to TODO.md file.
    
    按 board.categories 顺序写入栏目，每个栏目下写入对应任务。
    """
    lines = []
    
    # Write front matter settings at the beginning
    if board.settings:
        lines.append("---\n")
        for key, value in board.settings.items():
            lines.append(f"{key}: {value}\n")
        lines.append("---\n")
        lines.append("\n")
    
    lines.append("# TUIDO\n")
    lines.append("\n")

    def format_task(task: Task) -> str:
        """Format a task as markdown."""
        content = task.title
        if task.tags:
            content += " " + " ".join(f"#{tag}" for tag in task.tags)
        if task.priority:
            content += f" !{task.priority}"
        return f"- {content}"

    # 按栏目顺序写入
    categories_to_write = board.categories if board.categories else ["Todo", "In Progress", "Done"]
    
    for category in categories_to_write:
        tasks = board.get_tasks_by_category(category)
        # 即使栏目没有任务也写入空栏目（保留栏目结构）
        lines.append(f"## {category}\n")
        for task in tasks:
            lines.append(format_task(task) + "\n")
        lines.append("\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
