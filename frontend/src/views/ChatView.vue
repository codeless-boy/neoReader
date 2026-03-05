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
        <span class="chat-title">AI 助手</span>
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
      
      <!-- Trae-like Input Area -->
      <div class="chat-input-container">
        <!-- Context Pills -->
        <div class="context-pills" v-if="selectedBookId">
          <div class="context-pill">
            <el-icon><Notebook /></el-icon>
            <span class="pill-text">{{ selectedBookTitle }}</span>
            <el-icon class="close-icon" @click="clearBookSelection"><Close /></el-icon>
          </div>
        </div>

        <div class="input-box-wrapper" :class="{ 'has-context': !!selectedBookId }">
          <div class="input-controls-left">
            <el-popover
              placement="top-start"
              :width="320"
              trigger="click"
              v-model:visible="bookSelectorVisible"
              popper-class="book-selector-popover"
            >
              <template #reference>
                <el-button class="add-context-btn" circle text title="添加书籍上下文">
                  <el-icon><Plus /></el-icon>
                </el-button>
              </template>
              
              <div class="book-selector-content">
                <div class="selector-header">
                  <el-input 
                    v-model="bookSearchQuery" 
                    placeholder="搜索书籍..." 
                    prefix-icon="Search" 
                    size="small" 
                    clearable
                  />
                </div>
                <div class="book-list">
                  <div 
                    v-for="book in filteredBooks" 
                    :key="book.id" 
                    class="book-item"
                    :class="{ active: book.id === selectedBookId }"
                    @click="selectBook(book.id)"
                  >
                    <div class="book-item-icon">
                      <el-icon><Notebook /></el-icon>
                    </div>
                    <div class="book-item-info">
                      <div class="book-item-title">{{ book.title }}</div>
                      <div class="book-item-meta">{{ formatSize(book.file_size) }}</div>
                    </div>
                    <el-icon v-if="book.id === selectedBookId" class="check-icon"><Check /></el-icon>
                  </div>
                  <div v-if="filteredBooks.length === 0" class="no-books">
                    <el-empty description="暂无相关书籍" :image-size="60" />
                  </div>
                </div>
              </div>
            </el-popover>
          </div>
          
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="输入消息... (Shift+Enter 换行)"
            @keydown.enter.prevent="handleEnter"
            resize="none"
            :disabled="loading"
            class="trae-input"
          />
          
          <div class="input-controls-right">
            <el-button 
              type="primary" 
              class="send-btn" 
              :loading="loading" 
              @click="sendMessage" 
              :disabled="!inputMessage.trim()"
              circle
            >
              <el-icon><Position /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="footer-info">
          <span>模型: GLM-4-Flash</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { User, Service, ChatDotRound, Plus, Delete, Notebook, Close, Search, Check, Position } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { sendChatStream, getChatHistory, getChatSessions, deleteChatSession } from '../api/llm'
import { getSettings } from '../api/settings'
import { getBooks, type Book } from '../api/books'
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
const books = ref<Book[]>([])
const selectedBookId = ref<number | undefined>(undefined)
const bookSearchQuery = ref('')
const bookSelectorVisible = ref(false)

const selectedBookTitle = computed(() => {
  if (!selectedBookId.value) return ''
  const book = books.value.find(b => b.id === selectedBookId.value)
  return book ? book.title : ''
})

const filteredBooks = computed(() => {
  if (!bookSearchQuery.value) return books.value
  const query = bookSearchQuery.value.toLowerCase()
  return books.value.filter(b => b.title.toLowerCase().includes(query))
})

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const selectBook = (id: number) => {
  selectedBookId.value = id
  bookSelectorVisible.value = false
}

const clearBookSelection = (e?: Event) => {
  if (e) e.stopPropagation()
  selectedBookId.value = undefined
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadBooks = async () => {
  try {
    const res = await getBooks()
    books.value = res.data
  } catch (error) {
    console.error('Failed to load books:', error)
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
  
  const apiKey = settings.value['llm.provider.glm.api_key']
  const modelName = settings.value['llm.model.glm.name'] || 'glm-4-flash'
  
  if (!apiKey) {
    ElMessage.warning('请先在系统设置中配置 GLM API Key')
    return
  }
  
  messages.value.push({ role: 'user', content })
  inputMessage.value = ''
  loading.value = true
  await scrollToBottom()
  
  const aiMessageIndex = messages.value.push({ role: 'assistant', content: '' }) - 1
  
  try {
    await sendChatStream(
      {
        provider: 'glm',
        model: modelName,
        config_key: 'llm.provider.glm.api_key',
        prompt: content,
        temperature: 0.7,
        session_id: sessionId.value,
        book_id: selectedBookId.value
      },
      (chunk) => {
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
  loadBooks()
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
  min-width: 0;
  position: relative;
}

.chat-header {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  color: #303133;
  height: 60px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20px 100px 20px; /* Add padding at bottom for input area */
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
  max-width: 85%;
}

.message-wrapper.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.ai-message {
  align-self: flex-start;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 4px; /* Square with rounded corners like IDEs */
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
  min-width: 0;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.user-message .message-bubble {
  background-color: #ecf5ff; /* Lighter blue for user */
  color: #303133;
  border: 1px solid #d9ecff;
}

.ai-message .message-bubble {
  background-color: transparent; /* IDE style often transparent for AI */
  padding-left: 0;
  color: #303133;
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

/* Trae-like Input Area Styles */
.chat-input-container {
  padding: 20px;
  background-color: #fff;
  border-top: 1px solid #ebeef5;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
}

.context-pills {
  margin-bottom: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.context-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #ecf5ff;
  color: #409eff;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 12px;
  border: 1px solid #d9ecff;
}

.pill-text {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close-icon {
  cursor: pointer;
  font-size: 12px;
  opacity: 0.6;
}

.close-icon:hover {
  opacity: 1;
}

.input-box-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 12px;
  padding: 8px 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
  background-color: #fff;
}

.input-box-wrapper:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.input-controls-left {
  display: flex;
  align-items: center;
  padding-bottom: 2px;
}

.add-context-btn {
  font-size: 16px;
  color: #909399;
  padding: 6px;
}

.add-context-btn:hover {
  color: #409eff;
  background-color: #f0f2f5;
}

.trae-input {
  flex: 1;
}

.trae-input :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 6px 0;
  resize: none;
  background-color: transparent;
  max-height: 200px;
}

.input-controls-right {
  display: flex;
  align-items: center;
  padding-bottom: 2px;
}

.send-btn {
  width: 32px;
  height: 32px;
  min-height: 32px;
  padding: 0;
}

.footer-info {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

/* Book Selector Popover Styles */
.book-selector-content {
  display: flex;
  flex-direction: column;
  max-height: 300px;
}

.selector-header {
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f2f5;
  margin-bottom: 5px;
}

.book-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.book-item:hover {
  background-color: #f5f7fa;
}

.book-item.active {
  background-color: #ecf5ff;
}

.book-item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f0f2f5;
  border-radius: 4px;
  color: #909399;
}

.book-item.active .book-item-icon {
  background-color: #d9ecff;
  color: #409eff;
}

.book-item-info {
  flex: 1;
  min-width: 0;
}

.book-item-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.book-item.active .book-item-title {
  color: #409eff;
}

.book-item-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.check-icon {
  color: #409eff;
}

.no-books {
  padding: 20px 0;
  display: flex;
  justify-content: center;
}
</style>
