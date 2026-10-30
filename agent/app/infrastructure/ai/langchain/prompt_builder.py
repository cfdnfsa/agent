"""公共消息模板：使用 LangChain 组装节点提示词与已准备好的上游数据。"""

from langchain_core.messages import SystemMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


# ---------- 使用公共模板组装模型输入
def build_chat_prompt(context_text: str, system_prompt: str | None) -> ChatPromptValue:
    """只填充公共模板变量；数据库中的提示词正文作为完整消息原样使用。

    Args:
        context_text: 调用方已选好并转换成文字的上游上下文，不在这里读取流程状态。
        system_prompt: 节点选中的任务说明，未选择提示词时为 None。

    Returns:
        可以直接交给 model.invoke 的 LangChain 消息对象。
    """
    messages: list[SystemMessage | HumanMessagePromptTemplate] = []
    if system_prompt is not None:
        # 直接创建消息，正文中的 JSON 花括号不会被识别成模板变量。
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessagePromptTemplate.from_template("以下是本次流程传入的数据：\n{context}"))
    template = ChatPromptTemplate.from_messages(messages)
    return template.format_prompt(context=context_text)
