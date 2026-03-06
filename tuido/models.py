"""Data models for tuido."""

from pathlib import Path
from typing import Any, Optional, Self

import yaml
from pydantic import BaseModel, Field


class RemoteConfig(BaseModel):
    """飞书配置模型，自动从 YAML 配置加载.

    配置文件格式:
        remote:
          api_endpoint: https://fsopen.bytedance.net/open-apis
          table_app_token: xxx
          table_id: yyy
          view_id: zzz
          bot_app_id: aaa
          bot_app_secret: bbb
    """

    feishu_api_endpoint: str = ""
    feishu_table_app_token: str = ""
    feishu_table_id: str = ""
    feishu_table_view_id: str = ""
    feishu_bot_app_id: str = ""
    feishu_bot_app_secret: str = ""

    @classmethod
    def from_yaml(cls, config_path: Path) -> Self:
        """从 YAML 文件加载配置.

        Args:
            config_path: YAML 配置文件路径

        Returns:
            RemoteConfig 实例
        """
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config or "remote" not in config:
                return cls()

            remote = config["remote"]
            return cls(
                feishu_api_endpoint=remote.get("feishu_api_endpoint", ""),
                feishu_table_app_token=remote.get("feishu_table_app_token", ""),
                feishu_table_id=remote.get("feishu_table_id", ""),
                feishu_table_view_id=remote.get("feishu_table_view_id", ""),
                feishu_bot_app_id=remote.get("feishu_bot_app_id", ""),
                feishu_bot_app_secret=remote.get("feishu_bot_app_secret", ""),
            )
        except (yaml.YAMLError, IOError):
            return cls()

    def is_valid(self) -> bool:
        """检查配置是否有效（所有必需字段都已配置）."""
        return all(
            [
                self.feishu_api_endpoint,
                self.feishu_table_app_token,
                self.feishu_table_id,
                self.feishu_table_view_id,
                self.feishu_bot_app_id,
                self.feishu_bot_app_secret,
            ]
        )

    def get_missing_fields(self) -> list[str]:
        """获取缺失的配置字段列表."""
        missing = []
        if not self.feishu_api_endpoint:
            missing.append("feishu_api_endpoint")
        if not self.feishu_table_app_token:
            missing.append("feishu_table_app_token")
        if not self.feishu_table_id:
            missing.append("feishu_table_id")
        if not self.feishu_table_view_id:
            missing.append("feishu_table_view_id")
        if not self.feishu_bot_app_id:
            missing.append("feishu_bot_app_id")
        if not self.feishu_bot_app_secret:
            missing.append("feishu_bot_app_secret")
        return missing


class GlobalConfig(BaseModel):
    """全局配置模型，自动从 YAML 配置加载.

    配置文件格式:
        theme: atom-one-dark
        remote:
          api_endpoint: https://fsopen.bytedance.net/open-apis
          table_app_token: xxx
          table_id: yyy
          view_id: zzz
          bot_app_id: aaa
          bot_app_secret: bbb
    """

    theme: str = ""
    remote: RemoteConfig = Field(default_factory=RemoteConfig)

    @classmethod
    def from_yaml(cls, config_path: Path) -> Self:
        """从 YAML 文件加载配置.

        Args:
            config_path: YAML 配置文件路径

        Returns:
            GlobalConfig 实例
        """
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                return cls()

            return cls(
                theme=config.get("theme", ""),
                remote=RemoteConfig.from_yaml(config_path),
            )
        except (yaml.YAMLError, IOError):
            return cls()

    def save(self, config_path: Path) -> None:
        """保存配置到 YAML 文件.

        Args:
            config_path: YAML 配置文件路径
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config: dict[str, Any] = {
            "theme": self.theme,
        }

        # 只保存非空的 remote 配置
        if self.remote and self.remote.is_valid():
            config["remote"] = self.remote.model_dump()

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)


class FeishuTask(BaseModel):
    """Represents a task for Feishu table export."""

    title: str
    project: str | None = None
    status: str = "Todo"  # 对应本地 Task 的 column（栏目）
    tags: list[str] = []
    priority: str = ""
    timestamp: str = ""


class Task(BaseModel):
    """Represents a single task."""

    model_config = {"arbitrary_types_allowed": True}

    title: str
    column: str = "Todo"  # 所属栏目名称（对应二级标题）
    tags: list[str] = []
    priority: Optional[str] = None
    project: Optional[str] = None  # 项目名称（用于全局视图）
    updated_at: Optional[str] = None  # 最后更新时间，格式: YYYY-MM-DDTHH:MM

    def __str__(self) -> str:
        return f"[{self.column}] {self.title}"


class Board(BaseModel):
    """Represents a Kanban board with tasks.

    数据存储结构：columns 是 OrderedDict，key 为栏目名，value 为该栏目下的任务列表。
    栏目顺序由 dict 的 key 顺序决定（Python 3.7+ dict 保持插入顺序）。
    """

    model_config = {"arbitrary_types_allowed": True}

    title: str = "TODO Board"
    columns: dict[str, list[Task]] = {}
    settings: dict = {}

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
        """Reorder a task within its column. Returns True if reordered."""
        tasks = self.columns.get(task.column, [])

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
        return list(self.columns.keys()) or ["Todo", "Active", "Done"]

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

        return True

    def delete_task(self, task: Task) -> bool:
        """Delete a task from the board. Returns True if deleted."""
        tasks = self.columns.get(task.column, [])
        if task in tasks:
            tasks.remove(task)
            return True
        return False

    def add_task(self, title: str, column: str) -> Task | None:
        """Add a new task to the specified column. Returns the created task or None if column doesn't exist."""
        if column not in self.columns:
            return None

        from datetime import datetime

        task = Task(
            title=title,
            column=column,
            updated_at=datetime.now().strftime("%Y-%m-%dT%H:%M"),
        )
        self.columns[column].insert(0, task)
        return task

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
            timestamp = record.get("Timestamp", "")

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
                updated_at=timestamp if timestamp else None,
            )

            # Add to appropriate column
            if status not in columns_data:
                columns_data[status] = []
            columns_data[status].append(task)

        # Define column order - common status values
        # We'll keep the order: Todo -> Active -> Review -> Done
        # Any other statuses will be appended after these
        predefined_order = ["Todo", "Active", "Review", "Done"]

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
            settings={"theme": "dracula"},
        )
