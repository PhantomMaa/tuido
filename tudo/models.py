"""Data models for tudo."""

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
    """Represents a Kanban board with tasks."""

    title: str = "TODO Board"
    tasks: list[Task] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)  # 栏目顺序列表

    def get_tasks_by_category(self, category: str) -> list[Task]:
        """Get all tasks in the given category."""
        return [t for t in self.tasks if t.category == category]

    def move_task(self, task: Task, new_category: str) -> None:
        """Move a task to a new category."""
        task.category = new_category

    def reorder_task(self, task: Task, direction: str) -> bool:
        """Reorder a task within its category. Returns True if reordered."""
        # Get tasks in same category
        same_category_tasks = [t for t in self.tasks if t.category == task.category]

        try:
            current_idx = same_category_tasks.index(task)
        except ValueError:
            return False

        if direction == "up" and current_idx > 0:
            # Swap with previous task in same category
            other_task = same_category_tasks[current_idx - 1]
        elif direction == "down" and current_idx < len(same_category_tasks) - 1:
            # Swap with next task in same category
            other_task = same_category_tasks[current_idx + 1]
        else:
            return False

        # Find indices in main tasks list and swap
        idx1 = self.tasks.index(task)
        idx2 = self.tasks.index(other_task)
        self.tasks[idx1], self.tasks[idx2] = self.tasks[idx2], self.tasks[idx1]
        return True

    def get_all_categories(self) -> list[str]:
        """Get all categories in order.
        
        优先使用 self.categories 中定义的顺序，
        对于没有在 categories 列表中的任务，按出现顺序追加。
        """
        # 从预设顺序中获取有任务的栏目
        result = []
        seen = set()
        
        for cat in self.categories:
            if any(t.category == cat for t in self.tasks):
                result.append(cat)
                seen.add(cat)
        
        # 追加未在预设顺序中的栏目（按任务出现顺序）
        for task in self.tasks:
            if task.category not in seen:
                result.append(task.category)
                seen.add(task.category)
        
        return result if result else ["Todo", "In Progress", "Done"]

    def add_category(self, category: str) -> None:
        """Add a category if not exists."""
        if category not in self.categories:
            self.categories.append(category)

    def move_category(self, category: str, direction: str) -> bool:
        """Move a category left or right in the order."""
        if category not in self.categories:
            return False
        
        idx = self.categories.index(category)
        if direction == "left" and idx > 0:
            self.categories[idx], self.categories[idx - 1] = self.categories[idx - 1], self.categories[idx]
            return True
        elif direction == "right" and idx < len(self.categories) - 1:
            self.categories[idx], self.categories[idx + 1] = self.categories[idx + 1], self.categories[idx]
            return True
        return False
