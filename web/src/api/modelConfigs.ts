/** 模型配置接口：集中维护请求类型和路径，页面只处理展示与交互。 */
export type ModelProvider = 'openai' | 'ollama' | 'anthropic' | 'google_genai'

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

interface ApiResult<T> {
  code: number
  message: string
  data: T
}

export interface ModelConfigPage {
  items: ModelConfig[]
  total: number
  page: number
  page_size: number
}

/** 解析后端统一返回；网络错误转换成便于页面展示的说明，不记录请求内容。 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/model-configs${path}`, options)
  } catch {
    throw new Error('无法连接服务，请确认前后端已启动后重试。')
  }

  let result: ApiResult<T>
  try {
    result = await response.json()
  } catch {
    throw new Error('服务暂时不可用，请确认后端已启动后重试。')
  }
  if (!response.ok || result.code !== 0) {
    throw new Error(result.message || '操作失败，请稍后重试。')
  }
  return result.data
}

export function listModelConfigs(page: number, pageSize: number): Promise<ModelConfigPage> {
  return request(`?page=${page}&page_size=${pageSize}`)
}

/** 新增和编辑共用提交结构；编辑时省略 model_api_key 表示保留原密钥。 */
export function saveModelConfig(modelId: number | null, modelConfig: ModelConfigRequest): Promise<ModelConfig> {
  return request(modelId === null ? '' : `/${modelId}`, {
    method: modelId === null ? 'POST' : 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(modelConfig),
  })
}

export function deleteModelConfig(modelId: number): Promise<null> {
  return request(`/${modelId}`, { method: 'DELETE' })
}
