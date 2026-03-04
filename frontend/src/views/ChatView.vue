<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <el-icon class="empty-icon"><ChatDotRound /></el-icon>
        <p>有什么我可以帮你的吗？</p>
      </div>
      
      <div 
        v-for="(msg, index) in messages" 
        :key="index" 
        class="message-wrapper"
        :class="{ 'user-message': msg.role === 'user', 'ai-message': msg.role === 'assistant' }"
      >
        <div class="avatar">
          <el-icon v-if="msg.role === 'user'"><User /></el-icon>
          <el-icon v-else><Service /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-bubble" v-if="msg.content || !loading || msg.role !== 'assistant'">
            {{ msg.content }}
          </div>
          <div class="message-bubble loading-bubble" v-else>
            <span class="dot">.</span>
            <span class="dot">.</span>
            <span class="dot">.</span>
          </div>
        </div>
      </div>
      

    </div>
    
    <div class="chat-input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          @keydown.enter.prevent="handleEnter"
          resize="none"
          :disabled="loading"
        />
        <div class="input-actions">
          <el-button type="primary" :loading="loading" @click="sendMessage" :disabled="!inputMessage.trim()">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { User, Service, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { sendChatStream } from '../api/llm'
import { getSettings } from '../api/settings'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const settings = ref<any>({})

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadConfig = async () => {
  try {
    const allSettings = await getSettings()
    // Flatten settings for easier access
    if (allSettings.model) {
      if (allSettings.model.provider) {
        allSettings.model.provider.forEach((s: any) => settings.value[s.key] = s.value)
      }
      if (allSettings.model.model) {
        allSettings.model.model.forEach((s: any) => settings.value[s.key] = s.value)
      }
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    ElMessage.error('加载配置失败，请确保已配置 API Key')
  }
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  sendMessage()
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || loading.value) return
  
  // Check configuration
  const apiKey = settings.value['llm.provider.glm.api_key']
  const modelName = settings.value['llm.model.glm.name'] || 'glm-4-flash'
  
  if (!apiKey) {
    ElMessage.warning('请先在系统设置中配置 GLM API Key')
    return
  }
  
  // Add user message
  messages.value.push({ role: 'user', content })
  inputMessage.value = ''
  loading.value = true
  await scrollToBottom()
  
  // Prepare AI message placeholder
  const aiMessageIndex = messages.value.push({ role: 'assistant', content: '' }) - 1
  
  try {
    await sendChatStream(
      {
        provider: 'glm',
        model: modelName,
        api_key: apiKey,
        prompt: content,
        temperature: 0.7
      },
      (chunk) => {
        // Update AI message content
        messages.value[aiMessageIndex].content += chunk
        scrollToBottom()
      },
      (error) => {
        console.error('Chat stream error:', error)
        ElMessage.error(error || '生成失败，请稍后重试')
        if (!messages.value[aiMessageIndex].content) {
          messages.value[aiMessageIndex].content = `[错误] ${error}`
        }
      }
    )
  } catch (error: any) {
    console.error('Chat error:', error)
    const errorMsg = error.message || '发送失败，请稍后重试'
    ElMessage.error(errorMsg)
    if (!messages.value[aiMessageIndex].content) {
      messages.value[aiMessageIndex].content = `[系统错误] ${errorMsg}`
    }
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px); /* Adjust based on header height */
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-wrapper.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.ai-message {
  align-self: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
  color: #606266;
  flex-shrink: 0;
}

.user-message .avatar {
  background-color: #409eff;
  color: #fff;
}

.ai-message .avatar {
  background-color: #67c23a;
  color: #fff;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
}

.user-message .message-bubble {
  background-color: #409eff;
  color: #fff;
  border-top-right-radius: 2px;
}

.ai-message .message-bubble {
  background-color: #f4f4f5;
  color: #303133;
  border-top-left-radius: 2px;
}

.loading-bubble {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.dot {
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  padding: 20px;
  border-top: 1px solid #e6e6e6;
  background-color: #fff;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
