"""模型配置的进程内缓存：命中直接返回实体，未命中再用短会话查询数据库。"""

from threading import Lock

from app.core.app_logging import logger, request_id_context
from app.infrastructure.database.db_connection import db_session_factory
from app.modules.model_config.entity import ModelConfig
from app.modules.model_config.repository import ModelConfigRepository


# 只保存完整配置实体，供内部模型调用只读使用；不保存 Session，也不作为接口响应。
model_config_cache: dict[int, ModelConfig] = {}
# 保护“读取、未命中加载、写入”和失效操作，避免并发加载把已失效的旧值放回缓存。
model_config_cache_lock = Lock()


# ---------- 优先从内存读取模型配置
def get_model_config(model_id: int) -> ModelConfig | None:
    """按ID返回完整配置，数据库也没有时返回 None，且不缓存空值。

    Args:
        model_id: 模型配置表主键，调用方从节点配置或请求中取得。

    Returns:
        包含 Key 的原模型实体，只在内部使用；配置不存在时返回 None。
    """
    with model_config_cache_lock:
        model_config = model_config_cache.get(model_id)
        if model_config is not None:

            logger.debug("请求ID=%s 操作=读取模型配置缓存 模型ID=%s 命中=True", request_id_context.get(), model_id)

            return model_config

        logger.debug("请求ID=%s 操作=读取模型配置缓存 模型ID=%s 命中=False", request_id_context.get(), model_id)

        # 只有未命中才创建查询会话；退出两个 with 后提交只读事务并关闭会话。
        with db_session_factory() as db_session:
            with db_session.begin():
                model_config = ModelConfigRepository(db_session).get_by_id(model_id, include_api_key=True)

        # expire_on_commit=False 保留已加载字段；缓存前已关闭会话，后续不触发隐式查库。
        if model_config is not None:
            model_config_cache[model_id] = model_config
        return model_config


# ---------- 清除指定模型配置的缓存
def invalidate_model_config(model_id: int) -> None:
    """写操作提交成功后调用，下次读取时重新查库；不修改已经交给运行中节点的实体。"""
    with model_config_cache_lock:
        model_config_cache.pop(model_id, None)

    logger.debug("请求ID=%s 操作=清除模型配置缓存 模型ID=%s", request_id_context.get(), model_id)

