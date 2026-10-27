/** 解析后端统一返回，供模型管理和调试台共用。 */
interface ApiResult<T> {
  code: number
  message: string
  data: T
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, options)
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
