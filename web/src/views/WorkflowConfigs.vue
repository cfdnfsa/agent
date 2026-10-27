<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  deleteWorkflowConfig, getWorkflowConfig, listWorkflowConfigs, saveWorkflowConfig,
  type WorkflowConfigRequest, type WorkflowConfigSummary,
} from '../api/workflowConfigs'

const workflowConfigs = ref<WorkflowConfigSummary[]>([])
const currentPage = ref(1)
const pageSize = 20
const totalCount = ref(0)
const isLoading = ref(false)
const isLoadingDetail = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const isBusy = computed(() => isLoading.value || isLoadingDetail.value || isSaving.value || isDeleting.value)
const loadError = ref('')
const actionError = ref('')
const formError = ref('')
const deleteError = ref('')
const successMessage = ref('')
const isEditorVisible = ref(false)
const isDeleteVisible = ref(false)
const isReadOnly = ref(false)
const editingWorkflowId = ref<number | null>(null)
const deletingWorkflow = ref<WorkflowConfigSummary | null>(null)
const workflowForm = reactive<WorkflowConfigRequest>({ workflow_name: '', workflow_definition: '' })
const editorTitle = computed(() => {
  if (isReadOnly.value) return '流程详情'
  return editingWorkflowId.value === null ? '新增流程' : '编辑流程'
})

/** 将接口错误显示在当前页面或弹窗，不额外包装错误类型。 */
function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

/** 保留旧列表直到加载成功，删除最后一页的末条记录后自动退回有效页码。 */
async function loadWorkflows(page = currentPage.value): Promise<void> {
  if (isLoading.value) return
  isLoading.value = true
  loadError.value = ''
  try {
    let workflowPage = await listWorkflowConfigs(page, pageSize)
    const lastPage = Math.max(1, Math.ceil(workflowPage.total / pageSize))
    if (page > lastPage) workflowPage = await listWorkflowConfigs(lastPage, pageSize)
    workflowConfigs.value = workflowPage.items
    totalCount.value = workflowPage.total
    currentPage.value = workflowPage.page
  } catch (error) {
    loadError.value = errorMessage(error)
  } finally {
    isLoading.value = false
  }
}

/** 新建时清空表单，不自动填入或生成任何流程内容。 */
function openCreate(): void {
  if (isBusy.value) return
  editingWorkflowId.value = null
  isReadOnly.value = false
  workflowForm.workflow_name = ''
  workflowForm.workflow_definition = ''
  formError.value = ''
  actionError.value = ''
  successMessage.value = ''
  isEditorVisible.value = true
}

/** 先加载完整详情再打开弹窗；readOnly 为 true 时只展示，不提供保存操作。 */
async function openWorkflow(workflowId: number, readOnly: boolean): Promise<void> {
  if (isBusy.value) return
  isLoadingDetail.value = true
  actionError.value = ''
  successMessage.value = ''
  try {
    const workflowConfig = await getWorkflowConfig(workflowId)
    editingWorkflowId.value = workflowConfig.id
    workflowForm.workflow_name = workflowConfig.workflow_name
    workflowForm.workflow_definition = workflowConfig.workflow_definition
    isReadOnly.value = readOnly
    formError.value = ''
    isEditorVisible.value = true
  } catch (error) {
    // 失败时不打开编辑框，避免将没有读取到的定义覆盖成空字符串。
    actionError.value = `流程详情加载失败：${errorMessage(error)}`
  } finally {
    isLoadingDetail.value = false
  }
}

/** 名称和定义原样提交，不 trim、不解析 JSON；失败时保留弹窗中的输入。 */
async function submitWorkflow(): Promise<void> {
  if (isSaving.value || isReadOnly.value) return
  isSaving.value = true
  formError.value = ''
  const isEditing = editingWorkflowId.value !== null
  try {
    await saveWorkflowConfig(editingWorkflowId.value, {
      workflow_name: workflowForm.workflow_name,
      workflow_definition: workflowForm.workflow_definition,
    })
    isEditorVisible.value = false
    successMessage.value = isEditing ? '流程配置已更新。' : '流程配置已添加。'
    await loadWorkflows(isEditing ? currentPage.value : 1)
  } catch (error) {
    formError.value = errorMessage(error)
  } finally {
    isSaving.value = false
  }
}

/** 保存中保留弹窗，防止重复操作或丢失本次输入。 */
function closeEditor(done: () => void): void {
  if (!isSaving.value) done()
}

/** 删除只需要列表中的 ID 和名称，无需读取大文本详情。 */
function openDelete(workflowConfig: WorkflowConfigSummary): void {
  if (isBusy.value) return
  deletingWorkflow.value = workflowConfig
  deleteError.value = ''
  actionError.value = ''
  successMessage.value = ''
  isDeleteVisible.value = true
}

/** 删除请求结束前保留确认窗口。 */
function closeDelete(done: () => void): void {
  if (!isDeleting.value) done()
}

/** 删除成功刷新当前页，失败时保留确认窗口并显示原因。 */
async function confirmDelete(): Promise<void> {
  if (!deletingWorkflow.value || isDeleting.value) return
  isDeleting.value = true
  deleteError.value = ''
  try {
    await deleteWorkflowConfig(deletingWorkflow.value.id)
    isDeleteVisible.value = false
    successMessage.value = '流程配置已删除。'
    await loadWorkflows()
  } catch (error) {
    deleteError.value = errorMessage(error)
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => loadWorkflows())
</script>

<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">流程管理</p>
      <h1>流程配置</h1>
      <p class="page-description">维护流程名称与定义内容。</p>
    </div>
    <el-button type="primary" :disabled="isBusy" @click="openCreate">＋ 新增流程</el-button>
  </div>

  <el-alert
    v-if="successMessage" class="page-alert" :title="successMessage" type="success"
    show-icon @close="successMessage = ''"
  />
  <el-alert
    v-if="actionError" class="page-alert" :title="actionError" type="error"
    show-icon @close="actionError = ''"
  />
  <el-alert v-if="loadError" class="page-alert" title="流程列表加载失败" type="error" :closable="false" show-icon>
    <p>{{ loadError }}</p>
    <el-button link type="primary" :disabled="isBusy" @click="loadWorkflows()">重新加载</el-button>
  </el-alert>

  <el-card shadow="never" class="model-panel">
    <template #header>
      <div class="panel-header">
        <div class="panel-title"><h2>流程列表</h2><el-tag type="info" effect="plain">{{ totalCount }} 个</el-tag></div>
        <el-button :loading="isLoading" :disabled="isLoadingDetail || isSaving || isDeleting" @click="loadWorkflows()">刷新列表</el-button>
      </div>
    </template>

    <el-table
      v-loading="isLoading || isLoadingDetail" :data="workflowConfigs" row-key="id"
      :aria-busy="isLoading || isLoadingDetail" class="model-table"
    >
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="workflow_name" label="流程名称" min-width="220" show-overflow-tooltip />
      <!-- @vue-generic {WorkflowConfigSummary} -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="isBusy" :aria-label="`查看流程 ${row.id}`" @click="openWorkflow(row.id, true)">详情</el-button>
          <el-button link type="primary" :disabled="isBusy" :aria-label="`编辑流程 ${row.id}`" @click="openWorkflow(row.id, false)">编辑</el-button>
          <el-button link type="danger" :disabled="isBusy" :aria-label="`删除流程 ${row.id}`" @click="openDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :image-size="88" :description="isLoading ? '正在加载流程配置…' : loadError ? '暂时无法加载列表，请检查服务连接' : '还没有流程配置，添加第一个流程吧'">
          <el-button v-if="!isLoading && !loadError" type="primary" plain :disabled="isBusy" @click="openCreate">新增流程</el-button>
        </el-empty>
      </template>
    </el-table>

    <div class="pagination">
      <span>每页 {{ pageSize }} 条</span>
      <el-pagination
        :current-page="currentPage" :page-size="pageSize" :total="totalCount" :pager-count="5"
        :disabled="isBusy" background layout="total, prev, pager, next"
        @update:current-page="loadWorkflows"
      />
    </div>
  </el-card>

  <el-dialog
    v-model="isEditorVisible" :title="editorTitle" width="720px" class="model-dialog"
    :close-on-click-modal="false" :close-on-press-escape="!isSaving"
    :show-close="!isSaving" :before-close="closeEditor"
  >
    <p v-if="editingWorkflowId !== null" class="field-hint">流程ID：{{ editingWorkflowId }}</p>
    <el-form
      id="workflow-config-form" :model="workflowForm" label-position="top"
      :disabled="isSaving" novalidate @submit.prevent="submitWorkflow"
    >
      <el-form-item label="流程名称">
        <el-input v-model="workflowForm.workflow_name" :readonly="isReadOnly" placeholder="例如：文章总结" />
      </el-form-item>
      <el-form-item label="流程定义">
        <el-input
          v-model="workflowForm.workflow_definition" type="textarea" :rows="14"
          :readonly="isReadOnly" placeholder="粘贴或输入流程定义"
        />
      </el-form-item>
    </el-form>
    <el-alert v-if="formError" :title="formError" type="error" :closable="false" show-icon />
    <template #footer>
      <el-button :disabled="isSaving" @click="isEditorVisible = false">{{ isReadOnly ? '关闭' : '取消' }}</el-button>
      <el-button
        v-if="!isReadOnly" type="primary" native-type="submit" form="workflow-config-form" :loading="isSaving"
      >保存配置</el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="isDeleteVisible" title="删除流程配置" width="420px" class="model-dialog"
    :close-on-click-modal="false" :close-on-press-escape="!isDeleting"
    :show-close="!isDeleting" :before-close="closeDelete"
  >
    <p class="delete-description">确定删除「{{ deletingWorkflow?.workflow_name }}」（ID：{{ deletingWorkflow?.id }}）吗？</p>
    <el-alert v-if="deleteError" :title="deleteError" type="error" :closable="false" show-icon />
    <template #footer>
      <el-button :disabled="isDeleting" @click="isDeleteVisible = false">取消</el-button>
      <el-button type="danger" :loading="isDeleting" @click="confirmDelete">确认删除</el-button>
    </template>
  </el-dialog>
</template>
