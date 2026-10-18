<template>
  <div class="script-list">
    <div class="page-header">
      <h1 class="page-title">{{ $t('uiAutomation.script.title') }}</h1>
      <div class="header-actions">
        <el-select v-model="selectedProject" :placeholder="$t('uiAutomation.common.selectProject')" style="width: 200px; margin-right: 15px" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" @click="openRecording">
          <el-icon><Plus /></el-icon>
          {{ $t('uiAutomation.recording.recordScript') }}
        </el-button>
        <el-button type="primary" plain :loading="uploadingScript" @click="openUpload">
          <el-icon><Upload /></el-icon>
          {{ $t('uiAutomation.script.uploadScript') }}
        </el-button>
        <input
          ref="scriptFileInput"
          class="script-file-input"
          type="file"
          accept=".py"
          @change="handleScriptFileChange"
        >
      </div>
    </div>

    <div class="main-content">
      <el-table :data="scripts" stripe style="width: 100%">
        <el-table-column type="index" :label="$t('uiAutomation.script.index')" width="60" />
        <el-table-column :label="$t('uiAutomation.script.projectColumn')" width="150">
          <template #default="{ row }">
            {{ row.project?.name || $t('uiAutomation.script.unknownProject') }}
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('uiAutomation.script.nameColumn')" min-width="300" show-overflow-tooltip />
        <el-table-column :label="$t('uiAutomation.script.languageColumn')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.language === 'python' ? 'success' : 'primary'">
              {{ getLanguageText(row.language) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('uiAutomation.script.frameworkColumn')" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.framework === 'playwright' ? 'warning' : 'info'">
              {{ getFrameworkText(row.framework) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('uiAutomation.script.createTimeColumn')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('uiAutomation.script.operationColumn')" width="410" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" text type="primary" @click="replayScript(row)">
                <el-icon><VideoPlay /></el-icon>
                {{ $t('uiAutomation.replay.button') }}
              </el-button>
              <el-button size="small" text type="primary" @click="historyScript(row)">
                <el-icon><Clock /></el-icon>
                {{ $t('uiAutomation.history.button') }}
              </el-button>
              <el-button size="small" text @click="viewScript(row)">
                <el-icon><View /></el-icon>
                {{ $t('uiAutomation.script.viewDetail') }}
              </el-button>
              <el-button size="small" text @click="editScript(row)">
                <el-icon><Edit /></el-icon>
                {{ $t('uiAutomation.script.edit') }}
              </el-button>
              <el-tooltip :content="$t('uiAutomation.script.delete')">
                <el-button size="small" text type="danger" :aria-label="$t('uiAutomation.script.delete')" @click="deleteScript(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="showDetailDialog" :title="$t('uiAutomation.script.scriptDetail')" width="70%">
      <div v-if="currentScript" class="script-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('uiAutomation.script.scriptName')" :span="2">{{ currentScript.name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.script.project')">{{ currentScript.project?.name || $t('uiAutomation.script.unknownProject') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.script.language')">{{ getLanguageText(currentScript.language) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.script.framework')">{{ getFrameworkText(currentScript.framework) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.script.scriptType')">{{ getScriptTypeText(currentScript.script_type) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.script.createTime')" :span="2">{{ formatTime(currentScript.created_at) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.script.updateTime')" :span="2">{{ formatTime(currentScript.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="script-content">
          <h4>{{ $t('uiAutomation.script.scriptContent') }}</h4>
          <pre class="code-view">{{ currentScript.content || $t('uiAutomation.script.noContent') }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">{{ $t('uiAutomation.script.close') }}</el-button>
        <el-button type="primary" @click="editScript(currentScript)">{{ $t('uiAutomation.script.editScript') }}</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" :title="$t('uiAutomation.script.editScript')" width="80%" :close-on-click-modal="false">
      <div v-if="editingScript" class="script-editor">
        <el-form label-position="top" class="edit-script-name">
          <el-form-item :label="$t('uiAutomation.script.scriptName')">
            <el-input v-model="editingScript.name" maxlength="200" show-word-limit />
          </el-form-item>
        </el-form>
        <div class="editor-container">
          <textarea
            v-model="editingScript.content"
            class="code-editor"
            :placeholder="$t('uiAutomation.script.scriptEditorPlaceholder')"
            spellcheck="false"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="showEditDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
        <el-button type="primary" @click="saveEditedScript" :loading="saving">{{ $t('uiAutomation.script.save') }}</el-button>
      </template>
    </el-dialog>

    <RecordingWizard v-model:visible="recordingVisible" :project-id="selectedProject" @imported="openImportedScript" />
    <ScriptReplayDialog v-model:visible="replayVisible" :script="currentScript" />
    <ScriptHistoryDialog v-model:visible="historyVisible" :script="currentScript" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete, VideoPlay, Clock, Upload } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import {
  getUiProjects,
  getTestScripts,
  updateTestScript,
  deleteTestScript,
  importRecordedScript
} from '@/api/ui_automation'
import RecordingWizard from './RecordingWizard.vue'
import ScriptReplayDialog from './ScriptReplayDialog.vue'
import ScriptHistoryDialog from './ScriptHistoryDialog.vue'

const router = useRouter()
const { t } = useI18n()

// 响应式数据
const projects = ref([])
const selectedProject = ref('')
const scripts = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 对话框控制
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const recordingVisible = ref(false)
const replayVisible = ref(false)
const historyVisible = ref(false)
const scriptFileInput = ref(null)
const uploadingScript = ref(false)

// 当前操作的脚本
const currentScript = ref(null)
const editingScript = ref(null)
const saving = ref(false)

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    ElMessage.error(t('uiAutomation.script.messages.loadProjectsFailed'))
    console.error('获取项目列表失败:', error)
  }
}

// 加载脚本列表
const loadScripts = async () => {
  if (!selectedProject.value) {
    scripts.value = []
    total.value = 0
    return
  }

  try {
    const response = await getTestScripts({
      project: selectedProject.value,
      page: currentPage.value,
      page_size: pageSize.value
    })

    // 处理分页响应
    if (response.data.results) {
      scripts.value = response.data.results
      total.value = response.data.count || 0
    } else {
      scripts.value = response.data
      total.value = response.data.length
    }
  } catch (error) {
    ElMessage.error(t('uiAutomation.script.messages.loadScriptsFailed'))
    console.error('获取脚本列表失败:', error)
  }
}

// 项目切换
const onProjectChange = async () => {
  currentPage.value = 1
  await loadScripts()
}

// 页面大小改变
const handleSizeChange = async () => {
  currentPage.value = 1
  await loadScripts()
}

// 当前页改变
const handleCurrentChange = async () => {
  await loadScripts()
}

// 打开录制向导
const openRecording = () => {
  if (!selectedProject.value) {
    ElMessage.warning(t('uiAutomation.scriptEditor.messages.selectProject'))
    return
  }
  recordingVisible.value = true
}

const openUpload = () => {
  if (!selectedProject.value) {
    ElMessage.warning(t('uiAutomation.scriptEditor.messages.selectProject'))
    return
  }
  scriptFileInput.value?.click()
}

const handleScriptFileChange = async event => {
  const input = event.target
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.py')) {
    ElMessage.warning(t('uiAutomation.recording.pythonFileOnly'))
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning(t('uiAutomation.recording.fileTooLarge'))
    return
  }

  uploadingScript.value = true
  try {
    const content = await file.text()
    await importRecordedScript({ project: selectedProject.value, name: file.name, content })
    ElMessage.success(t('uiAutomation.recording.importSuccess'))
    await loadScripts()
  } catch (error) {
    ElMessage.error(error.response?.data?.error || t('uiAutomation.recording.importFailed'))
  } finally {
    uploadingScript.value = false
  }
}

const openImportedScript = async script => {
  await loadScripts()
  router.push({ path: '/ui-automation/scripts/editor', query: { scriptId: script.id } })
}

const replayScript = script => {
  currentScript.value = script
  replayVisible.value = true
}

const historyScript = script => {
  currentScript.value = script
  historyVisible.value = true
}

const handleRowCommand = (command, script) => {
  if (command === 'detail') viewScript(script)
  if (command === 'edit') editScript(script)
  if (command === 'delete') deleteScript(script)
}

// 查看脚本详情
const viewScript = (script) => {
  currentScript.value = script
  showDetailDialog.value = true
}

// 编辑脚本
const editScript = (script) => {
  editingScript.value = { ...script, name: (script.name || '').replace(/\.py$/i, '') }
  showDetailDialog.value = false
  showEditDialog.value = true
}

// 保存编辑的脚本
const saveEditedScript = async () => {
  const name = editingScript.value?.name.trim().replace(/\.py$/i, '')
  if (!editingScript.value || !name) {
    ElMessage.warning(t('uiAutomation.script.messages.enterScriptName'))
    return
  }

  try {
    saving.value = true

    await updateTestScript(editingScript.value.id, {
      name,
      content: editingScript.value.content
    })

    ElMessage.success(t('uiAutomation.script.messages.saveSuccess'))
    showEditDialog.value = false

    // 重新加载脚本列表
    await loadScripts()
  } catch (error) {
    ElMessage.error(t('uiAutomation.script.messages.saveFailed'))
    console.error('脚本保存失败:', error)
  } finally {
    saving.value = false
  }
}

// 删除脚本
const deleteScript = async (script) => {
  try {
    await ElMessageBox.confirm(
      t('uiAutomation.script.messages.deleteConfirm', { name: script.name }),
      t('uiAutomation.script.messages.confirmDelete'),
      {
        confirmButtonText: t('uiAutomation.common.confirm'),
        cancelButtonText: t('uiAutomation.common.cancel'),
        type: 'warning'
      }
    )

    await deleteTestScript(script.id)
    ElMessage.success(t('uiAutomation.script.messages.deleteSuccess'))

    // 重新加载脚本列表
    await loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('uiAutomation.script.messages.deleteFailed'))
      console.error('删除失败:', error)
    }
  }
}

// 辅助方法
const getScriptTypeText = (type) => {
  const typeMap = {
    'CODE': t('uiAutomation.script.scriptTypes.CODE'),
    'VISUAL': t('uiAutomation.script.scriptTypes.VISUAL'),
    'KEYWORD': t('uiAutomation.script.scriptTypes.KEYWORD')
  }
  return typeMap[type] || type
}

const getLanguageText = (language) => {
  const languageMap = {
    'python': 'Python',
    'javascript': 'JavaScript'
  }
  return languageMap[language] || language || t('uiAutomation.status.unknown')
}

const getFrameworkText = (framework) => {
  const frameworkMap = {
    'playwright': 'Playwright',
    'selenium': 'Selenium'
  }
  return frameworkMap[framework] || framework || t('uiAutomation.status.unknown')
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString()
}

// 组件挂载
onMounted(async () => {
  await loadProjects()

  if (projects.value.length > 0) {
    selectedProject.value = projects.value[0].id
    await loadScripts()
  }
})
</script>

<style scoped>
.script-list {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e6e6e6;
  background: white;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.script-file-input {
  display: none;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
  background: #f5f5f5;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.row-actions {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.script-detail {
  padding: 10px;
}

.script-content {
  margin-top: 20px;
}

.script-content h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.code-view {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.script-editor {
  display: flex;
  flex-direction: column;
  height: 600px;
}

.edit-script-name { padding: 14px 15px 0; }

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background-color: #fafafa;
  border-bottom: 1px solid #e6e6e6;
}

.script-name {
  font-weight: bold;
  font-size: 16px;
}

.editor-info {
  display: flex;
  align-items: center;
}

.editor-container {
  flex: 1;
  position: relative;
}

.code-editor {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  padding: 15px;
  background-color: #1e1e1e;
  color: #d4d4d4;
  tab-size: 2;
}
</style>
