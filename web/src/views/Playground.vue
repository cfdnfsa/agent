<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ChatPanel from '../components/ChatPanel.vue'
import { listModelConfigs, type ModelConfig } from '../api/modelConfigs'
import { askModel } from '../api/playground'

const modelOptions = ref<ModelConfig[]>([])
const selectedModelId = ref<number | null>(null)
const isLoading = ref(false)
const isSending = ref(false)
const loadError = ref('')

/** 复用现有分页接口读取模型，避免下拉框只能选到模型列表第一页。 */
async function loadModels(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    const firstPage = await listModelConfigs(1, 100)
    const loadedModels = [...firstPage.items]
    for (let page = 2; page <= Math.ceil(firstPage.total / 100); page++) {
      loadedModels.push(...(await listModelConfigs(page, 100)).items)
    }
    modelOptions.value = loadedModels
    if (!loadedModels.some(model => model.id === selectedModelId.value)) {
      selectedModelId.value = loadedModels[0]?.id ?? null
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '模型列表加载失败。'
  } finally {
    isLoading.value = false
  }
}

function submitQuestion(question: string): Promise<string> {
  if (selectedModelId.value === null) return Promise.reject(new Error('请先选择模型。'))
  return askModel(selectedModelId.value, question)
}

onMounted(() => loadModels())
</script>

<template>
  <div class="page-heading">
    <div><p class="eyebrow">模型调试</p><h1>调试台</h1><p class="page-description">选择一个模型，进行最基础的一问一答。</p></div>
  </div>
  <el-alert v-if="loadError" class="page-alert" :title="loadError" type="error" :closable="false" show-icon />
  <el-card shadow="never" class="model-panel">
    <template #header>
      <div class="playground-selector">
        <label for="playground-model">选择模型</label>
        <el-select
          id="playground-model" v-model="selectedModelId" filterable :loading="isLoading"
          :disabled="isLoading || isSending" placeholder="请选择已配置的模型" class="model-picker"
        >
          <el-option v-for="model in modelOptions" :key="model.id" :label="`${model.model_name} · ${model.model_code}`" :value="model.id" />
        </el-select>
        <el-button :loading="isLoading" :disabled="isSending" @click="loadModels">刷新模型</el-button>
      </div>
    </template>
    <p v-if="!isLoading && !loadError && modelOptions.length === 0" class="page-note">请先到“模型配置”页面添加模型。</p>
    <!-- 切换模型时重新创建展示组件，清空旧气泡，避免误以为存在上下文。 -->
    <ChatPanel
      :key="selectedModelId ?? 'no-model'" :disabled="isLoading || selectedModelId === null"
      :submit-question="submitQuestion" @busy-change="isSending = $event"
    />
  </el-card>
  <p class="page-note">问答内容仅在当前页面展示，不保存聊天记录；发送问题会产生真实模型调用。</p>
</template>
