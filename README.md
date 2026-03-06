# Tuido 📝

A TUI (Terminal User Interface) Kanban board for TODO.md files.

## Features

- 📋 Parse TODO.md files with simple list syntax
- 📊 **Dynamic columns** based on markdown sections (`## Heading`)
- 🎨 Multiple themes (Dracula, Nord, Monokai, Solarized, etc.)
- ⌨️ Vim-style keybindings (h/j/k/l)
- ↔️ Move tasks between columns with Shift+Arrow keys
- 🔃 Reorder tasks within column (including subtasks)
- 🏷️ Support for tags (#tag), priority (!P0/!P1/!P2/!P3/!P4), timestamp (~YYYY-MM-DDTHH:MM)
- 💾 Save changes back to TODO.md
- 🌏 **Global view** - View all projects' tasks from Feishu table
- 🔄 **Bi-directional sync** - Push to and pull from Feishu table
- 📁 **Hierarchical tasks** - Support for subtasks with indentation

## Installation

```bash
# Clone or download the repository
cd tuido

# Install in editable mode
pip install -e .
```

## Usage

```bash
# Open TODO.md in current directory (default)
tuido open
tuido open --path .

# Create a sample TODO.md file
tuido create
tuido create --path /path/to/project

# List tasks (optionally filtered)
tuido list
tuido list --status "Active"
tuido list --tag feature
tuido list --priority P1

# Add a new task
tuido add "Fix bug #bug !P0"
tuido add "Update documentation #docs" --path /path/to/project

# Pick the top task and move to next column
tuido pick
tuido pick --path /path/to/project

# Push tasks to Feishu table
tuido push
tuido push --path /path/to/project

# Pull tasks from Feishu table
tuido pull
tuido pull --path /path/to/project

# View all projects from Feishu (global view)
tuido global-view

# Push global view tasks to Feishu
tuido global-view --push
```

**Note:** `--path` is optional for most commands and defaults to the current directory (`.`).

## Keyboard Shortcuts

### Navigation (Vim-style)
- `↑` / `k` - Previous task
- `↓` / `j` - Next task
- `←` / `h` - Previous column
- `→` / `l` - Next column

### Move Tasks (Between Columns)
- `Shift+↑` / `Shift+K` - Move task up (reorder within column)
- `Shift+↓` / `Shift+J` - Move task down (reorder within column)
- `Shift+←` / `Shift+H` - Move task to left column
- `Shift+→` / `Shift+L` - Move task to right column

### Actions
- `a` - Add new task
- `d` - Delete task
- `e` - Edit task
- `r` - Refresh from file
- `s` - Save to file
- `t` - Switch theme
- `q` / `Ctrl+C` - Quit
- `?` - Show help

## TODO.md Format

```markdown
---
theme: dracula
---

# TODO

## Todo
- Task to do #feature !P1 ~2026-02-28T10:30
- Another task #bug ~2026-02-28T09:00

## Active
- Currently working on ~2026-02-28T14:00
  - Subtask 1 #backend
  - Subtask 2 #frontend

## Done
- Completed task ~2026-02-27T16:30
```

### Dynamic Columns

Columns are automatically created from `## ` headings in your TODO.md file. You can define any columns you need:

- `## Todo` - Tasks to do
- `## Active` - Tasks being worked on
- `## Done` - Completed tasks

The column order follows the order they appear in the file.

### Task Syntax

- `- ` - Task prefix (required)
- `#tag` - Tags (e.g., #feature, #bug, #docs)
- `!P0` / `!P1` / `!P2` / `!P3` / `!P4` - Priority (P0 = highest, P4 = lowest)
- `~YYYY-MM-DDTHH:MM` - Last updated timestamp (e.g., ~2026-02-28T14:30)

Task status is determined by which section (`## Todo`, `## Active`, etc.) it belongs to.

### Inline Styling

Task titles support Markdown-style inline formatting in the TUI:

- `**bold**` or `__bold__` - **Bold text**
- `` `code` `` - `Code text` (cyan color)
- `~~strikethrough~~` - ~~Strikethrough text~~

Examples:
```markdown
- Implement **bold** and `code` support !P1 #ui
- ~~Deprecated feature~~ will be removed in v2.0
- **Important:** Check `config.yaml` before running
```

**Note:** The timestamp is automatically updated when you move or reorder tasks in the TUI, and is synced with Feishu's `Timestamp` field.

### Subtasks (Hierarchical Tasks)

Use 2-space indentation to create subtasks:

```markdown
## Todo
- Parent task !P1
  - Subtask 1
  - Subtask 2
    - Grandchild task
```

**Rules:**
- 2 spaces = 1 level of indentation
- Subtasks move with their parent when moving between columns
- Subtasks can be reordered independently within the same parent

## Configuration

### Front Matter (TODO.md)

Add configuration at the beginning of your TODO.md:

```markdown
---
theme: nord
remote:
  feishu_api_endpoint: https://open.feishu.cn/open-apis
  feishu_table_app_token: your_app_token
  feishu_table_id: your_table_id
  feishu_table_view_id: your_view_id
---
```

### Global Config (~/.config/tuido/config.yaml)

For Feishu integration, create the config file:

```yaml
feishu:
  api_endpoint: https://open.feishu.cn/open-apis
  table_app_token: your_table_app_token
  table_id: your_table_id
  table_view_id: your_table_view_id
  bot_app_id: your_bot_app_id
  bot_app_secret: your_bot_app_secret
```

## Global View

View tasks from all projects in a single read-only interface:

```bash
# Show global view from Feishu table
tuido global-view
```

**Configuration:**

Create `~/.config/tuido/config.yaml` with your Feishu credentials (see above).

The global view displays tasks from all projects organized by status columns (Todo, Active, Review, Blocked, Done).

## Feishu Sync

### Push to Feishu

Push local tasks to Feishu table:

```bash
tuido push
```

Features:
- Compares local tasks with remote records
- Shows diff preview before pushing
- Creates new tasks, updates modified ones
- Deletes orphaned remote records

### Pull from Feishu

Pull remote tasks from Feishu to local:

```bash
tuido pull
```

Features:
- Fetches tasks from Feishu for the current project
- Shows diff preview before applying
- Adds new tasks, updates modified ones
- Removes local tasks deleted remotely
- Automatically saves to TODO.md

## Requirements

- Python 3.12+
- textual
- rich
- requests
- pyyaml
- loguru
