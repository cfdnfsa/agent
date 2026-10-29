<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MarkerType, VueFlow, useVueFlow, type Connection, type Edge, type Node, type XYPosition } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import WorkflowCanvasNode from '../components/WorkflowCanvasNode.vue'
import {
  workflowNodeLabel, workflowNodeTypes,
  type WorkflowCanvasEdgeData, type WorkflowCanvasNodeData, type WorkflowDefinition, type WorkflowNodeType,
} from '../components/workflowNodes'
import { getWorkflowConfig, runWorkflowConfig, saveWorkflowConfig, type WorkflowInput, type WorkflowResult } from '../api/workflowConfigs'
import { listModelConfigs, type ModelConfig } from '../api/modelConfigs'

const route = useRoute()
const router = useRouter()
const { screenToFlowCoordinate, fitView, removeNodes, removeEdges } = useVueFlow({ id: 'workflow-designer' })
// 画布类型含递归组件定义，使用浅层引用；节点配置本身单独保持响应式。
const nodes = shallowRef<Node<WorkflowCanvasNodeData>[]>([])
const edges = shallowRef<Edge<WorkflowCanvasEdgeData>[]>([])
const workflowId = ref<number | null>(null)
const workflowName = ref('')
const originalDefinition = ref<WorkflowDefinition>({ start_node_id: null, return_node_id: null, nodes: [], edges: [] })
const rawDefinition = ref('')
const selectedNodeId = ref<string | null>(null)
const selectedEdgeId = ref<string | null>(null)
const modelOptions = ref<ModelConfig[]>([])
const isLoading = ref(true)
const isLoadingModels = ref(false)
const isSaving = ref(false)
const isRunning = ref(false)
const loadError = ref('')
const definitionError = ref('')
const modelError = ref('')
const saveError = ref('')
const runError = ref('')
const successMessage = ref('')
// 运行输入与流程配置分开，始终通过固定字段访问，不随保存画布写入数据库。
const workflowInput = reactive<WorkflowInput>({ text: '', user_id: null })
const runResult = ref<WorkflowResult | null>(null)
const showToolbox = ref(true)
const showSettings = ref(true)
const isReadOnly = computed(() => route.query.readonly === '1')
const isBusy = computed(() => isLoading.value || isSaving.value || isRunning.value)
const canEdit = computed(() => !isReadOnly.value && !isBusy.value && !loadError.value && !definitionError.value)
const startNodes = computed(() => nodes.value.filter(node => node.data?.definition.type === 'start'))
const returnNodes = computed(() => nodes.value.filter(node => node.data?.definition.type === 'return'))
// 根据当前画布推导ID，按钮删除、键盘删除和重新添加都会自动同步，保存时不沿用旧ID。
const startNodeId = computed(() => startNodes.value[0]?.id ?? null)
const returnNodeId = computed(() => returnNodes.value[0]?.id ?? null)
const canRun = computed(() => canEdit.value && startNodes.value.length === 1 && returnNodes.value.length === 1)
const selectedDefinition = computed(() => nodes.value.find(node => node.id === selectedNodeId.value)?.data?.definition ?? null)
const hasSelection = computed(() => selectedDefinition.value !== null || edges.value.some(edge => edge.id === selectedEdgeId.value))

/** 错误显示在当前页，配置输入保持原值。 */
function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

/** 纯文本显示数据，保留换行；对象展开为 JSON，不作为 HTML 执行。 */
function formatData(value: unknown): string {
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2) ?? ''
}

/** 按当前流程结构读取节点和连线，保存前不改写数据库。 */
async function applyDefinition(): Promise<void> {
  try {
    const definition: WorkflowDefinition = rawDefinition.value === '' ? { start_node_id: null, return_node_id: null, nodes: [], edges: [] } : JSON.parse(rawDefinition.value)
    if (!definition || !Array.isArray(definition.nodes) || !Array.isArray(definition.edges)) {
      throw new Error('流程定义需要包含 nodes 和 edges 列表。')
    }
    if ((definition.start_node_id !== null && typeof definition.start_node_id !== 'string') || (definition.return_node_id !== null && typeof definition.return_node_id !== 'string')) {
      throw new Error('流程定义需要包含 start_node_id 和 return_node_id；未添加对应节点时填写 null。')
    }
    // 这里只检查画布显示所需结构，不校验模型、参数内容或流程业务规则。
    if (definition.nodes.some(node => !node || typeof node.id !== 'string' || typeof node.type !== 'string' || !node.config || typeof node.config !== 'object' || Array.isArray(node.config))) {
      throw new Error('节点需要包含 id、type 和 config 对象。')
    }
    if (definition.edges.some(edge => !edge || typeof edge.id !== 'string' || typeof edge.source !== 'string' || typeof edge.target !== 'string')) {
      throw new Error('连线需要包含 id、source 和 target。')
    }
    originalDefinition.value = definition
    nodes.value = definition.nodes.map((node, index) => ({
      id: node.id, type: 'workflow', position: node.position ?? { x: 80 + index * 280, y: 160 },
      data: reactive({ definition: node }),
    }))
    edges.value = definition.edges.map(edge => ({ ...edge, type: 'smoothstep', markerEnd: MarkerType.ArrowClosed, data: { definition: edge } }))
    selectedNodeId.value = definition.start_node_id
    selectedEdgeId.value = null
    definitionError.value = ''
    await nextTick()
    await fitView({ padding: 0.25 })
  } catch (error) {
    // 保留无法解析的原文并禁止画布保存，避免已保存内容被空图覆盖。
    definitionError.value = `无法显示画布：${errorMessage(error)}`
  }
}

/** 新流程自带开始和返回节点，由用户连线；已有流程原样读取完整定义。 */
async function loadWorkflow(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  definitionError.value = ''
  saveError.value = ''
  runError.value = ''
  successMessage.value = ''
  runResult.value = null
  workflowInput.text = ''
  workflowInput.user_id = null
  nodes.value = []
  edges.value = []
  try {
    workflowId.value = route.params.workflowId === 'new' ? null : Number(route.params.workflowId)
    if (workflowId.value === null) {
      workflowName.value = ''
      rawDefinition.value = JSON.stringify({ start_node_id: 'start_1', return_node_id: 'return_1', nodes: [
        { id: 'start_1', name: '开始 1', type: 'start', position: { x: 80, y: 160 }, config: {} },
        { id: 'return_1', name: '返回 1', type: 'return', position: { x: 640, y: 160 }, config: {} },
      ], edges: [] })
    } else {
      const workflow = await getWorkflowConfig(workflowId.value)
      workflowName.value = workflow.workflow_name
      rawDefinition.value = workflow.workflow_definition
    }
    await applyDefinition()
  } catch (error) {
    loadError.value = errorMessage(error)
  } finally {
    isLoading.value = false
  }
}

/** 分页读取全部模型，已有节点的模型ID不会因列表刷新被自动改写。 */
async function loadModels(): Promise<void> {
  isLoadingModels.value = true
  modelError.value = ''
  try {
    const firstPage = await listModelConfigs(1, 100)
    const models = [...firstPage.items]
    for (let page = 2; page <= Math.ceil(firstPage.total / 100); page++) {
      models.push(...(await listModelConfigs(page, 100)).items)
    }
    modelOptions.value = models
  } catch (error) {
    modelError.value = errorMessage(error)
  } finally {
    isLoadingModels.value = false
  }
}

/** 开始和返回节点分别只能有一个；按钮、拖拽和添加入口共用此规则。 */
function canAddNode(type: WorkflowNodeType): boolean {
  if (!canEdit.value) return false
  if (type === 'start') return startNodes.value.length === 0
  if (type === 'return') return returnNodes.value.length === 0
  return true
}

/** 点击添加时自动排开；拖入时使用落点坐标，配置只保留当前必需的模型ID。 */
function addNode(type: WorkflowNodeType, position?: XYPosition): void {
  if (!canAddNode(type)) return
  let index = 1
  while (nodes.value.some(node => node.id === `${type}_${index}`)) index++
  const id = `${type}_${index}`
  const config = type === 'llm' ? { model_config_id: modelOptions.value[0]?.id ?? null } : {}
  nodes.value = [...nodes.value, {
    id, type: 'workflow', position: position ?? { x: 80 + nodes.value.length * 280, y: 160 },
    data: reactive({ definition: { id, name: `${workflowNodeLabel(type)} ${index}`, type, config } }),
  }]
  selectNode(id)
  successMessage.value = ''
  if (!position) void nextTick(() => fitView({ padding: 0.25 }))
}

/** 工具箱拖拽只携带节点类型。 */
function startDrag(event: DragEvent, type: WorkflowNodeType): void {
  if (!canAddNode(type) || !event.dataTransfer) return
  event.dataTransfer.setData('application/vueflow', type)
  event.dataTransfer.effectAllowed = 'copy'
}

/** 由 Vue Flow 转换坐标，缩放或平移后仍在鼠标落点添加节点。 */
function dropNode(event: DragEvent): void {
  event.preventDefault()
  const type = event.dataTransfer?.getData('application/vueflow') as WorkflowNodeType
  if (workflowNodeTypes.some(nodeType => nodeType.type === type)) {
    addNode(type, screenToFlowCoordinate({ x: event.clientX, y: event.clientY }))
  }
}

/** 连线记录数据方向；返回节点只能接收数据，不能再连接下游。 */
function connectNodes(connection: Connection): void {
  if (!canEdit.value) return
  const sourceDefinition = nodes.value.find(node => node.id === connection.source)?.data?.definition
  if (sourceDefinition?.type === 'return') return
  const definition = { id: `edge_${crypto.randomUUID()}`, source: connection.source, target: connection.target }
  edges.value = [...edges.value, { ...definition, type: 'smoothstep', markerEnd: MarkerType.ArrowClosed, data: { definition } }]
}

/** 选中画布节点，右侧显示相应配置。 */
function selectNode(nodeId: string): void {
  selectedNodeId.value = nodeId
  selectedEdgeId.value = null
  showSettings.value = true
}

/** 删除节点时同时删除关联连线，运行和详情模式禁止修改。 */
function deleteSelected(): void {
  if (!canEdit.value) return
  if (selectedNodeId.value) removeNodes([selectedNodeId.value])
  if (selectedEdgeId.value) removeEdges([selectedEdgeId.value])
  selectedNodeId.value = null
  selectedEdgeId.value = null
}

/** 只保存配置和坐标，本次输入、运行结果和画布内部状态不进入定义。 */
async function saveWorkflow(): Promise<number | null> {
  if (!canEdit.value) return null
  isSaving.value = true
  saveError.value = ''
  successMessage.value = ''
  const definition: WorkflowDefinition = {
    ...originalDefinition.value,
    start_node_id: startNodeId.value,
    return_node_id: returnNodeId.value,
    nodes: nodes.value.map(node => ({ ...node.data!.definition, id: node.id, position: { x: node.position.x, y: node.position.y } })),
    edges: edges.value.map(edge => ({ ...edge.data?.definition, id: edge.id, source: edge.source, target: edge.target })),
  }
  try {
    const workflow = await saveWorkflowConfig(workflowId.value, { workflow_name: workflowName.value, workflow_definition: JSON.stringify(definition) })
    workflowId.value = workflow.id
    rawDefinition.value = workflow.workflow_definition
    originalDefinition.value = definition
    await router.replace(`/workflow-configs/${workflow.id}`)
    successMessage.value = '流程已保存。'
    return workflow.id
  } catch (error) {
    saveError.value = errorMessage(error)
    return null
  } finally {
    isSaving.value = false
  }
}

/** 先保存当前画布再运行，页面只展示最终数据或公共错误说明。 */
async function runWorkflow(): Promise<void> {
  if (!canRun.value) return
  runError.value = ''
  runResult.value = null
  const savedId = await saveWorkflow()
  if (savedId === null) return
  isRunning.value = true
  try {
    runResult.value = await runWorkflowConfig(savedId, workflowInput)
  } catch (error) {
    runError.value = errorMessage(error)
  } finally {
    isRunning.value = false
  }
}

// 新建保存后先更新 workflowId，再切换地址，避免重复读取刚保存的内容。
watch(() => route.params.workflowId, () => {
  const targetId = route.params.workflowId === 'new' ? null : Number(route.params.workflowId)
  if (targetId !== workflowId.value) void loadWorkflow()
})
onMounted(() => { void loadWorkflow(); void loadModels() })
</script>

<template>
  <div class="workflow-editor">
    <header class="designer-heading">
      <div class="designer-name">
        <el-button :disabled="isBusy" @click="router.push('/workflow-configs')">返回列表</el-button>
        <el-input v-model="workflowName" :readonly="isReadOnly" :disabled="isBusy" placeholder="流程名称" aria-label="流程名称" />
        <el-tag v-if="isReadOnly" type="info">只读详情</el-tag>
      </div>
      <div class="designer-actions">
        <el-button @click="showToolbox = !showToolbox">工具箱</el-button>
        <el-button @click="showSettings = !showSettings">配置</el-button>
        <el-button @click="fitView({ padding: 0.25 })">适应画布</el-button>
        <el-button v-if="isReadOnly" type="primary" :disabled="isBusy || !!loadError" @click="router.replace({ query: {} })">编辑流程</el-button>
        <el-button v-else type="primary" :disabled="!canEdit" :loading="isSaving" @click="saveWorkflow">保存</el-button>
      </div>
    </header>
    <div class="designer-alerts">
      <el-alert v-if="successMessage" :title="successMessage" type="success" show-icon @close="successMessage = ''" />
      <el-alert v-if="saveError" :title="saveError" type="error" show-icon @close="saveError = ''" />
      <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon><el-button link type="primary" @click="loadWorkflow">重新加载</el-button></el-alert>
      <el-alert v-if="definitionError" :title="definitionError" type="error" :closable="false" show-icon />
    </div>

    <div v-loading="isLoading" class="designer-workspace">
      <aside v-if="showToolbox" class="designer-sidebar">
        <h2>节点工具箱</h2>
        <p class="designer-hint">拖入画布，或点击添加。</p>
        <button v-for="nodeType in workflowNodeTypes" :key="nodeType.type" type="button" class="palette-node" :draggable="canAddNode(nodeType.type)" :disabled="!canAddNode(nodeType.type)" @dragstart="startDrag($event, nodeType.type)" @click="addNode(nodeType.type)">
          <span>{{ nodeType.badge }}</span><div><strong>{{ nodeType.label }}</strong><small>{{ nodeType.description }}</small></div>
        </button>
        <p class="designer-hint">从右侧圆点拖到下个节点左侧，建立数据连线。</p>
        <p class="designer-hint">每个流程需要一个开始和一个返回节点。返回只能作为终点，其他支路也可独立结束。</p>
      </aside>

      <section class="designer-canvas" @drop="dropNode" @dragover.prevent>
        <VueFlow
          id="workflow-designer" v-model:nodes="nodes" v-model:edges="edges" fit-view-on-init
          :nodes-draggable="canEdit" :nodes-connectable="canEdit" :edges-updatable="false" :delete-key-code="canEdit ? 'Delete' : null"
          @connect="connectNodes" @node-click="({ node }) => selectNode(node.id)"
          @edge-click="({ edge }) => { selectedEdgeId = edge.id; selectedNodeId = null }"
          @pane-click="() => { selectedNodeId = null; selectedEdgeId = null }"
        >
          <template #node-workflow="nodeProps">
            <WorkflowCanvasNode v-bind="nodeProps" :can-run="canRun" :running="isRunning" @run="runWorkflow" />
          </template>
        </VueFlow>
        <div v-if="nodes.length === 0 && !isLoading" class="canvas-empty">从左侧添加开始节点</div>
      </section>

      <aside v-if="showSettings" class="designer-settings">
        <div class="panel-header"><h2>节点配置</h2><el-button v-if="hasSelection && !isReadOnly" link type="danger" :disabled="!canEdit" @click="deleteSelected">删除选中</el-button></div>
        <template v-if="selectedDefinition">
          <p class="designer-node-id">{{ workflowNodeLabel(selectedDefinition.type) }} · {{ selectedDefinition.id }}</p>
          <!-- 名称只用于展示，不改节点 ID，也不增加必填、去空格或重名限制。 -->
          <el-form label-position="top" :disabled="!canEdit">
            <el-form-item label="节点名称">
              <el-input v-model="selectedDefinition.name" :readonly="isReadOnly" :placeholder="workflowNodeLabel(selectedDefinition.type)" />
            </el-form-item>
          </el-form>
          <template v-if="selectedDefinition.type === 'start'">
            <p class="designer-hint">接收本次输入，点击节点旁的 ▶ 运行。</p>
            <label class="input-label" for="workflow-user-id">用户ID（可选）</label>
            <el-input id="workflow-user-id" v-model="workflowInput.user_id" :readonly="isReadOnly" :disabled="isBusy" placeholder="后续记忆等功能使用，可不填" />
            <label class="input-label" for="workflow-test-input">测试文字</label>
            <el-input id="workflow-test-input" v-model="workflowInput.text" type="textarea" :rows="7" :readonly="isReadOnly" :disabled="isBusy" placeholder="输入一段文字" />
            <p class="designer-hint">仅用于本次运行，不随流程保存。运行前会自动保存当前画布。</p>
            <el-button type="success" :disabled="!canRun" :loading="isRunning" @click="runWorkflow">▶ 运行</el-button>
          </template>
          <template v-else-if="selectedDefinition.type === 'llm'">
            <el-form label-position="top" :disabled="!canEdit">
              <el-form-item label="模型">
                <el-select v-model="selectedDefinition.config.model_config_id" filterable clearable :loading="isLoadingModels" placeholder="选择模型">
                  <el-option v-for="model in modelOptions" :key="model.id" :label="`${model.model_name}（${model.model_code}）`" :value="model.id" />
                </el-select>
              </el-form-item>
            </el-form>
            <el-alert v-if="modelError" :title="modelError" type="error" :closable="false"><el-button link type="primary" :disabled="isLoadingModels" @click="loadModels">重新加载模型</el-button></el-alert>
            <p class="designer-hint">接收一个上游，文字直接交给模型，对象转为 JSON 文字。多路输入请先连接收敛节点。</p>
          </template>
          <p v-else-if="selectedDefinition.type === 'merge'" class="designer-hint">将多个上游连到左侧圆点，等待全部完成后，按节点 ID 收集结果并传给下游，无需额外配置。</p>
          <p v-else-if="selectedDefinition.type === 'return'" class="designer-hint">把一个上游的数据原样返回给调用方，无需额外配置。此节点不能连接下游；多路结果先经过收敛节点。本次运行仍会等待其他支路完成。</p>
          <p v-else class="designer-hint">当前节点配置会保留，暂未提供配置面板。</p>
        </template>
        <p v-else class="designer-hint">点击节点查看配置，选中连线后可以删除。</p>
        <div v-if="definitionError" class="definition-recovery">
          <h2>原始流程定义</h2>
          <el-input v-model="rawDefinition" type="textarea" :rows="9" :readonly="isReadOnly" aria-label="原始流程定义" />
          <el-button v-if="!isReadOnly" :disabled="isBusy || !!loadError" @click="applyDefinition">重新加载画布</el-button>
        </div>
      </aside>
    </div>

    <section v-if="isRunning || runResult || runError" class="run-result" aria-label="流程运行结果">
      <div class="result-toolbar">
        <h2>运行结果</h2>
        <el-button link :disabled="isRunning" @click="runResult = null; runError = ''">清空</el-button>
      </div>
      <div class="result-content">
        <p v-if="isRunning" class="designer-hint">正在运行…</p>
        <el-alert v-else-if="runError" :title="runError" type="error" :closable="false" show-icon />
        <pre v-else-if="runResult">{{ formatData(runResult.payload) }}</pre>
      </div>
    </section>
  </div>
</template>

<style scoped>
.workflow-editor { height: 100%; display: flex; flex-direction: column; background: #fff; }
.designer-heading, .designer-name, .designer-actions, .result-toolbar { display: flex; align-items: center; gap: 10px; }
.designer-heading { flex-shrink: 0; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #e4e7ed; flex-wrap: wrap; }
.designer-name { flex: 1; min-width: 260px; }
.designer-name .el-input { max-width: 300px; }
.designer-actions { flex-wrap: wrap; }
.designer-actions .el-button { margin: 0; }
.designer-alerts { flex-shrink: 0; max-height: 160px; overflow: auto; }
.designer-alerts .el-alert { border-radius: 0; }
.designer-workspace { flex: 1; min-height: 0; display: flex; }
.designer-sidebar, .designer-settings { flex-shrink: 0; padding: 20px 16px; overflow: auto; }
.designer-sidebar { width: 180px; border-right: 1px solid #e4e7ed; }
.designer-settings { width: 300px; border-left: 1px solid #e4e7ed; }
.designer-hint { color: #909399; font-size: 12px; line-height: 1.8; }
.palette-node { display: flex; align-items: center; gap: 10px; width: 100%; padding: 12px 10px; margin: 12px 0; border: 1px solid #e4e7ed; border-radius: 7px; background: #fff; text-align: left; cursor: grab; color: #303133; }
.palette-node:disabled { cursor: default; opacity: 0.65; }
.palette-node > span { color: var(--el-color-primary); font-size: 13px; width: 24px; }
.palette-node strong { font-size: 13px; font-weight: 500; }
.palette-node small { display: block; margin-top: 5px; color: #909399; font-size: 11px; line-height: 1.5; }
.designer-canvas { position: relative; flex: 1; min-width: 0; background-color: #fafbfe; background-image: radial-gradient(#d8dce6 1px, transparent 1px); background-size: 18px 18px; }
.canvas-empty { position: absolute; inset: 0; display: grid; place-items: center; color: #909399; font-size: 13px; pointer-events: none; }
.designer-node-id { font-size: 11px; color: #909399; line-height: 1.8; overflow-wrap: anywhere; }
.input-label { display: block; margin: 16px 0 10px; font-size: 13px; }
.definition-recovery { margin-top: 20px; }
.definition-recovery .el-textarea { margin: 12px 0; }
.run-result { flex-shrink: 0; height: 26vh; min-height: 120px; max-height: 40vh; display: flex; flex-direction: column; border-top: 1px solid #e4e7ed; }
.result-toolbar { flex-shrink: 0; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #ebeef5; }
.result-content { padding: 12px 20px; overflow: auto; }
.result-content pre { margin: 0; font-family: Consolas, monospace; font-size: 12px; line-height: 1.7; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 900px) {
  .designer-sidebar { width: 140px; padding: 16px 10px; }
  .designer-settings { width: 260px; }
  .designer-heading { padding: 10px; }
}
@media (max-width: 650px) {
  .designer-workspace { position: relative; }
  .designer-sidebar, .designer-settings { position: absolute; top: 0; bottom: 0; z-index: 5; background: #fff; box-shadow: 0 0 10px #0001; }
  .designer-sidebar { left: 0; }
  .designer-settings { right: 0; width: 240px; }
}
</style>
