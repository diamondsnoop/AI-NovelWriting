# Webnovel Writer 功能报告

## 1. 项目框架与主要功能

这个项目是一个基于 Claude Code 的长篇网文创作系统。它不是单纯“让模型写小说”，而是把小说创作拆成一套有状态、有流程、有检查、有恢复能力的流水线。

可以把它理解成一个“小说工厂”：
- `skills/` 像工厂的工序单，规定每一步要做什么。
- `agents/` 像不同岗位的工人，分别负责取材、审稿、校对、记账。
- `scripts/` 和 `scripts/data_modules/` 像后台调度和仓储系统，负责把流程、状态、索引、检索都管起来。
- `templates/`、`references/`、`genres/` 像工厂里的标准模板和操作手册。
- `dashboard/` 像监控大屏，用来查看项目当前状态。

### 它的核心功能

1. 小说项目初始化  
创建作品目录、状态文件、设定模板和总纲模板，让一部新小说有统一骨架。

2. 大纲规划  
把总纲细化成分卷规划、章节节拍表、时间线和章节大纲。

3. 章节写作  
不是直接生成正文，而是先准备上下文，再起草，再审查，再润色，再回写状态。

4. 多维质量审查  
检查设定一致性、剧情连贯性、人物是否 OOC、节奏是否失衡、爽点是否不足、追读感是否够强。

5. 状态管理与记忆管理  
把“这本书目前写到哪里、有哪些人物、有哪些伏笔、哪些关系发生了变化”保存下来，防止模型后面忘记。

6. RAG 检索辅助  
在写某一章时，自动检索前文相关信息，减少前后打架。

7. 断点恢复  
如果写作或审查在中途被打断，可以检测停在哪一步，并按规则恢复。

8. 项目查询与可视化  
可以查询角色、设定、伏笔、节奏，也可以打开一个只读 Dashboard 查看全局情况。

## 2. 这些功能是如何实现的

下面按“文件块/代码块负责什么任务，最后实现什么功能”来拆。

### A. 外层入口块：统一命令入口

相关文件：
- `webnovel-writer/scripts/webnovel.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/project_locator.py`

这一块负责把各种零散能力收口成一个统一入口。

它完成的任务：
- 识别当前真正的小说项目根目录，而不是误把工作区根目录当成项目目录。
- 提供统一命令分发，比如把“初始化、状态管理、索引管理、RAG、工作流、备份”这些命令转发到对应模块。
- 统一处理参数和路径，减少不同脚本各自处理路径带来的混乱。

最终实现的功能：
- 让整个系统可以像一个“总控制台”一样工作。

通俗比喻：
- 它像商场的一楼总服务台。用户只需要到一个窗口提需求，服务台再把事情分发给正确的部门。

### B. 流程定义块：把创作拆成固定工序

相关文件：
- `webnovel-writer/skills/webnovel-init/SKILL.md`
- `webnovel-writer/skills/webnovel-plan/SKILL.md`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- `webnovel-writer/skills/webnovel-query/SKILL.md`
- `webnovel-writer/skills/webnovel-resume/SKILL.md`
- `webnovel-writer/skills/webnovel-dashboard/SKILL.md`

这一块不是具体代码执行层，而是流程规则层。

它完成的任务：
- 规定每个命令有哪些步骤。
- 规定每一步该读哪些资料、该产出什么文件、哪些步骤可以跳、哪些步骤不能跳。
- 规定不同模式，比如标准模式、快速模式、最简模式。
- 规定失败时怎么处理，中断时怎么恢复。

最终实现的功能：
- 把“写小说”从一次性对话，变成一套可重复执行的标准流程。

通俗比喻：
- 这像做手术前的标准操作清单。不是“医生想怎么做就怎么做”，而是每一步都写清楚，避免漏项。

### C. 初始化块：建立小说项目骨架

相关文件：
- `webnovel-writer/scripts/init_project.py`
- `webnovel-writer/templates/output/*`
- `webnovel-writer/templates/genres/*`
- `webnovel-writer/templates/golden-finger-templates.md`

这一块负责从零生成一部小说的基础工程。

它完成的任务：
- 创建目录，例如正文、设定集、大纲、`.webnovel` 运行目录。
- 创建或补全 `state.json` 的基础结构。
- 生成总纲模板、主角卡、世界观、力量体系、反派设计等模板文件。
- 根据题材映射不同模板，支持复合题材和别名归一化。

最终实现的功能：
- 用户运行一次初始化后，项目就不再是空目录，而是有完整写作骨架的“可开工项目”。

通俗比喻：
- 它像盖楼前先把地基、钢筋和房间分区都搭好，后面装修和入住才不会乱。

### D. 上下文构建块：写每章前先准备“任务包”

相关文件：
- `webnovel-writer/scripts/extract_chapter_context.py`
- `webnovel-writer/scripts/chapter_outline_loader.py`
- `webnovel-writer/scripts/chapter_paths.py`
- `webnovel-writer/scripts/data_modules/context_manager.py`
- `webnovel-writer/scripts/data_modules/context_ranker.py`
- `webnovel-writer/scripts/data_modules/context_weights.py`
- `webnovel-writer/references/context-contract-v2.md`

这一块负责在写某一章之前，把真正需要的信息组织出来。

它完成的任务：
- 读取这一章对应的大纲片段。
- 读取前几章摘要，而不是粗暴塞进整本书正文。
- 从 `state.json` 提炼当前主角状态、剧情进度、最近 Strand、紧急伏笔等信息。
- 调用上下文管理器，生成更结构化的写作合同，比如本章目标、阻力、代价、未闭合问题、读者信号、写作指导。
- 在需要时触发 RAG，补充前文相关信息。

最终实现的功能：
- 给写作模块一份“足够写、又不过载”的上下文包。

通俗比喻：
- 它像导演开拍前发给演员的“本场戏 briefing”：这场戏要达到什么效果、和上场怎么接、不能演错什么。

### E. 写作执行块：从草稿到可发布正文

相关文件：
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/agents/context-agent.md`
- `webnovel-writer/agents/data-agent.md`
- `webnovel-writer/skills/webnovel-write/references/*`

这一块是核心产出层。

它完成的任务：
- 先由 Context Agent 生成创作执行包。
- 按规则生成章节草稿。
- 在部分模式下做风格适配，只改表达，不改剧情事实。
- 把草稿送去质量审查。
- 根据问题做润色和修补。
- 最后把最终正文交给数据层回写。

最终实现的功能：
- 不是“生成一段文本”，而是生成一章能进入长期连载体系的正文。

通俗比喻：
- 它像流水线上的装配工位。原料不是直接扔出去卖，而是经过组装、质检、返修后才出厂。

### F. 审查块：多检查员并行质检

相关文件：
- `webnovel-writer/agents/consistency-checker.md`
- `webnovel-writer/agents/continuity-checker.md`
- `webnovel-writer/agents/ooc-checker.md`
- `webnovel-writer/agents/high-point-checker.md`
- `webnovel-writer/agents/pacing-checker.md`
- `webnovel-writer/agents/reader-pull-checker.md`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- `webnovel-writer/references/checker-output-schema.md`

这一块负责给生成出来的章节做多角度检查。

它完成的任务：
- 一致性检查：设定、地点、时间、能力是否冲突。
- 连贯性检查：上一章和这一章之间是否接得上。
- OOC 检查：人物行为是否偏离人设。
- 爽点检查：高潮、打脸、兑现是否足够。
- 节奏检查：主线、感情线、世界线比例是否失衡。
- 追读感检查：章末钩子、悬念和期待管理是否有效。
- 把多个检查结果汇总成统一报告和评分。

最终实现的功能：
- 让章节不是“模型觉得差不多就行”，而是经过一套明确维度的质检。

通俗比喻：
- 这像一篇稿子同时过编辑、校对、剧情顾问和读者测试，而不是只让一个人拍脑袋决定。

### G. 状态块：保存运行中的“小说真相”

相关文件：
- `webnovel-writer/scripts/data_modules/state_manager.py`
- `webnovel-writer/scripts/update_state.py`
- `webnovel-writer/scripts/data_modules/state_validator.py`
- `webnovel-writer/references/project-memory-schema.md`

这一块负责保存轻量但关键的运行状态。

它完成的任务：
- 管理 `state.json` 的结构和默认字段。
- 保存进度，例如写到第几章、总字数、当前卷。
- 保存主角状态、金手指状态、伏笔列表、Strand 追踪器、章节元信息。
- 做增量写入和加锁，避免并行任务相互覆盖。
- 校验状态格式是否符合要求。

最终实现的功能：
- 保证系统始终知道“现在小说写到哪、主角处于什么状态、有哪些未回收信息”。

通俗比喻：
- 它像剧组的场记本。演员换了衣服、道具用了几次、哪条线索还没回收，场记都得记住，不然下一场就穿帮。

### H. 索引块：把大信息量装进数据库

相关文件：
- `webnovel-writer/scripts/data_modules/index_manager.py`
- `webnovel-writer/scripts/data_modules/index_chapter_mixin.py`
- `webnovel-writer/scripts/data_modules/index_entity_mixin.py`
- `webnovel-writer/scripts/data_modules/index_debt_mixin.py`
- `webnovel-writer/scripts/data_modules/index_reading_mixin.py`
- `webnovel-writer/scripts/data_modules/index_observability_mixin.py`
- `webnovel-writer/scripts/data_modules/sql_state_manager.py`

这一块负责把大量、频繁查询的数据放进 `index.db`。

它完成的任务：
- 存章节元数据、场景切片、实体出场记录。
- 存实体别名、状态变化、关系变化。
- 存审查分数、追读力指标、债务追踪、无效事实、工具调用统计。
- 把原来不适合继续放在 `state.json` 里的大块信息迁移到 SQLite。

最终实现的功能：
- 让系统在长期连载时还能快速查人、查地点、查伏笔、查某章质量。

通俗比喻：
- `state.json` 像钱包，装少量常用现金；`index.db` 像仓库账本，货很多时必须放仓库而不是塞口袋里。

### I. RAG 检索块：写当前章时翻前文资料

相关文件：
- `webnovel-writer/scripts/data_modules/rag_adapter.py`
- `webnovel-writer/scripts/data_modules/query_router.py`
- `webnovel-writer/scripts/data_modules/api_client.py`
- `webnovel-writer/docs/rag-and-config.md`

这一块负责让系统在写当前章节时，不只依赖当前对话记忆。

它完成的任务：
- 根据问题类型决定走向量检索、BM25、混合检索还是图谱混合检索。
- 在有 embedding key 时走语义检索，没有时回退到 BM25。
- 结合 rerank 提高返回片段的相关性。
- 给上下文构建和查询功能提供更可靠的前文召回。

最终实现的功能：
- 减少“前面写过但后面忘了”的情况。

通俗比喻：
- 它像写新一章前，助手先去档案室把最相关的旧卷宗翻出来，而不是让作者凭记忆硬想。

### J. 查询块：不是只会写，也会回答“这本书现在是什么状态”

相关文件：
- `webnovel-writer/skills/webnovel-query/SKILL.md`
- `webnovel-writer/scripts/status_reporter.py`
- `webnovel-writer/scripts/golden_three_checker.py`

这一块负责对项目当前状态做查询和摘要。

它完成的任务：
- 查询角色、力量体系、势力、物品、地点。
- 查询伏笔紧急度。
- 查询金手指状态。
- 查询 Strand 节奏是否失衡。
- 输出健康报告和重点告警。

最终实现的功能：
- 让用户和系统都能快速“盘点这本书现在到底是什么情况”。

通俗比喻：
- 它像飞行仪表盘，不是帮你开飞机，但会告诉你油量、速度、航向和警报。

### K. 断点恢复块：中断后不靠猜测继续

相关文件：
- `webnovel-writer/scripts/workflow_manager.py`
- `webnovel-writer/skills/webnovel-resume/SKILL.md`
- `webnovel-writer/skills/webnovel-resume/references/workflow-resume.md`

这一块负责记录写作任务的进度，并在中断后恢复。

它完成的任务：
- 记录当前命令、当前步骤、已完成步骤、失败步骤、产物状态。
- 输出调用轨迹，方便排查问题。
- 检测任务是停在起草、审查、润色还是回写。
- 按不同中断位置提供不同恢复策略，而不是一律强行续写。

最终实现的功能：
- 让长流程任务有“续跑”能力。

通俗比喻：
- 它像下载管理器。文件下到一半断网时，它会告诉你断在哪，而不是从头猜着下或者直接当成功了。

### L. 可视化块：只读 Dashboard

相关文件：
- `webnovel-writer/dashboard/server.py`
- `webnovel-writer/dashboard/app.py`
- `webnovel-writer/dashboard/watcher.py`
- `webnovel-writer/dashboard/path_guard.py`
- `webnovel-writer/dashboard/frontend/src/*`

这一块负责把项目状态可视化。

它完成的任务：
- 启动本地 Web 服务。
- 解析项目根目录。
- 读取 `.webnovel` 和正文相关信息。
- 监听项目文件变化并刷新视图。
- 做路径保护，确保只读且只访问项目范围内文件。

最终实现的功能：
- 让用户不用直接翻数据库和 JSON，也能看项目进度、关系图、章节信息、状态摘要。

通俗比喻：
- 它像医院的信息大屏，把病历、指标和流程状态图形化展示出来，但不直接做手术。

### M. 模板与参考资料块：让流程有统一标准

相关文件：
- `webnovel-writer/templates/*`
- `webnovel-writer/references/*`
- `webnovel-writer/genres/*`

这一块不是执行代码，但作用很大。

它完成的任务：
- 提供设定模板、大纲模板、题材模板。
- 提供世界观、冲突设计、爽点设计、节奏规划、风格适配等参考文档。
- 给各个 Skill 在不同阶段提供“该读什么资料”的依据。

最终实现的功能：
- 让系统输出不是完全随机，而是尽量落在一套稳定的网文工程方法里。

通俗比喻：
- 这像厨师的菜谱库和后厨标准手册。做的是不同菜，但火候和流程有统一标准。

## 3. 功能与实现的对应关系

### 功能 1：初始化小说项目

由这些块共同完成：
- 流程定义块
- 初始化块
- 模板与参考资料块
- 外层入口块

结果：
- 生成一套可继续规划和写作的项目骨架。

### 功能 2：规划分卷和章节

由这些块共同完成：
- 流程定义块
- 模板与参考资料块
- 状态块

结果：
- 从总纲走到卷级、章级规划，写作时不容易失控。

### 功能 3：写单章正文

由这些块共同完成：
- 外层入口块
- 上下文构建块
- 写作执行块
- 审查块
- 状态块
- 索引块

结果：
- 得到一章正文，并且把这章对全书造成的影响同步写回系统。

### 功能 4：控制长期连载中的一致性

由这些块共同完成：
- 状态块
- 索引块
- 审查块
- RAG 检索块

结果：
- 减少设定打架、角色失真、伏笔忘记回收。

### 功能 5：中断恢复和运行维护

由这些块共同完成：
- 断点恢复块
- 查询块
- 可视化块

结果：
- 让长链路写作不是一次性的“黑盒动作”，而是可观察、可定位、可恢复。

## 4. 一句话总结

这个项目最重要的价值，不是“它能写小说”，而是“它把长篇小说写作做成了一个可管理的系统”。

如果只模仿表面的提示词，很难复刻它的效果；如果把它的流程层、状态层、索引层和审查层学走，才算真正读懂这个项目。
