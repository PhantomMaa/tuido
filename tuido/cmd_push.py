"""Push command implementation for tuido."""

from datetime import datetime
from pathlib import Path
from typing import Any

from tuido import util
from tuido.feishu import FeishuTable, fetch_project_tasks
from tuido.models import Board, FeishuTask
from tuido.config import load_global_config


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
        and normalize_tags(task.tags)
        == normalize_tags(
            record.get("Tags", []) if isinstance(record.get("Tags"), list) else record.get("Tags", "").split(", ") if record.get("Tags") else []
        )
        and task.priority == record.get("Priority", "")
        and task.timestamp == record.get("Timestamp", "")
    )


def compare_tasks_with_records(
    local_tasks: list[FeishuTask], remote_records: list[dict[str, Any]]
) -> tuple[list[FeishuTask], list[FeishuTask], list[tuple[FeishuTask, dict[str, Any]]], list[dict[str, Any]]]:
    """Compare local tasks with remote records.

    Args:
        local_tasks: List of local FeishuTask objects
        remote_records: List of remote records from Feishu

    Returns:
        Tuple of (new_tasks, unchanged_tasks, modified_tasks, orphaned_records)
        - new_tasks: Tasks that don't exist in remote
        - unchanged_tasks: Tasks that match exactly with remote
        - modified_tasks: Tasks that exist but have different fields
        - orphaned_records: Remote records that don't exist in local (will be deleted)
    """
    # Build a map of remote records by task title for quick lookup
    remote_map: dict[str, dict[str, Any]] = {}
    for record in remote_records:
        task_key = record.get("Task", "")
        if task_key:
            remote_map[task_key] = record

    # Build a set of local task titles for quick lookup
    local_task_titles = {task.task for task in local_tasks}

    new_tasks: list[FeishuTask] = []
    unchanged_tasks: list[FeishuTask] = []
    modified_tasks: list[tuple[FeishuTask, dict[str, Any]]] = []
    orphaned_records: list[dict[str, Any]] = []

    for task in local_tasks:
        if task.task not in remote_map:
            new_tasks.append(task)
        else:
            remote_record = remote_map[task.task]
            if task_matches_record(task, remote_record):
                unchanged_tasks.append(task)
            else:
                modified_tasks.append((task, remote_record))

    # Find orphaned records (exist in remote but not in local)
    for task_title, record in remote_map.items():
        if task_title not in local_task_titles:
            orphaned_records.append(record)

    return new_tasks, unchanged_tasks, modified_tasks, orphaned_records


def print_diff_preview(
    new_tasks: list[FeishuTask],
    unchanged_tasks: list[FeishuTask],
    modified_tasks: list[tuple[FeishuTask, dict[str, Any]]],
    orphaned_records: list[dict[str, Any]],
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

    # Modified tasks
    if modified_tasks:
        print(f"\n🟡 变更任务 ({len(modified_tasks)} 个):")
        for task, remote in modified_tasks:
            print(f"   ~ [{task.status}] {task.task}")
            # Show field differences
            if task.status != remote.get("Status", ""):
                print(f"     状态: {remote.get('Status', '')} → {task.status}")
            if normalize_tags(task.tags) != normalize_tags(
                remote.get("Tags", []) if isinstance(remote.get("Tags"), list) else remote.get("Tags", "").split(", ") if remote.get("Tags") else []
            ):
                old_tags = remote.get("Tags", "")
                new_tags = ", ".join(task.tags)
                print(f"     标签: {old_tags} → {new_tags}")
            if task.priority != remote.get("Priority", ""):
                old_priority = remote.get("Priority", "") or "(无)"
                new_priority = task.priority or "(无)"
                print(f"     优先级: {old_priority} → {new_priority}")
            if task.timestamp != remote.get("Timestamp", ""):
                old_timestamp = remote.get("Timestamp", "") or "(无)"
                new_timestamp = task.timestamp or "(无)"
                print(f"     时间戳: {old_timestamp} → {new_timestamp}")

    # Orphaned records (to be deleted)
    if orphaned_records:
        print(f"\n🔴 删除任务 ({len(orphaned_records)} 个) - 远程比本地多出的任务:")
        for record in orphaned_records:
            print(f"   - [{record.get('Status', '')}] {record.get('Task', '')}")

    print(f"\n{'='*60}")
    delete_info = f", {len(orphaned_records)} 删除" if orphaned_records else ""
    print(f"总结: {len(new_tasks)} 新增, {len(modified_tasks)} 变更{delete_info}, {len(unchanged_tasks)} 未变更")
    print(f"{'='*60}\n")


def push_to_feishu(board: Board, project_name: str) -> bool:
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
                timestamp=task.updated_at or "",
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
        remote_records = fetch_project_tasks(
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
    new_tasks, unchanged_tasks, modified_tasks, orphaned_records = compare_tasks_with_records(tasks, remote_records)

    # Print diff preview
    print_diff_preview(new_tasks, unchanged_tasks, modified_tasks, orphaned_records, len(tasks), len(remote_records))

    # Calculate tasks to actually push (new + modified)
    tasks_to_push = new_tasks + [task for task, _ in modified_tasks]

    # Check if there's anything to do
    if not tasks_to_push and not orphaned_records:
        print("No changes to push. All tasks are already in sync.")
        return True

    # Ask for confirmation
    print(f"即将推送 {len(tasks_to_push)} 个任务到飞书表格:")
    print(f"  - 新增: {len(new_tasks)} 个")
    if modified_tasks:
        print(f"  - 变更: {len(modified_tasks)} 个(以本地为准，更新远程任务)")
    if orphaned_records:
        print(f"  - 删除: {len(orphaned_records)} 个 (以本地为准，删除远程多余任务)")
    response = input("\n确认执行? (y/N): ").strip().lower()
    if response not in ("y", "yes"):
        print("已取消推送。")
        return True

    # Initialize Feishu bot
    try:
        bot = FeishuTable(api_endpoint, config.bot_app_id, config.bot_app_secret, feishu_table_app_token, feishu_table_id)
    except Exception as e:
        print(f"Error initializing Feishu bot: {e}")
        return False

    success_count = 0
    fail_count = 0

    # 1. Create new tasks using batch_create
    if new_tasks:
        records = []
        for task in new_tasks:
            fields = {
                "Task": task.task,
                "Project": task.project,
                "Status": task.status,
                "Tags": task.tags,
                "Priority": task.priority,
                "Timestamp": util.parse_timestamp_to_ms(task.timestamp),
            }
            record = {"fields": fields}
            records.append(record)

        try:
            if bot.batch_create(records):
                print(f"✓ 成功创建 {len(records)} 个新任务")
                success_count += len(records)
            else:
                print(f"✗ 创建 {len(records)} 个新任务失败")
                fail_count += len(records)
        except Exception as e:
            print(f"✗ 创建新任务时出错: {e}")
            fail_count += len(records)

    # 2. Update modified tasks using update API with record_id
    for task, remote_record in modified_tasks:
        record_id = remote_record.get("record_id")
        if not record_id:
            print(f"✗ 无法更新任务 '{task.task}': 缺少 record_id")
            fail_count += 1
            continue

        fields = {
            "Task": task.task,
            "Project": task.project,
            "Status": task.status,
            "Tags": task.tags,
            "Priority": task.priority,
            "Timestamp": util.parse_timestamp_to_ms(task.timestamp),
        }
        try:
            if bot.update(feishu_table_app_token, feishu_table_id, record_id, fields):
                print(f"✓ 更新任务: {task.task}")
                success_count += 1
            else:
                print(f"✗ 更新任务失败: {task.task}")
                fail_count += 1
        except Exception as e:
            print(f"✗ 更新任务 '{task.task}' 时出错: {e}")
            fail_count += 1

    # 3. Delete orphaned records (remote records that don't exist locally)
    if orphaned_records:
        print(f"\n删除 {len(orphaned_records)} 个远程多余任务...")
        orphaned_record_ids = [record.get("record_id", "") for record in orphaned_records if record.get("record_id", "")]
        if orphaned_record_ids:
            try:
                if bot.batch_delete(orphaned_record_ids):
                    print(f"✓ 成功删除 {len(orphaned_record_ids)} 个远程任务")
                    success_count += len(orphaned_record_ids)
                else:
                    print(f"✗ 删除 {len(orphaned_record_ids)} 个远程任务失败")
                    fail_count += len(orphaned_record_ids)
            except Exception as e:
                print(f"✗ 删除远程任务时出错: {e}")
                fail_count += len(orphaned_record_ids)

    # Summary
    if fail_count == 0:
        print(f"\n✅ 成功推送所有 {success_count} 个任务到飞书表格。")
        return True
    else:
        print(f"\n⚠️ 推送完成: {success_count} 个成功, {fail_count} 个失败。")
        return fail_count == 0


def run_push_command(board: Board, todo_file: Path) -> int:
    """Run the push command.

    Args:
        board: The Board object containing tasks
        todo_file: Path to the TODO.md file

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine project name
    # Use parent directory name as project name
    if todo_file.is_dir():
        project_name = todo_file.name
    else:
        project_name = todo_file.parent.name

    success = push_to_feishu(board, project_name)
    return 0 if success else 1
