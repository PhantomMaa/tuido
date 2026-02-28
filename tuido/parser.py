import re
from pathlib import Path
from .models import Task, Board


def parse_task_content(content: str) -> dict:
    """Parse task content to extract metadata."""
    result = {
        "title": content,
        "tags": [],
        "priority": None,
        "updated_at": None,
    }

    # Extract tags (e.g., #bug, #feature)
    tag_pattern = r"#(\w+)"
    tags = re.findall(tag_pattern, content)
    result["tags"] = tags
    result["title"] = re.sub(tag_pattern, "", content).strip()

    # Extract priority (e.g., !P0, !P1, !P2, !P3, !P4)
    priority_pattern = r"!([Pp][0-4])"
    priority_match = re.search(priority_pattern, content)
    if priority_match:
        result["priority"] = priority_match.group(1).upper()
        result["title"] = re.sub(
            priority_pattern, "", result["title"]
        ).strip()

    # Extract timestamp (e.g., ~2026-02-28T14:30)
    timestamp_pattern = r"~(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})"
    timestamp_match = re.search(timestamp_pattern, content)
    if timestamp_match:
        result["updated_at"] = timestamp_match.group(1)
        result["title"] = re.sub(timestamp_pattern, "", result["title"]).strip()

    return result


def parse_front_matter(lines: list[str]) -> tuple[dict, int]:
    """Parse YAML front matter from the beginning of file.
    
    Standard format:
        ---
        key: value
        nested:
          subkey: subvalue
        ---
        # Title
        content...
    
    Supports nested blocks with 2-space indentation.
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
    
    # Parse settings content between --- markers with support for nested blocks
    current_nested_key = None
    
    for i in range(1, end_idx):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            continue
        
        # Check if this is a nested block start (key: with no value, followed by indented content)
        # or a simple key: value
        if ':' in stripped:
            key, value = stripped.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Check if next non-empty line is indented (indicating a nested block)
            next_line_indent = 0
            for j in range(i + 1, end_idx):
                next_stripped = lines[j].strip()
                if next_stripped and not next_stripped.startswith('#'):
                    next_line_indent = len(lines[j]) - len(lines[j].lstrip())
                    break
            
            current_indent = len(line) - len(line.lstrip())
            
            if not value and next_line_indent > current_indent:
                # This is a nested block start
                current_nested_key = key
                settings[key] = {}
            elif current_nested_key is not None:
                # Check if this line is indented under current nested block
                if current_indent > 0:
                    settings[current_nested_key][key] = value
                else:
                    # Back to top level
                    current_nested_key = None
                    settings[key] = value
            else:
                # Top level key-value
                settings[key] = value
        elif current_nested_key is not None:
            # Handle lines that might be part of nested block but don't have ':'
            current_indent = len(line) - len(line.lstrip())
            if current_indent == 0:
                current_nested_key = None
    
    return settings, end_idx + 1


def parse_todo_file(file_path: Path) -> Board:
    """Parse a TODO.md file and return a Board.
    
    栏目(Column)从二级标题(##)读取，按文件中的顺序展示。
    支持层级任务（通过缩进表示）。
    """
    board = Board(title="TODO Board")

    if not file_path.exists():
        # 默认栏目
        board.columns = {"Todo": [], "In Progress": [], "Done": []}
        return board

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse front matter settings
    settings, start_idx = parse_front_matter(lines)
    board.settings = settings

    current_column = None
    parent_stack: list[Task] = []  # 用于跟踪父任务层级

    for _, line in enumerate(lines[start_idx:], start_idx + 1):
        stripped = line.strip()

        if not stripped:
            continue

        # Check for section headers (二级标题 ##)
        if stripped.startswith("## "):
            column_name = stripped[3:].strip()
            current_column = column_name
            # 确保栏目存在（保留空栏目）
            if column_name not in board.columns:
                board.columns[column_name] = []
            # 切换栏目时清空父任务栈
            parent_stack.clear()
            continue

        # Only parse lines starting with '- '
        if stripped.startswith("- "):
            # 如果没有当前栏目，使用默认值
            if current_column is None:
                current_column = "Todo"
                if current_column not in board.columns:
                    board.columns[current_column] = []
            
            # 计算层级深度（通过前导空格数）
            leading_spaces = len(line) - len(line.lstrip())
            level = leading_spaces // 2  # 每2个空格一个层级
            
            content = stripped[2:].strip()
            metadata = parse_task_content(content)

            task = Task(
                title=metadata["title"],
                column=current_column,
                tags=metadata["tags"],
                priority=metadata["priority"],
                level=level,
                updated_at=metadata["updated_at"],
            )
            
            # 处理层级关系
            # 调整父任务栈到当前层级
            while len(parent_stack) > level:
                parent_stack.pop()
            
            if level > 0 and parent_stack:
                # 这是一个子任务
                parent = parent_stack[-1]
                task.parent = parent
                parent.subtasks.append(task)
            else:
                # 这是一个顶级任务，清空栈并从当前开始
                parent_stack.clear()
            
            # 将当前任务加入栈（它可能是后续任务的父任务）
            parent_stack.append(task)
            
            # 只将顶级任务加入栏目列表
            if level == 0:
                board.columns[current_column].append(task)

    # 如果没有解析到任何栏目，使用默认值
    if not board.columns:
        board.columns = {"Todo": [], "In Progress": [], "Done": []}
    
    return board


def save_todo_file(file_path: Path, board: Board) -> None:
    """Save board back to TODO.md file.

    按 board.columns 顺序写入栏目，每个栏目下写入对应任务。
    支持层级任务（通过缩进表示）。
    """
    import yaml

    lines = []

    # Write front matter settings at the beginning
    if board.settings:
        lines.append("---\n")
        # Use YAML dump for proper nested structure handling
        yaml_content = yaml.safe_dump(
            board.settings,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        lines.append(yaml_content)
        lines.append("---\n")
        lines.append("\n")
    
    lines.append("# TUIDO\n")
    lines.append("\n")

    def format_task(task: Task, indent_level: int = 0) -> str:
        """Format a task as markdown with proper indentation."""
        indent = "  " * indent_level
        content = task.title
        if task.tags:
            content += " " + " ".join(f"#{tag}" for tag in task.tags)
        if task.priority:
            content += f" !{task.priority.upper()}"
        if task.updated_at:
            content += f" ~{task.updated_at}"
        return f"{indent}- {content}"
    
    def write_task_with_subtasks(task: Task, indent_level: int = 0) -> list[str]:
        """递归写入任务及其子任务。"""
        result = [format_task(task, indent_level) + "\n"]
        for subtask in task.subtasks:
            result.extend(write_task_with_subtasks(subtask, indent_level + 1))
        return result

    # 按栏目顺序写入（board.columns 是有序 dict）
    for column, tasks in board.columns.items():
        # 即使栏目没有任务也写入空栏目（保留栏目结构）
        lines.append(f"## {column}\n")
        for task in tasks:
            lines.extend(write_task_with_subtasks(task))
        lines.append("\n")

    # Join lines and strip trailing whitespace to avoid extra blank lines at end
    content = "".join(lines).rstrip()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
