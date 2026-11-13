<script setup lang="ts">
import { nextTick, ref } from 'vue'

const props = defineProps<{
  disabled: boolean
  submitQuestion: (question: string) => Promise<string>
}>()
const emit = defineEmits<{ busyChange: [isBusy: boolean] }>()
const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
const question = ref('')
const isSending = ref(false)
const sendError = ref('')
const messageContainer = ref<HTMLElement>()

async function scrollToBottom(): Promise<void> {
  await nextTick()
  messageContainer.value?.scrollTo({ top: messageContainer.value.scrollHeight })
}

/** 气泡只用于展示；交给调用方的永远只有当前问题，便于以后复用到流程调试。 */
async function sendQuestion(): Promise<void> {
  const currentQuestion = question.value
  if (props.disabled || isSending.value) return
  isSending.value = true
  emit('busyChange', true)
  sendError.value = ''
  messages.value.push({ role: 'user', content: currentQuestion })
  void scrollToBottom()
  try {
    const answer = await props.submitQuestion(currentQuestion)
    messages.value.push({ role: 'assistant', content: answer })
    question.value = ''
  } catch (error) {
    // 失败时保留输入框内容，撤回这次未完成的气泡；用户可再次点击发送重试。
    messages.value.pop()
    sendError.value = error instanceof Error ? error.message : '回答失败，请稍后重试。'
  } finally {
    isSending.value = false
    emit('busyChange', false)
    void scrollToBottom()
  }
}

function clearMessages(): void {
  messages.value = []
  question.value = ''
  sendError.value = ''
}
</script>

<template>
  <section class="chat-panel" aria-label="单轮问答">
    <div class="chat-toolbar">
      <span>每次提问独立处理，不携带历史消息。</span>
      <el-button text :disabled="isSending" @click="clearMessages">清空</el-button>
    </div>
    <div ref="messageContainer" class="chat-messages" role="log" aria-label="问答内容" aria-live="polite">
      <el-empty v-if="messages.length === 0" :image-size="80" description="选择模型，开始提问吧" />
      <article v-for="(message, index) in messages" :key="index" class="chat-message" :class="message.role">
        <span class="chat-role">{{ message.role === 'user' ? '你' : '回答' }}</span>
        <!-- 直接渲染纯文本，保留换行，不将模型输出作为 HTML 执行。 -->
        <div class="chat-bubble">{{ message.content }}</div>
      </article>
      <p v-if="isSending" class="chat-pending" role="status">正在回答…</p>
    </div>
    <el-alert v-if="sendError" :title="sendError" type="error" :closable="false" show-icon />
    <form class="chat-composer" @submit.prevent="sendQuestion">
      <el-input
        v-model="question" type="textarea" :autosize="{ minRows: 3, maxRows: 7 }"
        :disabled="disabled || isSending"
        placeholder="输入你的问题…" aria-label="当前问题"
      />
      <div class="chat-send">
        <el-button type="primary" native-type="submit" :loading="isSending" :disabled="disabled">发送</el-button>
      </div>
    </form>
  </section>
</template>
