import json

from tuido.feishu import FeishuTable
from tuido.config import load_global_config
from tuido.models import FeishuTask

feishu_table_view_id: str


def _init_feishu_table():
    config = load_global_config()
    global feishu_table_view_id
    feishu_table_view_id = config.remote.feishu_table_view_id

    feishu_table = FeishuTable(
        config.remote.feishu_api_endpoint,
        config.remote.feishu_bot_app_id,
        config.remote.feishu_bot_app_secret,
        config.remote.feishu_table_app_token,
        config.remote.feishu_table_id,
    )
    return feishu_table


# pytest tests/test_feishu.py::test_batch_create -s
def test_batch_create():
    feishu_table = _init_feishu_table()

    tasks = [FeishuTask(title="任务1", project="项目1", status="进行中", tags=["标签1"], priority="P1")]
    records = [
        {"fields": {"Task": t.title, "Project": t.project, "Status": t.status, "Tags": t.tags, "Priority": t.priority, "Timestamp": 1674206443000}}
        for t in tasks
    ]
    result = feishu_table.batch_create(records)
    print(result)


# pytest tests/test_feishu.py::test_fetch_all -s
def test_fetch_all():
    feishu_table = _init_feishu_table()
    result = feishu_table.fetch_all(
        feishu_table_view_id, ["Task", "Project", "Status", "Tags", "Priority", "Timestamp"], condition=("Project", "xelm")
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
