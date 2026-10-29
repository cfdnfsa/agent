# 流程节点

本包与 workflow_config、workflow_runtime 同级，负责“每种节点具体做什么”。运行模块负责加载流程和准备节点，ai/langgraph 引擎负责框架构建和执行；本包不反向导入运行模块。factory 创建大模型节点时通过统一缓存入口取得配置，未命中查询也在准备阶段结束；节点的 run、execute 不查库，也不调用后续节点。

按职责分为 [base](base/README.md)（公共能力和数据）与 [node](node/README.md)（具体节点实现），factory.py 留在外层作为创建入口。依赖方向为 node → base，factory → node、base；base 不反向引用具体节点。

## 文件入口

| 文件 | 职责 |
|---|---|
| base/base_node.py | BaseNode.run 统一读取输入、调用 execute、记录日志、提交当前节点输出 |
| node/start_node.py | StartNode 读取 inputs.text，原样交给下游；user_id 留在运行状态中 |
| node/llm_node.py | LlmNode 使用已加载的模型实体调用 LangChain invoke |
| node/merge_node.py | MergeNode 按上游节点ID收集全部结果，无额外配置 |
| node/return_node.py | ReturnNode 原样输出一个上游的数据，作为唯一接口返回 |
| factory.py | create_node 按 type 创建节点，大模型配置通过 model_config/cache.py 读取 |
| base/data/ | 节点定义、节点配置、本次输入和图状态，一个对象一个文件，供节点与运行模块共用 |

建议先读 base/base_node.py，了解 `run → read_input → execute → 提交输出`，再读 node 下的具体节点，最后看 factory.py。LangGraph 调用 node.run(state)，子类实现自己的 read_input、execute；公共 run 不需要在各节点重复编写。

## 数据与边界

- 普通处理节点接收一个上游，多路结果先连接收敛节点。文字直接交给模型，对象或列表转为 JSON 文字。
- 收敛输出形如 `{"llm_a":"回答A","llm_b":"回答B"}`。等待全部上游由 ai/langgraph 引擎的列表连线实现，收敛节点只收集数据。
- 每个流程恰好一个返回节点，它接收一个上游且没有下游，config 为空对象。其他分支也可独立结束，但接口只取返回节点的数据；本次图执行仍等待所有分支完成，不自动转为后台任务。
- 节点对象仅保存配置；WorkflowInput 固定为 text 和可选 user_id，通过 state.inputs.text、state.inputs.user_id 读取。用户ID暂时预留，不自动拼入模型输入，也不保存上下文记忆。WorkflowState 保存每次请求的输入与节点输出，节点ID沿用已保存定义，运行时不生成新ID。
- base/data/workflow_state.py 中的 merge_node_outputs 只合并状态存储增量，不负责等待。WorkflowState 的 TYPE_CHECKING 元信息声明仅帮助类型检查，实际状态字段仍为 inputs、node_outputs。
- 模型实体由 factory 通过共享缓存取得，再原样传入 LlmNode；查询会话在执行图前关闭，不随节点保留。Key 仅供内部调用，不输出模型配置；日志由 BaseNode 统一记录，正文只在 DEBUG 级别输出。缓存失效规则见 [模型配置](../model_config/README.md#模型配置缓存)。

以后新增节点，在 node 下添加对应文件并维护 factory.py 的类型分支；[workflow_runtime](../workflow_runtime/README.md) 组织运行和返回结果，[ai/langgraph](../../infrastructure/ai/langgraph/README.md) 集中处理图的构建与执行。大模型创建入口位于 ai/langchain/model_client.py。流程定义与示例见 [最小流程格式](../../../../docs/workflow-definition.md)。
