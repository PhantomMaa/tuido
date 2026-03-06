"""Command for adding a new task to TODO.md."""

from pathlib import Path

import click


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
    if todo_file.exists():
        existing_content = todo_file.read_text(encoding="utf-8")
    else:
        existing_content = ""

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
