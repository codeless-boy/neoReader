<template>
  <div class="reader-container" :style="containerStyle">
    <div class="reader-header" :class="{ 'header-hidden': !showToolbar }">
      <div class="header-left">
        <el-button @click="$router.push('/')" :icon="Back" circle plain />
        <el-button @click="drawerVisible = true" :icon="List" circle plain style="margin-left: 10px" />
        <span class="book-title">{{ book?.title }}</span>
      </div>
      <div class="header-right">
        <el-popover placement="bottom" :width="300" trigger="click">
          <template #reference>
            <el-button :icon="Setting" circle plain />
          </template>
          <div class="settings-panel">
            <div class="setting-item">
              <span class="label">字号</span>
              <div class="control">
                <el-button @click="fontSize = Math.max(14, fontSize - 2)" size="small" circle>-</el-button>
                <span class="value">{{ fontSize }}</span>
                <el-button @click="fontSize = Math.min(32, fontSize + 2)" size="small" circle>+</el-button>
              </div>
            </div>
            <div class="setting-item">
              <span class="label">主题</span>
              <div class="theme-options">
                <div 
                  v-for="(t, key) in themes" 
                  :key="key"
                  class="theme-option"
                  :style="{ backgroundColor: t.bg, border: `1px solid ${t.text}` }"
                  @click="currentThemeKey = key as string"
                  :class="{ active: currentThemeKey === key }"
                >
                  <span :style="{ color: t.text }">A</span>
                </div>
              </div>
            </div>
          </div>
        </el-popover>
      </div>
    </div>

    <div class="reader-content-wrapper" @click="toggleToolbar">
      <div class="paper-container" :style="paperStyle">
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在加载...</span>
        </div>
        
        <div v-else class="content-body">
          <h2 v-if="currentChapter" class="chapter-title">{{ currentChapter.title }}</h2>
          <div class="text-content">{{ content }}</div>
        </div>

        <div class="reader-footer" v-if="!loading && chapters.length > 0">
          <el-button 
            :disabled="!prevChapter" 
            @click.stop="prevChapter && jumpToChapter(prevChapter)"
            text
          >
            上一章
          </el-button>
          <el-button 
            :disabled="!nextChapter" 
            @click.stop="nextChapter && jumpToChapter(nextChapter)"
            text
          >
            下一章
          </el-button>
        </div>
      </div>
    </div>

    <el-drawer v-model="drawerVisible" title="目录" direction="ltr" size="320px" class="toc-drawer">
      <div v-if="chaptersLoading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>
      <div v-else class="chapter-list">
        <div
          v-for="chapter in chapters"
          :key="chapter.id"
          class="chapter-item"
          :class="{ active: currentChapter?.id === chapter.id }"
          @click="jumpToChapter(chapter)"
        >
          <span class="chapter-index">{{ chapter.ordering + 1 }}</span>
          <span class="chapter-name">{{ chapter.title }}</span>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getBook, getBookContent, getChapters, type Book, type Chapter } from '../api/books'
import { Back, Setting, List, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const bookId = Number(route.params.id)
const book = ref<Book>()
const content = ref('')
const loading = ref(false)
const showToolbar = ref(true)

// Chapters
const drawerVisible = ref(false)
const chapters = ref<Chapter[]>([])
const chaptersLoading = ref(false)
const currentChapter = ref<Chapter | null>(null)

// Computed next/prev chapters
const prevChapter = computed(() => {
  if (!currentChapter.value || chapters.value.length === 0) return null
  const index = chapters.value.findIndex(c => c.id === currentChapter.value?.id)
  if (index > 0) return chapters.value[index - 1]
  return null
})

const nextChapter = computed(() => {
  if (!currentChapter.value || chapters.value.length === 0) return null
  const index = chapters.value.findIndex(c => c.id === currentChapter.value?.id)
  if (index < chapters.value.length - 1) return chapters.value[index + 1]
  return null
})

// Settings
const fontSize = ref(18)
const currentThemeKey = ref('light')

const themes: Record<string, { bg: string, paper: string, text: string }> = {
  light: { bg: '#f5f7fa', paper: '#ffffff', text: '#2c3e50' },
  dark: { bg: '#121212', paper: '#1e1e1e', text: '#cfcfcf' },
  sepia: { bg: '#f4ecd8', paper: '#fffbf0', text: '#5b4636' },
  green: { bg: '#cce8cf', paper: '#e3f2e4', text: '#333333' }
}

const currentTheme = computed(() => themes[currentThemeKey.value])

const containerStyle = computed(() => ({
  backgroundColor: currentTheme.value.bg,
  color: currentTheme.value.text
}))

const paperStyle = computed(() => ({
  backgroundColor: currentTheme.value.paper,
  fontSize: `${fontSize.value}px`,
  color: currentTheme.value.text,
  boxShadow: currentThemeKey.value === 'dark' ? 'none' : '0 4px 20px rgba(0,0,0,0.05)'
}))

const toggleToolbar = () => {
  showToolbar.value = !showToolbar.value
}

const loadBookInfo = async () => {
  try {
    const res = await getBook(bookId)
    book.value = res.data
  } catch (error) {
    ElMessage.error('获取书籍信息失败')
  }
}

const loadChapters = async () => {
  chaptersLoading.value = true
  try {
    const res = await getChapters(bookId)
    chapters.value = res.data
    // Initialize first chapter if none selected
    if (chapters.value.length > 0 && !currentChapter.value) {
      currentChapter.value = chapters.value[0]
      loadChapterContent(chapters.value[0])
    } else if (chapters.value.length === 0) {
      loadFullContent()
    }
  } catch (error) {
    console.error('Failed to load chapters', error)
  } finally {
    chaptersLoading.value = false
  }
}

const loadChapterContent = async (chapter: Chapter) => {
  loading.value = true
  try {
    const index = chapters.value.findIndex(c => c.id === chapter.id)
    let limit = 100000 
    
    if (index < chapters.value.length - 1) {
      const nextC = chapters.value[index + 1]
      limit = nextC.start_offset - chapter.start_offset
    } else {
      limit = -1 
    }
    
    const res = await getBookContent(bookId, chapter.start_offset, limit === -1 ? 10000000 : limit)
    content.value = res.data.content
    
    // Scroll to top of content wrapper
    const wrapper = document.querySelector('.reader-content-wrapper')
    if (wrapper) wrapper.scrollTop = 0
  } catch (error) {
    ElMessage.error('加载章节内容失败')
  } finally {
    loading.value = false
  }
}

const loadFullContent = async () => {
  loading.value = true
  try {
    const res = await getBookContent(bookId, 0, 100000)
    content.value = res.data.content
  } catch (error) {
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
  }
}

const jumpToChapter = async (chapter: Chapter) => {
  drawerVisible.value = false
  currentChapter.value = chapter
  await loadChapterContent(chapter)
}

watch(() => route.params.id, (newId) => {
  if (newId) {
    book.value = undefined
    content.value = ''
    currentChapter.value = null
    chapters.value = []
    loadBookInfo()
    loadChapters()
  }
})

onMounted(() => {
  loadBookInfo()
  loadChapters()
})
</script>

<style scoped>
.reader-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: background-color 0.3s, color 0.3s;
  position: relative;
}

.reader-header {
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 1px 10px rgba(0,0,0,0.05);
  transition: transform 0.3s ease;
}

.header-hidden {
  transform: translateY(-100%);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.book-title {
  font-weight: 600;
  font-size: 16px;
  color: #333;
  margin-left: 10px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding-top: 60px; /* Space for header */
  scroll-behavior: smooth;
  display: block; /* Use block layout instead of flex to ensure height expansion */
}

.paper-container {
  width: 100%;
  max-width: 800px;
  min-height: calc(100vh - 100px);
  margin: 20px auto; /* Center horizontally */
  padding: 60px 80px;
  border-radius: 8px;
  transition: all 0.3s ease;
  position: relative;
  box-sizing: border-box;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: inherit;
  opacity: 0.6;
  gap: 10px;
}

.chapter-title {
  font-size: 1.5em;
  font-weight: bold;
  margin-bottom: 40px;
  text-align: center;
  opacity: 0.9;
}

.content-body {
  width: 100%;
  max-width: 100%;
}

.text-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  font-family: 'Georgia', 'Microsoft YaHei', serif;
  line-height: 1.8;
  text-align: justify;
  max-width: 100%;
}

.reader-footer {
  margin-top: 60px;
  padding-top: 40px;
  border-top: 1px solid rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-between;
}

/* Settings Panel */
.settings-panel {
  padding: 10px;
}

.setting-item {
  margin-bottom: 15px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-item .label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.setting-item .control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #f5f7fa;
  padding: 5px 10px;
  border-radius: 20px;
}

.setting-item .value {
  font-weight: bold;
  font-size: 14px;
}

.theme-options {
  display: flex;
  gap: 10px;
}

.theme-option {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.theme-option:hover {
  transform: scale(1.1);
}

.theme-option.active {
  box-shadow: 0 0 0 2px #409eff;
}

/* Drawer Styles */
.chapter-list {
  padding: 10px 0;
}

.chapter-item {
  padding: 12px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  display: flex;
  align-items: center;
  transition: background-color 0.2s;
}

.chapter-item:hover {
  background-color: #f9f9f9;
}

.chapter-item.active {
  color: #409eff;
  background-color: #ecf5ff;
  font-weight: 500;
}

.chapter-index {
  font-size: 12px;
  color: #999;
  width: 40px;
  flex-shrink: 0;
}

.chapter-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 768px) {
  .paper-container {
    margin: 0;
    padding: 30px 20px;
    border-radius: 0;
    min-height: 100vh;
  }
  
  .reader-content-wrapper {
    padding-top: 56px;
  }
  
  .reader-header {
    background-color: #fff;
  }
}
</style>
