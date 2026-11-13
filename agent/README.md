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

写接口直接接收 JSON，提交哪些字段就更新哪些字段，复用公共事务、错误处理和返回结构。LLM 节点通过可选 prompt_config_id 选择提示词，由 factory 调用 get_prompt_config 按需读取完整实体；未命中才用短会话查库，增删改提交成功后清除对应缓存。所选提示词按节点变量来源渲染后作为系统消息，公共 LangChain 模板把上游上下文填入用户消息；未选提示词时只生成用户消息。管理列表和详情仍直接查库，接口和缓存规则见 [提示词配置包文档](app/modules/prompt_config/README.md)。


## 流程运行

app/workflow 集中维护流程运行与节点，配置 CRUD 留在 app/modules/workflow_config，框架代码位于 app/infrastructure/ai。

```text
app/workflow/
├─ data/              按 definition、execution、task、io 分组，一类一文件
├─ runtime/           HTTP 入口、配置加载、流程与任务执行
└─ nodes/
   ├─ base/          节点基类和公共处理
   ├─ node/          basic 放基础节点，llm 放模型节点与专用数据
   └─ factory.py     选择类型，准备配置资源
```

POST /api/workflow-configs/{id}/run 接收 `{"text":"你好","user_id":"user_001"}`，user_id 可省略，返回 data.payload，允许文字、对象或列表。当前画布支持开始、大模型、意图分析、收敛、返回节点，以及固定串行和并行分支；用“开始 → 意图分析 → 返回”可查看任务列表。

内部 run_task 使用独立状态复用节点组，按任务ID保存最终结果，保留原问题与用户ID；自动分发尚未接入画布。完整运行步骤、节点说明、输入范围和任务边界统一维护在 [流程文档](app/workflow/README.md)，保存格式见 [流程协议](../docs/workflow-definition.md)。

默认 INFO 日志关联请求、流程、任务和节点；排查时使用 `uv run python -m uvicorn main:app --reload --log-level debug` 查看输入输出。模型配置与 Key 不输出，运行数据不写回配置。

## 代码阅读入口

| 文档 | 内容 |
|---|---|
| [流程运行与节点](app/workflow/README.md) | 建议先读 BaseNode，再读具体节点和 executor |
| [AI 框架](app/infrastructure/ai/README.md) | LangGraph 的注册、连线、编译执行，以及 LangChain 模型调用 |
| [公共能力](app/core/README.md) | 环境配置、请求日志、异常和统一返回 |
| [数据库能力](app/infrastructure/database/README.md) | 连接池、会话、ORM 与事务 |
| [模型配置](app/modules/model_config/README.md) | CRUD、Key 与缓存 |
| [提示词配置](app/modules/prompt_config/README.md) | 名称、正文与缓存 |
| [流程配置](app/modules/workflow_config/README.md) | 定义文本与 CRUD |
| [调试台](app/modules/playground/README.md) | 单轮问答 |
| [Python 学习指南](Python学习指南.md) | 基本语法及 Spring 对照 |
| [协作规则](AGENTS.md) | 命名、注释、日志和文档维护要求 |

项目使用 Python 命名空间包，不放空的 __init__.py；从当前后端目录启动，原有命令保持有效。主要功能入口维护一份 README，子目录用代码注释说明，不再逐层复制文档。
