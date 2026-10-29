<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position, type NodeProps } from '@vue-flow/core'
import { workflowNodeLabel, workflowNodeTypes, type WorkflowCanvasNodeData } from './workflowNodes'

const props = defineProps<NodeProps<WorkflowCanvasNodeData> & { canRun: boolean; running: boolean }>()
const emit = defineEmits<{ run: [] }>()
const nodeType = computed(() => props.data.definition.type)
const nodeName = computed(() => props.data.definition.name || workflowNodeLabel(nodeType.value))
const badge = computed(() => workflowNodeTypes.find(item => item.type === nodeType.value)?.badge ?? '节')
</script>

<template>
  <div class="workflow-node" :class="[`workflow-node-${nodeType}`, { 'is-selected': selected }]">
    <button v-if="nodeType === 'start'" class="run-trigger nodrag nopan" type="button" :disabled="!canRun" aria-label="运行流程" title="运行流程" @click.stop="emit('run')">{{ running ? '…' : '▶' }}</button>
    <Handle v-if="nodeType !== 'start'" type="target" :position="Position.Left" :connectable="connectable" />
    <div class="workflow-node-title"><span class="workflow-node-badge">{{ badge }}</span><span class="workflow-node-label" :title="nodeName">{{ nodeName }}</span></div>
    <div class="workflow-node-id" :title="id">{{ id }}</div>
    <Handle v-if="nodeType !== 'return'" type="source" :position="Position.Right" :connectable="connectable" />
  </div>
</template>

<style scoped>
.workflow-node { width: 190px; padding: 14px 16px; border: 1px solid #dcdfe6; border-radius: 9px; background: #fff; box-shadow: 0 3px 12px #3031330a; }
.workflow-node.is-selected { border-color: var(--el-color-primary); box-shadow: 0 0 0 2px var(--el-color-primary-light-8); }
.workflow-node-title { display: flex; align-items: center; gap: 9px; font-size: 14px; font-weight: 600; }
.workflow-node-label { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.workflow-node-badge { display: grid; place-items: center; flex-shrink: 0; width: 27px; height: 27px; border-radius: 6px; background: var(--el-color-primary-light-9); color: var(--el-color-primary); font-size: 12px; }
.workflow-node-start .workflow-node-badge { background: #ecf5ff; color: #409eff; }
.workflow-node-return .workflow-node-badge { background: #f0f9eb; color: #67c23a; }
.run-trigger { position: absolute; right: calc(100% + 9px); top: 22px; width: 30px; height: 30px; border: 1px solid #67c23a; border-radius: 6px; color: #529b2e; background: #f0f9eb; cursor: pointer; }
.run-trigger:disabled { opacity: 0.5; cursor: default; }
.workflow-node-id { margin-top: 9px; color: #909399; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.workflow-node :deep(.vue-flow__handle) { width: 9px; height: 9px; border: 2px solid #fff; background: var(--el-color-primary); }
</style>
