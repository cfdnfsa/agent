# Agent 后端

Python 3.12+ + FastAPI + Uvicorn，使用 uv 管理依赖。

当前是个人使用的极简版本：配置接口直接接收 JSON 并交给数据库实体，不维护重复 DTO，不加必填、格式、长度、枚举或范围等业务校验。输入不自动去空格，数据库既有约束和框架/SDK 基础要求仍生效。

在本目录执行。首次使用时复制 `.env.example` 为 `.env` 并填写 PostgreSQL 连接配置；本机已经配置的 `.env` 无需覆盖。

```powershell
uv sync --locked
uv run python -m uvicorn main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看接口文档，启动命令保持不变。

## 模型配置

先在目标数据库执行仓库中的 `sql/pgsql.sql`，应用不会自动建表。当前后端使用 PostgreSQL；`sql/mysql.sql` 保留为 MySQL 5.7+ 初始化脚本。

模型接口、请求示例、分页、Key 修改规则和真实模型测试见 [模型配置包文档](app/modules/model_config/README.md)。保存配置后可通过 `POST /api/model-configs/{id}/test` 验证文本调用，通过 `POST /api/playground/chat` 进行无上下文的单轮问答。

数据库连接、ORM 公共能力放在 `app/infrastructure/database`，模型业务放在 `app/modules/model_config`。增删改查使用 SQLAlchemy ORM；Service 写操作通过数据库公共包的 `@transactional` 统一提交或回滚，模型调用保留查询阶段的局部事务。按当前要求未添加测试脚本。

## 代码阅读入口

| 文档 | 内容 |
|---|---|
| [Python 学习指南](Python学习指南.md) | 命名、self、类型标注、依赖注入、数据库会话和 `_` / `__` |
| [公共能力](app/core/README.md) | 配置、日志、公共异常和统一返回结构 |
| [数据库公共能力](app/infrastructure/database/README.md) | 连接池、会话、ORM 公共字段和事务 |
| [模型配置管理](app/modules/model_config/README.md) | 接口、数据结构、业务流程和数据库操作 |
| [模型调用公共能力](app/infrastructure/llm/README.md) | LangChain 模型集成、实体传参、基础地址和错误处理 |
| [调试台](app/modules/playground/README.md) | 选择模型进行单轮问答，不保存聊天记录 |
| [后端协作规则](AGENTS.md) | 后续中文注释和包文档维护约定 |

各代码文件中已补充中文说明。项目使用 Python 命名空间包，不放空的 `__init__.py`；仍从当前后端根目录使用 `uvicorn main:app --reload` 启动。

维护时优先采用直白的普通函数和现有分层，辅助方法默认不加前导 `_`。具体要求记录在 `AGENTS.md`；`model_client.py` 通过数据库实体创建 LangChain 模型，URL 原样传给 SDK；模型测试和问答在各自 Service 中直接调用框架的 invoke。模型异常暂时沿用公共错误处理，不单独分类。
