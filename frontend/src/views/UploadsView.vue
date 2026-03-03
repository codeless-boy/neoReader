<template>
  <div class="uploads-container">
    <div class="header">
      <h2>上传记录</h2>
      <el-button @click="fetchBooks" :icon="Refresh" circle />
    </div>

    <el-table :data="books" style="width: 100%" v-loading="loading">
      <el-table-column prop="title" label="书名" min-width="150" />
      <el-table-column prop="file_size" label="大小" width="100">
        <template #default="scope">
          {{ formatFileSize(scope.row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="added_at" label="上传时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.added_at) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="300">
        <template #default="scope">
          <!-- Pending Status -->
          <el-tag v-if="scope.row.status === 'pending'" type="info">等待处理</el-tag>
          
          <!-- Success Status -->
          <el-tag v-else-if="scope.row.status === 'success'" type="success">处理完成</el-tag>
          
          <!-- Processing Status with Steps -->
          <div v-else-if="scope.row.status === 'processing'" class="processing-steps">
            <el-steps :active="getStepActive(scope.row.processing_stage)" finish-status="success" simple size="small">
              <el-step title="初始化" />
              <el-step title="编码检测" />
              <el-step title="章节解析" />
              <el-step title="完成" />
            </el-steps>
          </div>
          
          <!-- Failed Status with Error Steps -->
          <div v-else-if="scope.row.status === 'failed'" class="failed-status">
            <el-popover
              placement="top-start"
              title="错误详情"
              :width="300"
              trigger="hover"
              :content="scope.row.error_message || '未知错误'"
            >
              <template #reference>
                <div class="processing-steps">
                  <el-steps :active="getStepActive(scope.row.failed_stage)" finish-status="success" process-status="error" simple size="small">
                    <el-step title="初始化" />
                    <el-step title="编码检测" />
                    <el-step title="章节解析" />
                    <el-step title="完成" />
                  </el-steps>
                </div>
              </template>
            </el-popover>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="scope">
          <el-button 
            v-if="scope.row.status === 'success'"
            type="primary" 
            link 
            @click="$router.push(`/read/${scope.row.id}`)"
          >
            阅读
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getBooks, type Book, type ProcessingStage } from '../api/books'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const books = ref<Book[]>([])
const loading = ref(true)
let pollInterval: number | null = null

const fetchBooks = async () => {
  try {
    const res = await getBooks(0, 50) // Get latest 50 books
    books.value = res.data
    
    // Check if we need to poll
    const hasProcessing = books.value.some(b => b.status === 'processing' || b.status === 'pending')
    if (hasProcessing && !pollInterval) {
      startPolling()
    } else if (!hasProcessing && pollInterval) {
      stopPolling()
    }
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  pollInterval = window.setInterval(async () => {
    try {
      const res = await getBooks(0, 50)
      books.value = res.data
      const hasProcessing = books.value.some(b => b.status === 'processing' || b.status === 'pending')
      if (!hasProcessing) {
        stopPolling()
      }
    } catch (e) {
      // Silent error during polling
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const formatFileSize = (size: number) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

const getStepActive = (stage?: ProcessingStage) => {
  if (!stage) return 0
  switch (stage) {
    case 'init': return 0
    case 'encoding': return 1
    case 'parsing': return 2
    case 'completed': return 3
    default: return 0
  }
}

const getFailedStageText = (stage?: ProcessingStage) => {
  switch (stage) {
    case 'init': return '初始化失败'
    case 'encoding': return '编码检测失败'
    case 'parsing': return '章节解析失败'
    case 'completed': return '保存失败'
    default: return '未知阶段'
  }
}

onMounted(() => {
  fetchBooks()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.uploads-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  min-height: calc(100vh - 100px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.processing-steps {
  width: 100%;
  max-width: 400px;
}

.error-steps {
  display: flex;
  align-items: center;
  cursor: help;
}

.error-stage-text {
  font-size: 13px;
  color: #f56c6c;
}
</style>
