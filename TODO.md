---
theme: dracula
---

# TODO

## Todo
- Support for due dates #enhancement
- Export to different formats (JSON, CSV) #feature
- Implement task editing within TUI #feature !high
- 在变更开始时给用户发通知 !high
- 飞书消息通道切换至机器人，卡片上提供回滚和标记成功的按钮。大模型切到豆包等方舟平台上提供的模型 #feature

## In Progress
- Integration with GitHub Issues  (waiting for API key) #integration
- Color themes #ui
- 将迁移结果更新到飞书表格 #feature

## Blocked
- Add search/filter functionality #feature !high

## Done
- 观测异常和标记成功逻辑从 dsyncer 迁移至旁路观测 #feature !high
- 增加回滚的日志，用于统计失败中回滚的占比 !high
- decc 重构为每个接口合并调用大模型
- spacex 流程里增加前置状态过滤
- 批量刷新多维表格里的任务状态
- 制作迁移进展大盘
- 在飞书表格里增加消费流量的统计，以可以按照流量进行迁移优先级的选择
- 优化统计算法的风险判断，减少误判
- 新增资源分配的逻辑，根据 mq 消费 tps，动态计算分配的 dflow 进程数 !high
- 链路流量的参考值改为上一天的峰值 tps
- 飞书表格里对任务增加所属业务的信息
- 增加会话记忆
- 增加指令。/clear 清空记忆
- 增加天级别持续观测，覆盖完整的业务峰谷周期
- 飞书卡片在输出可点击跳转的链接
- 增加 NODE_ERROR 的批量观测和异常告警
- 记录迁移成功的任务
- 风险观测启动的卡片上，增加新 DFlow 任务ID
- 发送风险告警时，添加 At All
- SpaceX 并行网关并发任务数调整为10
- 风险警告的卡片上，对接飞书上传图片，直接显示图片内容
- 批量观测大盘增加风险观测区间

