# 最小流程与运行

前端使用 Vue Flow，后台用 LangGraph 执行。当前提供开始、大模型、收敛、返回节点，页面只显示返回节点的数据，排查信息看后端日志。配置管理位于 workflow_config，执行位于 [workflow_runtime](../agent/app/modules/workflow_runtime/README.md)，具体节点位于同级 [workflow_nodes](../agent/app/modules/workflow_nodes/README.md)。串行示例见 [basic-chat.json](examples/basic-chat.json)，模型ID 1 需换成实际配置ID。

## 流程结构

定义顶层包含 start_node_id、return_node_id、nodes、edges。前两个字段明确指定开始与返回位置，例如：

```json
{
  "start_node_id": "start_1",
  "return_node_id": "return_1",
  "nodes": [
    {"id": "start_1", "type": "start", "config": {}},
    {"id": "return_1", "type": "return", "config": {}}
  ],
  "edges": [
    {"id": "edge_1", "source": "start_1", "target": "return_1"}
  ]
}
```

前端随画布增删自动更新这两个ID，未添加对应节点的草稿保存为 null，运行时必须有值。后端直接读取ID，并在整理上游时检查引用与节点类型、唯一性是否一致，不再单独查找。全部末端仍从连线计算，不额外保存上游关系或末端列表。按当前格式读写，不自动补齐缺少这两个字段的旧定义。

| 类型 | config | 行为 |
|---|---|---|
| start | {} | 输出本次输入的 text；user_id 暂存在运行状态中，界面提供测试输入和运行按钮 |
| llm | model_config_id、可选 prompt_config_id、data_transfer_mode | 接收上游上下文，公共模板组装用户消息，所选提示词作为可选系统消息 |
| merge | 可选 data_transfer_mode | 等待全部直接上游，合并各自允许传递的上下文，共同祖先按ID去重 |
| return | {} | 接收一个上游，只返回其最终业务结果；只能有一个，不能连接下游 |

节点包含 id、type、config，可选 name 自定义名称、position 保存坐标。名称允许为空或重复，不改变连线定位。连线包含 id、source、target，执行顺序由连线决定，不取决于节点数组顺序。节点目录由代码维护，不新建工具箱表。

LLM 的配置示例为 `{"model_config_id":1,"prompt_config_id":2,"data_transfer_mode":"accumulate"}`，两个ID按实际记录填写。提示词可省略或为 null，未选择时不添加系统消息；选中时从缓存读取正文原样作为系统提示词，不替换其中的变量文字。引用的提示词不存在时返回 HTTP 404，提示词正文不保存在流程定义中。

## 数据传递方式

LLM 和收敛节点可选择 config.data_transfer_mode，省略时默认 accumulate：

- accumulate（累计传递）：保留收到的上游数据，再加入当前处理结果。
- result_only（仅当前结果）：只向下游传递本节点结果，不改变本节点已经收到的输入。

例如 `a → b → d`，默认 d 收到 a、b 的数据；b 选择 result_only 后，d 只收到 b。这个规则指本次流程的上游上下文，不涉及再次请求时的对话历史。运行记录仍保存全部节点输出，传递范围只沿实际连线确定，无关分支不自动进入上下文。

公共 NodeContext.results 按节点ID保存传递内容，NodeOutput.value 保存当前结果、context 保存给下游的数据。LLM 的内部 LlmNodeOutput.message 另存原始模型回复，默认业务结果仍是正文；返回节点只取上游 value，不返回完整模型对象或累计记录。

文字转换由节点公共函数完成，消息组装使用 AI 层的 ChatPromptTemplate。系统消息是选中的提示词原文，用户消息统一为“以下是本次流程传入的数据：”加上下文 JSON；提示词中的花括号不会被当作模板变量。表结构不变，传递方式保存在现有流程文本中。

每个可运行的流程必须恰好有一个 start 和一个 return 节点。前端禁用这两类节点的重复添加和拖拽，删除后可重新添加；return 只有输入圆点，不能连接下游。后端准备节点时确认开始、返回唯一且与指定ID一致，并检查返回节点只有一个上游且没有下游。配置保存接口仍按原文保存，不自动添加或迁移节点。

大模型和返回节点都接一个上游，多路输入先接收敛节点。全部业务末端自动连接框架 END，其中只有返回节点的数据作为响应，其他分支可以独立结束。返回节点不等于框架 END，也不会让其他分支转到后台；当前等待所有分支完成，未处理的分支异常仍影响请求。每次请求有独立状态，不保存上下文记忆。后台队列、循环、判断和工具能力后续再做。

固定并行分支可以这样连接：

```text
       ┌→ 大模型A ─┐
开始 ──┤          ├→ 收敛 → 大模型C → 返回
       └→ 大模型B ─┘
```

收敛节点形如 `{"id":"merge_1","type":"merge","config":{"data_transfer_mode":"accumulate"}}`，将两条上游连线的 target 都指向 merge_1 即可。框架通过列表形式 add_edge 等待全部上游，即使分支长度不同也不会提前执行收敛。默认合并为 `{"start_1":"问题","llm_a":"回答A","llm_b":"回答B"}`，共同祖先 start_1 只保留一份，累计模式不再嵌套一份收敛快照。选择 result_only 后，以 merge_1 为键传递收集到的对象。这只适用于固定并行分支，条件分支的汇合规则以后单独处理。

## 页面使用

1. 新增流程，自带开始和返回节点；拖入大模型，按“开始 → 大模型 → 返回”连线，选择模型和可选提示词。也可直接连接“开始 → 返回”，原样返回输入。
2. 选中节点可在右侧改名；LLM、收敛可选择数据传递方式；开始节点填写本次测试文字，可选填用户ID。
3. 点击开始旁的 ▶ 或右侧运行按钮，页面自动保存画布，再执行并展示最终数据或错误。

需要合并返回时，从开始节点分出多条连线，各分支连接收敛节点，再连接返回节点；收敛默认累计传递，也可以继续连接大模型。无需返回的支路可以独立结束，仍参与本次同步执行。

全屏画布的工具箱、配置区可收起。测试文字、用户ID和结果只在页面内存中，刷新或离开后清除。打印节点、每步数据面板和 debug 查询参数已移除。

## HTTP 与日志

`POST /api/workflow-configs/{id}/run`，请求体：

```json
{"text": "你好", "user_id": "user_001"}
```

成功响应：

```json
{"code": 0, "message": "成功", "data": {"payload": "模型生成的回答"}}
```

请求体固定使用 text 与可选 user_id；user_id 可省略或为 null，由 WorkflowInput 对象承载，FastAPI 仅做基础字段解析。开始节点原样输出 text，用户ID留在 state.inputs.user_id 中供后续记忆等节点读取，不自动加入模型问题，不增加旧字段兼容。输入和结果不写回流程配置。

响应 payload 可以是文字、对象或列表；对象直接作为 JSON 数据返回。失败沿用统一错误结构。默认 INFO 日志关联请求、流程和节点，排查时启动 `uv run python -m uvicorn main:app --reload --log-level debug`，额外查看输入输出正文，模型配置和 Key 不输出。配置读取完成即结束数据库事务，再等待模型。

## 对象与保存

固定结构使用带类型和中文字段说明的 dataclass：workflow_nodes/base/data/ 按对象维护节点定义、输入和状态，workflow_runtime/data/ 按对象维护流程连线、流程定义和最终结果，均为一类一文件。JSON 只在边界读取和序列化，动态业务内容保留 Any。workflow_definition 仍为普通文本，配置保存接口不解析或改写内容，表结构不变。

流程加载直接返回 WorkflowDefinition，节点创建时按模型ID读取统一进程内缓存，命中直接返回实体，未命中再用短会话查库。模型调用前查询会话已经关闭，不再为每次流程运行收集模型ID和组装模型 Map；配置增删改提交后使对应缓存失效。流程定义本身仍每次从数据库读取。

workflow_runtime/executor.py 负责准备节点和选择返回数据；StateGraph、连线、编译和执行集中在 [ai/langgraph](../agent/app/infrastructure/ai/langgraph/README.md)。模型创建集中在同级 ai/langchain，沿用现有模型实体和输入输出，不增加框架配置转换层。

节点配置、连线、坐标和扩展字段按当前定义直接读写。无法解析的原文保留供修正，不用空图覆盖。
