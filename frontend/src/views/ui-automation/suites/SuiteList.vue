<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ $t('uiAutomation.suite.title') }}</h1>
      <el-select v-model="projectId" :placeholder="$t('uiAutomation.common.selectProject')" style="width: 200px; margin-right: 15px" @change="onProjectChange">
        <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
      </el-select>
      <el-button type="primary" @click="handleNewSuite">
        <el-icon><Plus /></el-icon>
        {{ $t('uiAutomation.suite.newSuite') }}
      </el-button>
    </div>

    <div class="card-container">
      <div class="filter-bar">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchText"
              :placeholder="$t('uiAutomation.suite.searchPlaceholder')"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
        </el-row>
      </div>

      <el-table :data="suites" v-loading="loading" style="width: 100%">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" :label="$t('uiAutomation.suite.suiteName')" min-width="200">
          <template #default="{ row }">
            <el-link @click="editSuite(row.id)" type="primary">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('uiAutomation.common.description')" min-width="200" show-overflow-tooltip />
        <el-table-column :label="$t('uiAutomation.suite.testCaseCount')" width="120">
          <template #default="{ row }">
            {{ row.test_case_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('uiAutomation.suite.executionStatus')" width="100">
          <template #default="{ row }">
            <el-tag :type="getExecutionStatusTag(row.execution_status)">
              {{ getExecutionStatusText(row.execution_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('uiAutomation.suite.passedCount')" width="90">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: bold;">{{ row.passed_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('uiAutomation.suite.failedCount')" width="90">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold;">{{ row.failed_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('uiAutomation.common.createTime')" width="180" :formatter="formatDate" />
        <el-table-column prop="updated_at" :label="$t('uiAutomation.common.updateTime')" width="180" :formatter="formatDate" />
        <el-table-column :label="$t('uiAutomation.common.operation')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="editSuite(row.id)">
              <el-icon><Edit /></el-icon>
              {{ $t('uiAutomation.common.edit') }}
            </el-button>
            <el-button size="small" type="success" @click="runSuite(row)">
              <el-icon><RefreshRight /></el-icon>
              {{ $t('uiAutomation.common.run') }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteSuite(row.id)">
              <el-icon><Delete /></el-icon>
              {{ $t('uiAutomation.common.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑套件对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEditing ? $t('uiAutomation.suite.editSuite') : $t('uiAutomation.suite.createSuite')"
      width="1100px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="formRules" label-width="100px">
        <el-form-item :label="$t('uiAutomation.suite.suiteName')" prop="name">
          <el-input v-model="createForm.name" :placeholder="$t('uiAutomation.suite.rules.nameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.description')" prop="description">
          <el-input v-model="createForm.description" type="textarea" :placeholder="$t('uiAutomation.common.description')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.suite.testCases')">
          <div class="test-case-selector">
            <div class="selector-panel">
              <div class="panel-header">
                <h4>{{ $t('uiAutomation.suite.availableCases') }}</h4>
                <el-input
                  v-model="testCaseSearchText"
                  :placeholder="$t('uiAutomation.suite.searchCases')"
                  size="small"
                  clearable
                  style="width: 200px;"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </div>
              <div class="panel-actions">
                <el-button size="small" text type="primary" :icon="Check" :disabled="!addableTestCases.length" @click="addAllTestCases">
                  {{ $t('uiAutomation.suite.addAll') }}
                </el-button>
                <el-button size="small" text type="success" :icon="Plus" :disabled="!checkedTestCases.length" @click="addCheckedTestCases">
                  {{ $t('uiAutomation.suite.addChecked') }}
                </el-button>
              </div>
              <div class="panel-content">
                <el-table
                  ref="availableTableRef"
                  :data="filteredAvailableTestCases"
                  row-key="id"
                  height="300"
                  @row-click="handleTestCaseRowClick"
                  @selection-change="checkedTestCases = $event"
                  :row-class-name="getTestCaseRowClassName"
                >
                  <el-table-column type="selection" width="44" :selectable="isTestCaseAddable" />
                  <el-table-column prop="name" :label="$t('uiAutomation.suite.caseName')" min-width="150" show-overflow-tooltip />
                  <el-table-column prop="priority" :label="$t('uiAutomation.suite.priority')" width="80">
                    <template #default="{ row }">
                      <el-tag size="small" :type="getPriorityTag(row.priority)">
                        {{ getPriorityText(row.priority) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" :label="$t('uiAutomation.common.status')" width="80">
                    <template #default="{ row }">
                      <el-tag size="small" :type="getCaseStatusTag(row.status)">
                        {{ getCaseStatusText(row.status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('uiAutomation.common.operation')" width="80">
                    <template #default="{ row }">
                      <el-button size="small" text :disabled="!isTestCaseAddable(row)" @click.stop="addTestCase(row)">
                        <el-icon><ArrowRight /></el-icon>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>

            <div class="selector-panel">
              <div class="panel-header">
                <h4>{{ $t('uiAutomation.suite.selectedCases') }} ({{ selectedTestCases.length }})</h4>
              </div>
              <div class="panel-actions">
                <el-button size="small" text type="danger" :icon="Delete" :disabled="!selectedTestCases.length" @click="clearSelectedTestCases">
                  {{ $t('uiAutomation.suite.clearSelected') }}
                </el-button>
                <el-button size="small" text type="warning" :icon="Minus" :disabled="!checkedSelectedTestCases.length" @click="removeCheckedTestCases">
                  {{ $t('uiAutomation.suite.removeChecked') }}
                </el-button>
              </div>
              <div class="panel-content">
                <el-table
                  ref="selectedTableRef"
                  :data="selectedTestCases"
                  row-key="id"
                  height="300"
                  @selection-change="checkedSelectedTestCases = $event"
                  @row-click="handleSelectedTestCaseRowClick"
                >
                  <el-table-column type="selection" width="44" />
                  <el-table-column prop="name" :label="$t('uiAutomation.suite.caseName')" min-width="150" show-overflow-tooltip />
                  <el-table-column prop="priority" :label="$t('uiAutomation.suite.priority')" width="80">
                    <template #default="{ row }">
                      <el-tag size="small" :type="getPriorityTag(row.priority)">
                        {{ getPriorityText(row.priority) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('uiAutomation.common.operation')" width="120">
                    <template #default="{ row, $index }">
                      <div class="selected-case-actions">
                        <el-button
                          size="small"
                          text
                          @click.stop="moveUp($index)"
                          :disabled="$index === 0"
                        >
                          <el-icon><Top /></el-icon>
                        </el-button>
                        <el-button
                          size="small"
                          text
                          @click.stop="moveDown($index)"
                          :disabled="$index === selectedTestCases.length - 1"
                        >
                          <el-icon><Bottom /></el-icon>
                        </el-button>
                        <el-button
                          size="small"
                          text
                          type="danger"
                          @click.stop="removeTestCase($index)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelCreate">{{ $t('uiAutomation.common.cancel') }}</el-button>
          <el-button type="primary" @click="handleCreate" :loading="saving">{{ $t('uiAutomation.common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 运行配置对话框 -->
    <el-dialog v-model="showRunDialog" :title="$t('uiAutomation.suite.runConfig')" width="600px" :close-on-click-modal="false">
      <el-form :model="runConfig" label-width="120px">
        <el-form-item :label="$t('uiAutomation.suite.testEngine')">
          <el-select v-model="runConfig.engine" :placeholder="$t('uiAutomation.suite.testEngine')">
            <el-option label="Playwright" value="playwright" />
            <el-option label="Selenium" value="selenium" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.suite.browser')">
          <el-select v-model="runConfig.browser" :placeholder="$t('uiAutomation.suite.browser')">
            <el-option label="Chrome" value="chrome" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="Safari" value="safari" />
            <el-option label="Edge" value="edge" />
          </el-select>
        </el-form-item>
        <!-- 套件运行使用同一个初始登录态，登录态步骤仍由用例自身控制。 -->
        <el-form-item v-if="runConfig.engine === 'playwright'" label="登录态">
          <el-select v-model="runConfig.storage_state_id" placeholder="无登录态" clearable>
            <el-option v-for="state in storageStates" :key="state.id" :label="state.name" :value="state.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.suite.executionMode')">
          <el-radio-group v-model="runConfig.headless">
            <el-radio :label="false">{{ $t('uiAutomation.suite.headedMode') }}</el-radio>
            <el-radio :label="true">{{ $t('uiAutomation.suite.headlessMode') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRunDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
          <el-button
            type="primary"
            @click="confirmRunSuite"
            :loading="running"
          >
            {{ $t('uiAutomation.suite.startExecution') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Edit, Delete, RefreshRight, Collection,
  ArrowRight, Top, Bottom, Check, Minus
} from '@element-plus/icons-vue'
import {
  getUiProjects,
  getTestSuites,
  createTestSuite,
  updateTestSuite,
  deleteTestSuite,
  getTestCases,
  getTestSuiteTestCases,
  addTestCaseToTestSuite,
  removeTestCaseFromTestSuite,
  updateTestCaseOrder,
  runTestSuite,
  getStorageStates
} from '@/api/ui_automation'
import { useI18n } from 'vue-i18n'
import { getPreferredProjectId, useRememberedProject } from '@/utils/projectSelection'

const { t } = useI18n()

// 响应式数据
const projects = ref([])
const projectId = ref('')
useRememberedProject(projectId, projects)
const suites = ref([])
const loading = ref(false)
const searchText = ref('')
const total = ref(0)
const pagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 对话框控制
const showCreateDialog = ref(false)
const showRunDialog = ref(false)
const isEditing = ref(false)
const currentSuiteId = ref(null)
const saving = ref(false)
const running = ref(false)

// 表单数据
const createForm = reactive({
  name: '',
  description: ''
})

// 表单验证规则 - 使用 computed 实现动态国际化
const formRules = computed(() => ({
  name: [{ required: true, message: t('uiAutomation.suite.rules.nameRequired'), trigger: 'blur' }]
}))

// 测试用例相关
const availableTestCases = ref([])
const selectedTestCases = ref([])
const testCaseSearchText = ref('')
const availableTableRef = ref(null)
const checkedTestCases = ref([])
const selectedTableRef = ref(null)
const checkedSelectedTestCases = ref([])
const selectedTestCaseIds = computed(() => new Set(selectedTestCases.value.map(tc => tc.id)))
const isTestCaseAddable = (testCase) => !selectedTestCaseIds.value.has(testCase.id)

// 运行配置
const runConfig = reactive({
  engine: 'playwright',
  browser: 'chrome',
  headless: false,
  storage_state_id: null
})
const storageStates = ref([])
const currentRunningSuite = ref(null)

// 计算属性 - 过滤后的可用测试用例
const filteredAvailableTestCases = computed(() => {
  if (!testCaseSearchText.value) {
    return availableTestCases.value
  }
  return availableTestCases.value.filter(tc =>
    tc.name.toLowerCase().includes(testCaseSearchText.value.toLowerCase()) ||
    (tc.description && tc.description.toLowerCase().includes(testCaseSearchText.value.toLowerCase()))
  )
})
const addableTestCases = computed(() => filteredAvailableTestCases.value.filter(isTestCaseAddable))

const clearCheckedTestCases = () => {
  availableTableRef.value?.clearSelection()
  checkedTestCases.value = []
}

watch(testCaseSearchText, clearCheckedTestCases)

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error(t('uiAutomation.project.messages.loadFailed'))
  }
}

// 加载测试套件列表
const loadSuites = async () => {
  if (!projectId.value) {
    suites.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const response = await getTestSuites({
      project: projectId.value,
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      search: searchText.value
    })

    if (response.data.results) {
      suites.value = response.data.results
      total.value = response.data.count || 0
    } else {
      suites.value = response.data
      total.value = response.data.length
    }
  } catch (error) {
    console.error('获取测试套件列表失败:', error)
    ElMessage.error(t('uiAutomation.suite.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

// 加载可用测试用例
const loadAvailableTestCases = async () => {
  availableTestCases.value = []
  if (!projectId.value) return

  try {
    const cases = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const response = await getTestCases({ project: projectId.value, page, page_size: 1000 })
      cases.push(...(response.data.results || response.data))
      hasNext = Boolean(response.data.next)
      page++
    }
    availableTestCases.value = cases
  } catch (error) {
    console.error('获取测试用例列表失败:', error)
    ElMessage.error(t('uiAutomation.suite.messages.loadCasesFailed'))
  }
}

// 项目切换
const onProjectChange = async () => {
  pagination.currentPage = 1
  await loadSuites()
}

// 搜索处理
const handleSearch = async () => {
  pagination.currentPage = 1
  await loadSuites()
}

// 分页处理
const handleSizeChange = async () => {
  pagination.currentPage = 1
  await loadSuites()
}

const handleCurrentChange = async () => {
  await loadSuites()
}

// 新增套件
const handleCreate = async () => {
  if (!createForm.name) {
    ElMessage.warning(t('uiAutomation.suite.messages.inputName'))
    return
  }

  if (!projectId.value) {
    ElMessage.warning(t('uiAutomation.suite.messages.selectProject'))
    return
  }

  saving.value = true
  try {
    const suiteData = {
      project: projectId.value,
      name: createForm.name,
      description: createForm.description
    }

    let suiteId
    if (isEditing.value) {
      // 更新套件
      await updateTestSuite(currentSuiteId.value, suiteData)
      suiteId = currentSuiteId.value
    } else {
      // 创建套件
      const response = await createTestSuite(suiteData)
      suiteId = response.data.id
    }

    // 保存测试用例关联
    // 编辑时即使已选用例为空，也需要清除旧关联。
    if (isEditing.value) {
      const existingTestCases = await getTestSuiteTestCases(suiteId)
      for (const tc of existingTestCases.data) {
        await removeTestCaseFromTestSuite(suiteId, tc.test_case.id)
      }
    }

    // 添加新的关联
    for (let i = 0; i < selectedTestCases.value.length; i++) {
      await addTestCaseToTestSuite(suiteId, {
        test_case_id: selectedTestCases.value[i].id,
        order: i
      })
    }

    ElMessage.success(t(isEditing.value ? 'uiAutomation.suite.messages.updateSuccess' : 'uiAutomation.suite.messages.createSuccess'))
    showCreateDialog.value = false
    await loadSuites()
    resetForm()
  } catch (error) {
    console.error('保存测试套件失败:', error)
    ElMessage.error(t('uiAutomation.suite.messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

// 编辑套件
const editSuite = async (id) => {
  try {
    // 加载套件详情
    const suites_data = suites.value.find(s => s.id === id)
    if (!suites_data) return

    resetForm()
    currentSuiteId.value = id
    isEditing.value = true
    createForm.name = suites_data.name
    createForm.description = suites_data.description

    // 加载已选测试用例
    const response = await getTestSuiteTestCases(id)
    selectedTestCases.value = [...response.data].sort((a, b) => a.order - b.order).map(item => item.test_case)

    // 加载可用测试用例
    await loadAvailableTestCases()

    showCreateDialog.value = true
  } catch (error) {
    console.error('加载套件详情失败:', error)
    ElMessage.error(t('uiAutomation.suite.messages.loadDetailFailed'))
  }
}

// 删除套件
const deleteSuite = async (id) => {
  try {
    await ElMessageBox.confirm(t('uiAutomation.suite.messages.deleteConfirm'), t('uiAutomation.messages.confirm.tip'), {
      confirmButtonText: t('uiAutomation.common.confirm'),
      cancelButtonText: t('uiAutomation.common.cancel'),
      type: 'warning'
    })

    await deleteTestSuite(id)
    ElMessage.success(t('uiAutomation.suite.messages.deleteSuccess'))
    await loadSuites()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除测试套件失败:', error)
      ElMessage.error(t('uiAutomation.suite.messages.deleteFailed'))
    }
  }
}

// 运行套件
const runSuite = async (suite) => {
  // 检查是否包含测试用例
  if (!suite.test_case_count || suite.test_case_count === 0) {
    ElMessage.warning(t('uiAutomation.suite.messages.noCases'))
    return
  }

  currentRunningSuite.value = suite
  // 每次打开运行对话框都重新按套件项目加载登录态。
  runConfig.storage_state_id = null
  try {
    const response = await getStorageStates({ project: suite.project?.id || suite.project_id, page_size: 200 })
    storageStates.value = response.data.results || response.data
  } catch { storageStates.value = [] }
  showRunDialog.value = true
}

// 确认运行套件
const confirmRunSuite = async () => {
  running.value = true
  try {
    const requestData = {
      use_ai: false,
      engine: runConfig.engine,
      browser: runConfig.browser,
      headless: runConfig.headless,
      storage_state_id: runConfig.engine === 'playwright' ? runConfig.storage_state_id : null
    }

    const response = await runTestSuite(currentRunningSuite.value.id, requestData)

    ElMessage.success(t('uiAutomation.suite.messages.startSuccess'))
    showRunDialog.value = false

    // 立即刷新一次以显示"运行中"状态
    await loadSuites()

    // 开始轮询检查执行状态
    pollSuiteStatus(currentRunningSuite.value.id)
  } catch (error) {
    console.error('执行测试套件失败:', error)
    // 如果后端返回了错误消息，显示具体错误
    const errorMsg = error.response?.data?.error || t('uiAutomation.suite.messages.executeFailed')
    ElMessage.error(errorMsg)
  } finally {
    running.value = false
  }
}

// 轮询检查套件执行状态
const pollSuiteStatus = (suiteId) => {
  let pollCount = 0
  const maxPolls = 120 // 最多轮询2分钟（每秒一次）

  const pollInterval = setInterval(async () => {
    pollCount++

    try {
      // 重新加载套件列表
      await loadSuites()

      // 查找当前套件的状态
      const currentSuite = suites.value.find(s => s.id === suiteId)

      if (currentSuite && currentSuite.execution_status !== 'running') {
        // 执行完成，停止轮询
        clearInterval(pollInterval)

        // 根据状态显示消息
        if (currentSuite.execution_status === 'passed') {
          ElMessage.success(`${t('uiAutomation.suite.messages.executionComplete')}: ${t('uiAutomation.suite.messages.allPassed')} (${currentSuite.passed_count}/${currentSuite.passed_count + currentSuite.failed_count})`)
        } else if (currentSuite.execution_status === 'failed') {
          ElMessage.warning(`${t('uiAutomation.suite.messages.executionComplete')}: ${t('uiAutomation.suite.messages.partialFailed')} (${t('uiAutomation.suite.messages.passed')}: ${currentSuite.passed_count}, ${t('uiAutomation.status.failed')}: ${currentSuite.failed_count})`)
        }
      }

      // 超过最大轮询次数，停止轮询
      if (pollCount >= maxPolls) {
        clearInterval(pollInterval)
        ElMessage.info(t('uiAutomation.suite.messages.longExecution'))
      }
    } catch (error) {
      console.error('轮询套件状态失败:', error)
      // 发生错误时停止轮询
      clearInterval(pollInterval)
    }
  }, 3000) // 每3秒轮询一次
}

// 测试用例管理方法
const handleTestCaseRowClick = (row, column) => {
  if (column.type === 'selection' || !isTestCaseAddable(row)) return
  availableTableRef.value?.toggleRowSelection(row)
}

const getTestCaseRowClassName = ({ row }) => {
  // 如果已选中，添加特殊样式
  return selectedTestCases.value.some(tc => tc.id === row.id) ? 'selected-row' : ''
}

const addTestCase = (testCase) => {
  // 检查是否已存在
  if (selectedTestCases.value.some(tc => tc.id === testCase.id)) {
    ElMessage.warning(t('uiAutomation.suite.messages.caseAdded'))
    return
  }
  selectedTestCases.value.push({ ...testCase })
  availableTableRef.value?.toggleRowSelection(testCase, false)
}

const addTestCases = (testCases) => {
  const ids = new Set(selectedTestCaseIds.value)
  for (const testCase of testCases) {
    if (ids.has(testCase.id)) continue
    selectedTestCases.value.push({ ...testCase })
    ids.add(testCase.id)
  }
  clearCheckedTestCases()
}

// 搜索时仅添加当前筛选结果，已有用例及其顺序保持不变。
const addAllTestCases = () => addTestCases(addableTestCases.value)
const addCheckedTestCases = () => {
  const checkedIds = new Set(checkedTestCases.value.map(tc => tc.id))
  addTestCases(addableTestCases.value.filter(tc => checkedIds.has(tc.id)))
}

const removeTestCase = (index) => {
  const testCase = selectedTestCases.value[index]
  selectedTableRef.value?.toggleRowSelection(testCase, false)
  checkedSelectedTestCases.value = checkedSelectedTestCases.value.filter(tc => tc.id !== testCase.id)
  selectedTestCases.value.splice(index, 1)
}

const clearSelectedChecks = () => {
  selectedTableRef.value?.clearSelection()
  checkedSelectedTestCases.value = []
}

const clearSelectedTestCases = () => {
  selectedTestCases.value = []
  clearSelectedChecks()
}

const removeCheckedTestCases = () => {
  const checkedIds = new Set(checkedSelectedTestCases.value.map(tc => tc.id))
  selectedTestCases.value = selectedTestCases.value.filter(tc => !checkedIds.has(tc.id))
  clearSelectedChecks()
}

const handleSelectedTestCaseRowClick = (row, column) => {
  if (column.type === 'selection') return
  selectedTableRef.value?.toggleRowSelection(row)
}

const moveUp = (index) => {
  if (index > 0) {
    const temp = selectedTestCases.value[index]
    selectedTestCases.value[index] = selectedTestCases.value[index - 1]
    selectedTestCases.value[index - 1] = temp
  }
}

const moveDown = (index) => {
  if (index < selectedTestCases.value.length - 1) {
    const temp = selectedTestCases.value[index]
    selectedTestCases.value[index] = selectedTestCases.value[index + 1]
    selectedTestCases.value[index + 1] = temp
  }
}

// 重置表单
const resetForm = () => {
  clearCheckedTestCases()
  clearSelectedChecks()
  createForm.name = ''
  createForm.description = ''
  selectedTestCases.value = []
  testCaseSearchText.value = ''
  isEditing.value = false
  currentSuiteId.value = null
}

// 取消创建
const cancelCreate = () => {
  showCreateDialog.value = false
  resetForm()
}

// 新增套件按钮点击
const handleCreateButtonClick = async () => {
  resetForm()
  await loadAvailableTestCases()
  showCreateDialog.value = true
}

// 辅助方法
const formatDate = (row, column, cellValue) => {
  if (!cellValue) return ''
  return new Date(cellValue).toLocaleString()
}

const getExecutionStatusTag = (status) => {
  const statusMap = {
    'not_run': 'info',
    'passed': 'success',
    'failed': 'danger',
    'running': 'warning'
  }
  return statusMap[status] || 'info'
}

const getExecutionStatusText = (status) => {
  const statusKey = {
    'not_run': 'notRun',
    'passed': 'passed',
    'failed': 'failed',
    'running': 'running'
  }[status]
  return statusKey ? t(`uiAutomation.status.${statusKey}`) : t('uiAutomation.status.unknown')
}

const getPriorityTag = (priority) => {
  const priorityMap = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return priorityMap[priority] || 'info'
}

const getPriorityText = (priority) => {
  const priorityKey = {
    'high': 'high',
    'medium': 'medium',
    'low': 'low'
  }[priority]
  return priorityKey ? t(`uiAutomation.priority.${priorityKey}`) : t('uiAutomation.status.unknown')
}

const getCaseStatusTag = (status) => {
  const statusMap = {
    'draft': 'info',
    'ready': 'primary',
    'running': 'warning',
    'passed': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

const getCaseStatusText = (status) => {
  const statusKey = {
    'draft': 'draft',
    'ready': 'ready',
    'running': 'running',
    'passed': 'passed',
    'failed': 'failed'
  }[status]
  return statusKey ? t(`uiAutomation.status.${statusKey}`) : t('uiAutomation.status.unknown')
}

// 监听新增套件按钮
const originalShowCreateDialog = showCreateDialog
onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    projectId.value = getPreferredProjectId(projects.value, projects.value[0].id)
    await loadSuites()
  }
})

// 监听对话框打开事件
const openCreateDialog = async () => {
  if (!isEditing.value) {
    await loadAvailableTestCases()
  }
}

// 修改新增套件按钮点击事件
const handleNewSuite = async () => {
  resetForm()
  await loadAvailableTestCases()
  showCreateDialog.value = true
}
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 4px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.card-container {
  background: white;
  padding: 20px;
  border-radius: 4px;
}

.filter-bar {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

// 测试用例选择器样式
.test-case-selector {
  display: flex;
  gap: 20px;
  width: 100%;
}

.selector-panel {
  flex: 1;
  min-width: 0;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.panel-header {
  background: #f5f7fa;
  padding: 12px 15px;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;

  h4 {
    margin: 0;
    font-size: 14px;
    color: #303133;
  }
}

.panel-actions {
  display: flex;
  flex-wrap: wrap;
  padding: 4px 10px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.panel-content {
  padding: 10px;
}

.selected-case-actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 4px;

  .el-button {
    flex: 0 0 28px;
    width: 28px;
    margin: 0;
    padding: 0;
  }
}


:deep(.selected-row) {
  background-color: #f0f9ff !important;
}

:deep(.el-table__row) {
  cursor: pointer;

  &:hover {
    background-color: #f5f7fa;
  }
}

.mode-description {
  margin-top: 8px;

  .description-text {
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }
}
</style>
