---
theme: rose-pine-moon
remote:
  feishu_api_endpoint: https://fsopen.bytedance.net/open-apis
  feishu_table_app_token: FcS8bHGgRatZFZsrlDrl1nDOgeg
  feishu_table_id: tblY5rSJzlWRPRoU
  feishu_table_view_id: vewyMDUelr
---

# TUIDO

## Todo
- push、pull 命令增加对二级任务的支持
- 为每个任务增加记录最后更新时间的功能

## In Progress
- `--global-view` 模式下，也支持切换主题。这个设置保存到 `~/.config/tui/config.yaml` 里

## Done
- push 命令能够预览远程比本地多出来的任务，真正执行时，以本地为准，将多余远程任务做删除
- 增加 `~/.config/tuido/config.json` 的配置方式
- 支持 --pull 命令，从远程拉取变化的任务列表 #feature
- 支持汇总到飞书多维表格，能够全局展示多项目的任务列表 !P1
- 修复 `tuido --publish` 重复上传记录的问题 #bugfix
- 增加 `tuido --publish` 命令将本地任务列表上传到远程飞书表格
- `tuido --global-view` 改为从 `~/.config/tuido/config.json` 读取配置
- 支持切换主题 #ui
- 支持层级展示 !P1
- 支持左右移动卡片，相当于迁移卡片状态
- 支持上下移动卡片，对任务排序
- 为空的栏目也显示 !P1