from pathlib import Path

from tuido.cli import find_todo_file
from tuido.feishu import FeishuTable
from tuido import envs
from tuido.models import FeishuTask
from tuido.parser import parse_todo_file


def _init_feishu_table():
    todo_file = find_todo_file(Path("."))
    board = parse_todo_file(todo_file)
    settings = board.settings
    remote_config = settings.get("remote", {})
    table_app_token = remote_config.get("feishu_table_app_token")
    table_id = remote_config.get("feishu_table_id")
    table_view_id = remote_config.get("feishu_table_view_id")
    feishu_table = FeishuTable(envs.bot_app_id, envs.bot_app_secret, table_app_token, table_id, table_view_id)
    return feishu_table


# pytest tests/test_feishu.py::test_batch_create -s
def test_batch_create():
    feishu_table = _init_feishu_table()

    tasks = [FeishuTask(task="任务1", project="项目1", status="进行中", tags=["标签1"], priority="高")]
    records = [{"fields": {"Task": t.task, "Project": t.project, "Status": t.status, "Tags": t.tags, "Priority": t.priority}} for t in tasks]
    result = feishu_table.batch_create(records)
    print(result)


# pytest tests/test_feishu.py::test_fetch_all -s
def test_fetch_all():
    feishu_table = _init_feishu_table()

    result = feishu_table.fetch_all(["Task", "Project", "Status", "Tags", "Priority"])
    print(result)
