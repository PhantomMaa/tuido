"""Command for adding a new task to TODO.md."""

import re
from pathlib import Path

import click


def add_to_feishu(content: str) -> int:
    """Add a task directly to Feishu table when no local TODO.md exists.

    Args:
        content: Task content (title, tags, priority etc.)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from datetime import datetime

    from tuido.config import load_global_config
    from tuido.feishu import FeishuTable
    from tuido import util

    # Load global config
    global_config = load_global_config()

    if not global_config.remote.is_valid():
        config_path = Path.home() / ".config" / "tuido" / "config.yaml"
        missing = global_config.remote.get_missing_fields()
        click.echo(f"Error: Missing Feishu configuration in {config_path}", err=True)
        for field in missing:
            click.echo(f"  - remote.{field}", err=True)
        click.echo("\nPlease add the following to your config:", err=True)
        click.echo(
            """remote:
  feishu_api_endpoint: https://open.feishu.cn/open-apis
  feishu_table_app_token: your_table_app_token
  feishu_table_id: your_table_id
  feishu_table_view_id: your_table_view_id
  feishu_bot_app_id: your_bot_app_id
  feishu_bot_app_secret: your_bot_app_secret""",
            err=True,
        )
        return 1

    # Parse content for tags and priority
    tags = []
    priority = ""
    title = content

    # Extract tags (#tag)
    tag_matches = re.findall(r"#(\w+)", content)
    if tag_matches:
        tags = tag_matches
        title = re.sub(r"#\w+", "", title).strip()

    # Extract priority (!P0-4)
    priority_match = re.search(r"!P([0-4])", content)
    if priority_match:
        priority = f"P{priority_match.group(1)}"
        title = re.sub(r"!P[0-4]", "", title).strip()

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M")

    # Get project name from current directory
    project = Path.cwd().name

    # Prepare record fields
    fields = {
        "Task": title,
        "Project": project,
        "Status": "Todo",
        "Tags": tags,
        "Priority": priority,
        "Timestamp": util.parse_timestamp_to_ms(timestamp),
    }

    # Initialize Feishu bot and create record
    try:
        bot = FeishuTable(
            global_config.remote.feishu_api_endpoint,
            global_config.remote.feishu_bot_app_id,
            global_config.remote.feishu_bot_app_secret,
            global_config.remote.feishu_table_app_token,
            global_config.remote.feishu_table_id,
        )

        record = {"fields": fields}
        if bot.batch_create([record]):
            click.echo(f"✓ Added to Feishu: {content}")
            return 0
        else:
            click.echo("✗ Failed to add task to Feishu", err=True)
            return 1
    except Exception as e:
        click.echo(f"✗ Error adding task to Feishu: {e}", err=True)
        return 1


def run_add_command(todo_file: Path, content: str) -> int:
    """Add a new task to the TODO.md file.

    Args:
        todo_file: Path to TODO.md file
        content: Task content (title, tags, priority etc.)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from datetime import datetime

    # Read existing content
    if not todo_file.exists():
        # No local TODO.md, try to add directly to Feishu
        return add_to_feishu(content)

    existing_content = todo_file.read_text(encoding="utf-8")

    # Find the first column (## Section) to insert task
    lines = existing_content.splitlines() if existing_content else []

    # If file is empty or has no columns, create a basic structure
    if not lines or not any(line.startswith("## ") for line in lines):
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M")
        new_content = f"# TUIDO\n\n## Todo\n- {content} ~{timestamp}\n"
        todo_file.write_text(new_content, encoding="utf-8")
        click.echo(f"✓ Added: {content}")
        return 0

    # Find the first ## section and insert task after it
    insert_index = -1
    for i, line in enumerate(lines):
        if line.startswith("## "):
            insert_index = i + 1
            break

    if insert_index > 0:
        # Insert new task line after the first section header
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M")
        new_task_line = f"- {content} ~{timestamp}"
        lines.insert(insert_index, new_task_line)

        # Write back
        todo_file.write_text("\n".join(lines), encoding="utf-8")
        click.echo(f"✓ Added: {content}")
    else:
        # Fallback: append to end
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M")
        new_task_line = f"- {content} ~{timestamp}\n"
        with open(todo_file, "a", encoding="utf-8") as f:
            f.write(new_task_line)
        click.echo(f"✓ Added: {content}")

    return 0
