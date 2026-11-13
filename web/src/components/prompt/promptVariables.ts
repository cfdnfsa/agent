/** 提示词命名变量与来源选项，模板正文和节点绑定分别保存。 */
import type { PromptVariableBinding } from '../workflow/workflowNodes'

export interface PromptVariableOption {
  key: string
  label: string
  binding: PromptVariableBinding
}

export const builtinPromptVariables: PromptVariableOption[] = [
  { key: 'question', label: '本次用户问题', binding: { source: 'question' } },
  { key: 'upstream', label: '当前输入范围的全部上游结果', binding: { source: 'upstream' } },
]

/** 与后端采用相同的命名占位符规则，普通 JSON、双花括号原样保留。 */
export function getPromptVariableNames(content: string): string[] {
  const names: string[] = []
  for (const match of content.matchAll(/(?<!\{)\{([\p{L}_][\p{L}\p{N}_]*)\}(?!\})/gu)) {
    if (!names.includes(match[1]!)) names.push(match[1]!)
  }
  return names
}

/** 下拉框使用稳定的来源键，节点改名不会改写绑定。 */
export function promptVariableKey(binding?: PromptVariableBinding): string {
  if (!binding) return ''
  if (binding.source === 'node') return `node:${binding.node_id ?? ''}`
  return binding.source
}

/** 选择上游节点时自动生成变量名，用户无需输入占位符。 */
export function preparePromptVariable(
  content: string, bindings: Record<string, PromptVariableBinding>, option: PromptVariableOption,
): { name: string; bindings: Record<string, PromptVariableBinding> } {
  const nextBindings = { ...bindings }
  let name = option.key
  if (option.binding.source === 'node') {
    name = ''
    for (const existingName of getPromptVariableNames(content)) {
      if (promptVariableKey(bindings[existingName]) === option.key) {
        name = existingName
        break
      }
    }
    if (!name) {
      let index = 1
      while (getPromptVariableNames(content).includes(`node_output_${index}`) || nextBindings[`node_output_${index}`]) index++
      name = `node_output_${index}`
    }
    nextBindings[name] = { ...option.binding }
  }
  return { name, bindings: nextBindings }
}
