# Agent 后端

Python 3.12+ + FastAPI + Uvicorn，使用 uv 管理依赖。

在本目录执行。首次使用时复制 `.env.example` 为 `.env` 并填写 PostgreSQL 连接配置；本机已经配置的 `.env` 无需覆盖。

```powershell
uv sync --locked
uv run python -m uvicorn main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看接口文档，启动命令保持不变。

## 模型配置

先在目标数据库执行仓库中的 `sql/pgsql.sql`，应用不会自动建表。当前后端使用 PostgreSQL；`sql/mysql.sql` 保留为 MySQL 5.7+ 初始化脚本。

模型接口、请求示例、分页和 Key 修改规则见 [模型配置包文档](app/modules/model_config/README.md)。本阶段仅保存配置，尚未实现模型连接或调用。

数据库连接、ORM 公共能力放在 `app/infrastructure/database`，模型业务放在 `app/modules/model_config`。增删改查使用 SQLAlchemy ORM，事务由 Service 提交或回滚。按当前要求未添加测试脚本。

## 代码阅读入口

| 文档 | 内容 |
|---|---|
| [Python 学习指南](Python学习指南.md) | `_` 和 `__` 的含义 |
| [公共能力](app/core/README.md) | 配置、日志、公共异常和统一返回结构 |
| [数据库公共能力](app/infrastructure/database/README.md) | 连接池、会话、ORM 公共字段和事务 |
| [模型配置管理](app/modules/model_config/README.md) | 接口、数据结构、业务流程和数据库操作 |
| [后端协作规则](AGENTS.md) | 后续中文注释和包文档维护约定 |

各代码文件中已补充中文说明。项目使用 Python 命名空间包，不放空的 `__init__.py`；仍从当前后端根目录使用 `uvicorn main:app --reload` 启动。
