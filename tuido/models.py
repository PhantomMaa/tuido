"""Data models for tuido."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Self

import yaml


@dataclass
class FeishuConfig:
    """飞书配置模型，自动从 YAML 配置加载."""

    api_endpoint: str = ""
    table_app_token: str = ""
    table_id: str = ""
    table_view_id: str = ""
    bot_app_id: str = ""
    bot_app_secret: str = ""
    theme: str = "dracula"

    @classmethod
    def from_yaml(cls, config_path: Path) -> Self:
        """从 YAML 文件加载配置.

        Args:
            config_path: YAML 配置文件路径

        Returns:
            FeishuConfig 实例
        """
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config or "feishu" not in config:
                return cls()

            feishu = config["feishu"]
            return cls(
                api_endpoint=feishu.get("api_endpoint", ""),
                table_app_token=feishu.get("table_app_token", ""),
                table_id=feishu.get("table_id", ""),
                table_view_id=feishu.get("table_view_id", ""),
                bot_app_id=feishu.get("bot_app_id", ""),
                bot_app_secret=feishu.get("bot_app_secret", ""),
                theme=config.get("theme", "dracula"),
            )
        except (yaml.YAMLError, IOError):
            return cls()

    @classmethod
    def from_default_path(cls) -> Self:
        """从默认路径 ~/.config/tuido/config.yaml 加载配置.

        Returns:
            FeishuConfig 实例
        """
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        return cls.from_yaml(config_path)

    def is_valid(self) -> bool:
        """检查配置是否有效（所有必需字段都已配置）."""
        return all(
            [
                self.api_endpoint,
                self.table_app_token,
                self.table_id,
                self.table_view_id,
                self.bot_app_id,
                self.bot_app_secret,
            ]
        )

    def get_missing_fields(self) -> list[str]:
        """获取缺失的配置字段列表."""
        missing = []
        if not self.api_endpoint:
            missing.append("api_endpoint")
        if not self.table_app_token:
            missing.append("table_app_token")
        if not self.table_id:
            missing.append("table_id")
        if not self.table_view_id:
            missing.append("table_view_id")
        if not self.bot_app_id:
            missing.append("bot_app_id")
        if not self.bot_app_secret:
            missing.append("bot_app_secret")
        return missing


@dataclass
class FeishuTask:
    """Represents a task for Feishu table export."""

    task: str
    project: str
    status: str
    tags: list[str]
    priority: str


@dataclass
class Task:
    """Represents a single task."""

    title: str
    column: str = "Todo"  # 所属栏目名称（对应二级标题）
    tags: list[str] = field(default_factory=list)
    priority: Optional[str] = None
    level: int = 0  # 层级深度，0为父任务，1+为子任务
    parent: Optional["Task"] = None  # 父任务引用
    subtasks: list["Task"] = field(default_factory=list)  # 子任务列表
    project: Optional[str] = None  # 项目名称（用于全局视图）

    def __str__(self) -> str:
        return f"[{self.column}] {self.title}"


@dataclass
class Board:
    """Represents a Kanban board with tasks.

    数据存储结构：columns 是 OrderedDict，key 为栏目名，value 为该栏目下的任务列表。
    栏目顺序由 dict 的 key 顺序决定（Python 3.7+ dict 保持插入顺序）。
    """

    title: str = "TODO Board"
    columns: dict[str, list[Task]] = field(default_factory=dict)
    settings: dict = field(default_factory=dict)

    def get_tasks_by_column(self, column: str) -> list[Task]:
        """Get all tasks in the given column."""
        return self.columns.get(column, [])

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks in file order (by column order, then by position in column)."""
        result = []
        for tasks in self.columns.values():
            result.extend(tasks)
        return result

    def reorder_task(self, task: Task, direction: str) -> bool:
        """Reorder a task within its column or parent. Returns True if reordered."""
        # 确定任务所在的列表（栏目列表或父任务的子任务列表）
        if task.level == 0:
            # 顶级任务：在 column 列表中
            tasks = self.columns.get(task.column, [])
        else:
            if task.parent is None:
                return False

            tasks = task.parent.subtasks

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

    def get_all_columns(self) -> list[str]:
        """Get all columns in order."""
        return list(self.columns.keys()) or ["Todo", "In Progress", "Done"]

    def move_task_to_column(self, task: Task, new_column: str, insert_at: str = "end") -> bool:
        """Move a task to a different column. Returns True if moved.

        Args:
            task: The task to move.
            new_column: The target column name.
            insert_at: Where to insert the task in the new column. "start" for beginning, "end" for end.
        """
        if new_column not in self.columns:
            return False

        old_tasks = self.columns.get(task.column, [])
        if task not in old_tasks:
            return False

        # Remove from old column
        old_tasks.remove(task)
        # Add to new column
        task.column = new_column
        if insert_at == "start":
            self.columns[new_column].insert(0, task)
        else:
            self.columns[new_column].append(task)

        # 递归更新所有子任务的 column 属性
        self._update_subtask_columns(task, new_column)
        return True

    def _update_subtask_columns(self, task: Task, new_column: str) -> None:
        """递归更新子任务的 column 属性。"""
        for subtask in task.subtasks:
            subtask.column = new_column
            self._update_subtask_columns(subtask, new_column)

    @classmethod
    def from_feishu_records(cls, records: list[dict[str, str]]) -> "Board":
        """Create a Board from Feishu table records.

        Args:
            records: List of records from Feishu, each containing Task, Project, Status, Tags, Priority

        Returns:
            Board instance with tasks organized by status (column)
        """
        # Group tasks by status (column)
        columns_data: dict[str, list[Task]] = {}

        for record in records:
            # Extract fields with defaults
            title = record.get("Task", "")
            project = record.get("Project", "")
            status = record.get("Status", "Todo")
            tags_str = record.get("Tags", "")
            priority = record.get("Priority", "")

            # Skip empty tasks
            if not title:
                continue

            # Parse tags
            tags: list[str] = []
            if tags_str:
                if isinstance(tags_str, list):
                    tags = tags_str
                else:
                    tags = [t.strip() for t in str(tags_str).split(",") if t.strip()]

            # Create task - project is stored separately for display in global view
            task = Task(
                title=title,
                column=status,
                tags=tags,
                priority=priority if priority else None,
                project=project if project else None,
            )

            # Add to appropriate column
            if status not in columns_data:
                columns_data[status] = []
            columns_data[status].append(task)

        # Define column order - common status values
        # We'll keep the order: Todo -> In Progress -> Review -> Done
        # Any other statuses will be appended after these
        predefined_order = ["Todo", "In Progress", "Review", "Done"]

        # Build ordered columns dict
        ordered_columns: dict[str, list[Task]] = {}

        # First add predefined columns that exist in data
        for status in predefined_order:
            if status in columns_data:
                ordered_columns[status] = columns_data[status]

        # Then add any other columns not in predefined order
        for status in columns_data:
            if status not in ordered_columns:
                ordered_columns[status] = columns_data[status]

        return cls(
            title="Global Task View",
            columns=ordered_columns,
            settings={"theme": "dracula", "read_only": True},
        )
