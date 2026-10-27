<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  deleteModelConfig, listModelConfigs, saveModelConfig, testModelConfig,
  type ModelConfig, type ModelConfigRequest, type ModelProvider,
} from '../api/modelConfigs'

interface ModelConfigForm {
  model_name: string
  model_code: string
  model_provider: ModelProvider
  model_base_url: string
  model_api_key: string
  clear_api_key: boolean
}

const providerOptions: { value: ModelProvider; label: string }[] = [
  { value: 'openai', label: 'OpenAI 兼容' },
  { value: 'ollama', label: 'Ollama' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google_genai', label: 'Google GenAI' },
]
const modelConfigs = ref<ModelConfig[]>([])
const currentPage = ref(1)
const pageSize = 20
const totalCount = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const testingModelId = ref<number | null>(null)
const isBusy = computed(() => isLoading.value || isSaving.value || isDeleting.value || testingModelId.value !== null)
const loadError = ref('')
const formError = ref('')
const deleteError = ref('')
const successMessage = ref('')
const modelTestError = ref('')
const isEditorVisible = ref(false)
const isDeleteVisible = ref(false)
const editingModel = ref<ModelConfig | null>(null)
const deletingModel = ref<ModelConfig | null>(null)
const modelForm = reactive<ModelConfigForm>({
  model_name: '', model_code: '', model_provider: 'openai',
  model_base_url: '', model_api_key: '', clear_api_key: false,
})

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

/** 保留原列表直到刷新成功；删除最后一条时自动退回有效页码。 */
async function loadModels(page = currentPage.value): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    let modelConfigPage = await listModelConfigs(page, pageSize)
    const lastPage = Math.max(1, Math.ceil(modelConfigPage.total / pageSize))
    if (page > lastPage) modelConfigPage = await listModelConfigs(lastPage, pageSize)
    modelConfigs.value = modelConfigPage.items
    totalCount.value = modelConfigPage.total
    currentPage.value = modelConfigPage.page
  } catch (error) {
    loadError.value = errorMessage(error)
  } finally {
    isLoading.value = false
  }
}

function providerLabel(provider: ModelProvider): string {
  return providerOptions.find(option => option.value === provider)?.label ?? provider
}

function formatDate(dateValue: string): string {
  // 后端时间没有时区偏移，按返回的数据库时间展示，不擅自进行时区换算。
  return dateValue.replace('T', ' ').slice(0, 16)
}

/** 只回填公开字段，输入内容不做格式或长度校验。 */
function openEditor(modelConfig: ModelConfig | null = null): void {
  editingModel.value = modelConfig
  formError.value = ''
  successMessage.value = ''
  Object.assign(modelForm, {
    model_name: modelConfig?.model_name ?? '',
    model_code: modelConfig?.model_code ?? '',
    model_provider: modelConfig?.model_provider ?? 'openai',
    model_base_url: modelConfig?.model_base_url ?? '',
    model_api_key: '', clear_api_key: false,
  })
  isEditorVisible.value = true
}

/** Key 留空时省略字段，勾选清除时提交 null；保存中禁止重复提交或关闭弹窗。 */
async function submitModel(): Promise<void> {
  if (isSaving.value) return

  const modelRequest: ModelConfigRequest = {
    model_name: modelForm.model_name,
    model_code: modelForm.model_code,
    model_provider: modelForm.model_provider,
    model_base_url: modelForm.model_base_url,
  }
  if (modelForm.clear_api_key) modelRequest.model_api_key = null
  else if (modelForm.model_api_key) modelRequest.model_api_key = modelForm.model_api_key

  isSaving.value = true
  formError.value = ''
  const isEditing = editingModel.value !== null
  try {
    await saveModelConfig(editingModel.value?.id ?? null, modelRequest)
    isEditorVisible.value = false
    modelForm.model_api_key = ''
    successMessage.value = isEditing ? '模型配置已更新。' : '模型配置已添加。'
    await loadModels(isEditing ? currentPage.value : 1)
  } catch (error) {
    formError.value = errorMessage(error)
  } finally {
    isSaving.value = false
  }
}

function closeEditor(done: () => void): void {
  if (!isSaving.value) done()
}

function openDelete(modelConfig: ModelConfig): void {
  deletingModel.value = modelConfig
  deleteError.value = ''
  successMessage.value = ''
  isDeleteVisible.value = true
}

function closeDelete(done: () => void): void {
  if (!isDeleting.value) done()
}

async function confirmDelete(): Promise<void> {
  if (!deletingModel.value || isDeleting.value) return
  isDeleting.value = true
  deleteError.value = ''
  try {
    await deleteModelConfig(deletingModel.value.id)
    isDeleteVisible.value = false
    successMessage.value = '模型配置已删除。'
    await loadModels()
  } catch (error) {
    deleteError.value = errorMessage(error)
  } finally {
    isDeleting.value = false
  }
}

/** 每次只测试一个模型；重复点击被拦截，成功或失败都只在当前页面提示。 */
async function testConnection(modelConfig: ModelConfig): Promise<void> {
  if (isBusy.value) return
  testingModelId.value = modelConfig.id
  successMessage.value = ''
  modelTestError.value = ''
  try {
    const testResult = await testModelConfig(modelConfig.id)
    successMessage.value = `「${modelConfig.model_name}」测试成功，耗时 ${testResult.elapsed_ms} ms。`
  } catch (error) {
    modelTestError.value = `「${modelConfig.model_name}」测试失败：${errorMessage(error)}`
  } finally {
    testingModelId.value = null
  }
}

onMounted(() => loadModels())
</script>

<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">模型管理</p>
      <h1>模型配置</h1>
      <p class="page-description">统一维护模型的接入方式、服务地址与 API Key。</p>
    </div>
    <el-button type="primary" :disabled="isBusy" @click="openEditor()">＋ 新增模型</el-button>
  </div>

  <el-alert
    v-if="successMessage" class="page-alert" :title="successMessage" type="success"
    show-icon @close="successMessage = ''"
  />
  <el-alert
    v-if="modelTestError" class="page-alert" :title="modelTestError" type="error"
    show-icon @close="modelTestError = ''"
  />
  <el-alert v-if="loadError" class="page-alert" title="模型列表加载失败" type="error" :closable="false" show-icon>
    <p>{{ loadError }}</p>
    <el-button link type="primary" :disabled="isBusy" @click="loadModels()">重新加载</el-button>
  </el-alert>

  <el-card shadow="never" class="model-panel">
    <template #header>
      <div class="panel-header">
        <div class="panel-title"><h2>模型列表</h2><el-tag type="info" effect="plain">{{ totalCount }} 个</el-tag></div>
        <el-button :loading="isLoading" :disabled="isSaving || isDeleting || testingModelId !== null" @click="loadModels()">刷新列表</el-button>
      </div>
    </template>

    <el-table v-loading="isLoading" :data="modelConfigs" row-key="id" :aria-busy="isLoading" class="model-table">
      <!-- @vue-generic {ModelConfig} -->
      <el-table-column label="模型名称 / 标识" min-width="200">
        <template #default="{ row }">
          <span class="model-name">{{ row.model_name }}</span>
          <span class="model-code">{{ row.model_code }}</span>
        </template>
      </el-table-column>
      <!-- @vue-generic {ModelConfig} -->
      <el-table-column label="接入方式" width="155">
        <template #default="{ row }"><el-tag type="info">{{ providerLabel(row.model_provider) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="model_base_url" label="服务地址" min-width="220" show-overflow-tooltip />
      <!-- @vue-generic {ModelConfig} -->
      <el-table-column label="API Key" width="110">
        <template #default="{ row }"><el-tag :type="row.has_api_key ? 'success' : 'info'" effect="plain">{{ row.has_api_key ? '已配置' : '未配置' }}</el-tag></template>
      </el-table-column>
      <!-- @vue-generic {ModelConfig} -->
      <el-table-column label="更新时间" width="175">
        <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
      </el-table-column>
      <!-- @vue-generic {ModelConfig} -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            link type="primary" :disabled="isBusy" :loading="testingModelId === row.id"
            :aria-label="`测试 ${row.model_name}`" @click="testConnection(row)"
          >测试</el-button>
          <el-button link type="primary" :disabled="isBusy" :aria-label="`编辑 ${row.model_name}`" @click="openEditor(row)">编辑</el-button>
          <el-button link type="danger" :disabled="isBusy" :aria-label="`删除 ${row.model_name}`" @click="openDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :image-size="88" :description="isLoading ? '正在加载模型配置…' : loadError ? '暂时无法加载列表，请检查服务连接' : '还没有模型配置，添加第一个模型吧'">
          <el-button v-if="!isLoading && !loadError" type="primary" plain @click="openEditor()">新增模型</el-button>
        </el-empty>
      </template>
    </el-table>

    <div class="pagination">
      <span>每页 {{ pageSize }} 条</span>
      <el-pagination
        :current-page="currentPage" :page-size="pageSize" :total="totalCount" :pager-count="5"
        :disabled="isBusy" background layout="total, prev, pager, next"
        @update:current-page="loadModels"
      />
    </div>
  </el-card>
  <p class="page-note">API Key 保存后不回显。测试使用已保存的配置进行真实模型调用，可能消耗少量额度。</p>

  <el-dialog
    v-model="isEditorVisible" :title="editingModel ? '编辑模型' : '新增模型'"
    width="560px" class="model-dialog" :close-on-click-modal="false"
    :close-on-press-escape="!isSaving" :show-close="!isSaving" :before-close="closeEditor"
    @close="modelForm.model_api_key = ''"
  >
    <el-form
      id="model-config-form" :model="modelForm" label-position="top"
      :disabled="isSaving" novalidate @submit.prevent="submitModel"
    >
      <div class="form-grid">
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="modelForm.model_name" placeholder="例如：日常问答模型" />
        </el-form-item>
        <el-form-item label="模型标识" prop="model_code">
          <el-input v-model="modelForm.model_code" placeholder="服务端的实际模型标识" />
        </el-form-item>
      </div>
      <el-form-item label="接入方式" prop="model_provider">
        <el-select v-model="modelForm.model_provider" filterable allow-create placeholder="选择或填写接入方式">
          <el-option v-for="provider in providerOptions" :key="provider.value" :label="provider.label" :value="provider.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="服务地址" prop="model_base_url">
        <el-input v-model="modelForm.model_base_url" placeholder="https://api.example.com/v1" />
        <span class="field-hint">填写模型服务基础地址，保存时不检查地址格式。</span>
      </el-form-item>
      <el-form-item label="API Key（选填）" prop="model_api_key">
        <el-input
          v-model="modelForm.model_api_key" type="password" autocomplete="new-password"
          :disabled="modelForm.clear_api_key"
          :placeholder="editingModel?.has_api_key ? '已配置，留空则保留原密钥' : '无需密钥时可留空'"
        />
        <span class="field-hint">{{ editingModel ? '输入新密钥可替换原值，留空不会修改。' : '密钥保存后不会回显。' }}</span>
      </el-form-item>
      <el-form-item v-if="editingModel?.has_api_key">
        <el-checkbox v-model="modelForm.clear_api_key">清除已保存的 API Key</el-checkbox>
      </el-form-item>
    </el-form>
    <el-alert v-if="formError" :title="formError" type="error" :closable="false" show-icon />
    <template #footer>
      <el-button :disabled="isSaving" @click="isEditorVisible = false">取消</el-button>
      <el-button type="primary" native-type="submit" form="model-config-form" :loading="isSaving">保存配置</el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="isDeleteVisible" title="删除模型配置" width="420px" class="model-dialog"
    :close-on-click-modal="false" :close-on-press-escape="!isDeleting"
    :show-close="!isDeleting" :before-close="closeDelete"
  >
    <p class="delete-description">确定删除「{{ deletingModel?.model_name }}」吗？配置删除后无法恢复。</p>
    <el-alert v-if="deleteError" :title="deleteError" type="error" :closable="false" show-icon />
    <template #footer>
      <el-button :disabled="isDeleting" @click="isDeleteVisible = false">取消</el-button>
      <el-button type="danger" :loading="isDeleting" @click="confirmDelete">确认删除</el-button>
    </template>
  </el-dialog>
</template>
