<template>
  <div class="home-container">
    <div class="toolbar">
      <el-upload
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        accept=".txt"
      >
        <el-button type="primary">上传书籍</el-button>
      </el-upload>
    </div>

    <div class="content-wrapper">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="books.length === 0" class="empty-state">
        <el-empty description="暂无书籍，请点击上方按钮上传" />
      </div>
      <div v-else class="grid">
        <el-card
          v-for="book in books"
          :key="book.id"
          class="book-card"
          :body-style="{ padding: '0px' }"
          @click="openBook(book.id)"
        >
          <div class="book-cover">
            <span class="cover-text">{{ book.title.charAt(0) }}</span>
          </div>
          <div class="book-info">
            <div class="book-title">{{ book.title }}</div>
            <div class="book-meta">
              <span>{{ (book.file_size / 1024).toFixed(1) }} KB</span>
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                circle
                @click.stop="handleDelete(book.id)"
              />
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getBooks, uploadBook, deleteBook, type Book } from '../api/books'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const books = ref<Book[]>([])
const loading = ref(true)
const router = useRouter()

const fetchBooks = async () => {
  try {
    const res = await getBooks()
    books.value = res.data
  } catch (error) {
    ElMessage.error('获取书籍列表失败')
  } finally {
    loading.value = false
  }
}

const handleFileChange = async (file: any) => {
  if (!file.raw) return
  try {
    await uploadBook(file.raw)
    ElMessage.success('上传成功')
    fetchBooks()
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

const handleDelete = (id: number) => {
  ElMessageBox.confirm('确定要删除这本书吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteBook(id)
      ElMessage.success('删除成功')
      fetchBooks()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const openBook = (id: number) => {
  router.push(`/read/${id}`)
}

onMounted(fetchBooks)
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  padding-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.book-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.book-card:hover {
  transform: translateY(-5px);
}

.book-cover {
  height: 240px;
  background-color: #e0e0e0;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 64px;
  color: #fff;
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
}

.book-info {
  padding: 10px;
}

.book-title {
  font-size: 16px;
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 5px;
}

.book-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}
</style>
