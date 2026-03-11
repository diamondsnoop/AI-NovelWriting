# Codex 长篇小说系统模块设计文档 v2

## 0. 文档目的

这份文档在前一版基础上做结构修正，重点解决 5 个容易在实现阶段失控的问题：

1. `context_engine` 的归属不清
2. 缺少统一 `llm_client`
3. `retrieval` 过度拆分
4. `decision` 与 `workflow` 的调用边界不够硬
5. 状态层与日志层容易混淆

目标不是多写模块，而是把边界定得更稳。

## 1. 设计总原则

### 1.1 `workflow` 负责流程级控制

`workflow` 负责：

- 选择执行顺序
- 决定是否暂停
- 决定是否进入询问
- 决定是否回滚或恢复

它不负责具体写正文，也不负责具体审稿。

### 1.2 业务模块负责执行，不负责全局流程改向

`creation`、`review`、`retrieval`、`memory`、`presentation` 都只能：

- 返回业务结果
- 返回标准化 signal

不能直接改变流程走向。

### 1.3 上下文组包属于流程桥接，不属于正文创作

写作前的上下文整理，本质上是把多个来源的信息组装成“执行包”。
它像开拍前的场记本，不像真正下笔写戏的编剧。

因此它应该归到 `workflow`，而不是 `creation`。

### 1.4 统一模型调用必须下沉到基础设施层

如果写作、审查、决策都各自调用模型，后面一定会出现：

- 参数不一致
- 错误处理不一致
- 日志不一致
- 切模型时改一片

所以所有模型调用都必须走统一入口。

## 2. 一级模块总览

系统建议拆成 9 个一级模块：

1. `foundation`
2. `interaction`
3. `workflow`
4. `decision`
5. `creation`
6. `review`
7. `memory`
8. `retrieval`
9. `presentation`

其中：

- `foundation` 是横向底座
- 其他 8 个模块构成产品主体

## 3. 模块设计

### 3.1 `foundation`

职责：

- 提供所有模块共用的基础设施

子模块：

- `foundation.project_locator`
  - 定位当前工作区和当前小说项目
- `foundation.path_guard`
  - 做路径访问保护
- `foundation.config`
  - 统一加载系统配置和项目配置
- `foundation.io`
  - 统一文本、JSON、数据库和文件锁读写
- `foundation.logging`
  - 统一记录运行日志、错误日志、性能日志
- `foundation.llm_client`
  - 统一管理模型调用入口
  - 管理任务级模型配置
  - 管理超时、重试、错误处理
  - 记录调用日志、时延和成本
  - 支持后续模型路由和替换

边界：

- 不负责写作
- 不负责审查
- 不负责用户裁决

### 3.2 `interaction`

职责：

- 接收用户命令
- 管理当前交互会话
- 把请求交给 `workflow`

子模块：

- `interaction.cli`
  - 统一命令入口
- `interaction.session`
  - 管理当前会话和当前任务展示
- `interaction.command_registry`
  - 管理命令定义、别名和帮助

边界：

- 不直接操作项目状态
- 不直接写正文
- 不直接查数据库

### 3.3 `workflow`

职责：

- 负责所有流程级编排
- 负责消费标准化 signal
- 负责决定是否进入 `decision`

子模块：

- `workflow.init_flow`
- `workflow.plan_flow`
- `workflow.write_flow`
- `workflow.review_flow`
- `workflow.query_flow`
- `workflow.resume_flow`
- `workflow.learn_flow`
- `workflow.dashboard_flow`
- `workflow.state_tracker`
  - 记录当前任务执行到哪一步
  - 作用域为 `project_id + task_id`
  - 是跨 flow 共享的状态服务
  - 不是写死成不可替换的硬单例
- `workflow.context_assembler`
  - 组装章节执行包
  - 聚合大纲、摘要、当前状态、伏笔、节奏约束、检索结果
  - 只做聚合和打包，不做正文生成判断

边界：

- 不直接生成正文
- 不直接审稿
- 不直接写最终状态

### 3.4 `decision`

职责：

- 负责“该不该问”和“怎么问”
- 负责记录用户裁决

子模块：

- `decision.trigger_engine`
  - 负责生成决策信号
  - 由两类来源组成：
  - 规则信号：缺文件、覆盖写入、恢复分叉、高风险确认
  - 模型语义信号：设定冲突、信息不足、路线分叉、重大创作风险
- `decision.question_builder`
  - 把内部问题转成用户看得懂的问题
- `decision.resolution_store`
  - 保存用户裁决结果
- `decision.policy`
  - 规定哪些情况必须问，哪些可以自动处理

关键边界：

- `decision` 不直接控制流程
- `decision` 不直接暂停流程
- `decision` 不直接推进流程
- 它只响应 `workflow` 的调用，并把裁决结果交还给 `workflow`

通俗比喻：

它像收费站和岔路口提示牌，不负责开车，只负责让你做关键选择。

### 3.5 `creation`

职责：

- 负责实际创作产出

子模块：

- `creation.init_builder`
  - 初始化项目骨架和模板
- `creation.genre_engine`
  - 处理题材约束和题材模板
- `creation.outline_engine`
  - 生成分卷规划、节拍表、时间线、章节大纲
- `creation.writer_engine`
  - 根据执行包生成章节草稿
- `creation.style_engine`
  - 做风格适配，只改表达，不改剧情事实
- `creation.polish_engine`
  - 根据审查结果修补和润色正文

边界：

- 不直接读取散乱项目状态
- 不直接决定是否进入用户询问
- 不直接回写最终流程状态

### 3.6 `review`

职责：

- 负责多维质量检查

子模块：

- `review.consistency_checker`
- `review.continuity_checker`
- `review.character_checker`
- `review.pacing_checker`
- `review.high_point_checker`
- `review.reader_pull_checker`
- `review.report_builder`
- `review.gatekeeper`

关键规则：

- `workflow` 只调用一次 `review`
- `review` 内部负责并行调度多个 checker
- checker 只属于 `review` 的内部实现
- `review` 对外只返回统一报告、评分、问题列表和标准化 signal

边界：

- 不直接调用 `decision`
- 不直接回写最终状态
- 不直接改正文成稿

### 3.7 `memory`

职责：

- 维护项目级长期真相
- 保存可恢复状态切片

子模块：

- `memory.state_store`
  - 维护 progress、角色状态、伏笔状态、关系状态、chapter_meta
  - 统一容纳 checkpoints 和 snapshots
- `memory.index_store`
  - 管理结构化索引
  - 包括 chapters、scenes、entities、aliases、relationships、state_changes、review_metrics
- `memory.summary_store`
  - 管理章节摘要
- `memory.project_memory_store`
  - 管理 learn 功能产生的项目记忆
- `memory.validator`
  - 校验状态结构和回写结果是否合法

边界：

- 不负责创作判断
- 不负责流程控制
- 不负责运行 trace 记录

### 3.8 `retrieval`

职责：

- 把前文相关信息找回来

子模块：

- `retrieval.query_router`
  - 判断当前查询意图
- `retrieval.search_engine`
  - 对外唯一检索入口
  - 内部用策略模式支持关键词、向量、混合等方式
- `retrieval.rerank_engine`
  - 对候选结果重新排序
- `retrieval.scene_indexer`
  - 把正文切成可检索片段
- `retrieval.context_recall`
  - 为写作流程提供最相关的召回结果

边界：

- 不判断内容好坏
- 不决定流程走向

### 3.9 `presentation`

职责：

- 负责展示、诊断和运维辅助

子模块：

- `presentation.dashboard`
  - 只读 Web Dashboard
- `presentation.status_report`
  - 生成健康报告
- `presentation.ops_tools`
  - 提供索引重建、状态诊断、向量重建、测试入口

边界：

- 不直接改正文
- 不直接推进流程
- Dashboard 默认只读

## 4. 模块调用规则

### 4.1 允许的主方向

- `interaction -> workflow`
- `workflow -> creation`
- `workflow -> review`
- `workflow -> retrieval`
- `workflow -> decision`
- `workflow -> memory`
- `workflow -> presentation`

### 4.2 允许的例外

- `interaction -> presentation`

但只允许纯展示入口，不允许业务判断和状态更新。

### 4.3 禁止方向

- `creation -> decision`
- `review -> decision`
- `retrieval -> decision`
- `creation -> workflow`
- `review -> workflow`
- `memory -> workflow`
- `presentation -> workflow`

## 5. 关键调用链

### 5.1 写作链路

1. `interaction` 接收写作命令
2. `workflow.write_flow` 启动任务
3. `workflow.state_tracker` 建立任务状态
4. `workflow.context_assembler` 组装执行包
5. `retrieval.context_recall` 提供相关召回
6. `creation.writer_engine` 生成草稿
7. `creation.style_engine` 做表达层处理
8. `review` 内部并行审查并汇总报告
9. `workflow` 判断是否需要进入 `decision`
10. 如有必要，`workflow -> decision`
11. `creation.polish_engine` 根据报告或裁决做修补
12. `workflow -> memory` 正式回写状态、摘要、索引
13. `workflow -> presentation.status_report` 可选输出报告

### 5.2 查询链路

1. `interaction`
2. `workflow.query_flow`
3. `retrieval.query_router`
4. `memory`
5. `retrieval.search_engine`
6. `presentation` 或结构化文本输出

### 5.3 恢复链路

1. `interaction`
2. `workflow.resume_flow`
3. `workflow.state_tracker`
4. `memory.state_store`
5. `workflow` 判断风险
6. 必要时进入 `decision`
7. 回到原流程或执行回滚

## 6. 最容易失控的模块

### 6.1 `workflow`

风险：

- 容易膨胀成超大流程脚本

控制方式：

- 只做顺序编排和 signal 消费
- 不做具体业务逻辑

### 6.2 `decision`

风险：

- 问得太多，用户被打断
- 问得太少，AI 擅自推进

控制方式：

- 规则信号负责硬条件
- 模型语义信号负责高层创作判断
- 最终是否进入询问由 `workflow` 决定

### 6.3 `memory`

风险：

- 状态字段无限膨胀
- 状态和日志混在一起

控制方式：

- 轻量状态放 JSON
- 结构化索引放数据库
- 可恢复切片放状态层
- 运行 trace 放日志层

### 6.4 `review`

风险：

- 说很多，但报告没有行动价值

控制方式：

- 每个 checker 只负责一个维度
- 报告必须输出“问题 -> 定位 -> 修补建议”

## 7. 对 Claude Code 原结构的迁移

- `skills/*` 迁移为 `workflow` 主流程定义
- `agents/*` 迁移为 `creation` 与 `review` 的角色分工
- `scripts/*` 迁移为 `foundation`、`memory`、`presentation` 和部分 `workflow` 支撑逻辑
- `AskUserQuestion` 迁移为正式 `decision` 层
- Claude 风格子代理调度迁移为模块内调度和统一 `llm_client`

## 8. 一句话总结

这一版的重点不是“多加几个模块”，而是把控制流、上下文组包、模型调用和状态边界四件事锁死。
这些边界一旦先定清，后面写代码时返工会少很多。
