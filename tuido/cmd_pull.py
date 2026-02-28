"""Pull command implementation for tuido."""

from pathlib import Path
from typing import Any

from tuido.feishu import fetch_project_tasks
from tuido.models import Board, FeishuTask, Task
from tuido.config import load_global_config
from tuido.parser import save_todo_file


def normalize_tags(tags: list[str]) -> str:
    """Normalize tags list to a comparable string."""
    return ", ".join(sorted(tags)) if tags else ""


def record_to_feishu_task(record: dict[str, Any]) -> FeishuTask:
    """Convert a Feishu record to FeishuTask object."""
    tags = record.get("Tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return FeishuTask(
        task=record.get("Task", ""),
        project=record.get("Project", ""),
        status=record.get("Status", ""),
        tags=tags,
        priority=record.get("Priority", ""),
    )


def feishu_task_to_task(feishu_task: FeishuTask) -> Task:
    """Convert a FeishuTask to local Task object."""
    return Task(
        title=feishu_task.task,
        column=feishu_task.status,
        tags=feishu_task.tags,
        priority=feishu_task.priority if feishu_task.priority else None,
    )


def task_matches_record(task: Task, feishu_task: FeishuTask) -> bool:
    """Check if a local Task matches a FeishuTask.

    Returns True if all fields match.
    """
    # Extract tags from task
    task_tags = normalize_tags(task.tags)
    feishu_tags = normalize_tags(feishu_task.tags)

    return (
        task.title == feishu_task.task
        and task.column == feishu_task.status
        and task_tags == feishu_tags
        and (task.priority or "") == feishu_task.priority
    )


def compare_remote_with_local(
    remote_records: list[dict[str, Any]], local_tasks: list[Task]
) -> tuple[list[FeishuTask], list[tuple[Task, FeishuTask]], list[Task]]:
    """Compare remote records with local tasks.

    Args:
        remote_records: List of remote records from Feishu
        local_tasks: List of local Task objects (flattened)

    Returns:
        Tuple of (new_tasks, modified_tasks, deleted_tasks)
        - new_tasks: Tasks that exist in remote but not in local
        - modified_tasks: Tasks that exist but have different fields (local, remote)
        - deleted_tasks: Tasks that exist in local but not in remote
    """
    # Build a map of local tasks by title for quick lookup
    local_map: dict[str, Task] = {}
    for task in local_tasks:
        local_map[task.title] = task

    new_tasks: list[FeishuTask] = []
    modified_tasks: list[tuple[Task, FeishuTask]] = []
    remote_task_keys: set[str] = set()

    # Compare remote records with local
    for record in remote_records:
        feishu_task = record_to_feishu_task(record)
        task_key = feishu_task.task

        if not task_key:
            continue

        remote_task_keys.add(task_key)

        if task_key not in local_map:
            # This is a new task from remote
            new_tasks.append(feishu_task)
        else:
            local_task = local_map[task_key]
            if not task_matches_record(local_task, feishu_task):
                modified_tasks.append((local_task, feishu_task))

    # Find deleted tasks (in local but not in remote)
    deleted_tasks: list[Task] = []
    for task_title, local_task in local_map.items():
        if task_title not in remote_task_keys:
            deleted_tasks.append(local_task)

    return new_tasks, modified_tasks, deleted_tasks


def flatten_tasks(board: Board) -> list[Task]:
    """Flatten all tasks from board, including subtasks."""
    all_tasks: list[Task] = []

    def collect_task(task: Task):
        all_tasks.append(task)
        for subtask in task.subtasks:
            collect_task(subtask)

    for column_tasks in board.columns.values():
        for task in column_tasks:
            collect_task(task)

    return all_tasks


def print_pull_preview(
    new_tasks: list[FeishuTask],
    modified_tasks: list[tuple[Task, FeishuTask]],
    deleted_tasks: list[Task],
    total_remote: int,
    total_local: int,
) -> None:
    """Print a formatted diff preview for pull operation."""
    print(f"\n{'='*60}")
    print(f"📥 拉取预览: {total_remote} 个远程任务 vs {total_local} 个本地任务")
    print(f"{'='*60}")

    # New tasks (from remote)
    if new_tasks:
        print(f"\n🟢 新增任务 ({len(new_tasks)} 个) - 将从远程添加:")
        for task in new_tasks:
            print(f"   + [{task.status}] {task.task}")
            if task.tags:
                print(f"     标签: {', '.join(task.tags)}")
            if task.priority:
                print(f"     优先级: {task.priority}")

    # Modified tasks
    if modified_tasks:
        print(f"\n🟡 变更任务 ({len(modified_tasks)} 个) - 将更新本地:")
        for local_task, remote_task in modified_tasks:
            print(f"   ~ [{remote_task.status}] {remote_task.task}")
            # Show field differences
            if local_task.column != remote_task.status:
                print(f"     状态: {local_task.column} → {remote_task.status}")
            local_tags = normalize_tags(local_task.tags)
            remote_tags = normalize_tags(remote_task.tags)
            if local_tags != remote_tags:
                print(f"     标签: {local_tags or '(无)'} → {remote_tags or '(无)'}")
            local_priority = local_task.priority or "(无)"
            remote_priority = remote_task.priority or "(无)"
            if local_priority != remote_priority:
                print(f"     优先级: {local_priority} → {remote_priority}")

    # Deleted tasks (in local but not in remote)
    if deleted_tasks:
        print(f"\n🔴 删除任务 ({len(deleted_tasks)} 个) - 本地存在但远程已删除:")
        for task in deleted_tasks:
            print(f"   - [{task.column}] {task.title}")

    # Unchanged count
    unchanged_count = total_local - len(deleted_tasks) - len(modified_tasks)
    if unchanged_count > 0:
        print(f"\n⚪ 未变更任务 ({unchanged_count} 个)")

    print(f"\n{'='*60}")
    print(f"总结: {len(new_tasks)} 新增, {len(modified_tasks)} 变更, {len(deleted_tasks)} 删除")
    print(f"{'='*60}\n")


def apply_remote_changes(
    board: Board,
    new_tasks: list[FeishuTask],
    modified_tasks: list[tuple[Task, FeishuTask]],
    deleted_tasks: list[Task],
) -> Board:
    """Apply remote changes to local board.

    Returns a new Board with updated tasks.
    """
    # Create a new board with same settings
    new_board = Board(
        title=board.title,
        settings=board.settings.copy(),
    )

    # Copy existing columns structure
    for column_name in board.columns.keys():
        new_board.columns[column_name] = []

    # Build sets for quick lookup
    deleted_set = {task.title for task in deleted_tasks}
    modified_map = {local.title: remote for local, remote in modified_tasks}

    # Process existing tasks
    for column_name, tasks in board.columns.items():
        for task in tasks:
            # Skip deleted tasks
            if task.title in deleted_set:
                continue

            # Check if this task is modified
            if task.title in modified_map:
                remote_task = modified_map[task.title]
                # Create updated task from remote
                updated_task = Task(
                    title=remote_task.task,
                    column=remote_task.status,
                    tags=remote_task.tags,
                    priority=remote_task.priority if remote_task.priority else None,
                    subtasks=task.subtasks,  # Preserve subtasks
                )

                # Check if column changed
                if remote_task.status != column_name:
                    # Add to new column
                    if remote_task.status not in new_board.columns:
                        new_board.columns[remote_task.status] = []
                    new_board.columns[remote_task.status].append(updated_task)
                else:
                    new_board.columns[column_name].append(updated_task)
            else:
                # Task unchanged, keep as is
                new_board.columns[column_name].append(task)

    # Add new tasks from remote
    for feishu_task in new_tasks:
        new_task = feishu_task_to_task(feishu_task)
        if feishu_task.status not in new_board.columns:
            new_board.columns[feishu_task.status] = []
        new_board.columns[feishu_task.status].append(new_task)

    return new_board


def pull_from_feishu(board: Board, project_name: str, dry_run: bool = False) -> tuple[bool, Board]:
    """Pull tasks from Feishu table.

    Args:
        board: The Board object containing local tasks
        project_name: Project name to identify tasks in Feishu
        dry_run: If True, only preview changes without applying

    Returns:
        Tuple of (success, updated_board)
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
        return False, board

    config = load_global_config()
    if not config.bot_app_id or not config.bot_app_secret:
        print("Error: bot_app_id and bot_app_secret not found in global config.")
        print("Please add the following to ~/.config/tuido/config.yaml:")
        print(
            """feishu:
  bot_app_id: your_bot_app_id
  bot_app_secret: your_bot_app_secret"""
        )
        return False, board

    # Flatten local tasks for comparison
    local_tasks = flatten_tasks(board)

    # Fetch remote records for this project
    try:
        print(f"Fetching remote records from Feishu for project '{project_name}'...")
        remote_records = fetch_project_tasks(
            api_endpoint,
            config.bot_app_id,
            config.bot_app_secret,
            feishu_table_app_token,
            feishu_table_id,
            feishu_table_view_id,
            project_name,
        )
        print(f"Found {len(remote_records)} remote records.")
    except Exception as e:
        print(f"Error fetching remote records: {e}")
        return False, board

    # Compare remote with local
    new_tasks, modified_tasks, deleted_tasks = compare_remote_with_local(
        remote_records, local_tasks
    )

    # Print diff preview
    print_pull_preview(
        new_tasks, modified_tasks, deleted_tasks, len(remote_records), len(local_tasks)
    )

    # In dry-run mode, just return after preview
    if dry_run:
        return True, board

    # Check if there are any changes
    if not new_tasks and not modified_tasks and not deleted_tasks:
        print("No changes to pull. All tasks are already in sync.")
        return True, board

    # Ask for confirmation
    print(f"即将拉取 {len(new_tasks) + len(modified_tasks) + len(deleted_tasks)} 个变更到本地:")
    if new_tasks:
        print(f"  - 新增: {len(new_tasks)} 个")
    if modified_tasks:
        print(f"  - 变更: {len(modified_tasks)} 个")
    if deleted_tasks:
        print(f"  - 删除: {len(deleted_tasks)} 个")
    response = input("\n确认执行? (y/N): ").strip().lower()
    if response not in ("y", "yes"):
        print("已取消拉取。")
        return True, board

    # Apply changes
    try:
        updated_board = apply_remote_changes(board, new_tasks, modified_tasks, deleted_tasks)
        print(f"\n✅ 成功拉取所有变更到本地。")
        return True, updated_board
    except Exception as e:
        print(f"\n❌ 拉取失败: {e}")
        return False, board


def run_pull_command(board: Board, todo_file: Path) -> int:
    """Run the pull command.

    Args:
        board: The Board object containing tasks
        todo_file: Path to the TODO.md file
        dry_run: If True, only preview changes without applying

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine project name
    # Use parent directory name as project name
    if todo_file.is_dir():
        project_name = todo_file.name
    else:
        project_name = todo_file.parent.name

    success, updated_board = pull_from_feishu(board, project_name)

    if success:
        # Save the updated board back to file
        try:
            save_todo_file(todo_file, updated_board)
            print(f"已更新文件: {todo_file}")
            return 0
        except Exception as e:
            print(f"保存文件失败: {e}")
            return 1

    return 0 if success else 1
