# Codex 长篇小说系统数据设计文档（讨论稿）

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

“这本书现在是什么状态” 和 “这次任务跑到了哪一步” 不是一回事。

前者是长期事实。
后者是短期过程。

通俗比喻：

- 长期事实像病历
- 短期过程像这次挂号排队到几号

不能混写在一张纸上。

### 1.2 结构化状态和原始正文分开

正文是正文。
状态是从正文里抽出来、便于查询和恢复的结构化信息。

例如：

- 第 31 章正文是一整篇文章
- “林河在第 31 章突破到二阶” 是结构化状态

这两类信息不能互相代替。

### 1.3 可恢复数据和日志分开

能用于恢复任务的数据，必须是结构化、可重放、可定位的。

日志只是帮助排错，不是业务真相。

通俗比喻：

- 可恢复数据像存档点
- 日志像监控录像

## 2. 数据分层

建议把系统数据分成 5 层：

1. 项目元数据
2. 项目长期状态
3. 任务执行状态
4. 结构化索引与检索数据
5. 运行日志与观测数据

## 3. 核心数据对象

## 3.1 `project`

### 含义

一部小说项目的总容器。

### 需要保存的信息

- `project_id`
- `title`
- `genre_profile`
- `created_at`
- `updated_at`
- `active_volume`
- `active_chapter`
- `project_root`
- `status`

### 作用

- 让系统知道“当前在操作哪本书”
- 为其他所有数据对象提供挂靠点

### 主要读写方

- 写入：`workflow.init_flow`
- 读取：所有流程

## 3.2 `project_state`

### 含义

这本书当前的长期真相。

### 建议内容

- `progress`
  - 当前卷
  - 当前章
  - 已完成章节数
- `protagonist_state`
  - 主角当前实力、资源、伤势、目标
- `world_state`
  - 世界规则、局势、公开事件
- `plot_threads`
  - 主线、支线、冲突线
- `foreshadowing_state`
  - 已埋伏笔、待回收伏笔、已回收伏笔
- `relationship_state`
  - 主要人物关系当前状态
- `arc_state`
  - 当前卷目标、阶段、节奏位置

### 作用

- 为新一章写作提供当前全书状态
- 为查询和审查提供结构化依据

### 主要读写方

- 写入：`workflow -> memory`
- 读取：`workflow.context_assembler`、`query_flow`、`review`

### 建议存放位置

- `state.json` 或等价项目状态文件

## 3.3 `workflow_task_state`

### 含义

某一次任务执行到哪里了。

### 建议内容

- `task_id`
- `project_id`
- `task_type`
  - `init` / `plan` / `write` / `review` / `query` / `resume` / `learn`
- `started_at`
- `updated_at`
- `current_step`
- `completed_steps`
- `failed_steps`
- `task_status`
- `artifacts`
  - 当前任务产生了哪些中间结果
- `resume_token`

### 作用

- 支持中断恢复
- 让系统知道任务停在了哪里

### 主要读写方

- 写入：`workflow.state_tracker`
- 读取：`resume_flow`

### 作用域

- `project_id + task_id`

## 3.4 `chapter`

### 含义

一章正文及其元信息。

### 建议内容

- `chapter_id`
- `project_id`
- `volume_no`
- `chapter_no`
- `title`
- `status`
  - 草稿 / 已审查 / 已定稿
- `outline_ref`
- `content_ref`
- `word_count`
- `created_at`
- `updated_at`
- `version`

### 作用

- 管理每章正式内容
- 支持版本追踪和重新审查

### 主要读写方

- 写入：`creation.writer_engine` 产出后由 `workflow -> memory`
- 读取：`retrieval`、`review`、`query`

### 注意

正文内容本体和元信息可以分开存。
元信息适合进索引，正文适合保留为独立文本文件。

## 3.5 `chapter_summary`

### 含义

每章的压缩摘要。

### 建议内容

- `chapter_id`
- `summary_short`
- `summary_detailed`
- `key_events`
- `character_changes`
- `state_changes`
- `foreshadowing_changes`

### 作用

- 让上下文准备不必每次重读整章
- 为查询和审查提供快速入口

### 主要读写方

- 写入：写作完成后的回写阶段
- 读取：`workflow.context_assembler`、`query_flow`

## 3.6 `entity`

### 含义

人物、地点、势力、物品、规则等可被命名和追踪的对象。

### 建议内容

- `entity_id`
- `project_id`
- `entity_type`
- `name`
- `aliases`
- `description`
- `first_seen_chapter`
- `current_status`
- `tags`

### 作用

- 支持查询
- 支持一致性审查
- 支持关系图谱

### 主要读写方

- 写入：回写阶段的实体抽取
- 读取：`query_flow`、`review`、`retrieval`

## 3.7 `relationship`

### 含义

实体和实体之间的关系。

### 建议内容

- `relationship_id`
- `project_id`
- `source_entity_id`
- `target_entity_id`
- `relationship_type`
- `current_state`
- `changed_in_chapter`
- `evidence_ref`

### 作用

- 跟踪人物关系、阵营关系、师徒关系、敌对关系等

### 主要读写方

- 写入：回写阶段
- 读取：`query_flow`、`presentation.dashboard`

## 3.8 `foreshadowing`

### 含义

伏笔对象。

### 建议内容

- `foreshadowing_id`
- `project_id`
- `description`
- `introduced_in_chapter`
- `related_entities`
- `status`
  - 未回收 / 部分回收 / 已回收
- `resolved_in_chapter`

### 作用

- 防止埋了不收
- 支持节奏和兑现检查

### 主要读写方

- 写入：回写阶段
- 读取：`review`、`query_flow`、`status_report`

## 3.9 `review_record`

### 含义

一次审查的完整结果。

### 建议内容

- `review_id`
- `project_id`
- `chapter_id`
- `review_mode`
- `scores`
  - 一致性、连贯性、人设、节奏、高潮、追读感
- `issues`
- `fix_suggestions`
- `gate_result`
- `created_at`

### 作用

- 让审查不是一句口头评价，而是可追踪记录
- 支持后续二次修补和质量分析

### 主要读写方

- 写入：`review`
- 读取：`creation.polish_engine`、`status_report`

## 3.10 `decision_record`

### 含义

用户在关键节点做过的裁决记录。

### 建议内容

- `decision_id`
- `project_id`
- `task_id`
- `decision_type`
  - 补信息 / 裁决冲突 / 方向分叉 / 高风险确认
- `question`
- `options`
- `selected_option`
- `user_note`
- `created_at`

### 作用

- 让系统知道过去分叉是怎么选的
- 避免同一问题反复问

### 主要读写方

- 写入：`decision`
- 读取：`workflow`、`decision.policy`

## 3.11 `project_memory`

### 含义

系统从长期协作中提炼出的项目级经验。

### 建议内容

- `memory_id`
- `project_id`
- `memory_type`
  - 文风偏好 / 节奏偏好 / 禁忌写法 / 常用结构
- `content`
- `confidence`
- `source_refs`

### 作用

- 支持 learn 功能
- 让系统逐渐贴合这本书的写法

### 主要读写方

- 写入：`learn_flow`
- 读取：`creation`、`review`

## 3.12 `retrieval_document`

### 含义

可被检索的正文片段或结构化片段。

### 建议内容

- `doc_id`
- `project_id`
- `source_type`
  - 正文 / 摘要 / 设定 / 大纲 / 审查记录
- `source_ref`
- `chunk_text`
- `chunk_index`
- `tags`

### 作用

- 为 BM25、向量检索、混合检索提供统一输入对象

### 主要读写方

- 写入：`retrieval.scene_indexer`
- 读取：`retrieval.search_engine`

## 3.13 `embedding_record`

### 含义

检索对象对应的向量记录。

### 建议内容

- `embedding_id`
- `doc_id`
- `project_id`
- `vector_ref`
- `embedding_model`
- `created_at`

### 作用

- 支撑语义检索

### 主要读写方

- 写入：索引构建流程
- 读取：`retrieval.search_engine`

## 3.14 `checkpoint_snapshot`

### 含义

可用于恢复的状态切片。

### 建议内容

- `snapshot_id`
- `project_id`
- `task_id`
- `snapshot_type`
  - workflow checkpoint / review checkpoint / chapter execution snapshot
- `step_name`
- `state_payload`
- `created_at`

### 作用

- 断点恢复
- 审查回放
- 故障诊断

### 主要读写方

- 写入：`workflow -> memory`
- 读取：`resume_flow`

## 3.15 `operation_log`

### 含义

运行时观测日志。

### 建议内容

- `log_id`
- `project_id`
- `task_id`
- `module`
- `action`
- `level`
- `message`
- `metrics`
- `created_at`

### 作用

- 观测、诊断、排障

### 主要读写方

- 写入：`foundation.logging`
- 读取：运维和调试场景

### 注意

它不是业务恢复来源。

## 4. 数据放置建议

## 4.1 文件

适合放文件的内容：

- 正文章节
- 设定文档
- 大纲文档
- 模板

原因：

- 这些内容天然是长文本
- 人工阅读和手动修改方便

## 4.2 JSON 状态文件

适合放 JSON 的内容：

- `project`
- `project_state`
- 部分 `workflow_task_state`

原因：

- 轻量
- 可直接查看
- 容易做项目级快照

## 4.3 SQLite 或等价结构化存储

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

原因：

- 查询频繁
- 关系清楚
- 需要筛选、排序、聚合

## 4.4 向量存储

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

## 6. 当前版本最容易被质疑的地方

这份讨论稿里，我预判最容易被挑战的有 4 点：

1. `project_state` 是否会越长越胖
2. `chapter_summary` 和 `retrieval_document` 是否重复
3. `decision_record` 是否应该进入长期状态而不是单独表
4. `checkpoint_snapshot` 和 `workflow_task_state` 的边界是否还不够硬

这些都值得继续讨论。

## 7. 一句话总结

这份文档的核心意思是：

系统不能只会“写”，还必须知道“写到了哪、改了什么、为什么这么改、出了问题怎么恢复”。

数据设计就是把这些“记住的能力”先定下来。
