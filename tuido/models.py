"""Data models for tuido."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """Represents a single task."""

    title: str
    category: str = "Todo"  # 所属栏目名称（对应二级标题）
    description: str = ""
    tags: list[str] = field(default_factory=list)
    priority: Optional[str] = None
    line_number: int = 0  # Track line number for file updates
    raw_text: str = ""  # Original raw text

    def __str__(self) -> str:
        return f"[{self.category}] {self.title}"


@dataclass
class Board:
    """Represents a Kanban board with tasks.

    数据存储结构：columns 是 OrderedDict，key 为栏目名，value 为该栏目下的任务列表。
    栏目顺序由 dict 的 key 顺序决定（Python 3.7+ dict 保持插入顺序）。
    """

    title: str = "TODO Board"
    columns: dict[str, list[Task]] = field(default_factory=dict)
    settings: dict = field(default_factory=dict)

    def get_tasks_by_category(self, category: str) -> list[Task]:
        """Get all tasks in the given category."""
        return self.columns.get(category, [])

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks in file order (by category order, then by position in category)."""
        result = []
        for tasks in self.columns.values():
            result.extend(tasks)
        return result

    def reorder_task(self, task: Task, direction: str) -> bool:
        """Reorder a task within its category. Returns True if reordered."""
        tasks = self.columns.get(task.category, [])

        try:
            current_idx = tasks.index(task)
        except ValueError:
            return False

        if direction == "up" and current_idx > 0:
            # Swap with previous task
            tasks[current_idx], tasks[current_idx - 1] = tasks[current_idx - 1], tasks[current_idx]
            return True
        elif direction == "down" and current_idx < len(tasks) - 1:
            # Swap with next task
            tasks[current_idx], tasks[current_idx + 1] = tasks[current_idx + 1], tasks[current_idx]
            return True

        return False

    def get_all_categories(self) -> list[str]:
        """Get all categories in order."""
        return list(self.columns.keys()) or ["Todo", "In Progress", "Done"]

    def move_task_to_category(self, task: Task, new_category: str) -> bool:
        """Move a task to a different category. Returns True if moved."""
        if new_category not in self.columns:
            return False

        old_tasks = self.columns.get(task.category, [])
        if task not in old_tasks:
            return False

        # Remove from old category
        old_tasks.remove(task)
        # Add to new category
        task.category = new_category
        self.columns[new_category].append(task)
        return True
