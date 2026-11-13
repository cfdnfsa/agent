# AI Agent 工作流平台

一条保存的流程就是一个 Agent。HTTP 请求携带用户ID和一段需求，流程分析意图、执行所需任务并汇总返回。当前业务方向是只读查询，跨请求记忆后续再做；目标与计划维护在 [技术方案](AI_Agent_可视化工作流平台_技术方案_V1.md)。

## 工程与目录

web 和 agent 是两个独立工程，各自在自己的目录安装依赖、启动和使用 IDE 打开。

```text
web/                         Vue 3、TypeScript、Element Plus、Vue Flow
agent/                       Python 3.12+、FastAPI、SQLAlchemy
  app/core/                  配置、日志、异常和统一返回
  app/modules/               模型、提示词、流程配置管理及调试台
  app/workflow/              流程共用对象、运行组织和具体节点
  app/infrastructure/        数据库连接及 LangGraph、LangChain 接入
sql/                         PostgreSQL、MySQL 5.7+ 建表与初始化数据
docs/                        流程保存格式和示例
```

配置输入按原值提交与保存，数据库约束和框架基础要求仍生效。主要功能入口维护一份说明，子目录通过代码注释介绍；协作规则见 [后端](agent/AGENTS.md) 与 [前端](web/AGENTS.md)。

## 当前能力

- 模型、提示词、流程配置的基础增删改查；模型和提示词使用进程内按需缓存。
- 模型连接测试、无上下文的单轮问答；API Key 不回显。
- 全屏流程画布，支持开始、大模型、意图分析、收敛、返回节点，固定串行和并行连线。
- 节点独立选择直接或全部上游输入，提示词通过弹窗管理并点选变量；最终返回文字或 JSON，排查使用后端日志。
- 后端任务隔离运行入口：程序生成任务ID，每项任务独立保存状态，主图按任务ID汇总最终结果；当前尚未接入画布分发。

可先配置“开始 → 意图分析 → 返回”，确认实际离线模型的任务分类效果；示例见 [intent-analysis.json](docs/examples/intent-analysis.json)，模型ID按实际配置替换。下一步接任务分发，再逐步实现数据库只读查询和知识库检索。

## 启动与文档入口

| 文档 | 内容 |
|---|---|
| [后端启动](agent/README.md) | Python 依赖、环境配置和启动命令 |
| [前端启动与维护](web/README.md) | 页面、公共组件、接口和开发代理 |
| [流程运行与节点](agent/app/workflow/README.md) | runtime、nodes、data 的职责与任务隔离 |
| [AI 框架](agent/app/infrastructure/ai/README.md) | LangGraph 连线执行、LangChain 模型与消息 |
| [流程格式](docs/workflow-definition.md) | 画布定义、输入范围、提示词变量和 HTTP 协议 |
| [模型配置](agent/app/modules/model_config/README.md) | 字段、接口、Key 与缓存 |
| [提示词配置](agent/app/modules/prompt_config/README.md) | 接口、正文与缓存 |
| [流程配置](agent/app/modules/workflow_config/README.md) | 配置 CRUD 与文本定义 |
| [数据库 SQL](sql/README.md) | 建表和独立初始化数据 |
| [Python 学习指南](agent/Python学习指南.md) | 结合项目与 Spring 对照理解基本语法 |
| [目标与技术方案](AI_Agent_可视化工作流平台_技术方案_V1.md) | Agent 方向、当前边界和后续步骤 |

使用 PyCharm 打开本目录，可选择右上角 agent 运行配置启动后端；解释器为 agent/.venv。使用终端时分别进入后端或前端目录，按各自启动文档操作。
