# Tuido 📝

A TUI (Terminal User Interface) Kanban board for TODO.md files.

## Features

- 📋 Parse TODO.md files with simple list syntax
- 📊 **Dynamic columns** based on markdown sections (`## Heading`)
- 🎨 Multiple themes (Dracula, Nord, Monokai, Solarized, etc.)
- ⌨️ Vim-style keybindings (h/j/k/l)
- ↔️ Move tasks between columns with Shift+Arrow keys
- 🔃 Reorder tasks within column (including subtasks)
- 🏷️ Support for tags (#tag), priority (!P0/!P1/!P2/!P3/!P4)
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
# Open TODO.md in current directory
tuido .

# Open specific TODO.md file
tuido path/to/TODO.md

# Create a sample TODO.md file
tuido --create

# Push tasks to Feishu table
tuido --push

# Pull tasks from Feishu table
tuido --pull

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

### Reorder Tasks (Within Column / Parent)
- `Shift+↑` / `Shift+K` - Move task up
- `Shift+↓` / `Shift+J` - Move task down
  - Works for both top-level tasks and subtasks

### Actions
- `r` - Refresh from file
- `s` - Save to file
- `t` - Switch theme
- `q` - Quit
- `?` - Help

## TODO.md Format

```markdown
---
theme: dracula
---

# TODO

## Todo
- Task to do #feature !P1
- Another task #bug

## In Progress
- Currently working on
  - Subtask 1 #backend
  - Subtask 2 #frontend

## Done
- Completed task
```

### Dynamic Columns

Columns are automatically created from `## ` headings in your TODO.md file. You can define any columns you need:

- `## Todo` - Tasks to do
- `## In Progress` - Tasks being worked on
- `## Done` - Completed tasks

The column order follows the order they appear in the file.

### Task Syntax

- `- ` - Task prefix (required)
- `#tag` - Tags (e.g., #feature, #bug, #docs)
- `!P0` / `!P1` / `!P2` / `!P3` / `!P4` - Priority (P0 = highest, P4 = lowest)

Task status is determined by which section (`## Todo`, `## In Progress`, etc.) it belongs to.

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
tuido --global-view
```

**Configuration:**

Create `~/.config/tuido/config.yaml` with your Feishu credentials (see above).

The global view displays tasks from all projects organized by status columns (Todo, In Progress, Review, Blocked, Done).

## Feishu Sync

### Push to Feishu

Push local tasks to Feishu table:

```bash
tuido --push
```

Features:
- Compares local tasks with remote records
- Shows diff preview before pushing
- Creates new tasks, updates modified ones
- Deletes orphaned remote records

### Pull from Feishu

Pull remote tasks from Feishu to local:

```bash
tuido --pull
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
