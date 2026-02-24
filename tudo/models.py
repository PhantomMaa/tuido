"""Data models for tudo."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskStatus(Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Represents a single task."""

    title: str
    status: TaskStatus = TaskStatus.TODO
    description: str = ""
    tags: list[str] = field(default_factory=list)
    priority: Optional[str] = None
    line_number: int = 0  # Track line number for file updates
    raw_text: str = ""  # Original raw text

    def __str__(self) -> str:
        return f"[{self.status.value}] {self.title}"


@dataclass
class Board:
    """Represents a Kanban board with tasks."""

    title: str = "TODO Board"
    tasks: list[Task] = field(default_factory=list)

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """Get all tasks with the given status."""
        return [t for t in self.tasks if t.status == status]

    def move_task(self, task: Task, new_status: TaskStatus) -> None:
        """Move a task to a new status."""
        task.status = new_status

    def reorder_task(self, task: Task, direction: str) -> bool:
        """Reorder a task within its status group. Returns True if reordered."""
        # Get tasks with same status
        same_status_tasks = [t for t in self.tasks if t.status == task.status]
        
        try:
            current_idx = same_status_tasks.index(task)
        except ValueError:
            return False
        
        if direction == "up" and current_idx > 0:
            # Swap with previous task in same status group
            other_task = same_status_tasks[current_idx - 1]
        elif direction == "down" and current_idx < len(same_status_tasks) - 1:
            # Swap with next task in same status group
            other_task = same_status_tasks[current_idx + 1]
        else:
            return False
        
        # Find indices in main tasks list and swap
        idx1 = self.tasks.index(task)
        idx2 = self.tasks.index(other_task)
        self.tasks[idx1], self.tasks[idx2] = self.tasks[idx2], self.tasks[idx1]
        return True

    def get_all_statuses(self) -> list[TaskStatus]:
        """Get all statuses that have tasks, in order."""
        statuses = []
        for status in [
            TaskStatus.TODO,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.DONE,
        ]:
            if any(t.status == status for t in self.tasks):
                statuses.append(status)
        return (
            statuses
            if statuses
            else [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]
        )
