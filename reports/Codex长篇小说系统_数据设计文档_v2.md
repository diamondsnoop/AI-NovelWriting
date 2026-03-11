# Codex 长篇小说系统数据设计文档 v2

## 0. 文档目的

这份文档只回答一类问题：

- 系统到底要存哪些数据
- 这些数据分别放在哪里
- 谁负责写入，谁负责读取
- 哪些是长期状态，哪些是任务状态，哪些只是日志

它不是数据库建表说明书，也不是代码设计稿。
它的作用是先把“数据骨架”定出来，避免后面一边开发一边发明字段。

## 1. 设计原则

### 1.1 事实和过程分开

“这本书现在是什么状态”和“这次任务跑到了哪一步”不是一回事。

前者是长期事实。
后者是短期过程。

通俗比喻：

- 长期事实像病历
- 短期过程像这次挂号排队到几号

### 1.2 正文和结构化状态分开

正文是正文。
状态是从正文里抽出来、便于查询和恢复的结构化信息。

例如：

- 第 31 章正文是一整篇文章
- “林河在第 31 章突破到二阶”是结构化状态

这两类信息不能互相代替。

### 1.3 可恢复数据和日志分开

能用于恢复任务的数据，必须是结构化、可重放、可定位的。
日志只是帮助排错，不是业务真相。

通俗比喻：

- 可恢复数据像存档点
- 日志像监控录像

### 1.4 当前快照和历史变化分开

`project_state` 只保存“现在是什么样”。
历史变化不在这里累积。

历史变化应该落到实体、关系、伏笔等对象的变更记录里。

否则 `project_state` 会慢慢变成什么都往里塞的杂物箱。

## 2. 数据分层

建议把系统数据分成 5 层：

1. 项目元数据
2. 项目长期状态
3. 任务执行状态
4. 结构化索引与检索数据
5. 运行日志与观测数据

## 3. 核心数据对象

### 3.1 `project`

含义：

一部小说项目的总容器。

建议内容：

- `project_id`
- `title`
- `genre_profile`
- `created_at`
- `updated_at`
- `active_volume`
- `active_chapter`
- `project_root`
- `status`

主要读写方：

- 写入：`workflow.init_flow`
- 读取：所有流程

### 3.2 `project_state`

含义：

这本书当前的长期真相。

建议内容：

- `progress`
- `protagonist_state`
- `world_state`
- `plot_threads`
- `foreshadowing_state`
- `relationship_state`
- `arc_state`

关键规则：

- 这里只保存当前快照
- 不累计历史变化
- 历史变化应下沉到 `entity`、`relationship`、`foreshadowing` 等对象的变更记录

主要读写方：

- 写入：`workflow -> memory`
- 读取：`workflow.context_assembler`、`query_flow`、`review`

建议存放位置：

- `state.json` 或等价项目状态文件

### 3.3 `workflow_task_state`

含义：

某一次任务执行到哪里了。

建议内容：

- `task_id`
- `project_id`
- `task_type`
- `started_at`
- `updated_at`
- `current_step`
- `completed_steps`
- `failed_steps`
- `task_status`
- `snapshot_ids`
- `resume_token`

关键规则：

- 它只记录步骤级进度
- 不保存可重放的中间状态载荷
- 如果要关联中间结果，只保留 `checkpoint_snapshot` 的引用

主要读写方：

- 写入：`workflow.state_tracker`
- 读取：`resume_flow`

作用域：

- `project_id + task_id`

### 3.4 `chapter`

含义：

一章正文及其元信息。

建议内容：

- `chapter_id`
- `project_id`
- `volume_no`
- `chapter_no`
- `title`
- `status`
- `outline_ref`
- `content_ref`
- `word_count`
- `created_at`
- `updated_at`
- `version`

主要读写方：

- 写入：`creation.writer_engine` 产出后由 `workflow -> memory`
- 读取：`retrieval`、`review`、`query`

说明：

正文内容本体和元信息可以分开存。
元信息适合进索引，正文适合保留为独立文本文件。

### 3.5 `chapter_summary`

含义：

每章的结构化压缩摘要。

建议内容：

- `chapter_id`
- `summary_short`
- `summary_detailed`
- `key_events`
- `character_changes`
- `state_changes`
- `foreshadowing_changes`

主要读写方：

- 写入：写作完成后的回写阶段
- 读取：`workflow.context_assembler`、`query_flow`

关键规则：

- 它是语义压缩对象，不是检索切片对象
- 生成后应由 `retrieval.scene_indexer` 或等价索引流程切片进入 `retrieval_document`
- 在检索层里，它应作为 `source_type = summary` 的来源之一

### 3.6 `entity`

含义：

人物、地点、势力、物品、规则等可追踪对象。

建议内容：

- `entity_id`
- `project_id`
- `entity_type`
- `name`
- `aliases`
- `description`
- `first_seen_chapter`
- `current_status`
- `tags`
- `change_history_refs`

主要读写方：

- 写入：回写阶段的实体抽取
- 读取：`query_flow`、`review`、`retrieval`

### 3.7 `relationship`

含义：

实体和实体之间的关系。

建议内容：

- `relationship_id`
- `project_id`
- `source_entity_id`
- `target_entity_id`
- `relationship_type`
- `current_state`
- `changed_in_chapter`
- `evidence_ref`
- `change_history_refs`

主要读写方：

- 写入：回写阶段
- 读取：`query_flow`、`presentation.dashboard`

### 3.8 `foreshadowing`

含义：

伏笔对象。

建议内容：

- `foreshadowing_id`
- `project_id`
- `description`
- `introduced_in_chapter`
- `related_entities`
- `status`
- `resolved_in_chapter`
- `change_history_refs`

主要读写方：

- 写入：回写阶段
- 读取：`review`、`query_flow`、`status_report`

### 3.9 `review_record`

含义：

一次审查的完整结果。

建议内容：

- `review_id`
- `project_id`
- `chapter_id`
- `review_mode`
- `scores`
- `issues`
- `fix_suggestions`
- `gate_result`
- `created_at`

主要读写方：

- 写入：`review`
- 读取：`creation.polish_engine`、`status_report`

### 3.10 `decision_record`

含义：

用户在关键节点做过的裁决记录。

建议内容：

- `decision_id`
- `project_id`
- `task_id`
- `decision_type`
- `question`
- `options`
- `selected_option`
- `user_note`
- `created_at`

主要读写方：

- 写入：`decision`
- 读取：`workflow`、`decision.policy`、`creation`

补充说明：

- `creation` 读取它的目的，是避免生成与既有用户裁决相冲突的内容
- 后续如有必要，`review` 也可以读取它来检查新稿是否违背既定路线

### 3.11 `project_memory`

含义：

系统从长期协作中提炼出的项目级经验。

建议内容：

- `memory_id`
- `project_id`
- `memory_type`
- `content`
- `source_refs`

当前约束：

- 暂不保留 `confidence`
- 原因不是它不重要，而是当前阶段还没有定义清楚更新机制
- 等 `learn` 功能把“谁更新、何时更新、按什么规则变化”设计完整后，再补回类似字段

主要读写方：

- 写入：`learn_flow`
- 读取：`creation`、`review`

### 3.12 `retrieval_document`

含义：

可被检索的正文片段或结构化片段。

建议内容：

- `doc_id`
- `project_id`
- `source_type`
- `source_ref`
- `chunk_text`
- `chunk_index`
- `tags`

主要读写方：

- 写入：`retrieval.scene_indexer`
- 读取：`retrieval.search_engine`

说明：

- `source_type` 可包括：正文、摘要、设定、大纲、审查记录

### 3.13 `embedding_record`

含义：

检索对象对应的向量记录。

建议内容：

- `embedding_id`
- `doc_id`
- `project_id`
- `vector_ref`
- `embedding_model`
- `created_at`

主要读写方：

- 写入：索引构建流程
- 读取：`retrieval.search_engine`

### 3.14 `checkpoint_snapshot`

含义：

可用于恢复的状态切片。

建议内容：

- `snapshot_id`
- `project_id`
- `task_id`
- `snapshot_type`
- `step_name`
- `state_payload`
- `created_at`

关键规则：

- 它保存的是可重放、可恢复的状态数据
- 它不是步骤进度记录
- 它和 `workflow_task_state` 的边界必须是硬边界

主要读写方：

- 写入：`workflow -> memory`
- 读取：`resume_flow`

### 3.15 `operation_log`

含义：

运行时观测日志。

建议内容：

- `log_id`
- `project_id`
- `task_id`
- `module`
- `action`
- `level`
- `message`
- `metrics`
- `created_at`

主要读写方：

- 写入：`foundation.logging`
- 读取：运维和调试场景

关键规则：

- 它只用于观测和排障
- 它不是业务恢复来源

## 4. 数据放置建议

### 4.1 文件

适合放文件的内容：

- 正文章节
- 设定文档
- 大纲文档
- 模板

原因：

- 这些内容天然是长文本
- 人工阅读和手动修改方便

### 4.2 JSON 状态文件

适合放 JSON 的内容：

- `project`
- `project_state`
- 轻量任务状态索引

原因：

- 轻量
- 可直接查看
- 易做项目级快照

### 4.3 SQLite 或等价结构化存储

适合放数据库的内容：

- `chapter` 元信息
- `chapter_summary`
- `entity`
- `relationship`
- `foreshadowing`
- `review_record`
- `decision_record`
- `project_memory`
- `checkpoint_snapshot`
- `workflow_task_state`

原因：

- 查询频繁
- 关系清楚
- 需要筛选、排序、聚合

### 4.4 向量存储

适合放向量数据的内容：

- `embedding_record`

原因：

- 检索方式不同
- 和结构化索引分开更稳

## 5. 关键读写边界

### 5.1 谁能写长期状态

原则上只有：

- `workflow -> memory`

可以正式回写长期状态。

`creation` 和 `review` 只能产出候选结果，不能直接改项目真相。

### 5.2 谁能写任务状态

原则上只有：

- `workflow.state_tracker`

负责更新任务执行状态。

### 5.3 谁能写日志

原则上只有：

- `foundation.logging`

负责写运行观测日志。

### 5.4 谁能把摘要送进检索层

原则上由：

- `retrieval.scene_indexer` 或等价索引流程

负责把 `chapter_summary` 转换为 `retrieval_document`。

## 6. 当前版本的重点约束

1. `project_state` 只存当前快照，不存历史堆积
2. `workflow_task_state` 只存步骤级进度，不存中间状态载荷
3. `checkpoint_snapshot` 只存可重放的恢复数据
4. `chapter_summary` 和 `retrieval_document` 不合并，但必须有明确转换链路
5. `decision_record` 必须允许 `creation` 读取
6. `project_memory` 暂不引入没有更新机制支撑的 `confidence`

## 7. 一句话总结

数据设计的核心不是“多存一点”，而是“每类数据只承担一种职责”。
只要当前快照、历史变化、任务进度、恢复切片、检索切片和运行日志这几类东西不混，后面的实现就会稳很多。
