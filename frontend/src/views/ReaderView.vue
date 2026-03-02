<template>
  <div class="reader-container" :style="{ fontSize: fontSize + 'px', backgroundColor: theme.bg, color: theme.text }">
    <div class="toolbar" :style="{ backgroundColor: theme.bg, borderBottomColor: theme.text + '20' }">
      <el-button @click="$router.push('/')" :icon="Back" circle />
      <span class="book-title">{{ book?.title }}</span>
      <div class="settings">
        <el-button-group>
          <el-button @click="fontSize = Math.max(12, fontSize - 2)" size="small">A-</el-button>
          <el-button @click="fontSize = Math.min(32, fontSize + 2)" size="small">A+</el-button>
        </el-button-group>
        <el-dropdown trigger="click" @command="handleThemeChange" style="margin-left: 10px">
          <el-button circle :icon="Setting" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="light">亮色</el-dropdown-item>
              <el-dropdown-item command="dark">暗色</el-dropdown-item>
              <el-dropdown-item command="sepia">护眼</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="content-area" ref="contentArea">
      <div class="text-content">{{ content }}</div>
      <div class="pagination">
        <el-button v-if="hasMore" @click="loadMore" :loading="loading" type="primary" plain>加载更多</el-button>
        <span v-else class="end-text">--- 完 ---</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { getBook, getBookContent, type Book } from '../api/books'
import { Back, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const bookId = Number(route.params.id)
const book = ref<Book>()
const content = ref('')
const loading = ref(false)
const hasMore = ref(true)
const currentOffset = ref(0)
const chunkSize = 10000

// Settings
const fontSize = ref(18)
const theme = reactive({ bg: '#ffffff', text: '#333333' })

const themes: Record<string, { bg: string, text: string }> = {
  light: { bg: '#ffffff', text: '#333333' },
  dark: { bg: '#1a1a1a', text: '#cccccc' },
  sepia: { bg: '#f4ecd8', text: '#5b4636' }
}

const handleThemeChange = (command: string) => {
  const t = themes[command]
  if (t) {
    theme.bg = t.bg
    theme.text = t.text
  }
}

const loadBookInfo = async () => {
  try {
    const res = await getBook(bookId)
    book.value = res.data
  } catch (error) {
    ElMessage.error('获取书籍信息失败')
  }
}

const loadMore = async () => {
  if (loading.value || !hasMore.value) return
  loading.value = true
  try {
    const res = await getBookContent(bookId, currentOffset.value, chunkSize)
    content.value += res.data.content
    hasMore.value = res.data.has_more
    currentOffset.value += chunkSize
  } catch (error) {
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadBookInfo()
  loadMore()
})
</script>

<style scoped>
.reader-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: background-color 0.3s, color 0.3s;
}

.toolbar {
  height: 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  z-index: 10;
}

.book-title {
  font-weight: bold;
  font-size: 16px;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 10%; /* Responsive padding */
  scroll-behavior: smooth;
}

.text-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.8;
  padding-bottom: 20px;
}

.pagination {
  padding: 20px 0 40px;
  text-align: center;
}

.end-text {
  opacity: 0.6;
}

@media (max-width: 768px) {
  .content-area {
    padding: 20px 5%;
  }
}
</style>
