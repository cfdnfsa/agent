"""提示词配置的进程内缓存：命中直接返回实体，未命中再用短会话查询数据库。"""

from threading import Lock

from app.core.app_logging import logger, request_id_context
from app.infrastructure.database.db_connection import db_session_factory
from app.modules.prompt_config.entity import PromptConfig
from app.modules.prompt_config.repository import PromptConfigRepository


# 以提示词ID保存完整实体，仅供内部只读使用，不保存数据库会话。
prompt_config_cache: dict[int, PromptConfig] = {}
# 加载和失效使用同一把锁，避免并发查询把已经清除的旧配置重新写回。
prompt_config_cache_lock = Lock()


# ---------- 优先从内存读取提示词配置
def get_prompt_config(prompt_id: int) -> PromptConfig | None:
    """按ID返回完整实体，未找到时返回 None，不缓存空值。

    Args:
        prompt_id: 提示词配置表主键，后续流程节点选择提示词时使用。

    Returns:
        包含名称和正文的原提示词实体，查询会话已关闭；不存在时为 None。
    """
    with prompt_config_cache_lock:
        prompt_config = prompt_config_cache.get(prompt_id)
        if prompt_config is not None:

            logger.debug("请求ID=%s 操作=读取提示词配置缓存 提示词ID=%s 命中=True", request_id_context.get(), prompt_id)

            return prompt_config

        logger.debug("请求ID=%s 操作=读取提示词配置缓存 提示词ID=%s 命中=False", request_id_context.get(), prompt_id)

        # 只有未命中才创建会话；查询事务结束并关闭会话后，再把实体放入缓存。
        with db_session_factory() as db_session:
            with db_session.begin():
                prompt_config = PromptConfigRepository(db_session).get_by_id(prompt_id)

        # expire_on_commit=False 保留已加载的正文，后续读取缓存不会隐式查库。
        if prompt_config is not None:
            prompt_config_cache[prompt_id] = prompt_config
        return prompt_config


# ---------- 清除指定提示词配置的缓存
def invalidate_prompt_config(prompt_id: int) -> None:
    """写操作提交成功后清除，下次读取再查库；已交给调用方的实体保持原样。"""
    with prompt_config_cache_lock:
        prompt_config_cache.pop(prompt_id, None)

    logger.debug("请求ID=%s 操作=清除提示词配置缓存 提示词ID=%s", request_id_context.get(), prompt_id)
