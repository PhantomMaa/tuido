from tuido.feishu import FeishuTable
from tuido.config import get_global_view_config
from tuido.models import FeishuTask

feishu_table_view_id: str


def _init_feishu_table():
    config = get_global_view_config()
    feishu_api_endpoint = config.get("feishu_api_endpoint", "")
    feishu_bot_app_id = config.get("feishu_bot_app_id", "")
    feishu_bot_app_secret = config.get("feishu_bot_app_secret", "")
    feishu_table_app_token = config.get("feishu_table_app_token", "")
    feishu_table_id = config.get("feishu_table_id", "")
    global feishu_table_view_id
    feishu_table_view_id = config.get("feishu_table_view_id", "")

    feishu_table = FeishuTable(feishu_api_endpoint, feishu_bot_app_id, feishu_bot_app_secret, feishu_table_app_token, feishu_table_id)
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
    result = feishu_table.fetch_all(feishu_table_view_id, ["Task", "Project", "Status", "Tags", "Priority"])
    print(result)
