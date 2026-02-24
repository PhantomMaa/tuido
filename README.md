# Tudo 📝

A TUI (Terminal User Interface) Kanban board for TODO.md files.

## Features

- 📋 Parse TODO.md files with simple list syntax
- 🎯 Visual Kanban board with columns: Todo, In Progress, Blocked, Done
- ⌨️ Vim-style keybindings (h/j/k/l)
- ↔️ Move tasks between columns with Shift+Arrow keys
- 🏷️ Support for tags (#tag), priority (!high/!medium/!low), and assignees (@user)
- 💾 Save changes back to TODO.md

## Installation

```bash
# Clone or download the repository
cd tudo

# Install in editable mode
pip install -e .
```

## Usage

```bash
# Open TODO.md in current directory
tudo .

# Open specific TODO.md file
tudo path/to/TODO.md

# Create a sample TODO.md file
tudo . --create
```

## Keyboard Shortcuts

### Navigation
- `↑`/`k` - Previous task
- `↓`/`j` - Next task
- `←`/`h` - Previous column
- `→`/`l` - Next column

### Move Tasks
- `Shift+←` / `Shift+H` - Move task to left column
- `Shift+→` / `Shift+L` - Move task to right column

### Actions
- `r` - Refresh from file
- `s` - Save to file
- `q` - Quit
- `?` - Help

## TODO.md Format

```markdown
# TODO

## Todo
- Task to do #feature !high @dev
- Another task #bug @qa

## In Progress
- Currently working on this

## Blocked
- Waiting for something

## Done
- Completed task
```

### Syntax

- `- ` - Task prefix (required)
- `#tag` - Tags
- `!high` / `!medium` / `!low` / `!critical` - Priority
- `@username` - Assignee

Task status is determined by which section (`## Todo`, `## In Progress`, `## Blocked`, `## Done`) it belongs to.

## Requirements

- Python 3.9+
- textual
- rich
