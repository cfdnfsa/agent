"""流程运行服务：加载配置、执行流程和记录运行日志。"""

from time import perf_counter

from sqlalchemy.orm import Session

from app.core.app_logging import logger, request_id_context
from app.modules.workflow_nodes.base.data.workflow_input import WorkflowInput
from app.modules.workflow_runtime.config_loader import load_runtime_config
from app.modules.workflow_runtime.data.workflow_result import WorkflowResult
from app.modules.workflow_runtime.executor import run_workflow


class WorkflowRuntimeService:
    """负责流程运行，配置的新增、修改和删除由 workflow_config 模块维护。"""

    # ---------- 初始化流程运行服务
    def __init__(self, db_session: Session):
        """db_session 来自当前请求，仅交给加载器读取运行配置。"""
        self.db_session = db_session

    # ---------- 运行已保存的流程
    def run(self, workflow_id: int, workflow_input: WorkflowInput) -> WorkflowResult:
        """加载配置后运行数据流，前端只接收最终结果，排查信息留在后端日志中。

        Args:
            workflow_id: 已保存流程的主键。
            workflow_input: 本次输入对象，通过 .payload 查看实际业务数据。

        Returns:
            最终业务数据；异常继续交给公共异常处理。
        """
        runtime_config = load_runtime_config(self.db_session, workflow_id)
        started_at = perf_counter()

        logger.info("请求ID=%s 操作=运行流程开始 流程ID=%s", request_id_context.get(), workflow_id)

        try:
            result = run_workflow(runtime_config, workflow_input)
        except Exception:

            logger.error("请求ID=%s 操作=运行流程失败 流程ID=%s", request_id_context.get(), workflow_id, exc_info=True)

            raise

        logger.info("请求ID=%s 操作=运行流程成功 流程ID=%s 耗时=%.0f毫秒", request_id_context.get(), workflow_id, (perf_counter() - started_at) * 1000)

        return result
