/** 模型配置接口：集中维护请求类型和路径，页面只处理展示与交互。 */
import { request } from './request'

export type ModelProvider = string

export interface ModelConfig {
  id: number
  model_name: string
  model_code: string
  model_provider: ModelProvider
  model_base_url: string
  has_api_key: boolean
  created_at: string
  updated_at: string
}

export interface ModelConfigRequest {
  model_name: string
  model_code: string
  model_provider: ModelProvider
  model_base_url: string
  model_api_key?: string | null
}

export interface ModelConfigPage {
  items: ModelConfig[]
  total: number
  page: number
  page_size: number
}

export interface ModelConfigTestResult {
  elapsed_ms: number
}

export function listModelConfigs(page: number, pageSize: number): Promise<ModelConfigPage> {
  return request(`/api/model-configs?page=${page}&page_size=${pageSize}`)
}

/** 新增和编辑共用提交结构；编辑时省略 model_api_key 表示保留原密钥。 */
export function saveModelConfig(modelId: number | null, modelConfig: ModelConfigRequest): Promise<ModelConfig> {
  return request(modelId === null ? '/api/model-configs' : `/api/model-configs/${modelId}`, {
    method: modelId === null ? 'POST' : 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(modelConfig),
  })
}

export function deleteModelConfig(modelId: number): Promise<null> {
  return request(`/api/model-configs/${modelId}`, { method: 'DELETE' })
}

/** 测试仅提交已保存配置的 ID，密钥由后端读取，不返回模型原始回复。 */
export function testModelConfig(modelId: number): Promise<ModelConfigTestResult> {
  return request(`/api/model-configs/${modelId}/test`, { method: 'POST' })
}
