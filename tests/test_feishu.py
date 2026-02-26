from tuido.feishu import FeishuBot
from tuido import envs
from tuido.models import FeishuTask

TABLE_APP_TOKEN = "FcS8bHGgRatZFZsrlDrl1nDOgeg"
TABLE_ID = "tblY5rSJzlWRPRoU"


# pytest tests/test_feishu.py::test_batch_create -s
def test_batch_create():
    feishu_table = FeishuBot(envs.bot_app_id, envs.bot_app_secret)

    tasks = [FeishuTask(task="任务1", project="项目1", status="进行中", tags=["标签1"], priority="高")]
    records = [{"fields": {"Task": t.task, "Project": t.project, "Status": t.status, "Tags": t.tags, "Priority": t.priority}} for t in tasks]
    result = feishu_table.batch_create(TABLE_APP_TOKEN, TABLE_ID, records)
    print(result)
