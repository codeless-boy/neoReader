<template>
  <el-container class="settings-container">
    <el-aside width="200px" class="settings-aside">
      <el-menu
        :default-active="activeCategory"
        class="settings-menu"
        @select="handleSelect"
      >
        <el-menu-item 
          v-for="(groups, category) in settingsTree" 
          :key="category" 
          :index="category"
        >
          <el-icon>
            <component :is="getIcon(category)" />
          </el-icon>
          <span>{{ formatCategory(category) }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-main class="settings-main">
      <div v-if="activeCategory && settingsTree[activeCategory]">
        <div class="category-header">
          <h2 class="category-title">{{ formatCategory(activeCategory) }}</h2>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
        </div>
        
        <div 
          v-for="(settings, group) in settingsTree[activeCategory]" 
          :key="group" 
          class="settings-group"
        >
          <el-card class="group-card">
            <template #header>
              <div class="card-header">
                <span>{{ formatGroup(group) }}</span>
              </div>
            </template>
            
            <el-form label-position="top">
              <el-form-item 
                v-for="setting in settings" 
                :key="setting.key" 
                :label="setting.label"
              >
                <!-- Select -->
                <el-select 
                  v-if="setting.field_type === 'select'" 
                  v-model="setting.value" 
                >
                  <el-option
                    v-for="opt in parseOptions(setting.options)"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                
                <!-- Text / Number -->
                <el-input 
                  v-else-if="['text', 'number'].includes(setting.field_type)"
                  v-model="setting.value"
                  :type="setting.key.includes('api_key') ? 'password' : (setting.field_type === 'number' ? 'number' : 'text')"
                  :show-password="setting.key.includes('api_key')"
                />
                
                <!-- Boolean (Switch) -->
                <el-switch
                  v-else-if="setting.field_type === 'boolean'"
                  v-model="setting.value"
                  active-value="true"
                  inactive-value="false"
                />
                
                <!-- Readonly -->
                <el-input 
                  v-else-if="setting.field_type === 'readonly'"
                  v-model="setting.value"
                  disabled
                />
                
                <div v-if="setting.description" class="setting-desc">
                  {{ setting.description }}
                </div>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Monitor, 
  Folder, 
  Reading, 
  Setting, 
  Brush,
  Cpu
} from '@element-plus/icons-vue'
import { getSettings, updateSetting, type SettingsTree, type SystemSetting } from '../api/settings'

const settingsTree = ref<SettingsTree>({})
const activeCategory = ref('')

const iconMap: Record<string, any> = {
  appearance: Brush,
  storage: Folder,
  reader: Reading,
  system: Setting,
  model: Cpu
}

const getIcon = (category: string) => {
  return iconMap[category] || Setting
}

const formatCategory = (category: string) => {
  const map: Record<string, string> = {
    appearance: '外观设置',
    storage: '存储管理',
    reader: '阅读器',
    system: '系统信息',
    model: '模型设置'
  }
  return map[category] || category.charAt(0).toUpperCase() + category.slice(1)
}

const formatGroup = (group: string) => {
  const map: Record<string, string> = {
    provider: '服务商',
    model: '模型',
    Theme: '主题',
    Library: '书库',
    Display: '显示'
  }
  return map[group] || group
}

const parseOptions = (optionsStr?: string) => {
  if (!optionsStr) return []
  try {
    return JSON.parse(optionsStr)
  } catch (e) {
    console.error('Failed to parse options', e)
    return []
  }
}

const loadSettings = async () => {
  try {
    settingsTree.value = await getSettings()
    // Set first category as active if none selected
    if (!activeCategory.value && Object.keys(settingsTree.value).length > 0) {
      activeCategory.value = Object.keys(settingsTree.value)[0]
    }
  } catch (error) {
    ElMessage.error('加载设置失败')
    console.error(error)
  }
}

const handleSelect = (index: string) => {
  activeCategory.value = index
}

const saveSettings = async () => {
  if (!activeCategory.value || !settingsTree.value[activeCategory.value]) return
  
  try {
    const currentCategorySettings = settingsTree.value[activeCategory.value]
    const promises: Promise<any>[] = []
    
    // Collect all settings in current category
    Object.values(currentCategorySettings).forEach(settings => {
      settings.forEach(setting => {
        // Skip readonly settings
        if (setting.field_type !== 'readonly') {
          promises.push(updateSetting(setting.key, String(setting.value)))
        }
      })
    })
    
    await Promise.all(promises)
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
    // Reload to ensure consistency
    await loadSettings()
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-container {
  height: 100%;
  background-color: #f5f7fa;
}

.settings-aside {
  background-color: #fff;
  border-right: 1px solid #e6e6e6;
}

.settings-menu {
  border-right: none;
}

.settings-main {
  padding: 20px;
  overflow-y: auto;
}

.category-title {
  margin-bottom: 20px;
  font-size: 24px;
  color: #303133;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.category-header .category-title {
  margin-bottom: 0;
}

.settings-group {
  margin-bottom: 20px;
}

.group-card {
  margin-bottom: 20px;
}

.setting-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
