"""Command for adding a new task to TODO.md."""

from pathlib import Path
import click
from tuido.config import load_global_config
from tuido.parser import parse_task_content
from tuido.models import GlobalConfig
from datetime import datetime
from tuido import util


def _print_feishu_config_error() -> None:
    """Print Feishu configuration error message."""
    config_path = Path.home() / ".config" / "tuido" / "config.yaml"
    click.echo(f"Error: Missing Feishu configuration in {config_path}", err=True)
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


def _create_feishu_record(global_config: "GlobalConfig", fields: dict) -> bool:
    """Create a record in Feishu table.

    Args:
        global_config: Global configuration with Feishu credentials
        fields: Record fields to create

    Returns:
        True if successful, False otherwise
    """
    from tuido.feishu import FeishuTable

    bot = FeishuTable(
        global_config.remote.feishu_api_endpoint,
        global_config.remote.feishu_bot_app_id,
        global_config.remote.feishu_bot_app_secret,
        global_config.remote.feishu_table_app_token,
        global_config.remote.feishu_table_id,
    )

    record = {"fields": fields}
    return bot.batch_create([record])


def run_add_command_remote(content: str) -> int:
    """Add a task directly to Feishu table.

    Args:
        content: Task content (title, tags, priority etc.)

    Returns:
        Exit code (0 for success, 1 for error)
    """

    # Check Feishu config
    global_config = load_global_config()
    if not global_config.remote.is_valid():
        _print_feishu_config_error()
        return 1

    # Parse content using shared parser
    parsed = parse_task_content(content)

    # Get current timestamp and project
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M")

    # Prepare record fields
    fields = {
        "Task": parsed["title"] or content,
        "Project": None,
        "Status": "Todo",
        "Tags": parsed["tags"] or [],
        "Priority": parsed["priority"] or "",
        "Timestamp": util.parse_timestamp_to_ms(timestamp),
    }

    # Create record in Feishu
    try:
        if _create_feishu_record(global_config, fields):
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
