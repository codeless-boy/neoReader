<template>
  <div class="settings-container">
    <h2>系统设置</h2>
    <el-form label-width="120px">
      <el-form-item label="存储路径">
        <el-input v-model="storagePath" disabled placeholder="默认: backend/static/uploads" />
        <div class="tip">目前仅支持默认路径</div>
      </el-form-item>
      <el-form-item label="主题模式">
        <el-radio-group v-model="theme">
          <el-radio label="light">浅色</el-radio>
          <el-radio label="dark">深色</el-radio>
          <el-radio label="auto">跟随系统</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const storagePath = ref('backend/static/uploads')
const theme = ref('light')

const saveSettings = () => {
  ElMessage.success('设置已保存')
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 600px;
}

.tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}
</style>
