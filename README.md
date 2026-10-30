# AI Agent 工作流平台

仓库包含两个独立工程，各自在自己的目录中安装依赖、启动和使用 IDE 打开。

当前按个人使用的极简版本维护：配置输入原样保存，不增加业务字段校验、前端输入限制、重复 DTO 或无必要转换。数据库已有约束和框架/SDK 基础要求仍然生效。规则见 [后端规则](agent/AGENTS.md) 和 [前端规则](web/AGENTS.md)。

```text
web/    Vue 3 + TypeScript + Vite 前端
agent/  Python 3.12+ + FastAPI 后端
```

## 流程方向

目标是把一条保存的流程作为独立 Agent：HTTP 请求提供本次输入，后台执行并返回最终数据。前端使用 Vue Flow 编辑节点与连线，后端用 LangGraph 执行，模型调用复用 LangChain 集成。

后端分为 workflow_config（配置增删改查）、workflow_runtime（配置加载和执行）、workflow_nodes（具体节点能力）。运行模块复用配置模块的 Repository 并调用节点包，等待模型前结束数据库事务。固定结构使用有中文字段文档的对象，数据库定义仍保存为普通文本。

当前先做极简版本：

- 全屏画布，提供开始、大模型、收敛、返回节点，节点名称可以自定义。
- 每个流程只有一个开始节点，填写本次测试文字并点击 ▶ 运行；已有时禁止重复添加，后端运行前检查唯一入口。大模型只选择模型，直接处理上游数据。
- 固定并行分支可以连接收敛节点，由 LangGraph 等待全部上游，再按节点ID收集结果；无需额外配置。
- 每个流程只有一个返回节点，接收一个上游且没有下游，接口只返回它的数据；其他支路可以独立结束，当前仍等待所有支路完成。
- 去掉打印节点、步骤记录和前端调试面板，排查信息统一看后端日志；默认 INFO，临时用 --log-level debug 查看节点输入和输出。
- 运行前保存当前画布，本次输入固定为 text 与可选 user_id；开始节点输出文字，用户ID先留在运行状态中。输入和结果只在本次页面内存中，不写回流程定义；返回节点可输出文字或 JSON 数据。

workflow_nodes 按 base（基类和共用数据）、node（具体节点）分包，每种节点一个文件，外层 factory.py 创建节点；workflow_runtime 负责准备节点、识别入口末端和选择返回结果，data/ 按对象拆分文件。框架代码集中在 infrastructure/ai：langgraph 构建并执行流程图，langchain 创建模型。节点ID创建后保存，运行状态每次请求独立。

流程定义在 nodes、edges 之外明确保存 start_node_id、return_node_id，前端随节点增删更新，后端直接读取，并在整理节点和连线时检查引用。末端仍根据连线计算，数据库继续使用原文本字段。

模型配置统一通过 [进程内缓存](agent/app/modules/model_config/README.md#模型配置缓存) 读取：命中直接使用，未命中再查库；配置增删改提交成功后清除对应缓存。流程加载直接返回 WorkflowDefinition，不再打包模型 Map。

提示词配置通过 `/api/prompt-configs` 维护名称和正文，提供基础增删改查，名称允许重复，正文原样保存；流程节点选用提示词后续接入。

知识库、工具、MCP、Skill、判断、循环和流程定义缓存等后续按小步骤增加。


- [前端启动说明](web/README.md)
- [后端启动与 PyCharm 配置](agent/README.md)
- [流程配置接口与表结构](agent/app/modules/workflow_config/README.md)
- [提示词配置接口](agent/app/modules/prompt_config/README.md)
- [流程运行与日志](agent/app/modules/workflow_runtime/README.md)
- [流程节点与扩展入口](agent/app/modules/workflow_nodes/README.md)
- [AI 框架接入与执行](agent/app/infrastructure/ai/README.md)
- [最小流程格式与示例](docs/workflow-definition.md)
- [数据库初始化 SQL](sql/README.md)
- [流程方向](#流程方向)

使用 PyCharm 打开本目录后，可在右上角选择 `agent` 运行配置并启动后端；该配置使用 `agent/.venv` 中的解释器。
