# Tuido 📝

A TUI (Terminal User Interface) Kanban board for TODO.md files.

## Features

- 📋 Parse TODO.md files with simple list syntax
- 📊 **Dynamic columns** based on markdown sections (`## Heading`)
- 🎨 Multiple themes (Dracula, Nord, Monokai, Solarized, etc.)
- ⌨️ Vim-style keybindings (h/j/k/l)
- ↔️ Move tasks between columns with Shift+Arrow keys
- 🔃 Reorder tasks within column
- 🏷️ Support for tags (#tag), priority (!P0/!P1/!P2/!P3/!P4)
- 💾 Save changes back to TODO.md
- 🌍 **Global view** - View all projects' tasks from Feishu table

## Installation

```bash
# Clone or download the repository
cd tuido

# Install in editable mode
pip install -e .
```

## Usage

```bash
# Open TODO.md in current directory
tuido .

# Open specific TODO.md file
tuido path/to/TODO.md

# Create a sample TODO.md file
tuido . --create

# View all projects from Feishu (global view)
tuido --global-view
```

## Keyboard Shortcuts

### Navigation
- `↑`/`k` - Previous task
- `↓`/`j` - Next task
- `←`/`h` - Previous column
- `→`/`l` - Next column

### Move Tasks (Between Columns)
- `Shift+←` / `Shift+H` - Move task to left column
- `Shift+→` / `Shift+L` - Move task to right column

### Reorder Tasks (Within Column)
- `Shift+↑` / `Shift+K` - Move task up
- `Shift+↓` / `Shift+J` - Move task down

### Actions
- `r` - Refresh from file
- `s` - Save to file
- `t` - Switch theme
- `q` - Quit
- `?` - Help

## TODO.md Format

```markdown
# TODO

## Todo
- Task to do #feature !P1
- Another task #bug

## In Progress
- Currently working on this

## Review
- Waiting for review #pr

## Done
- Completed task
```

### Dynamic Columns

Columns are automatically created from `## ` headings in your TODO.md file. You can define any columns you need:

- `## Todo` - Tasks to do
- `## In Progress` - Tasks being worked on
- `## Review` - Tasks pending review
- `## Blocked` - Blocked tasks
- `## Done` - Completed tasks

The column order follows the order they appear in the file.

### Task Syntax

- `- ` - Task prefix (required)
- `#tag` - Tags (e.g., #feature, #bug, #docs)
- `!P0` / `!P1` / `!P2` / `!P3` / `!P4` - Priority (P0 = highest, P4 = lowest)

Task status is determined by which section (`## Todo`, `## In Progress`, etc.) it belongs to.

## Global View

View tasks from all projects in a single read-only interface:

```bash
# Show global view from Feishu table
tuido --global-view
```

The global view displays tasks from all projects organized by status columns (Todo, In Progress, Review, Blocked, Done).

## Requirements

- Python 3.9+
- textual
- rich
