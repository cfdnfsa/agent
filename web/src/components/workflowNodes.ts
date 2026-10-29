/** 通用节点目录与流程结构；节点能力由代码维护，不新增工具箱表。 */
export type WorkflowNodeType = 'start' | 'llm' | 'merge' | 'return'

export interface WorkflowNodeConfig {
  model_config_id?: number | null
  [key: string]: unknown
}

export interface WorkflowNodeDefinition {
  id: string
  /** 用户填写的显示名称，与用于连线的内部 ID 分开保存。 */
  name?: string
  type: string
  position?: { x: number; y: number }
  config: WorkflowNodeConfig
  [key: string]: unknown
}

export interface WorkflowEdgeDefinition {
  id: string
  source: string
  target: string
  [key: string]: unknown
}

export interface WorkflowDefinition {
  nodes: WorkflowNodeDefinition[]
  edges: WorkflowEdgeDefinition[]
  [key: string]: unknown
}

export interface WorkflowCanvasNodeData {
  definition: WorkflowNodeDefinition
}

export interface WorkflowCanvasEdgeData {
  definition: WorkflowEdgeDefinition
}

export const workflowNodeTypes: { type: WorkflowNodeType; label: string; description: string; badge: string }[] = [
  { type: 'start', label: '开始', description: '接收本次请求的输入', badge: '入' },
  { type: 'llm', label: '大模型', description: '处理上游传来的数据', badge: 'AI' },
  { type: 'merge', label: '收敛', description: '等待全部上游并收集结果', badge: '合' },
  { type: 'return', label: '返回', description: '将上游数据返回给调用方', badge: '出' },
]

/** 已知节点显示中文名称，其他类型保留原名称，避免把未知节点默认为其他能力。 */
export function workflowNodeLabel(type: string): string {
  return workflowNodeTypes.find(nodeType => nodeType.type === type)?.label ?? type
}
