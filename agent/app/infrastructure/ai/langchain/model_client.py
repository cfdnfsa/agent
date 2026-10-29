"""LangChain 模型创建入口：使用数据库实体创建模型，调用由 Service 或流程节点完成。"""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.errors.exceptions import BusinessError
from app.modules.model_config.entity import ModelConfig


# ---------- 根据接入方式创建模型
def create_chat_model(model_config: ModelConfig) -> BaseChatModel:
    """按配置的接入方式创建模型，不在这里发起请求。

    Args:
        model_config: 数据库查询出的完整实体，包含模型标识、地址、接入方式和 Key。

    Returns:
        可以直接调用 invoke 的 LangChain 模型对象；URL 原样交给对应 SDK。
    """
    if model_config.model_provider == "openai":
        return create_openai_model(model_config)
    if model_config.model_provider == "anthropic":
        return create_anthropic_model(model_config)
    if model_config.model_provider == "ollama":
        return create_ollama_model(model_config)
    if model_config.model_provider == "google_genai":
        return create_google_genai_model(model_config)
    raise BusinessError("当前接入方式没有对应的模型集成。")


# ---------- 创建 OpenAI 兼容模型
def create_openai_model(model_config: ModelConfig) -> ChatOpenAI:
    """使用实体中的模型标识、地址和 Key 创建 OpenAI 兼容模型。"""
    # 部分兼容服务不需要 Key；EMPTY 只是满足 SDK 的构造要求，不是实际密钥。
    return ChatOpenAI(
        model=model_config.model_code,
        base_url=model_config.model_base_url,
        api_key=SecretStr(model_config.model_api_key or "EMPTY"),
    )


# ---------- 创建 Anthropic 模型
def create_anthropic_model(model_config: ModelConfig) -> ChatAnthropic:
    """使用数据库实体创建 Anthropic 模型，返回可以直接 invoke 的对象。"""
    # SDK 的构造类型声明误将部分默认参数视为必填；用它提供的创建入口沿用默认值。
    return ChatAnthropic.model_validate({
        "model_name": model_config.model_code,
        "base_url": model_config.model_base_url,
        "api_key": SecretStr(model_config.model_api_key or "EMPTY"),
    })


# ---------- 创建 Ollama 模型
def create_ollama_model(model_config: ModelConfig) -> ChatOllama:
    """使用数据库实体创建 Ollama 模型；有 Key 时附加鉴权头。"""
    headers: dict[str, str] = {}
    if model_config.model_api_key:
        headers["Authorization"] = f"Bearer {model_config.model_api_key}"
    return ChatOllama(
        model=model_config.model_code,
        base_url=model_config.model_base_url,
        client_kwargs={"headers": headers},
    )


# ---------- 创建 Google Gemini 模型
def create_google_genai_model(model_config: ModelConfig) -> ChatGoogleGenerativeAI:
    """使用数据库实体创建 Google Gemini 模型，保留 API Key 鉴权方式。"""
    return ChatGoogleGenerativeAI(
        model=model_config.model_code,
        base_url=model_config.model_base_url,
        api_key=SecretStr(model_config.model_api_key or "EMPTY"),
        vertexai=False,
    )
