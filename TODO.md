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
- 修复 `--global-view --push` 时，对 project 解析的问题，导致的比对错误 #bugfix ~2026-03-06T12:16

## Active

## Done
- 改进命令行帮助信息，添加更多使用示例 #docs
- `tuido` 命令打开当前项目，`tuido .` 打开指定目录 #feature
- 增加 `tuido pick` 命令，在 TODO 里挑选最顶端的任务返回，并移动至下个栏目 #feature
- 增加 `tuido add` 命令，新增任务 #feature
- 增加 'e' 按键操作的支持，在 tui 下修改任务 #ui
- tui 显示，对标题增加行内样式，支持代码高亮、加粗、删除等样式 #ui
- 增加 'd' 按键操作的支持，在 tui 下删除任务 #ui
- 增加 'a' 按键操作的支持，在 tui 下添加任务 #ui
- 增加 `list --status "Active"` 命令，输出按照 status 过滤后的结果 #feature
- global-view 模式重新设计，读取自飞书表格 #feature
- `--global-view` 模式下，也支持切换主题。这个设置保存到 `~/.config/tuido/config.yaml` 里 #ui
- 为每个任务增加记录最后更新时间的功能 #feature
- push 命令能够预览远程比本地多出来的任务，真正执行时，以本地为准，将多余远程任务做删除 #feature
- 增加 `~/.config/tuido/config.yaml` 的配置方式 #feature
- 支持 --pull 命令，从远程拉取变化的任务列表 #feature
- 支持汇总到飞书多维表格，能够全局展示多项目的任务列表 #feature !P1
- 支持切换主题 #ui
- 支持层级展示 #feature !P1
- 支持左右移动卡片，相当于迁移卡片状态 #ui !P1
- 支持上下移动卡片，对任务排序 #ui !P1
- 为空的栏目也显示 #ui !P1