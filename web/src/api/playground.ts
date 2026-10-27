import { request } from './request'

interface ModelAnswer {
  answer: string
}

/** 每次只发送模型ID和当前问题，聊天气泡中的旧消息不会提交给后端。 */
export async function askModel(modelConfigId: number, question: string): Promise<string> {
  const result = await request<ModelAnswer>('/api/playground/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_config_id: modelConfigId, question }),
  })
  return result.answer
}
