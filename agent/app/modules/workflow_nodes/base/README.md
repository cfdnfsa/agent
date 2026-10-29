# 节点基础能力

- base_node.py：公共 run 执行入口，统一日志、读取输入、调用 execute、提交节点输出。
- [data/](data/README.md)：一个对象一个文件，分别维护节点定义、节点配置、WorkflowInput、WorkflowState；状态增量合并函数放在 workflow_state.py。

本包供具体节点、运行模块和 ai/langgraph 引擎使用，不反向导入 node、factory、workflow_runtime 或图引擎。节点基类只保存配置，每次请求的数据放在 WorkflowState。

整体关系见 [节点包说明](../README.md)。
