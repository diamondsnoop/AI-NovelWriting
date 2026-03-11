# Codex 长篇小说系统第一版骨架搭建文档

## 0. 文档目的

这份文档只说明第一版骨架怎么搭。

目标不是一次把功能做全，而是先把：

- 目录结构
- 基础底座
- 主控制流
- 最小可运行链路

搭正确。

## 1. 第一版骨架的目标

第一版骨架只做一件事：

**先打通一条最小但结构正确的主链路。**

这条链路至少包括：

1. 初始化项目
2. 启动写作任务
3. 组装上下文执行包
4. 生成章节草稿
5. 返回最小审查结果
6. 回写状态
7. 记录任务状态
8. 支持恢复查看

## 2. 第一版要搭的目录

建议先建立这些一级目录：

- `src/foundation`
- `src/interaction`
- `src/workflow`
- `src/decision`
- `src/creation`
- `src/review`
- `src/memory`
- `src/retrieval`
- `src/presentation`

以及最小工程支撑：

- `src/main` 或等价 CLI 入口
- `projects/`
- `templates/`
- `tests/`
- `docs/` 或当前 `reports/` 文档入口

## 3. 第一版优先实现的模块

### 3.1 `foundation`

第一批先落：

- `project_locator`
- `config`
- `io`
- `logging`
- `llm_client`
- `agent_runtime`

说明：

- `llm_client` 只负责统一模型调用
- `agent_runtime` 负责业务动作内部的模型执行组织

### 3.2 `interaction`

第一批先落：

- CLI 入口
- 命令注册

先支持这些命令：

- `init`
- `write`
- `resume`

其他命令先留接口，不急着做深。

### 3.3 `workflow`

第一批先落：

- `init_flow`
- `write_flow`
- `resume_flow`
- `state_tracker`
- `context_assembler`

说明：

- `workflow` 是唯一流程控制中心
- 第一版先只打通这 3 条流程

### 3.4 `memory`

第一批先落：

- `project`
- `project_state`
- `workflow_task_state`
- `checkpoint_snapshot`

以及最小读写能力。

### 3.5 `creation`

第一批先落：

- `init_builder`
- `writer_engine`

说明：

- `writer_engine` 的最小实现也必须走：
  - `creation -> agent_runtime -> llm_client`
- 不能直接 `creation -> llm_client`

### 3.6 `review`

第一批先落：

- 统一 `review` 接口
- 最小 `report_builder`
- 最小 `gatekeeper`

第一版先不做完整六检察器，只保留可扩展接口。

### 3.7 `decision`

第一版先预留：

- `decision signal`
- `decision_record`
- `workflow -> decision` 接口位

说明：

- 第一版可以先做最小实现
- 但接口不能缺位

## 4. 第一版主链路

### 4.1 初始化链路

1. 用户执行 `init`
2. `interaction` 调 `workflow.init_flow`
3. `workflow` 调 `creation.init_builder`
4. `workflow` 调 `memory` 写入项目基础数据
5. 建立初始项目状态

### 4.2 写作链路

1. 用户执行 `write`
2. `interaction` 调 `workflow.write_flow`
3. `workflow.state_tracker` 建立任务状态
4. `workflow.context_assembler` 组装执行包
5. `workflow` 调 `creation.writer_engine`
6. `creation.writer_engine -> agent_runtime -> llm_client`
7. 返回草稿
8. `workflow` 调 `review`
9. 返回最小审查结果
10. `workflow` 调 `memory` 回写
11. 更新任务状态与项目状态

### 4.3 恢复链路

1. 用户执行 `resume`
2. `interaction` 调 `workflow.resume_flow`
3. 读取 `workflow_task_state`
4. 读取 `checkpoint_snapshot`
5. 返回当前可恢复状态

## 5. 第一版不急着做深的内容

这些先留接口，不在骨架阶段做深：

- 完整 `plan_flow`
- 完整 `query_flow`
- 完整 `review` 多检查器并行
- 完整 `decision` 问答策略
- 完整 `retrieval` 检索链
- `learn`
- Dashboard

原因：

- 第一版目标是先把主链路打通
- 不是把所有功能都写成半成品

## 6. 第一版硬约束

1. `workflow` 仍然是唯一流程控制中心。
2. 所有模型调用统一经过 `llm_client`。
3. 所有创作和审查动作必须通过 `agent_runtime` 组织调用。
4. `creation` 不能直连 `llm_client`。
5. `review` 对外保持统一接口。
6. `workflow_task_state` 只存步骤级进度。
7. `checkpoint_snapshot` 只存可恢复状态数据。
8. 第一版只追求最小可运行，不追求功能齐全。

## 7. 推荐实施顺序

1. 建项目目录和基础工程文件
2. 建 `foundation`
3. 建 CLI 入口
4. 建 `workflow` 空壳和 `state_tracker`
5. 建 `memory` 最小数据读写
6. 建 `agent_runtime -> llm_client` 最小调用链
7. 建 `creation.writer_engine`
8. 建 `review` 最小返回结构
9. 打通 `init -> write -> resume`

## 8. 一句话总结

第一版骨架不是“把所有模块都写一点”，而是“先做出一条以后不用推翻的最小主链路”。
