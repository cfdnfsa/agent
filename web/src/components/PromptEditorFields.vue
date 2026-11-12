<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { InputInstance } from 'element-plus'
import { builtinPromptVariables, type PromptVariableOption } from './promptVariables'

const name = defineModel<string>('name', { required: true })
const content = defineModel<string>('content', { required: true })
const props = withDefaults(defineProps<{
  readonly?: boolean
  disabled?: boolean
  variableOptions?: PromptVariableOption[]
}>(), { readonly: false, disabled: false, variableOptions: () => builtinPromptVariables })
const emit = defineEmits<{ 'insert-variable': [key: string] }>()
const contentInput = ref<InputInstance>()
const variableSelection = ref<string | null>(null)
let cursor: { start: number; end: number } | null = null

/** 保存正文光标位置，点击变量菜单后仍插在原位置。 */
function rememberCursor(): void {
  const textarea = contentInput.value?.textarea
  if (textarea) cursor = { start: textarea.selectionStart, end: textarea.selectionEnd }
}

/** 父组件确定变量来源后，在当前光标处自动插入占位符。 */
async function insertVariable(token: string): Promise<void> {
  if (props.readonly || props.disabled) return
  const start = Math.min(cursor?.start ?? content.value.length, content.value.length)
  const end = Math.min(cursor?.end ?? start, content.value.length)
  content.value = content.value.slice(0, start) + token + content.value.slice(end)
  cursor = { start: start + token.length, end: start + token.length }
  await nextTick()
  const textarea = contentInput.value?.textarea
  textarea?.focus()
  textarea?.setSelectionRange(cursor.start, cursor.end)
}

/** 菜单只选择来源，不要求输入变量名或大括号。 */
function selectVariable(key: string): void {
  emit('insert-variable', key)
  variableSelection.value = null
}

defineExpose({ insertVariable })
</script>

<template>
  <el-form-item label="提示词名称">
    <el-input v-model="name" :readonly="readonly" :disabled="disabled" placeholder="输入提示词名称" />
  </el-form-item>
  <el-form-item label="提示词正文">
    <div class="prompt-content-editor">
      <el-select v-if="!readonly" v-model="variableSelection" class="variable-menu" :disabled="disabled" filterable placeholder="选择并插入变量" @change="selectVariable">
        <el-option v-for="option in variableOptions" :key="option.key" :value="option.key" :label="option.label" />
      </el-select>
      <el-input ref="contentInput" v-model="content" type="textarea" :rows="12" :readonly="readonly" :disabled="disabled" placeholder="输入提示词内容" @click="rememberCursor" @keyup="rememberCursor" @select="rememberCursor" />
      <p v-if="!readonly" class="prompt-editor-hint">从菜单选择变量即可插入，运行时自动替换。具体上游节点在流程中选择。</p>
    </div>
  </el-form-item>
</template>

<style scoped>
.prompt-content-editor { width: 100%; }
.variable-menu { width: 100%; margin-bottom: 10px; }
.prompt-editor-hint { margin: 8px 0 0; color: #909399; font-size: 12px; line-height: 1.6; }
</style>
