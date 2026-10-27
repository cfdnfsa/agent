"""应用配置入口：读取 .env 和环境变量，保留基础类型解析。"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """数据库连接配置，从环境变量或后端根目录的 .env 读取。"""

    # 这是 Pydantic 的读取规则，与业务中的 model_config 数据表无关。
    # 系统环境变量优先于 .env，部署时可以注入环境变量覆盖本地配置。
    model_config = SettingsConfigDict(
        # 根据当前文件定位 agent/.env，不受 PyCharm 工作目录设置的影响。
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        # .env 后续增加其他功能的配置时，这里只读取自己声明的字段。
        extra="ignore",
        # 配置错误不回显原始输入，避免错误日志泄露数据库密码。
        hide_input_in_errors=True,
    )

    # 字段自动对应 .env 中的同名大写变量，如 db_host 对应 DB_HOST。
    db_host: str = Field(description="数据库主机")
    # 未配置时使用 PostgreSQL 默认端口，连接是否成功由数据库驱动处理。
    db_port: int = Field(default=5432, description="数据库端口")
    db_name: str = Field(description="数据库名称")
    db_user: str = Field(description="数据库用户名")
    # SecretStr 只是在打印对象时隐藏内容，并不是加密；连接时才取出真实密码。
    db_password: SecretStr = Field(description="数据库密码，不输出到日志")

    # ---------- 初始化应用配置
    def __init__(self) -> None:
        """配置从环境读取，调用方无需传参；保留 BaseSettings 的读取和必填校验。"""
        # 显式声明无参入口，避免类型检查器将必填配置字段误判为必传构造参数。
        super().__init__()


# ---------- 读取并复用应用配置
@lru_cache
def get_settings() -> Settings:
    """复用配置对象，避免每次请求重复读取环境文件。"""
    # 第一次调用读取配置，后续直接使用缓存；修改连接配置后需重启服务。
    return Settings()
