"""Command for creating a sample TODO.md file."""

from pathlib import Path


SAMPLE_CONTENT = """---
theme: textual-dark
---

# TUIDO

## Todo
- Implement user authentication #feature !P1
- Write unit tests #testing
- Update documentation #docs

## Active
- Design database schema #backend

## Done
- Initial project setup #setup
- Create repository structure #setup
"""


def run_create_command(todo_file: Path) -> int:
    """Create a sample TODO.md file if it doesn't already exist."""
    if not todo_file.exists():
        todo_file.parent.mkdir(parents=True, exist_ok=True)
        todo_file.write_text(SAMPLE_CONTENT, encoding="utf-8")
        print(f"Created sample TODO.md at {todo_file}")
        return 0
    else:
        print(f"File already exists: {todo_file}")
        return 0
