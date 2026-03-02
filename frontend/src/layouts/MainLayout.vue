<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '200px'" class="aside">
      <div class="logo-container">
        <el-icon v-if="isCollapse" class="logo-icon"><Notebook /></el-icon>
        <span v-else class="logo-text">NeoReader</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :collapse="isCollapse"
        router
      >
        <el-menu-item index="/">
          <el-icon><Notebook /></el-icon>
          <template #title>书籍管理</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Notebook, Setting, Expand, Fold } from '@element-plus/icons-vue'

const isCollapse = ref(false)
const route = useRoute()

const activeMenu = computed(() => {
  if (route.path === '/settings') return '/settings'
  return '/'
})

const pageTitle = computed(() => {
  if (route.path === '/') return '书籍管理'
  if (route.path === '/settings') return '系统设置'
  return ''
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.aside {
  background-color: #fff;
  border-right: 1px solid #e6e6e6;
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #eee;
  background-color: #409eff;
  color: white;
}

.logo-text {
  font-weight: bold;
  font-size: 18px;
  white-space: nowrap;
}

.logo-icon {
  font-size: 24px;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.collapse-btn:hover {
  color: #409eff;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow: hidden; /* Prevent double scrollbar if content overflows */
  display: flex;
  flex-direction: column;
}
</style>
