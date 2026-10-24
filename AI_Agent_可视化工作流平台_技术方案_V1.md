# AI Agent 可视化工作流平台——技术方案 V1.0

> 状态：技术选型与分阶段实施基线（尚未开始实现）  
> 目标：一年内边学边做，形成可演示、可扩展的工程项目，并积累 Python AI 平台开发经验。

## 1. 项目定位

开发一套**轻量级、可扩展、可视化拖拽编排的 AI 工作流平台**，优先服务医院护士与患者的业务信息查询场景。

- 第一版以**工作流引擎**为核心，而不是自主 Agent。
- 通过预先配置的流程完成意图识别、条件判断、业务接口查询、并行汇总和回答生成。
- 每个 LLM 节点可独立选择模型与推理参数。
- 后续扩展 RAG 知识节点、数据库元数据检索、安全查询、Agent 与 MCP。
- 坚持**循序渐进、模块化单体、接口解耦、可扩展**，不为未来功能过早引入复杂基础设施。

## 2. 技术选型

| 层次 | 技术 | 用途 |
|---|---|---|
| 前端 | Vue 3 + TypeScript + Vue Flow + Element Plus | 拖拽画布、节点配置、调试界面 |
| 后端 | Python 3.12+ + FastAPI | REST API、SSE、业务编排服务 |
| 校验 | Pydantic v2 | API DTO、工作流 DSL 与节点配置校验 |
| 工作流 | LangGraph 1.x | 图执行、状态传递、分支、并行、循环、子图 |
| 模型适配 | LangChain 1.x | LLM 调用、消息和模型供应商适配 |
| 模型服务 | Ollama + OpenAI-compatible API | 本地 Gemma/Qwen 与兼容接口模型 |
| ORM | SQLAlchemy 2.x | ORM 实体映射、表达式查询，尽量不手写 SQL |
| 数据迁移 | Alembic | 数据库结构版本管理 |
| 数据库 | PostgreSQL | 工作流、模型配置、执行记录等 |
| 测试 | pytest | 单元测试、集成测试、工作流测试 |
| 部署 | Docker Compose | 本地与单机部署 |
| 后续扩展 | pgvector、Embedding、Reranker、MCP、Redis、Langfuse、OpenTelemetry | RAG、工具生态、性能与观测 |

**选型原则：** Python/FastAPI/SQLAlchemy/PostgreSQL 作为长期工程基础；LangGraph 是当前工作流执行实现，但以自有 DSL 隔离框架依赖。框架流行度与招聘需求可能变化，不承诺任何技术永远主流。

## 3. 总体架构

```text
Web（Vue 3 + Vue Flow） / Android（后续）
                    │
               REST / SSE
                    │
                 FastAPI
                    │
       ┌────────────┴────────────┐
       │                         │
  业务应用层                 工作流核心层
  - 模型管理                - Workflow DSL
  - 流程管理                - Validator
  - 运行管理                - Node Registry
  - 调试与日志              - Graph Compiler
                            - Node Executors
                            - State / Context
       │                         │
       └────────────┬────────────┘
                    │
                 LangGraph
                    │
         ┌──────────┼───────────┐
         │          │           │
      LLM 节点   HTTP 节点   控制/变量节点
         │          │
   Ollama/云模型   Java 医院业务 API
                    │
            HIS / LIS / 护理系统

数据持久化：Repository → SQLAlchemy ORM → PostgreSQL
```

- **Vue Flow** 负责画布和交互，不直接定义运行时语义。
- **Workflow DSL** 是稳定的、带版本号的 JSON 协议；包含节点、端口、连线、配置、变量引用。
- **Validator** 校验节点配置、连线、变量类型、分支和循环合法性。
- **Compiler** 将 DSL 转换为 LangGraph；不把 LangGraph 内部对象直接持久化为业务协议。
- **Node Registry / Executors** 按节点类型注册执行器，便于以后添加 RAG、MCP、Agent 节点。
- **Model Registry / Provider** 统一管理模型连接，LLM 节点通过 `model_id` 选择模型。
- **Repository** 封装数据库操作，业务 Service 不直接拼 SQL。

## 4. 第一版功能范围

### 4.1 可视化工作流

- 拖拽添加节点、连接端口、删除、复制、缩放、移动。
- 节点配置面板、变量引用、工作流保存/加载。
- 工作流 JSON 校验、运行、停止、查看节点输入输出及错误。
- 基础执行日志、耗时与 LLM Token 统计；SSE 展示运行进度。

### 4.2 节点类型

| 节点 | 能力 | 开发顺序 |
|---|---|---|
| Start / End | 输入与最终输出 | 首先 |
| LLM | 选择模型、Prompt、Temperature、Token 上限、结构化输出 | 首先 |
| HTTP | 调用已授权业务接口、参数映射、超时与错误处理 | 第二步 |
| Variable / Transform | 字段提取、赋值、转换 | 第二步 |
| Condition / Switch | IF/ELSE、多路条件分支 | 第三步 |
| Parallel / Join | 多条路径并行、结果汇总 | 第三步 |
| Loop / ForEach | 固定次数、条件循环、集合遍历 | 第四步 |
| Subflow | 复用其他工作流 | 第四步 |

**注意：** 上表是 V1 的目标能力，不代表首次提交即全部实现。每种控制流能力均需独立测试。Join 只等待实际激活的分支；并行写入共享状态须明确合并策略；循环须有最大次数、超时与并发限制。

### 4.3 多模型配置

- 全局配置 Provider、Base URL、模型标识、密钥引用、默认参数与启用状态。
- 每个 LLM 节点保存 `model_id`，可覆盖 Temperature、输出 Token、超时和 Prompt。
- 密钥存服务端安全配置，不随工作流 JSON 下发到前端。
- 节点输出可通过 Pydantic/JSON Schema 校验；失败时提供明确错误和受限重试。

## 5. Python 后端开发规范

采用熟悉的分层结构：

```text
Router（API） → Service → Repository → SQLAlchemy ORM → PostgreSQL
                         │
                    Workflow Engine
```

- SQLAlchemy 2.x Declarative ORM + `select().where()`、`update()` 等表达式 API。
- **原则上不手写 SQL、不拼接 SQL 字符串**；必要的复杂查询先评估 ORM 表达式。
- Repository 统一封装查询、分页、事务边界和通用条件。
- Alembic 管理迁移；Pydantic DTO 与 ORM Entity 分离。
- 通用基类可提供 `id`、`created_at`、`updated_at`；逻辑删除按表需求选择。
- 保持模块化单体，不提前拆微服务或引入 Kafka、Kubernetes。

## 6. 基础数据模型（建议）

| 对象 | 用途 |
|---|---|
| `model_provider` / `model_definition` | 模型连接及可选模型 |
| `workflow_definition` | 工作流元数据、DSL JSON、版本 |
| `workflow_execution` | 一次运行的状态、开始结束时间、错误 |
| `workflow_node_execution` | 节点执行输入输出、耗时、错误、模型使用信息 |

后续按需添加知识库、文档、向量索引、Agent、会话与长期记忆表。工作流发布版本和执行快照应关联，避免编辑流程影响正在运行的实例。

## 7. 医院业务查询示例

```text
Start：用户提出问题
  ↓
LLM：意图识别 / 参数提取（本地 Gemma）
  ↓
Condition：检验报告 / 住院费用 / 其他
  ├─ 检验报告 → HTTP：调用 LIS 查询接口
  ├─ 住院费用 → HTTP：调用 HIS 查询接口
  └─ 其他 → 返回不支持或人工处理提示
  ↓
LLM：根据真实查询结果生成易懂回答（可使用不同模型）
  ↓
End
```

这里是**条件择一路由**，不是并行。另一个独立示例可以让多个 HTTP 查询同时执行，再通过 Join 汇总。不得把未执行的条件分支误当成必须等待的并行分支。

## 8. 后续 RAG 与数据库智能查询

目标：把**表结构、字段含义、API 文档、业务规则、查询模板**整理成可检索知识，提供知识检索节点。

```text
用户问题
  ↓
RAG：检索相关表/字段/接口说明
  ↓
LLM：生成受约束的查询计划
  ↓
安全查询节点：验证身份、权限、参数、允许的操作
  ↓
调用已审核的业务 API / 查询模板
  ↓
返回真实数据并组织回答
```

**重要边界：** RAG 检索的是元数据和文档，**不是实时数据库查询本身**。医疗场景优先调用已审核的只读业务 API，不允许 LLM 任意生成 SQL 并直接访问生产数据库。未来如加入 Text-to-SQL，必须有白名单、只读权限、租户与患者级数据隔离、限行、超时、审计等防护。模型不能绕过业务系统授权，也不能编造检验结果或医嘱。

## 9. 分阶段实施路线

1. **基础骨架：** FastAPI、SQLAlchemy、Alembic、PostgreSQL、Vue 3；模型配置和流程保存。
2. **最小闭环：** Vue Flow 拖拽 `Start → LLM → End`；DSL 校验、编译、执行、结果展示。
3. **业务查询：** HTTP、变量映射、异常处理、医院模拟接口。
4. **流程控制：** 条件、多路分支、并行、Join、循环、ForEach、子流程；逐项增加测试。
5. **可用性增强：** 流程版本、SSE 调试、运行日志、超时重试、执行恢复。
6. **知识扩展：** RAG、元数据知识库、受控数据库查询节点。
7. **Agent 扩展：** MCP、Agent 节点、长期记忆、更多模型供应商。

## 10. 第一阶段验收标准

- 能新增/编辑模型配置，并测试本地 Ollama 模型连接。
- 能在浏览器拖拽并连接 Start、LLM、End 三类节点。
- 能保存、重新加载带版本号的工作流 DSL JSON。
- 能按节点指定模型、Prompt 和输入变量并执行。
- 能看到最终输出、节点耗时、错误信息；异常时不假装执行成功。
- ORM 完成工作流及模型配置的增删改查，业务代码不手写 SQL。
- 具备最小自动化测试，方便下一阶段添加新节点而不破坏已有能力。

---

**最终架构基线：** `Vue Flow → 自定义 Workflow DSL → LangGraph → LLM / HTTP / 控制流节点 → 医院业务 API`；管理数据使用 `FastAPI → Service → Repository → SQLAlchemy → PostgreSQL`。

**实施策略：** 先跑通最小闭环，再按节点类型逐个扩展；稳定协议与扩展接口，避免一次性开发完整 Dify。
