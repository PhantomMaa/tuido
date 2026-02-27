"""Command for creating a sample TODO.md file."""

from pathlib import Path


SAMPLE_CONTENT = """# TUIDO
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


def run_create_command(todo_file: Path) -> None:
    """Create a sample TODO.md file if it doesn't already exist."""
    if not todo_file.exists():
        todo_file.write_text(SAMPLE_CONTENT)
        print(f"Created sample TODO.md at {todo_file}")
    else:
        print(f"File already exists: {todo_file}")
