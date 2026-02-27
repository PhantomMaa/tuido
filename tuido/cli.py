"""Command line interface for tuido."""

import argparse
from pathlib import Path
from typing import Any

from .parser import parse_todo_file
from .ui import TuidoApp, GlobalViewApp
from .feishu import FeishuTable, fetch_global_tasks, fetch_existing_tasks
from .models import Board, FeishuTask
from .config import load_global_config


def find_todo_file(path: Path) -> Path:
    """Find TODO.md file in the given path."""
    if path.is_dir():
        # Look for TODO.md or TODO.md in the directory
        for filename in ["TODO.md", "TODO.MD", "todo.md", "Todo.md"]:
            todo_file = path / filename
            if todo_file.exists():
                return todo_file
        # Default to TODO.md if not found
        return path / "TODO.md"
    else:
        return path


def normalize_tags(tags: list[str]) -> str:
    """Normalize tags list to a comparable string."""
    return ", ".join(sorted(tags)) if tags else ""


def task_matches_record(task: FeishuTask, record: dict[str, Any]) -> bool:
    """Check if a FeishuTask matches a Feishu record.

    Returns True if all fields match.
    """
    return (
        task.task == record.get("Task", "")
        and task.project == record.get("Project", "")
        and task.status == record.get("Status", "")
        and normalize_tags(task.tags) == normalize_tags(record.get("Tags", []) if isinstance(record.get("Tags"), list) else record.get("Tags", "").split(", ") if record.get("Tags") else [])
        and task.priority == record.get("Priority", "")
    )


def compare_tasks_with_records(
    local_tasks: list[FeishuTask], remote_records: list[dict[str, Any]]
) -> tuple[list[FeishuTask], list[FeishuTask], list[tuple[FeishuTask, dict[str, Any]]]]:
    """Compare local tasks with remote records.

    Args:
        local_tasks: List of local FeishuTask objects
        remote_records: List of remote records from Feishu

    Returns:
        Tuple of (new_tasks, unchanged_tasks, modified_tasks)
        - new_tasks: Tasks that don't exist in remote
        - unchanged_tasks: Tasks that match exactly with remote
        - modified_tasks: Tasks that exist but have different fields
    """
    # Build a map of remote records by task title for quick lookup
    remote_map: dict[str, dict[str, Any]] = {}
    for record in remote_records:
        task_key = record.get("Task", "")
        if task_key:
            remote_map[task_key] = record

    new_tasks: list[FeishuTask] = []
    unchanged_tasks: list[FeishuTask] = []
    modified_tasks: list[tuple[FeishuTask, dict[str, Any]]] = []

    for task in local_tasks:
        if task.task not in remote_map:
            new_tasks.append(task)
        else:
            remote_record = remote_map[task.task]
            if task_matches_record(task, remote_record):
                unchanged_tasks.append(task)
            else:
                modified_tasks.append((task, remote_record))

    return new_tasks, unchanged_tasks, modified_tasks


def print_diff_preview(
    new_tasks: list[FeishuTask],
    unchanged_tasks: list[FeishuTask],
    modified_tasks: list[tuple[FeishuTask, dict[str, Any]]],
    total_local: int,
    total_remote: int,
) -> None:
    """Print a formatted diff preview."""
    print(f"\n{'='*60}")
    print(f"📊 同步预览: {total_local} 个本地任务 vs {total_remote} 个远程记录")
    print(f"{'='*60}")

    # New tasks
    if new_tasks:
        print(f"\n🟢 新增任务 ({len(new_tasks)} 个):")
        for task in new_tasks:
            print(f"   + [{task.status}] {task.task}")
            if task.tags:
                print(f"     标签: {', '.join(task.tags)}")
            if task.priority:
                print(f"     优先级: {task.priority}")

    # Modified tasks
    if modified_tasks:
        print(f"\n🟡 变更任务 ({len(modified_tasks)} 个):")
        for task, remote in modified_tasks:
            print(f"   ~ [{task.status}] {task.task}")
            # Show field differences
            if task.status != remote.get("Status", ""):
                print(f"     状态: {remote.get('Status', '')} → {task.status}")
            if normalize_tags(task.tags) != normalize_tags(remote.get("Tags", []) if isinstance(remote.get("Tags"), list) else remote.get("Tags", "").split(", ") if remote.get("Tags") else []):
                old_tags = remote.get("Tags", "")
                new_tags = ", ".join(task.tags)
                print(f"     标签: {old_tags} → {new_tags}")
            if task.priority != remote.get("Priority", ""):
                old_priority = remote.get("Priority", "") or "(无)"
                new_priority = task.priority or "(无)"
                print(f"     优先级: {old_priority} → {new_priority}")

    # Unchanged tasks
    if unchanged_tasks:
        print(f"\n⚪ 未变更任务 ({len(unchanged_tasks)} 个):")
        for task in unchanged_tasks:
            print(f"   = [{task.status}] {task.task}")

    print(f"\n{'='*60}")
    print(f"总结: {len(new_tasks)} 新增, {len(modified_tasks)} 变更, {len(unchanged_tasks)} 未变更")
    print(f"{'='*60}\n")


def push_to_feishu(board: Board, project_name: str, dry_run: bool = False) -> bool:
    """Push tasks to Feishu table.

    Args:
        board: The Board object containing tasks
        project_name: Project name to identify tasks in Feishu
        dry_run: If True, only preview changes without pushing

    Returns:
        True if successful, False otherwise
    """
    # Get Feishu config from board settings
    settings = board.settings
    remote_config = settings.get("remote", {})

    api_endpoint = remote_config.get("feishu_api_endpoint")
    feishu_table_app_token = remote_config.get("feishu_table_app_token")
    feishu_table_id = remote_config.get("feishu_table_id")
    feishu_table_view_id = remote_config.get("feishu_table_view_id")

    if not api_endpoint or not feishu_table_app_token or not feishu_table_id or not feishu_table_view_id:
        print("Error: Feishu table configuration not found in TODO.md front matter.")
        print("Please add the following to your TODO.md:")
        print(
            """---
remote:
  feishu_api_endpoint: your_api_endpoint
  feishu_table_app_token: your_app_token
  feishu_table_id: your_table_id
  feishu_table_view_id: your_table_view_id
---"""
        )
        return False

    config = load_global_config()
    if not config.bot_app_id or not config.bot_app_secret:
        print("Error: bot_app_id and bot_app_secret not found in global config.")
        print("Please add the following to ~/.config/tuido/config.yaml:")
        print(
            """feishu:
  bot_app_id: your_bot_app_id
  bot_app_secret: your_bot_app_secret"""
        )
        return False

    # Collect all tasks
    tasks: list[FeishuTask] = []

    def collect_tasks(column_name: str, task_list: list, parent_title: str = ""):
        """Recursively collect tasks and their subtasks."""
        for task in task_list:
            # Build full title with parent prefix if exists
            if parent_title:
                full_title = f"{parent_title} > {task.title}"
            else:
                full_title = task.title

            feishu_task = FeishuTask(
                task=full_title,
                project=project_name,
                status=column_name,
                tags=task.tags,
                priority=task.priority or "",
            )
            tasks.append(feishu_task)

            # Recursively collect subtasks
            if task.subtasks:
                collect_tasks(column_name, task.subtasks, full_title)

    # Iterate through all columns and collect tasks
    for column_name, task_list in board.columns.items():
        collect_tasks(column_name, task_list)

    if not tasks:
        print("No tasks found to push.")
        return True

    # Fetch existing remote records for this project
    try:
        print(f"Fetching existing records from Feishu for project '{project_name}'...")
        remote_records = fetch_existing_tasks(
            api_endpoint,
            config.bot_app_id,
            config.bot_app_secret,
            feishu_table_app_token,
            feishu_table_id,
            feishu_table_view_id,
            project_name,
        )
        print(f"Found {len(remote_records)} existing records.")
    except Exception as e:
        print(f"Error fetching existing records: {e}")
        return False

    # Compare local tasks with remote records
    new_tasks, unchanged_tasks, modified_tasks = compare_tasks_with_records(
        tasks, remote_records
    )

    # Print diff preview
    print_diff_preview(
        new_tasks, unchanged_tasks, modified_tasks, len(tasks), len(remote_records)
    )

    # In dry-run mode, just return after preview
    if dry_run:
        return True

    # Calculate tasks to actually push (new + modified)
    tasks_to_push = new_tasks + [task for task, _ in modified_tasks]

    if not tasks_to_push:
        print("No changes to push. All tasks are already in sync.")
        return True

    # Ask for confirmation
    print(f"即将推送 {len(tasks_to_push)} 个任务到飞书表格:")
    print(f"  - 新增: {len(new_tasks)} 个")
    print(f"  - 变更: {len(modified_tasks)} 个")
    response = input("\n确认执行? (y/N): ").strip().lower()
    if response not in ("y", "yes"):
        print("已取消推送。")
        return True

    # Convert to Feishu records format
    # Note: Tags should be an array for MultiSelect field type
    records = []
    for task in tasks_to_push:
        fields = {
            "Task": task.task,
            "Project": task.project,
            "Status": task.status,
            "Tags": task.tags,
            "Priority": task.priority,
        }
        record = {"fields": fields}
        records.append(record)

    # Initialize Feishu bot and push
    try:
        bot = FeishuTable(api_endpoint, config.bot_app_id, config.bot_app_secret, feishu_table_app_token, feishu_table_id)
        success = bot.batch_create(records)

        if success:
            print(f"Successfully pushed {len(records)} tasks to Feishu table.")
            return True
        else:
            print("Failed to push tasks to Feishu table.")
            return False
    except Exception as e:
        print(f"Error pushing to Feishu: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="tuido",
        description="A TUI Kanban board for TODO.md files",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to TODO.md file or directory containing it (default: .)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create a sample TODO.md if it doesn't exist",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push tasks to Feishu table (requires remote config in TODO.md)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview changes without pushing (shows diff between local and remote)",
    )
    parser.add_argument(
        "--global-view",
        action="store_true",
        dest="global_view",
        help="Show global view of all projects from Feishu table (requires GLOBAL_VIEW_* env vars)",
    )
    args = parser.parse_args()

    # Resolve the path
    target_path = Path(args.path).resolve()
    todo_file = find_todo_file(target_path)

    # Create sample file if requested and doesn't exist
    if args.create and not todo_file.exists():
        sample_content = """# TUIDO
---
theme: textual-dark
---

## Todo
- Implement user authentication #feature !P1
- Write unit tests #testing
  - backend tests #testing
  - frontend tests #testing
- Update documentation #docs

## In Progress
- Design database schema #backend

## Blocked
- Deploy to production #devops !P0

## Done
- Initial project setup #setup
- Create repository structure #setup
"""
        todo_file.write_text(sample_content)
        print(f"Created sample TODO.md at {todo_file}")
        return

    # Handle --global-view command
    if args.global_view:
        config = load_global_config()

        # Check required config values
        if not config.is_valid():
            config_path = Path.home() / ".config" / "tuido" / "config.yaml"
            missing = config.get_missing_fields()
            for field in missing:
                print(f"Error: feishu.{field} not found in {config_path}")
            return 1

        # Fetch tasks from Feishu
        try:
            print("Fetching global tasks from Feishu...")
            records = fetch_global_tasks(
                config.api_endpoint,
                config.bot_app_id,
                config.bot_app_secret,
                config.table_app_token,
                config.table_id,
                config.table_view_id,
            )
            print(f"Fetched {len(records)} tasks from Feishu.")

            # Convert to Board
            board = Board.from_feishu_records(records)

            # Launch the global view TUI
            app = GlobalViewApp(board)
            app.run()
            return 0

        except Exception as e:
            print(f"Error fetching global tasks: {e}")
            return 1

    # Check if file exists
    if not todo_file.exists():
        print(f"Error: TODO.md not found at {todo_file}")
        print("Use --create to create a sample file.")
        return

    # Parse the todo file
    board = parse_todo_file(todo_file)

    # Handle --push or --preview command
    if args.push or args.preview:
        # Determine project name
        project_name: str
        # Use parent directory name as project name
        if todo_file.is_dir():
            project_name = todo_file.name
        else:
            project_name = todo_file.parent.name

        success = push_to_feishu(board, project_name, dry_run=args.preview)
        return 0 if success else 1

    # Launch the TUI app (default behavior)
    app = TuidoApp(board, todo_file)
    app.run()


if __name__ == "__main__":
    main()
