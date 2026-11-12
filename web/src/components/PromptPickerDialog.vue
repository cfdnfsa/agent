<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { deletePromptConfig, getPromptConfig, listAllPromptConfigs, savePromptConfig, type PromptConfig, type PromptConfigRequest, type PromptConfigSummary } from '../api/promptConfigs'
import PromptEditorFields from './PromptEditorFields.vue'
import { getPromptVariableNames, preparePromptVariable, promptVariableKey, type PromptVariableOption } from './promptVariables'
import type { PromptVariableBinding } from './workflowNodes'

const props = defineProps<{
  modelValue: boolean
  promptId: number | null
  variables: Record<string, PromptVariableBinding>
  variableOptions: PromptVariableOption[]
  readonly: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [visible: boolean]
  apply: [selection: { promptId: number; variables: Record<string, PromptVariableBinding> }]
  changed: []
}>()
const options = ref<PromptConfigSummary[]>([])
const selectedId = ref<number | null>(null)
const loadedPrompt = ref<PromptConfig | null>(null)
const form = reactive<PromptConfigRequest>({ prompt_name: '', prompt_content: '' })
const mode = ref<'view' | 'create' | 'edit'>('view')
const bindings = ref<Record<string, PromptVariableBinding>>({})
const bindingDrafts = new Map<number, Record<string, PromptVariableBinding>>()
const editor = ref<InstanceType<typeof PromptEditorFields>>()
const isLoading = ref(false)
const isLoadingDetail = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const isDeleteVisible = ref(false)
const isReady = ref(false)
const listError = ref('')
const detailError = ref('')
const operationError = ref('')
const message = ref('')
let detailRequest = 0
const isBusy = computed(() => isLoading.value || isLoadingDetail.value || isSaving.value || isDeleting.value)
const variableNames = computed(() => getPromptVariableNames(form.prompt_content))
const canUse = computed(() => !props.readonly && mode.value === 'view' && isReady.value && selectedId.value !== null && !isBusy.value)
const missingSelectedOption = computed(() => selectedId.value !== null && !options.value.some(option => option.id === selectedId.value))

/** 变量来源是节点草稿，选择弹窗取消时不改动原节点。 */
function copyBindings(value: Record<string, PromptVariableBinding>): Record<string, PromptVariableBinding> {
  const copy: Record<string, PromptVariableBinding> = {}
  for (const [name, binding] of Object.entries(value)) copy[name] = { ...binding }
  return copy
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

/** 概要和正文分别读取，加载失败保留当前引用，不自动选第一条。 */
async function loadOptions(): Promise<void> {
  isLoading.value = true
  listError.value = ''
  try {
    options.value = await listAllPromptConfigs()
  } catch (error) {
    listError.value = errorMessage(error)
  } finally {
    isLoading.value = false
  }
}

/** 请求序号防止切换提示词或关闭弹窗后，较慢的响应覆盖当前正文。 */
async function loadDetail(): Promise<void> {
  const requestId = ++detailRequest
  const promptId = selectedId.value
  isReady.value = false
  loadedPrompt.value = null
  detailError.value = ''
  form.prompt_name = ''
  form.prompt_content = ''
  if (promptId === null) return
  isLoadingDetail.value = true
  try {
    const prompt = await getPromptConfig(promptId)
    if (requestId !== detailRequest || !props.modelValue) return
    loadedPrompt.value = prompt
    form.prompt_name = prompt.prompt_name
    form.prompt_content = prompt.prompt_content
    isReady.value = true
  } catch (error) {
    if (requestId === detailRequest) detailError.value = errorMessage(error)
  } finally {
    if (requestId === detailRequest) isLoadingDetail.value = false
  }
}

async function selectPrompt(promptId: number): Promise<void> {
  if (isBusy.value || mode.value !== 'view') return
  if (selectedId.value !== null) bindingDrafts.set(selectedId.value, copyBindings(bindings.value))
  selectedId.value = promptId
  bindings.value = copyBindings(bindingDrafts.get(promptId) ?? {})
  operationError.value = ''
  message.value = ''
  await loadDetail()
}

function createPrompt(): void {
  if (props.readonly || isBusy.value) return
  if (selectedId.value !== null) bindingDrafts.set(selectedId.value, copyBindings(bindings.value))
  mode.value = 'create'
  form.prompt_name = ''
  form.prompt_content = ''
  isReady.value = true
  bindings.value = {}
  detailError.value = ''
  operationError.value = ''
  message.value = ''
}

function editPrompt(): void {
  if (props.readonly || isBusy.value || !isReady.value || selectedId.value === null) return
  bindingDrafts.set(selectedId.value, copyBindings(bindings.value))
  mode.value = 'edit'
  operationError.value = ''
}

function cancelEdit(): void {
  if (isBusy.value) return
  mode.value = 'view'
  if (selectedId.value !== null) bindings.value = copyBindings(bindingDrafts.get(selectedId.value) ?? {})
  if (loadedPrompt.value) {
    form.prompt_name = loadedPrompt.value.prompt_name
    form.prompt_content = loadedPrompt.value.prompt_content
    isReady.value = true
  } else {
    form.prompt_name = ''
    form.prompt_content = ''
    isReady.value = false
    if (selectedId.value !== null) void loadDetail()
  }
  operationError.value = ''
}

/** 保存的是共享提示词库；变量来源继续保留在当前节点草稿中。 */
async function savePrompt(): Promise<void> {
  if (props.readonly || isBusy.value || !isReady.value || mode.value === 'view') return
  isSaving.value = true
  operationError.value = ''
  try {
    let promptId = selectedId.value
    if (mode.value === 'create') promptId = null
    const prompt = await savePromptConfig(promptId, form)
    selectedId.value = prompt.id
    loadedPrompt.value = prompt
    form.prompt_name = prompt.prompt_name
    form.prompt_content = prompt.prompt_content
    mode.value = 'view'
    message.value = '提示词已保存到公共提示词库。'
    bindingDrafts.set(prompt.id, copyBindings(bindings.value))
    emit('changed')
    await loadOptions()
  } catch (error) {
    operationError.value = errorMessage(error)
  } finally {
    isSaving.value = false
  }
}

async function deletePrompt(): Promise<void> {
  if (props.readonly || isBusy.value || selectedId.value === null) return
  isDeleting.value = true
  operationError.value = ''
  try {
    await deletePromptConfig(selectedId.value)
    bindingDrafts.delete(selectedId.value)
    selectedId.value = null
    loadedPrompt.value = null
    form.prompt_name = ''
    form.prompt_content = ''
    isReady.value = false
    isDeleteVisible.value = false
    bindings.value = {}
    message.value = '提示词已删除，请重新选择；已有节点引用需要重新选择或清除。'
    emit('changed')
    await loadOptions()
  } catch (error) {
    operationError.value = errorMessage(error)
  } finally {
    isDeleting.value = false
  }
}

/** 变量名自动生成，点击来源后由共用编辑器插入到光标位置。 */
function insertVariable(key: string): void {
  const option = props.variableOptions.find(item => item.key === key)
  if (!option || props.readonly || mode.value === 'view') return
  const prepared = preparePromptVariable(form.prompt_content, bindings.value, option)
  bindings.value = prepared.bindings
  void editor.value?.insertVariable(`{${prepared.name}}`)
}

function bindingValue(name: string): string {
  if (name === 'question' || name === 'upstream') return name
  return promptVariableKey(bindings.value[name])
}

function isMissingBinding(name: string): boolean {
  const key = bindingValue(name)
  return Boolean(key) && !props.variableOptions.some(option => option.key === key)
}

function selectBinding(name: string, key: string): void {
  if (props.readonly || isBusy.value) return
  const option = props.variableOptions.find(item => item.key === key)
  if (option) bindings.value[name] = { ...option.binding }
}

function applyPrompt(): void {
  if (!canUse.value || selectedId.value === null) return
  const selectedBindings: Record<string, PromptVariableBinding> = {}
  for (const name of variableNames.value) {
    if (name !== 'question' && name !== 'upstream' && bindings.value[name]) selectedBindings[name] = { ...bindings.value[name] }
  }
  emit('apply', { promptId: selectedId.value, variables: selectedBindings })
  emit('update:modelValue', false)
}

function closeDialog(): void {
  if (!isBusy.value) emit('update:modelValue', false)
}

function beforeClose(done: () => void): void {
  if (!isBusy.value) done()
}

watch(() => props.modelValue, async visible => {
  if (!visible) {
    detailRequest++
    isLoadingDetail.value = false
    return
  }
  mode.value = 'view'
  isDeleteVisible.value = false
  message.value = ''
  operationError.value = ''
  selectedId.value = props.promptId
  bindings.value = copyBindings(props.variables)
  bindingDrafts.clear()
  if (props.promptId !== null) bindingDrafts.set(props.promptId, copyBindings(props.variables))
  await Promise.allSettled([loadOptions(), loadDetail()])
}, { immediate: true })
</script>

<template>
  <el-dialog :model-value="modelValue" title="选择与管理提示词" width="min(880px, 94vw)" append-to-body :before-close="beforeClose" :close-on-click-modal="false" @update:model-value="emit('update:modelValue', $event)">
    <div class="prompt-picker-toolbar">
      <el-select :model-value="selectedId" filterable placeholder="选择提示词，下方查看完整正文" :loading="isLoading" :disabled="isBusy || mode !== 'view'" @update:model-value="selectPrompt">
        <el-option v-if="missingSelectedOption" :value="selectedId!" :label="loadedPrompt?.prompt_name ?? `提示词 ID：${selectedId}`" />
        <el-option v-for="option in options" :key="option.id" :value="option.id" :label="`${option.prompt_name}（ID：${option.id}）`" />
      </el-select>
      <template v-if="!readonly">
        <el-button :disabled="isBusy || mode !== 'view'" @click="createPrompt">新增</el-button>
        <el-button :disabled="isBusy || !isReady || mode !== 'view'" @click="editPrompt">编辑</el-button>
        <el-button type="danger" plain :disabled="isBusy || !isReady || mode !== 'view'" @click="isDeleteVisible = true">删除</el-button>
      </template>
    </div>
    <el-alert v-if="listError" :title="listError" type="error" :closable="false"><el-button link :disabled="isBusy" @click="loadOptions">重新加载列表</el-button></el-alert>
    <el-alert v-if="detailError" :title="detailError" type="error" :closable="false"><el-button link :disabled="isBusy" @click="loadDetail">重新加载正文</el-button></el-alert>
    <el-alert v-if="message" :title="message" type="success" :closable="false" />
    <el-alert v-if="operationError" :title="operationError" type="error" :closable="false" />
    <p v-if="mode !== 'view'" class="prompt-picker-hint">保存会更新公共提示词库，影响所有引用这份提示词的节点。</p>
    <p v-if="mode === 'create'" class="prompt-picker-title">新增提示词</p>
    <el-form v-if="selectedId !== null || mode === 'create'" label-position="top" v-loading="isLoadingDetail" @submit.prevent="savePrompt">
      <PromptEditorFields :key="`${selectedId}-${mode}`" ref="editor" v-model:name="form.prompt_name" v-model:content="form.prompt_content" :readonly="readonly || mode === 'view'" :disabled="isBusy || !isReady" :variable-options="variableOptions" @insert-variable="insertVariable" />
    </el-form>
    <el-empty v-else :description="readonly ? '选择一份提示词查看正文' : '选择一份提示词查看正文，或点击新增'" :image-size="65" />
    <div v-if="isReady && variableNames.length" class="prompt-bindings">
      <p class="prompt-picker-title">当前节点的变量来源</p>
      <div v-for="name in variableNames" :key="name" class="prompt-binding-row">
        <code v-text="'{' + name + '}'"></code>
        <span v-if="name === 'question'">本次用户问题</span>
        <span v-else-if="name === 'upstream'">当前输入范围的全部上游结果</span>
        <el-select v-else :model-value="bindingValue(name) || undefined" filterable :disabled="readonly || isBusy" placeholder="选择变量来源" @update:model-value="selectBinding(name, $event)">
          <el-option v-if="isMissingBinding(name)" :value="bindingValue(name)" label="来源已不可用，请重新选择" disabled />
          <el-option v-for="option in variableOptions" :key="option.key" :value="option.key" :label="option.label" />
        </el-select>
      </div>
      <p class="prompt-picker-hint">来源仅属于当前节点，点击“使用此提示词”后应用。缺少来源时运行会明确提示。</p>
    </div>
    <template #footer>
      <el-button :disabled="isBusy" @click="closeDialog">{{ readonly ? '关闭' : '取消' }}</el-button>
      <template v-if="!readonly && mode !== 'view'">
        <el-button :disabled="isBusy" @click="cancelEdit">取消编辑</el-button>
        <el-button type="primary" :disabled="isBusy || !isReady" :loading="isSaving" @click="savePrompt">保存提示词</el-button>
      </template>
      <el-button v-else-if="!readonly" type="primary" :disabled="!canUse" @click="applyPrompt">使用此提示词</el-button>
    </template>
    <el-dialog v-model="isDeleteVisible" title="删除公共提示词" width="min(440px, 92vw)" append-to-body :close-on-click-modal="false" :close-on-press-escape="!isBusy" :show-close="!isBusy">
      <p>确认删除“{{ loadedPrompt?.prompt_name }}”？引用它的节点需要重新选择提示词。</p>
      <el-alert v-if="operationError" :title="operationError" type="error" :closable="false" />
      <template #footer><el-button :disabled="isBusy" @click="isDeleteVisible = false">取消</el-button><el-button type="danger" :loading="isDeleting" :disabled="isBusy" @click="deletePrompt">确认删除</el-button></template>
    </el-dialog>
  </el-dialog>
</template>

<style scoped>
.prompt-picker-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.prompt-picker-toolbar .el-select { flex: 1; min-width: 220px; }
.prompt-picker-toolbar .el-button { margin-left: 0; }
.prompt-picker-hint { color: #909399; font-size: 12px; line-height: 1.7; }
.prompt-picker-title { margin: 14px 0; font-weight: 600; }
.prompt-binding-row { display: flex; align-items: center; gap: 12px; margin: 10px 0; }
.prompt-binding-row code { width: 150px; flex-shrink: 0; overflow-wrap: anywhere; }
.prompt-binding-row .el-select { flex: 1; }
@media (max-width: 600px) { .prompt-binding-row { flex-wrap: wrap; } .prompt-binding-row code { width: 100%; } }
</style>
