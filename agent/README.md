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

数据库连接、ORM 公共能力放在 `app/infrastructure/database`，模型业务放在 `app/modules/model_config`。增删改查使用 SQLAlchemy ORM；Service 写操作通过数据库公共包的 `@transactional` 统一提交或回滚。模型配置通过统一进程内缓存读取，未命中才用短会话查询，调用模型前已关闭查询会话；配置写入提交成功后清除对应缓存。按当前要求未添加测试脚本。

## 流程配置

`app/modules/workflow_config` 提供流程名称和定义文本的基础增删改查，接口前缀为 `/api/workflow-configs`。流程表只有 ID、名称、定义三个字段，没有时间字段；列表只读取 ID 和名称，详情返回完整定义。定义内容按字符串原样保存，保存时不解析或校验；通过运行接口才解析和执行流程。

先在目标数据库执行 `sql/pgsql.sql` 中新增的流程建表部分，也可以执行完整初始化脚本；已有表不会重复创建。MySQL 5.7+ 的对应定义保存在 `sql/mysql.sql`，流程大文本分别使用 PostgreSQL TEXT、MySQL LONGTEXT。详见 [流程配置包文档](app/modules/workflow_config/README.md) 和仓库 [SQL 说明](../sql/README.md)。

公共 Base 只声明 id；模型配置、流程配置和提示词配置都不维护创建时间、更新时间，表结构以当前初始化脚本为准。

## 提示词配置

`app/modules/prompt_config` 提供提示词新增、分页列表、详情、修改和删除，接口前缀为 `/api/prompt-configs`。表中只有 id、prompt_name、prompt_content，名称允许重复，正文原样保存；列表只读取 ID 和名称，详情才读取正文。先执行 `sql/pgsql.sql` 中的 prompt_config 建表语句，应用启动不自动建表。

写接口直接接收 JSON，提交哪些字段就更新哪些字段，复用公共事务、错误处理和返回结构。LLM 节点通过可选 prompt_config_id 选择提示词，由 factory 调用 get_prompt_config 按需读取完整实体；未命中才用短会话查库，增删改提交成功后清除对应缓存。节点调用模型时以系统消息传入正文，上游内容作为用户消息，不进行变量替换；未选择时直接使用上游输入。管理列表和详情仍直接查库，接口和缓存规则见 [提示词配置包文档](app/modules/prompt_config/README.md)。

## 流程运行

`app/modules/workflow_runtime` 独立负责执行，配置管理留在 workflow_config。接口为 `POST /api/workflow-configs/{id}/run`，请求体 `{"text":"你好","user_id":"user_001"}`，user_id 可省略或为 null。FastAPI 直接解析为 WorkflowInput，内部通过 .text、.user_id 访问；开始节点仅输出文字，用户ID暂时保留在状态中。返回 `{"payload":"模型回答"}`，payload 也可以是对象或列表。提供开始、大模型、收敛、返回节点，全部末端自动结束，接口只返回返回节点的数据。

流程定义直接保存 start_node_id、return_node_id，由前端随节点增删维护；草稿缺少对应节点时为 null，运行时必须有值。后端整理上游时确认恰好有一个开始和一个返回节点且与指定ID一致，返回节点必须接收一个上游且没有下游，不符合时返回公共业务错误，不再单独查找这两个节点。引擎接收单个 start_node_id，业务末端仍可有多个。其他分支独立结束但结果不混入响应，当前仍同步等待全部分支；后台任务和队列后续再做。

config_loader.py 查询流程文本、结束事务，再解析并直接返回 WorkflowDefinition，Service 组织执行；executor 准备节点、入口末端和返回策略，框架构建与执行交给 [ai/langgraph/engine.py](app/infrastructure/ai/langgraph/engine.py)。同级 [workflow_nodes](app/modules/workflow_nodes/README.md) 包的 base 子包维护 BaseNode 和共用数据，node 子包维护 StartNode、LlmNode、MergeNode、ReturnNode，外层 factory.py 按配置创建节点，通过模型配置缓存取得大模型实体。公共 run 读取输入、调用 execute、记录日志并提交输出；LangGraph 负责调度和等待全部上游，收敛节点按上游ID收集结果，返回节点原样传递一个上游的数据。大模型接收一个上游，对象转为 JSON 文字后调用模型。阅读节点逻辑时先看 workflow_nodes/base/base_node.py，再看 node 下的具体实现。

节点定义、输入和状态集中在 [workflow_nodes/base/data/](app/modules/workflow_nodes/base/data/README.md)，流程连线、流程定义和最终结果在 [workflow_runtime/data/](app/modules/workflow_runtime/data/README.md)，每个对象一个文件；运行包依赖节点包，节点包不反向依赖。例如 workflow_definition.nodes、node.config.model_config_id、result.payload，均有类型和中文 Attributes 文档；数据库和 JSON 存储字段不变。当前支持固定并行分支收敛，条件分支、循环和记忆后续再做。

AI 框架接入集中在 [infrastructure/ai](app/infrastructure/ai/README.md)：langgraph 负责流程图构建和执行，langchain/model_client.py 负责模型创建，模型测试、调试台和大模型节点复用同一个入口。MCP、Skills、提示词、工具等实际接入时再建目录，对应的配置管理仍放 modules。

默认 INFO 日志关联请求ID、流程ID与节点ID。需要排查数据时启动 `uv run python -m uvicorn main:app --reload --log-level debug`，在后端控制台查看节点输入和输出；模型配置和 Key 不输出。详见 [运行包文档](app/modules/workflow_runtime/README.md) 和 [最小流程定义](../docs/workflow-definition.md)。

## 代码阅读入口

| 文档 | 内容 |
|---|---|
| [Python 学习指南](Python学习指南.md) | 命名、self、类型标注、依赖注入、数据库会话和 `_` / `__` |
| [公共能力](app/core/README.md) | 配置、日志、公共异常和统一返回结构 |
| [数据库公共能力](app/infrastructure/database/README.md) | 连接池、会话、ORM 公共字段和事务 |
| [模型配置管理](app/modules/model_config/README.md) | 接口、数据结构、业务流程和数据库操作 |
| [提示词配置管理](app/modules/prompt_config/README.md) | 名称与正文、基础增删改查、概要分页 |
| [流程配置管理](app/modules/workflow_config/README.md) | 三字段流程表、文本定义、分页及基础增删改查 |
| [流程运行](app/modules/workflow_runtime/README.md) | 运行接口、统一配置加载、LangGraph 执行与日志 |
| [流程节点](app/modules/workflow_nodes/README.md) | 节点基类、开始、大模型、收敛、返回与节点创建入口 |
| [AI 公共能力](app/infrastructure/ai/README.md) | AI 框架接入与业务模块之间的职责 |
| [LangGraph 图引擎](app/infrastructure/ai/langgraph/README.md) | 节点注册、连线、编译与执行 |
| [模型调用公共能力](app/infrastructure/ai/langchain/README.md) | LangChain 模型集成、实体传参、基础地址和错误处理 |
| [调试台](app/modules/playground/README.md) | 选择模型进行单轮问答，不保存聊天记录 |
| [后端协作规则](AGENTS.md) | 后续中文注释和包文档维护约定 |

各代码文件中已补充中文说明。项目使用 Python 命名空间包，不放空的 `__init__.py`；仍从当前后端根目录使用 `uvicorn main:app --reload` 启动。

维护时优先采用直白的普通函数和现有分层，辅助方法默认不加前导 `_`。条件表达式展开为普通多行 if / else，集合使用普通 for 循环构建，可读性优先于减少行数。具体要求记录在 `AGENTS.md`；`model_client.py` 通过数据库实体创建 LangChain 模型，URL 原样传给 SDK；模型测试和问答在各自 Service 中直接调用框架的 invoke。模型异常暂时沿用公共错误处理，不单独分类。
