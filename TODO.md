---
theme: textual-dark
remote:
  feishu_api_endpoint: https://fsopen.bytedance.net/open-apis
  feishu_table_app_token: FcS8bHGgRatZFZsrlDrl1nDOgeg
  feishu_table_id: tblY5rSJzlWRPRoU
  feishu_table_view_id: vewyMDUelr
---

# TUIDO

## Todo
- `tuido --global-view` 从 `~/.config/tuido/config.json` 读取配置
- 修复 `tuido --publish` 重复上传记录的问题 #bugfix

## In Progress
- 支持汇总到飞书多维表格，能够全局展示多项目的任务列表 !P1

## Done
- 支持切换主题 #ui
- 支持层级展示 !P1
  - 读取逻辑，增加对层级的支持
  - 视觉上增加层级区分
  - 子卡片间支持调整顺序
  - 只有顶级卡片支持左右在栏目间迁移
- 支持左右移动卡片，相当于迁移卡片状态
- 支持上下移动卡片，对任务排序
- 为空的栏目也显示 !P1