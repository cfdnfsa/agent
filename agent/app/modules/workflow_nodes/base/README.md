# 节点基础能力

- base_node.py：公共 run 执行入口，统一日志、读取上游上下文、调用 execute、按数据传递方式准备下游上下文、提交节点输出。
- text.py：公共 convert_input_to_text，文字原样保留，对象或列表转为保留中文的 JSON 文字。只有需要文字的节点调用。
- [data/](data/README.md)：一个对象一个文件，维护节点定义、配置、输入、状态，以及 NodeContext、NodeOutput；状态增量合并函数放在 workflow_state.py。

默认 accumulate 累计传递收到的数据和当前结果；result_only 只传当前结果。读取范围沿 source_ids 和上游 context 确定，不直接把全部运行记录交给下游，也不删除已有记录。合并和传递使用新的 Map，公共节点层不修改上游保存的数据。

本包供具体节点、运行模块和 ai/langgraph 引擎使用，不反向导入 node、factory、workflow_runtime 或图引擎。节点基类只保存配置，每次请求的数据放在 WorkflowState。

整体关系见 [节点包说明](../README.md)。
