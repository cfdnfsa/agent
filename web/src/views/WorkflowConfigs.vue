<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteWorkflowConfig, listWorkflowConfigs, type WorkflowConfigSummary } from '../api/workflowConfigs'

const router = useRouter()
const workflowConfigs = ref<WorkflowConfigSummary[]>([])
const currentPage = ref(1)
const pageSize = 20
const totalCount = ref(0)
const isLoading = ref(false)
const isDeleting = ref(false)
const isBusy = computed(() => isLoading.value || isDeleting.value)
const loadError = ref('')
const deleteError = ref('')
const successMessage = ref('')
const isDeleteVisible = ref(false)
const deletingWorkflow = ref<WorkflowConfigSummary | null>(null)

/** 保留旧列表直到加载成功，删除末页最后一条后自动退回有效页码。 */
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
    loadError.value = error instanceof Error ? error.message : '流程列表加载失败。'
  } finally {
    isLoading.value = false
  }
}

/** 新建、详情和编排都进入画布页，详情通过查询参数启用只读模式。 */
function openDesigner(workflowId: number | 'new', readOnly = false): void {
  void router.push({ path: `/workflow-configs/${workflowId}`, query: readOnly ? { readonly: '1' } : {} })
}

/** 删除只需要列表中的主键和名称，不读取流程大文本。 */
function openDelete(workflowConfig: WorkflowConfigSummary): void {
  deletingWorkflow.value = workflowConfig
  deleteError.value = ''
  successMessage.value = ''
  isDeleteVisible.value = true
}

/** 删除请求结束前保留确认窗口。 */
function closeDelete(done: () => void): void {
  if (!isDeleting.value) done()
}

/** 删除失败保留窗口，成功后刷新当前页。 */
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
    deleteError.value = error instanceof Error ? error.message : '删除失败，请稍后重试。'
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
      <p class="page-description">通过节点与连线编排流程。</p>
    </div>
    <el-button type="primary" :disabled="isBusy" @click="openDesigner('new')">＋ 新增流程</el-button>
  </div>
  <el-alert v-if="successMessage" class="page-alert" :title="successMessage" type="success" show-icon @close="successMessage = ''" />
  <el-alert v-if="loadError" class="page-alert" title="流程列表加载失败" type="error" :closable="false" show-icon>
    <p>{{ loadError }}</p>
    <el-button link type="primary" :disabled="isBusy" @click="loadWorkflows()">重新加载</el-button>
  </el-alert>

  <el-card shadow="never" class="model-panel">
    <template #header>
      <div class="panel-header">
        <div class="panel-title"><h2>流程列表</h2><el-tag type="info" effect="plain">{{ totalCount }} 个</el-tag></div>
        <el-button :loading="isLoading" :disabled="isDeleting" @click="loadWorkflows()">刷新列表</el-button>
      </div>
    </template>
    <el-table v-loading="isLoading" :data="workflowConfigs" row-key="id" :aria-busy="isLoading" class="model-table">
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="workflow_name" label="流程名称" min-width="220" show-overflow-tooltip />
      <!-- @vue-generic {WorkflowConfigSummary} -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="isBusy" :aria-label="`查看流程 ${row.id}`" @click="openDesigner(row.id, true)">详情</el-button>
          <el-button link type="primary" :disabled="isBusy" :aria-label="`编排流程 ${row.id}`" @click="openDesigner(row.id)">编排</el-button>
          <el-button link type="danger" :disabled="isBusy" :aria-label="`删除流程 ${row.id}`" @click="openDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :image-size="88" :description="isLoading ? '正在加载流程配置…' : loadError ? '暂时无法加载列表，请检查服务连接' : '还没有流程配置，添加第一个流程吧'">
          <el-button v-if="!isLoading && !loadError" type="primary" plain :disabled="isBusy" @click="openDesigner('new')">新增流程</el-button>
        </el-empty>
      </template>
    </el-table>
    <div class="pagination">
      <span>每页 {{ pageSize }} 条</span>
      <el-pagination
        :current-page="currentPage" :page-size="pageSize" :total="totalCount" :pager-count="5"
        :disabled="isBusy" background layout="total, prev, pager, next" @update:current-page="loadWorkflows"
      />
    </div>
  </el-card>

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
