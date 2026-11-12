# 具体节点的数据对象

本目录存放具体节点使用的数据对象，一个类一个文件；公共节点定义、输入和运行状态仍放在 base/data。

- llm_node_resources.py：LlmNodeResources 保存普通 LLM、意图分析共用的模型与可选提示词实体。factory 统一加载，具体节点只使用。
- llm_node_output.py：LlmNodeOutput 继承公共 NodeOutput，value 是正文或意图结果对象，message 是 LangChain 原始回复。节点按输入范围读取 value，原始消息不自动进入模型输入或接口响应。
- intent_task.py：IntentTask，包含 type 和 question，任务类型为 database、knowledge、chat、unsupported。
- intent_analysis_result.py：IntentAnalysisResult，包含 tasks 列表；直接保存在 NodeOutput.value，返回时由现有框架序列化为 JSON 对象。

意图的两个结果类使用 Pydantic BaseModel，以便 PydanticOutputParser 直接把 JSON 解析成对象，避免手写转换。只声明任务结构，不增加长度、空白处理等限制；其他资源和运行对象继续使用 dataclass。

资源对象只保存准备好的配置，不持有数据库会话。输出对象只属于本次请求，保存在 WorkflowState.node_outputs 中，不写回资源对象。完整调用关系见 [具体节点说明](../README.md)。
