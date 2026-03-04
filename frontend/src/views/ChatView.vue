<template>
  <div class="chat-layout">
    <!-- Sidebar -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" class="new-chat-btn" @click="startNewChat">
          <el-icon><Plus /></el-icon> 新会话
        </el-button>
      </div>
      <div class="session-list">
        <div 
          v-for="session in sessions" 
          :key="session.id" 
          class="session-item"
          :class="{ active: session.id === sessionId }"
          @click="switchSession(session.id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <el-icon class="delete-icon" @click.stop="handleDeleteSession(session.id)"><Delete /></el-icon>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="chat-main">
      <div class="chat-header">
        <span>AI 助手</span>
      </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { User, Service, ChatDotRound, Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { sendChatStream, getChatHistory, getChatSessions, deleteChatSession } from '../api/llm'
import { getSettings } from '../api/settings'
import { v4 as uuidv4 } from 'uuid'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Session {
  id: string
  title: string
}

const messages = ref<Message[]>([])
const sessions = ref<Session[]>([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const settings = ref<any>({})
const sessionId = ref('')

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadSessions = async () => {
  try {
    sessions.value = await getChatSessions()
  } catch (error) {
    console.error('Failed to load sessions:', error)
  }
}

const initSession = async () => {
  await loadSessions()
  const storedSessionId = localStorage.getItem('chat_session_id')
  
  if (storedSessionId && sessions.value.some(s => s.id === storedSessionId)) {
    sessionId.value = storedSessionId
    await loadHistory()
  } else if (sessions.value.length > 0) {
    // Default to the most recent session (assuming API returns in some order, or just first)
    // Actually, usually we might want to start a new chat or pick the first one.
    // Let's pick the first one for now if exists.
    sessionId.value = sessions.value[0].id
    localStorage.setItem('chat_session_id', sessionId.value)
    await loadHistory()
  } else {
    startNewChat()
  }
}

const switchSession = async (id: string) => {
  if (sessionId.value === id) return
  sessionId.value = id
  localStorage.setItem('chat_session_id', id)
  await loadHistory()
}

const startNewChat = async () => {
  const newSessionId = uuidv4()
  sessionId.value = newSessionId
  localStorage.setItem('chat_session_id', newSessionId)
  messages.value = []
  // Optionally add to sessions list immediately or wait until first message?
  // Let's wait until first message or just refresh list later.
  // Actually better to just clear messages. The session won't appear in list until saved in DB.
}

const handleDeleteSession = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除该会话吗？', '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    
    await deleteChatSession(id)
    ElMessage.success('会话已删除')
    await loadSessions()
    
    if (sessionId.value === id) {
      if (sessions.value.length > 0) {
        await switchSession(sessions.value[0].id)
      } else {
        startNewChat()
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete session:', error)
      ElMessage.error('删除失败')
    }
  }
}

const loadHistory = async () => {
  if (!sessionId.value) return
  try {
    const history = await getChatHistory(sessionId.value)
    messages.value = history
    await scrollToBottom()
  } catch (error) {
    console.error('Failed to load history:', error)
    ElMessage.error('加载历史记录失败')
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
        config_key: 'llm.provider.glm.api_key',
        prompt: content,
        temperature: 0.7,
        session_id: sessionId.value
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
    // Refresh session list to show new session title if it was new
    loadSessions()
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
  initSession()
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 100px);
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.chat-sidebar {
  width: 260px;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  background-color: #f9fafe;
}

.sidebar-header {
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
}

.new-chat-btn {
  width: 100%;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  color: #606266;
  transition: background-color 0.2s;
}

.session-item:hover {
  background-color: #e6e8eb;
}

.session-item.active {
  background-color: #ecf5ff;
  color: #409eff;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.delete-icon {
  margin-left: 8px;
  opacity: 0;
  transition: opacity 0.2s;
  color: #909399;
}

.session-item:hover .delete-icon {
  opacity: 1;
}

.delete-icon:hover {
  color: #f56c6c;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* Prevent flex child from overflowing */
}

.chat-container {
  /* Legacy class kept just in case, but structure changed */
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  color: #303133;
  height: 50px;
  box-sizing: border-box;
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
  min-width: 0; /* Allow text truncate inside if needed */
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
