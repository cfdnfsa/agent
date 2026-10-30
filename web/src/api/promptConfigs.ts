/** 提示词配置接口：列表读取概要，编辑和详情单独读取正文。 */
import { request } from './request'

export interface PromptConfig {
  id: number
  prompt_name: string
  prompt_content: string
}

/** 列表接口只返回 ID 和名称，正文需要通过详情接口取得。 */
export type PromptConfigSummary = Pick<PromptConfig, 'id' | 'prompt_name'>

/** 新增和编辑直接提交名称、正文，自增 ID 由后端维护。 */
export type PromptConfigRequest = Omit<PromptConfig, 'id'>

export interface PromptConfigPage {
  items: PromptConfigSummary[]
  total: number
  page: number
  page_size: number
}

/** page、pageSize 是当前页码和每页数量，返回概要分页。 */
export function listPromptConfigs(page: number, pageSize: number): Promise<PromptConfigPage> {
  return request(`/api/prompt-configs?page=${page}&page_size=${pageSize}`)
}

/** 读取完整提示词，供编辑与只读详情使用。 */
export function getPromptConfig(promptId: number): Promise<PromptConfig> {
  return request(`/api/prompt-configs/${promptId}`)
}

/** ID 为空时新增，否则修改；名称和正文按输入原值提交。 */
export function savePromptConfig(promptId: number | null, promptConfig: PromptConfigRequest): Promise<PromptConfig> {
  let path = '/api/prompt-configs'
  let method = 'POST'
  if (promptId !== null) {
    path = `/api/prompt-configs/${promptId}`
    method = 'PUT'
  }
  return request(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(promptConfig),
  })
}

/** 按主键删除提示词，成功时公共响应中的 data 为 null。 */
export function deletePromptConfig(promptId: number): Promise<null> {
  return request(`/api/prompt-configs/${promptId}`, { method: 'DELETE' })
}
