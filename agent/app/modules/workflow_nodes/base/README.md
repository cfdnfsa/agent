# 节点基础能力

- base_node.py：公共 run 执行入口，统一日志、按预先确定的 input_ids 读取输入、调用 execute、保存当前结果。
- text.py：公共 convert_input_to_text，文字原样保留，对象或列表转为保留中文的 JSON 文字。使用现有 Pydantic 序列化能力支持嵌套的意图结果对象，只有需要文字的节点调用。
- prompt_variables.py：按当前节点选择的来源替换命名变量；question 取本次问题，upstream 取当前输入范围，其他变量按绑定读取。普通 JSON 和双花括号保留，替换值不再递归处理，缺少来源明确报错。
- [data/](data/README.md)：一个对象一个文件，维护节点定义、配置、输入、状态、WorkflowTask、TaskResult，以及 NodeContext、NodeOutput；状态增量合并函数放在 workflow_state.py。

WorkflowState 统一保存全部节点结果。input_scope 默认 all_upstream，读取当前节点的全部上游；direct_upstream 仅读取连线直接指向本节点的结果，可以包含多个。运行模块提前准备 input_ids，执行时只按ID取值，不读取无关分支，也不删除或修改其他节点的结果。source_ids 仍表示直接上游，用于 LangGraph 连线并等待全部完成；LLM、收敛共用 read_input，开始和返回分别覆盖自身的读取方式。

本包供具体节点、运行模块和 ai/langgraph 引擎使用，不反向导入 node、factory、workflow_runtime 或图引擎。节点基类只保存配置，每次请求的数据放在 WorkflowState。

主流程与每项任务各有自己的 WorkflowState。BaseNode 日志额外记录当前 task_id，主流程为 None；读到的 NodeContext.question 始终是原始用户问题。task_results 按任务ID归集最终结果，子图的 node_outputs 不合并到主图。

整体关系见 [节点包说明](../README.md)。
