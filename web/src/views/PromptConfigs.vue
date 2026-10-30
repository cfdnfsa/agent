<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  deletePromptConfig, getPromptConfig, listPromptConfigs, savePromptConfig,
  type PromptConfigRequest, type PromptConfigSummary,
} from '../api/promptConfigs'

const promptConfigs = ref<PromptConfigSummary[]>([])
const currentPage = ref(1)
const pageSize = 20
const totalCount = ref(0)
const isLoading = ref(false)
const isLoadingDetail = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const isBusy = computed(() => isLoading.value || isLoadingDetail.value || isSaving.value || isDeleting.value)
const loadError = ref('')
const formError = ref('')
const deleteError = ref('')
const successMessage = ref('')
const isEditorVisible = ref(false)
const isDeleteVisible = ref(false)
const isReadOnly = ref(false)
// 创建时空表单即可保存；编辑时必须成功读取完整正文，避免把概要当成完整配置。
const isFormReady = ref(false)
const editingPromptId = ref<number | null>(null)
const deletingPrompt = ref<PromptConfigSummary | null>(null)
const promptForm = reactive<PromptConfigRequest>({ prompt_name: '', prompt_content: '' })
const canSubmit = computed(() => isFormReady.value && !isReadOnly.value && !isBusy.value)
const editorTitle = computed(() => {
  if (isReadOnly.value) {
    return '提示词详情'
  }
  if (editingPromptId.value === null) {
    return '新增提示词'
  }
  return '编辑提示词'
})
const emptyDescription = computed(() => {
  if (isLoading.value) {
    return '正在加载提示词配置…'
  }
  if (loadError.value) {
    return '暂时无法加载列表，请检查服务连接'
  }
  return '还没有提示词配置，添加第一个提示词吧'
})

/** 沿用接口的公开错误说明，未知错误使用统一提示。 */
function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return '操作失败，请稍后重试。'
}

/** 保留旧列表直到刷新成功，删除末页最后一条时自动退回有效页码。 */
async function loadPrompts(page = currentPage.value): Promise<void> {
  if (isLoading.value) {
    return
  }
  isLoading.value = true
  loadError.value = ''
  try {
    let promptPage = await listPromptConfigs(page, pageSize)
    const lastPage = Math.max(1, Math.ceil(promptPage.total / pageSize))
    if (page > lastPage) {
      promptPage = await listPromptConfigs(lastPage, pageSize)
    }
    promptConfigs.value = promptPage.items
    totalCount.value = promptPage.total
    currentPage.value = promptPage.page
  } catch (error) {
    loadError.value = errorMessage(error)
  } finally {
    isLoading.value = false
  }
}

/** 编辑与详情都读取最新正文；失败时保留弹窗并禁止保存，允许重试。 */
async function loadPromptDetail(): Promise<void> {
  if (editingPromptId.value === null || isBusy.value) {
    return
  }
  isLoadingDetail.value = true
  isFormReady.value = false
  formError.value = ''
  try {
    const promptConfig = await getPromptConfig(editingPromptId.value)
    promptForm.prompt_name = promptConfig.prompt_name
    promptForm.prompt_content = promptConfig.prompt_content
    isFormReady.value = true
  } catch (error) {
    formError.value = errorMessage(error)
  } finally {
    isLoadingDetail.value = false
  }
}

/** 新增使用空表单，编辑和详情按选中记录ID读取完整配置。 */
async function openEditor(promptConfig: PromptConfigSummary | null = null, readOnly = false): Promise<void> {
  if (isBusy.value) {
    return
  }
  editingPromptId.value = null
  isReadOnly.value = readOnly
  isFormReady.value = true
  promptForm.prompt_name = ''
  promptForm.prompt_content = ''
  formError.value = ''
  successMessage.value = ''
  isEditorVisible.value = true
  if (promptConfig !== null) {
    editingPromptId.value = promptConfig.id
    isFormReady.value = false
    await loadPromptDetail()
  }
}

/** 读取正文或保存期间保持弹窗，防止并发操作改变正在处理的配置。 */
function closeEditor(done: () => void): void {
  if (!isSaving.value && !isLoadingDetail.value) {
    done()
  }
}

/** 名称和正文原样提交；保存失败保留输入，成功后刷新对应页码。 */
async function submitPrompt(): Promise<void> {
  if (!canSubmit.value) {
    return
  }
  isSaving.value = true
  formError.value = ''
  const isEditing = editingPromptId.value !== null
  try {
    await savePromptConfig(editingPromptId.value, promptForm)
    isEditorVisible.value = false
    if (isEditing) {
      successMessage.value = '提示词配置已更新。'
      await loadPrompts()
    } else {
      successMessage.value = '提示词配置已添加。'
      await loadPrompts(1)
    }
  } catch (error) {
    formError.value = errorMessage(error)
  } finally {
    isSaving.value = false
  }
}

/** 删除只需要概要中的ID、名称，打开确认弹窗时不查询正文。 */
function openDelete(promptConfig: PromptConfigSummary): void {
  if (isBusy.value) {
    return
  }
  deletingPrompt.value = promptConfig
  deleteError.value = ''
  successMessage.value = ''
  isDeleteVisible.value = true
}

/** 删除请求结束前保留确认弹窗。 */
function closeDelete(done: () => void): void {
  if (!isDeleting.value) {
    done()
  }
}

/** 删除失败保留错误与重试入口，成功后刷新列表。 */
async function confirmDelete(): Promise<void> {
  if (deletingPrompt.value === null || isDeleting.value) {
    return
  }
  isDeleting.value = true
  deleteError.value = ''
  try {
    await deletePromptConfig(deletingPrompt.value.id)
    isDeleteVisible.value = false
    successMessage.value = '提示词配置已删除。'
    await loadPrompts()
  } catch (error) {
    deleteError.value = errorMessage(error)
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => loadPrompts())
</script>

<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">提示词管理</p>
      <h1>提示词配置</h1>
      <p class="page-description">维护可复用的提示词名称和正文。</p>
    </div>
    <el-button type="primary" :disabled="isBusy" @click="openEditor()">＋ 新增提示词</el-button>
  </div>

  <el-alert v-if="successMessage" class="page-alert" :title="successMessage" type="success" show-icon @close="successMessage = ''" />
  <el-alert v-if="loadError" class="page-alert" title="提示词列表加载失败" type="error" :closable="false" show-icon>
    <p>{{ loadError }}</p>
    <el-button link type="primary" :disabled="isBusy" @click="loadPrompts()">重新加载</el-button>
  </el-alert>

  <el-card shadow="never" class="model-panel">
    <template #header>
      <div class="panel-header">
        <div class="panel-title"><h2>提示词列表</h2><el-tag type="info" effect="plain">{{ totalCount }} 个</el-tag></div>
        <el-button :loading="isLoading" :disabled="isLoadingDetail || isSaving || isDeleting" @click="loadPrompts()">刷新列表</el-button>
      </div>
    </template>
    <el-table v-loading="isLoading" :data="promptConfigs" row-key="id" :aria-busy="isLoading" class="model-table">
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="prompt_name" label="提示词名称" min-width="220" show-overflow-tooltip />
      <!-- @vue-generic {PromptConfigSummary} -->
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="isBusy" :aria-label="`编辑提示词 ${row.id}`" @click="openEditor(row)">编辑</el-button>
          <el-button link type="primary" :disabled="isBusy" :aria-label="`查看提示词 ${row.id}`" @click="openEditor(row, true)">详情</el-button>
          <el-button link type="danger" :disabled="isBusy" :aria-label="`删除提示词 ${row.id}`" @click="openDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :image-size="88" :description="emptyDescription">
          <el-button v-if="!isLoading && !loadError" type="primary" plain :disabled="isBusy" @click="openEditor()">新增提示词</el-button>
        </el-empty>
      </template>
    </el-table>
    <div class="pagination">
      <span>每页 {{ pageSize }} 条</span>
      <el-pagination
        :current-page="currentPage" :page-size="pageSize" :total="totalCount" :pager-count="5"
        :disabled="isBusy" background layout="total, prev, pager, next" @update:current-page="loadPrompts"
      />
    </div>
  </el-card>

  <el-dialog
    v-model="isEditorVisible" :title="editorTitle" width="720px" class="model-dialog"
    :close-on-click-modal="false" :close-on-press-escape="!isSaving && !isLoadingDetail"
    :show-close="!isSaving && !isLoadingDetail" :before-close="closeEditor"
  >
    <el-form
      id="prompt-config-form" v-loading="isLoadingDetail" :model="promptForm" label-position="top"
      :disabled="isSaving || isLoadingDetail || !isFormReady" novalidate @submit.prevent="submitPrompt"
    >
      <el-form-item label="提示词名称" prop="prompt_name">
        <el-input v-model="promptForm.prompt_name" :readonly="isReadOnly" placeholder="例如：问题分析助手" />
      </el-form-item>
      <el-form-item label="提示词正文" prop="prompt_content">
        <el-input v-model="promptForm.prompt_content" type="textarea" :rows="12" :readonly="isReadOnly" placeholder="输入提示词内容" />
      </el-form-item>
    </el-form>
    <el-alert v-if="formError" :title="formError" type="error" :closable="false" show-icon>
      <el-button v-if="!isFormReady && editingPromptId !== null" link type="primary" :disabled="isBusy" @click="loadPromptDetail">重新加载</el-button>
    </el-alert>
    <template #footer>
      <el-button v-if="isReadOnly" :disabled="isLoadingDetail" @click="isEditorVisible = false">关闭</el-button>
      <el-button v-else :disabled="isSaving || isLoadingDetail" @click="isEditorVisible = false">取消</el-button>
      <el-button v-if="!isReadOnly" type="primary" native-type="submit" form="prompt-config-form" :disabled="!canSubmit" :loading="isSaving">保存配置</el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="isDeleteVisible" title="删除提示词配置" width="420px" class="model-dialog"
    :close-on-click-modal="false" :close-on-press-escape="!isDeleting"
    :show-close="!isDeleting" :before-close="closeDelete"
  >
    <p class="delete-description">确定删除「{{ deletingPrompt?.prompt_name }}」吗？配置删除后无法恢复。</p>
    <el-alert v-if="deleteError" :title="deleteError" type="error" :closable="false" show-icon />
    <template #footer>
      <el-button :disabled="isDeleting" @click="isDeleteVisible = false">取消</el-button>
      <el-button type="danger" :loading="isDeleting" @click="confirmDelete">确认删除</el-button>
    </template>
  </el-dialog>
</template>
