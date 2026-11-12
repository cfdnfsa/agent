"""意图分析节点：调用模型拆分任务，使用框架解析为固定结构，不执行任务。"""

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompt_values import ChatPromptValue

from app.core.errors.exceptions import BusinessError
from app.infrastructure.ai.langchain.model_client import create_chat_model
from app.infrastructure.ai.langchain.prompt_builder import build_chat_prompt
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.base.prompt_variables import render_prompt_variables
from app.modules.workflow_nodes.base.text import convert_input_to_text
from app.modules.workflow_nodes.node.data.intent_analysis_result import IntentAnalysisResult
from app.modules.workflow_nodes.node.data.llm_node_output import LlmNodeOutput
from app.modules.workflow_nodes.node.data.llm_node_resources import LlmNodeResources


INTENT_ANALYSIS_INSTRUCTIONS = """你是意图分析助手，只分析用户需求并拆出待处理任务。
输入以节点ID组织，每个节点的值是用户问题或已有分析资料，不把节点ID当作用户需求。
任务类型固定为：
- database：需要查询用户相关的真实业务数据。
- knowledge：需要检索知识库中的说明、规则或参考资料。
- chat：无需查询外部数据的普通问答，或信息不足时需要向用户澄清的问题。
- unsupported：当前不支持的操作，包括新增、修改、删除业务数据。
一段需求可拆成多项任务，保留已给出的对象、时间和限制，不重复生成相同任务。
不要执行查询、生成SQL、编造结果或声称操作已经完成，不自行生成用户ID。
缺少必要信息时生成一项 chat 任务说明要澄清的问题，不猜测缺失条件。
只输出符合指定结构的 JSON 对象，包含 tasks 列表，每项包含 type 和 question。
"""


class IntentAnalysisNode(BaseNode):
    """职责独立的意图分析节点，复用已有模型、提示词资源和公共输入能力。

    Attributes:
        resources: factory 提前加载的模型与可选补充提示词，节点内不查库。
    """

    # ---------- 保存意图分析需要的模型与提示词
    def __init__(self, definition: WorkflowNode, source_ids: list[str], resources: LlmNodeResources):
        """接收配置资源，每次执行的输入和结果仍保存在本次流程状态中。

        Args:
            definition: 当前节点的定义，类型为 intent_analysis。
            source_ids: 当前节点全部直接上游ID，执行前由 LangGraph 等待它们完成。
            resources: 已加载的模型配置与可选补充说明。
        """
        super().__init__(definition, source_ids)
        self.resources = resources

    # ---------- 调用模型并解析任务列表
    def execute(self, node_input: NodeContext) -> LlmNodeOutput:
        """使用普通 invoke 和框架 JSON 解析，适用于未提供工具调用接口的模型。

        Args:
            node_input: 按当前节点 input_scope 选出的上游需求和资料。

        Returns:
            value 是 IntentAnalysisResult，message 保留原始模型回复，仅内部使用。
        """
        output_parser = PydanticOutputParser(pydantic_object=IntentAnalysisResult)
        model_input = self.build_model_input(node_input, output_parser.get_format_instructions())
        model = create_chat_model(self.resources.model_config)
        response = model.invoke(model_input)

        try:
            intent_result = output_parser.invoke(response)
        except OutputParserException:
            # 不附带含模型正文的原始解析异常，避免正文进入默认错误日志或接口响应。
            raise BusinessError("意图分析结果格式不正确，请检查模型或补充提示词") from None

        return LlmNodeOutput(value=intent_result, message=response)

    # ---------- 组装意图说明与输出结构要求
    def build_model_input(self, node_input: NodeContext, format_instructions: str) -> ChatPromptValue:
        """内置分类规则、可选业务补充和框架结构说明共同组成系统消息。

        Args:
            node_input: 当前节点选中的上游输入。
            format_instructions: 框架根据结果对象生成的 JSON 格式说明。

        Returns:
            可交给模型调用的消息；只替换补充正文中的变量，固定分类和框架格式说明保持原样。
        """
        prompt_parts = [INTENT_ANALYSIS_INSTRUCTIONS]
        if self.resources.prompt_config is not None:
            supplement = render_prompt_variables(
                self.resources.prompt_config.prompt_content, self.definition.config.prompt_variables, node_input,
            )
            prompt_parts.append(supplement)
        prompt_parts.append(format_instructions)
        system_prompt = "\n\n".join(prompt_parts)
        input_text = convert_input_to_text(node_input.results)
        return build_chat_prompt(input_text, system_prompt)
