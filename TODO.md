---
theme: atom-one-dark
remote:
  feishu_api_endpoint: https://fsopen.bytedance.net/open-apis
  feishu_table_app_token: FcS8bHGgRatZFZsrlDrl1nDOgeg
  feishu_table_id: tblY5rSJzlWRPRoU
  feishu_table_view_id: vewyMDUelr
---

# TUIDO

## Todo
- 修复 `--global-view --push` 时，对 project 解析的问题，导致的比对错误 #bugfix ~2026-03-06T12:09
- `tuido` 命令打开全部项目，`tuido .` 打开当前项目 !P2 ~2026-03-06T12:09

## Active

## Done
- 增加 `tuido pick` 命令，在 TODO 里挑选最顶端的任务返回，并移动至下个栏目 ~2026-03-06T12:09
- 增加 `tuido add` 命令，新增任务 #feature ~2026-03-06T12:02
- 增加 'e' 按键操作的支持，在 tui 下修改任务 !P2 ~2026-03-06T11:02
- tui 显示，对标题增加行内样式，支持代码高亮、加粗、删除等样式 !P2 ~2026-03-06T10:18
- 增加 'd' 按键操作的支持，在 tui 下删除任务 !P2 ~2026-03-06T00:01
- 增加 'a' 按键操作的支持，在 tui 下添加任务 !P2 ~2026-03-06T00:01
- 增加 `list --status "Active"` 命令，输出按照 status 过滤后的结果 ~2026-03-05T23:17
- global-view 模式重新设计，读取自 /tmp/TODO_global.md 文件 ~2026-03-05T16:41
- `--global-view` 模式下，也支持切换主题。这个设置保存到 `~/.config/tui/config.yaml` 里 ~2026-02-24T13:28
- 为每个任务增加记录最后更新时间的功能 ~2026-03-05T23:55
- push 命令能够预览远程比本地多出来的任务，真正执行时，以本地为准，将多余远程任务做删除 ~2026-02-24T13:28
- 增加 `~/.config/tuido/config.json` 的配置方式 ~2026-02-24T13:28
- 支持 --pull 命令，从远程拉取变化的任务列表 #feature ~2026-02-24T13:28
- 支持汇总到飞书多维表格，能够全局展示多项目的任务列表 !P1 ~2026-02-24T13:28
- 修复 `tuido --publish` 重复上传记录的问题 #bugfix ~2026-02-24T22:23
- 增加 `tuido --publish` 命令将本地任务列表上传到远程飞书表格 ~2026-02-24T23:00
- `tuido --global-view` 改为从 `~/.config/tuido/config.json` 读取配置 ~2026-02-24T22:23
- 支持切换主题 #ui ~2026-02-24T22:23
- 支持层级展示 !P1 ~2026-02-27T11:18
- 支持左右移动卡片，相当于迁移卡片状态 ~2026-02-27T11:18
- 支持上下移动卡片，对任务排序 ~2026-02-27T11:18
- 为空的栏目也显示 !P1 ~2026-02-27T11:18