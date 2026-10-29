/** 流程配置接口：定义字段通过字符串存储，画布按统一节点和连线结构读写。 */
import { request } from './request'

export interface WorkflowConfig {
  id: number
  workflow_name: string
  workflow_definition: string
}

/** 列表接口只返回概要，不包含流程定义文本。 */
export type WorkflowConfigSummary = Pick<WorkflowConfig, 'id' | 'workflow_name'>

/** 新增、编辑只提交名称和定义，自增 ID 不放入请求体。 */
export type WorkflowConfigRequest = Omit<WorkflowConfig, 'id'>

export interface WorkflowConfigPage {
  items: WorkflowConfigSummary[]
  total: number
  page: number
  page_size: number
}

/** 本次运行的固定输入，直接对应后端 WorkflowInput，不写入流程定义。 */
export interface WorkflowInput {
  /** 用户本次输入的文字。 */
  text: string
  /** 用户ID暂时预留，可不传或传 null。 */
  user_id?: string | null
}

export interface WorkflowResult {
  payload: unknown
}

/** page 是页码，pageSize 是每页数量，返回流程概要分页。 */
export function listWorkflowConfigs(page: number, pageSize: number): Promise<WorkflowConfigPage> {
  return request(`/api/workflow-configs?page=${page}&page_size=${pageSize}`)
}

/** 编辑和查看详情时单独读取完整定义，避免把概要中的缺失字段当成空值保存。 */
export function getWorkflowConfig(workflowId: number): Promise<WorkflowConfig> {
  return request(`/api/workflow-configs/${workflowId}`)
}

/** workflowId 为 null 时新增，否则修改；只序列化 HTTP 请求体，定义字符串保持原文。 */
export function saveWorkflowConfig(workflowId: number | null, workflowConfig: WorkflowConfigRequest): Promise<WorkflowConfig> {
  return request(workflowId === null ? '/api/workflow-configs' : `/api/workflow-configs/${workflowId}`, {
    method: workflowId === null ? 'POST' : 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflowConfig),
  })
}

/** 删除指定流程，成功时公共响应中的 data 为 null。 */
export function deleteWorkflowConfig(workflowId: number): Promise<null> {
  return request(`/api/workflow-configs/${workflowId}`, { method: 'DELETE' })
}

/** 提交本次文字与可选用户ID，返回节点结果可以是文字或 JSON 数据。 */
export function runWorkflowConfig(workflowId: number, workflowInput: WorkflowInput): Promise<WorkflowResult> {
  return request(`/api/workflow-configs/${workflowId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflowInput),
  })
}
