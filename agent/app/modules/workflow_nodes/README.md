# 流程节点

本包与 workflow_config、workflow_runtime 同级，负责“每种节点具体做什么”。运行模块负责加载流程和准备节点，ai/langgraph 引擎负责框架构建和执行；本包不反向导入运行模块。factory 创建大模型节点时通过统一缓存入口取得配置，未命中查询也在准备阶段结束；节点的 run、execute 不查库，也不调用后续节点。

按职责分为 [base](base/README.md)（公共能力和数据）与 [node](node/README.md)（具体节点实现），factory.py 留在外层作为创建入口。依赖方向为 node → base，factory → node、base；base 不反向引用具体节点。

## 文件入口

| 文件 | 职责 |
|---|---|
| base/base_node.py | BaseNode.run 按输入范围读取数据、调用 execute、记录日志、保存 NodeOutput |
| base/text.py | 公共文字转换，文字原样保留，对象和列表转为 JSON 文字 |
| node/start_node.py | StartNode 读取 inputs.text，原样交给下游；user_id 留在运行状态中 |
| node/llm_node.py | LlmNode 从 resources 读取模型和可选提示词，调用 LangChain invoke |
| node/data/llm_node_resources.py | LlmNodeResources 集中保存大模型节点需要的配置实体 |
| node/data/llm_node_output.py | LlmNodeOutput 保存正文与完整模型消息，继承公共 NodeOutput |
| node/merge_node.py | MergeNode 等待全部直接上游，按输入范围收集结果 |
| node/return_node.py | ReturnNode 只取一个上游的 value，作为唯一接口返回 |
| factory.py | create_node 选择类型，create_llm_node 组装大模型节点，load_model_config、load_prompt_config 分别读取配置 |
| base/data/ | 节点定义、节点配置、本次输入和图状态，一个对象一个文件，供节点与运行模块共用 |

建议先读 base/base_node.py，了解 `run → read_input → execute → 提交输出`，再读 node 下的具体节点，最后看 factory.py。LangGraph 调用 node.run(state)，子类实现自己的 read_input、execute；公共 run 不需要在各节点重复编写。

factory.py 内按小方法分工：`create_node → create_llm_node → load_model_config / load_prompt_config`。类型分支不堆积配置读取逻辑，读取方法通过原有缓存取得实体；模型必需，提示词可选，错误行为保持一致。create_llm_node 将实体放入 LlmNodeResources，再创建 `LlmNode(definition, source_ids, resources)`；后续新增资源时扩展资源对象，构造参数保持稳定。当前这些普通函数放在同一文件，后续有实际扩展再拆文件。

## 数据与边界

- 大模型可直接连接多个上游，由 LangGraph 等待全部直接上游完成。统一结果保存在 WorkflowState，NodeContext.results 只是当前节点按配置选出的输入，公共文字函数按需转换成 JSON 文字。收敛节点用于把选中的结果整理成一个对象，不是多路连线的必经节点。
- config.input_scope 默认 all_upstream，读取全部上游依赖链；direct_upstream 仅读取直接上游。例如 a → b → d，d 选 direct_upstream 就只使用 b，后续节点仍可独立选择读取 a。运行模块提前计算 input_ids，执行时只按ID取值；无关分支不进入输入。
- LLM 的 config 可保存 prompt_config_id，省略或为 null 时不添加系统消息。选中后 factory 通过 get_prompt_config 读取实体，找不到返回 HTTP 404；提示词正文原样作为 SystemMessage。ai/langchain/prompt_builder.py 使用 ChatPromptTemplate，将上游 JSON 文字填入固定用户消息，不替换数据库提示词中的花括号，也不增加跨请求历史。每个节点独立选择提示词。
- NodeOutput.value 是当前业务结果，输出对象不保存下游上下文。LLM 的 LlmNodeOutput 另存原始模型 message，默认 value 仍是正文；message 不自动进入模型输入或响应。
- 收敛按自己的输入范围收集结果。例如默认分支收集为 `{"start_1":"问题","llm_a":"回答A","llm_b":"回答B"}`，选择直接上游后只收集 llm_a、llm_b。上游ID去重，但收敛本身也保存为一份独立结果；后续节点选择全部上游时会同时读取原节点结果与收敛结果。等待全部上游由 ai/langgraph 引擎负责。
- 每个流程恰好一个返回节点，它接收一个上游且没有下游，config 为空对象。其他分支也可独立结束，但接口只取返回节点的数据；本次图执行仍等待所有分支完成，不自动转为后台任务。
- 节点对象仅保存配置；WorkflowInput 固定为 text 和可选 user_id，通过 state.inputs.text、state.inputs.user_id 读取。用户ID暂时预留，不自动拼入模型输入，也不保存上下文记忆。WorkflowState 保存每次请求的输入与节点输出，节点ID沿用已保存定义，运行时不生成新ID。
- base/data/workflow_state.py 中的 merge_node_outputs 只合并状态存储增量，不负责等待。WorkflowState 的 TYPE_CHECKING 元信息声明仅帮助类型检查，实际状态字段仍为 inputs、node_outputs。
- 模型和提示词实体由 factory 通过各自缓存取得，放入 LlmNodeResources 后交给 LlmNode，直接保留实体引用；查询会话在执行图前关闭，不随节点保留。资源对象位于 node/data，只保存此类节点需要的资源；WorkflowState 继续保存每次运行的输入与输出。Key 仅供内部调用，不输出模型配置或提示词正文；节点输入输出正文只在 DEBUG 级别记录。缓存规则见 [模型配置](../model_config/README.md#模型配置缓存) 和 [提示词配置](../prompt_config/README.md#提示词配置缓存)。

以后新增节点，在 node 下添加对应文件并维护 factory.py 的类型分支；[workflow_runtime](../workflow_runtime/README.md) 组织运行和返回结果，[ai/langgraph](../../infrastructure/ai/langgraph/README.md) 集中处理图的构建与执行。大模型创建入口位于 ai/langchain/model_client.py。流程定义与示例见 [最小流程格式](../../../../docs/workflow-definition.md)。
