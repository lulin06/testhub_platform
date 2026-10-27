<template>
  <div class="execution-list">
    <div class="header">
      <h1>{{ $t('execution.testPlan') }}</h1>
      <div class="header-actions">
        <el-button
          v-if="selectedPlans.length > 0"
          type="danger"
          :icon="Delete"
          @click="batchDeletePlans"
          :disabled="isDeleting">
          {{ $t('execution.batchDelete') }} ({{ selectedPlans.length }})
        </el-button>
        <el-button type="primary" @click="openCreatePlanDialog">
          <el-icon><Plus /></el-icon>
          {{ $t('execution.newPlan') }}
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-form :inline="true">
        <el-form-item :label="$t('execution.project')">
          <el-select v-model="filters.project" :placeholder="$t('execution.selectProject')" clearable style="width: 200px">
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.status')">
          <el-select v-model="filters.is_active" :placeholder="$t('execution.selectStatus')" clearable style="width: 120px">
            <el-option :label="$t('execution.filterActive')" :value="true"></el-option>
            <el-option :label="$t('execution.filterClosed')" :value="false"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilters">{{ $t('common.search') }}</el-button>
          <el-button @click="resetFilters">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table
      :data="testPlans"
      style="width: 100%"
      v-loading="loading"
      @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column
        type="index"
        :label="$t('execution.serialNumber')"
        width="80"
        :index="getSerialNumber" />
      <el-table-column prop="name" :label="$t('execution.planName')" min-width="200">
        <template #default="scope">
          <el-link type="primary" @click="viewPlan(scope.row.id)">
            {{ scope.row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="projects" :label="$t('execution.projects')" width="200">
        <template #default="scope">
          <span v-if="scope.row.projects && scope.row.projects.length > 0">
            {{ scope.row.projects.join(', ') }}
          </span>
          <span v-else>{{ $t('execution.noData') }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="version" :label="$t('execution.version')" width="120"></el-table-column>
      <el-table-column prop="creator.username" :label="$t('execution.creator')" width="120"></el-table-column>
      <el-table-column :label="$t('execution.status')" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'">
            {{ scope.row.is_active ? $t('execution.active') : $t('execution.closed') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="$t('execution.createdAt')" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column :label="$t('execution.actions')" width="220" fixed="right" class-name="action-col">
        <template #default="scope">
          <el-button size="small" type="primary" @click="viewPlan(scope.row.id)">
            {{ $t('execution.viewExecution') }}
          </el-button>
          <el-button size="small" type="warning" @click="editPlan(scope.row)">
            {{ $t('common.edit') }}
          </el-button>
          <el-button
            size="small"
            :type="scope.row.is_active ? 'danger' : 'success'"
            @click="togglePlanStatus(scope.row)">
            {{ scope.row.is_active ? $t('execution.closePlan') : $t('execution.activatePlan') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :small="false"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建测试计划对话框 -->
    <el-dialog :title="$t('execution.createPlanDialog')" v-model="isCreatePlanDialogOpen" width="600px" :close-on-click-modal="false">
      <el-form :model="newPlanForm" :rules="createPlanRules" ref="planFormRef" label-width="100px">
        <el-form-item :label="$t('execution.planName')" prop="name">
          <el-input v-model="newPlanForm.name" :placeholder="$t('execution.planNamePlaceholder')"></el-input>
        </el-form-item>
        <el-form-item :label="$t('execution.planDescription')">
          <el-input
            v-model="newPlanForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('execution.planDescriptionPlaceholder')">
          </el-input>
        </el-form-item>
        <el-form-item :label="$t('execution.relatedProjects')" prop="projects">
          <el-select
            v-model="newPlanForm.projects"
            multiple
            :placeholder="$t('execution.selectProjects')"
            style="width: 100%"
            @change="handleProjectChange">
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.relatedVersion')">
          <el-select v-model="newPlanForm.version" :placeholder="$t('execution.selectVersion')" style="width: 100%">
            <el-option v-for="item in versions" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.testCases')" prop="testcases">
          <div class="testcase-picker-trigger">
            <el-button
              type="primary"
              plain
              :disabled="!newPlanForm.projects || newPlanForm.projects.length === 0"
              @click="openTestcaseSelector('create')"
            >
              {{ $t('execution.selectTestcasesButton') }}
            </el-button>
            <span class="testcase-selection-tip">
              {{
                newPlanForm.testcases.length > 0
                  ? $t('execution.selectedTestcasesCount', { count: newPlanForm.testcases.length })
                  : $t('execution.noTestcasesSelected')
              }}
            </span>
            <el-button
              v-if="newPlanForm.testcases.length > 0"
              link
              type="primary"
              @click="openTestcaseSelector('create')"
            >
              {{ $t('execution.modifyTestcasesSelection') }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item :label="$t('execution.assignees')">
          <el-select v-model="newPlanForm.assignees" multiple :placeholder="$t('execution.selectAssignees')" style="width: 100%">
            <el-option v-for="item in users" :key="item.id" :label="item.username" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="isCreatePlanDialogOpen = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="createPlan" :loading="creating">{{ $t('execution.createPlan') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑测试计划对话框 -->
    <el-dialog :title="$t('execution.editPlanDialog')" v-model="isEditPlanDialogOpen" width="600px" :close-on-click-modal="false">
      <el-form :model="editPlanForm" :rules="editPlanRules" ref="editPlanFormRef" label-width="100px">
        <el-form-item :label="$t('execution.planName')" prop="name">
          <el-input v-model="editPlanForm.name" :placeholder="$t('execution.planNamePlaceholder')"></el-input>
        </el-form-item>
        <el-form-item :label="$t('execution.planDescription')">
          <el-input
            v-model="editPlanForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('execution.planDescriptionPlaceholder')">
          </el-input>
        </el-form-item>
        <el-form-item :label="$t('execution.relatedProjects')" prop="projects">
          <el-select v-model="editPlanForm.projects" multiple :placeholder="$t('execution.selectProjects')" style="width: 100%">
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.relatedVersion')">
          <el-select v-model="editPlanForm.version" :placeholder="$t('execution.selectVersion')" style="width: 100%">
            <el-option v-for="item in versions" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.testCases')" prop="testcases">
          <div class="testcase-picker-trigger">
            <el-button
              type="primary"
              plain
              :disabled="!editPlanForm.projects || editPlanForm.projects.length === 0"
              @click="openTestcaseSelector('edit')"
            >
              {{ $t('execution.selectTestcasesButton') }}
            </el-button>
            <span class="testcase-selection-tip">
              {{
                editPlanForm.testcases.length > 0
                  ? $t('execution.selectedTestcasesCount', { count: editPlanForm.testcases.length })
                  : $t('execution.noTestcasesSelected')
              }}
            </span>
            <el-button
              v-if="editPlanForm.testcases.length > 0"
              link
              type="primary"
              @click="openTestcaseSelector('edit')"
            >
              {{ $t('execution.modifyTestcasesSelection') }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item :label="$t('execution.assignees')">
          <el-select v-model="editPlanForm.assignees" multiple :placeholder="$t('execution.selectAssignees')" style="width: 100%">
            <el-option v-for="item in users" :key="item.id" :label="item.username" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.planStatus')">
          <el-switch
            v-model="editPlanForm.is_active"
            :active-text="$t('execution.activeText')"
            :inactive-text="$t('execution.inactiveText')">
          </el-switch>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="isEditPlanDialogOpen = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="updatePlan" :loading="updating">{{ $t('execution.updatePlan') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="testcaseSelectorVisible"
      :title="$t('execution.testcaseSelectorTitle')"
      width="min(1200px, 96vw)"
      class="testcase-selector-dialog"
      :close-on-click-modal="false"
    >
      <ResizableSplitPane v-model="testcaseSelectorSidebarWidth" :min-size="200" :max-size="380" :second-min-size="520" storage-key="execution-testcase-selector-sidebar-width" class="testcase-selector-container">
        <template #first>
        <aside class="testcase-library-panel">
          <div class="testcase-library-header">
            <strong>{{ $t('execution.testcaseLibrary') }}</strong>
            <el-input v-model="testcaseLibrarySearch" size="small" clearable :placeholder="$t('testcase.searchModules')">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>
          <div class="testcase-library-tree">
            <div class="testcase-library-node tree-root" :class="{ active: testcaseLibrarySelection.id === '__all__' }" @click="selectTestcaseLibraryNode({ id: '__all__', type: 'all' })">
              <el-icon><FolderOpened /></el-icon>
              <span class="testcase-library-node-name">{{ $t('testcase.allCases') }}</span>
              <span class="testcase-library-count">{{ filteredTestcases.length }}</span>
            </div>
          <el-tree
            ref="testcaseLibraryTreeRef"
            :data="filteredTestcaseLibraryTree"
            :props="{ label: 'label', children: 'children' }"
            node-key="id"
            default-expand-all
            highlight-current
            :expand-on-click-node="false"
            :current-node-key="testcaseLibrarySelection.id"
            @node-click="selectTestcaseLibraryNode"
          >
            <template #default="{ node, data }">
              <div class="testcase-library-node" :class="{ active: testcaseLibrarySelection.id === data.id }">
                <el-icon><component :is="data.type === 'all' || data.type === 'project' ? FolderOpened : Folder" /></el-icon>
                <span class="testcase-library-node-name" :title="node.label">{{ node.label }}</span>
                <span class="testcase-library-count">{{ data.count }}</span>
              </div>
            </template>
          </el-tree>
          <el-empty v-if="testcaseLibrarySearch.trim() && !filteredTestcaseLibraryTree.length" :description="$t('testcase.noModulesFound')" :image-size="60" />
          </div>
        </aside>
        </template>
        <template #second>
        <section class="testcase-library-list">
          <div class="testcase-search-bar">
            <el-form :inline="true">
              <el-form-item :label="$t('execution.testcaseKeyword')">
                <el-input v-model="testcaseSelectorFilters.keyword" :placeholder="$t('execution.testcaseKeywordPlaceholder')" clearable style="width: 200px" />
              </el-form-item>
              <el-form-item :label="$t('execution.testcasePriority')">
                <el-select v-model="testcaseSelectorFilters.priority" clearable style="width: 130px">
                  <el-option :label="$t('execution.allPriorities')" value="" />
                  <el-option :label="$t('testcase.low')" value="low" />
                  <el-option :label="$t('testcase.medium')" value="medium" />
                  <el-option :label="$t('testcase.high')" value="high" />
                  <el-option :label="$t('testcase.critical')" value="critical" />
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('execution.testcaseType')">
                <el-select v-model="testcaseSelectorFilters.test_type" clearable style="width: 150px">
                  <el-option :label="$t('execution.allTypes')" value="" />
                  <el-option :label="$t('testcase.functional')" value="functional" />
                  <el-option :label="$t('testcase.integration')" value="integration" />
                  <el-option :label="$t('testcase.api')" value="api" />
                  <el-option :label="$t('testcase.ui')" value="ui" />
                  <el-option :label="$t('testcase.performance')" value="performance" />
                  <el-option :label="$t('testcase.security')" value="security" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button @click="resetTestcaseSelectorFilters">{{ $t('execution.resetSearch') }}</el-button>
              </el-form-item>
            </el-form>
          </div>
          <div class="testcase-selector-table">
            <el-table
              ref="testcaseSelectorTableRef"
              :data="testcaseSelectorList"
              v-loading="loadingTestcases"
              @selection-change="handleTestcaseSelectorSelectionChange"
              row-key="id"
              height="100%"
            >
              <el-table-column type="selection" width="55" :reserve-selection="true" />
              <el-table-column :label="$t('execution.testcaseCode')" width="90">
                <template #default="{ row }">{{ row.id }}</template>
              </el-table-column>
              <el-table-column prop="title" :label="$t('execution.testcaseTitle')" min-width="260" show-overflow-tooltip />
              <el-table-column prop="priority" :label="$t('execution.testcasePriority')" width="120">
                <template #default="{ row }"><el-tag :class="`priority-tag ${row.priority}`">{{ getTestcasePriorityText(row.priority) }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="test_type" :label="$t('execution.testcaseType')" width="140">
                <template #default="{ row }">{{ getTestcaseTypeText(row.test_type) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </section>
        </template>
      </ResizableSplitPane>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="testcaseSelectorVisible = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="confirmTestcaseSelection">
            {{ $t('execution.confirmSelectTestcases', { count: testcaseTempSelectedIds.length }) }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Folder, FolderOpened, Search } from '@element-plus/icons-vue'
import ResizableSplitPane from '@/components/ResizableSplitPane.vue'
import api from '@/utils/api'

const { t } = useI18n()

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const updating = ref(false)
const testPlans = ref([])
const projects = ref([])
const versions = ref([])
const testcases = ref([])
const filteredTestcases = ref([])
const loadingTestcases = ref(false)
const users = ref([])
const selectedPlans = ref([])
const isDeleting = ref(false)
const testcaseSelectorVisible = ref(false)
const testcaseSelectorMode = ref('create')
const testcaseSelectorTableRef = ref()
const testcaseSelectorSidebarWidth = ref(250)
const testcaseSelectorModuleTrees = ref([])
const testcaseLibraryTreeRef = ref()
const testcaseLibrarySearch = ref('')
const testcaseLibrarySelection = ref({ id: '', type: 'all' })
const testcaseTempSelectedIds = ref([])
const isSyncingTestcaseSelectorSelection = ref(false)
const testcaseSelectorFilters = reactive({
  keyword: '',
  priority: '',
  test_type: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选
const filters = reactive({
  project: null,
  is_active: null
})

// 表单
const isCreatePlanDialogOpen = ref(false)
const isEditPlanDialogOpen = ref(false)
const planFormRef = ref()
const editPlanFormRef = ref()
const currentEditingPlan = ref(null)
const newPlanForm = reactive({
  name: '',
  description: '',
  projects: [], // 改为数组
  version: null,
  testcases: [],
  assignees: []
})

const editPlanForm = reactive({
  id: null,
  name: '',
  description: '',
  projects: [],
  version: null,
  testcases: [],
  assignees: [],
  is_active: true
})

const buildPlanRules = (form) => ({
  name: [
    { required: true, message: computed(() => t('execution.planNameRequired')), trigger: 'blur' }
  ],
  projects: [
    { required: true, message: computed(() => t('execution.projectsRequired')), trigger: 'change' }
  ],
  testcases: [
    {
      required: true,
      message: computed(() => t('execution.testcasesRequired')),
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (!form.projects || form.projects.length === 0) {
          callback(new Error(t('execution.selectProjectBeforeTestcases')))
        } else if (!value || value.length === 0) {
          callback(new Error(t('execution.testcasesRequired')))
        } else {
          callback()
        }
      }
    }
  ]
})

const createPlanRules = buildPlanRules(newPlanForm)
const editPlanRules = buildPlanRules(editPlanForm)

const fetchTestPlans = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      ...filters
    }
    // 过滤掉空值
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '') {
        delete params[key]
      }
    })

    const response = await api.get('/executions/plans/', { params })
    testPlans.value = response.data.results || response.data || []
    total.value = response.data.count || testPlans.value.length
  } catch (error) {
    ElMessage.error(t('execution.fetchListFailed'))
  } finally {
    loading.value = false
  }
}

const fetchBasicData = async () => {
  try {
    const [projectsRes, versionsRes, usersRes] = await Promise.all([
      api.get('/projects/'), // 只显示用户参与的项目
      api.get('/versions/'),
      api.get('/users/users/') // 修正用户API路径
    ])
    
    projects.value = (projectsRes.data.results || projectsRes.data || []).filter(item => item !== null && item !== undefined)
    versions.value = (versionsRes.data.results || versionsRes.data || []).filter(item => item !== null && item !== undefined)
    users.value = (usersRes.data.results || usersRes.data || []).filter(item => item !== null && item !== undefined)
  } catch (error) {
    console.error('获取基础数据失败:', error)
  }
}

// 根据选中的项目加载测试用例
const loadTestcasesByProjects = async (projectIds) => {
  if (!projectIds || projectIds.length === 0) {
    filteredTestcases.value = []
    return
  }

  loadingTestcases.value = true

  try {
    const params = new URLSearchParams()
    projectIds.forEach(id => params.append('project_ids', id))

    console.log('API URL:', `/executions/plans/testcases_by_projects/?${params.toString()}`)

    const response = await api.get(`/executions/plans/testcases_by_projects/?${params.toString()}`)
    console.log('API Response:', response.data)

    filteredTestcases.value = response.data.results || []
    console.log('Filtered testcases:', filteredTestcases.value)
  } catch (error) {
    console.error('Load testcases error:', error)
    if (error.response?.status === 400) {
      ElMessage.warning(error.response.data.detail || t('execution.selectProjectFirst'))
    } else if (error.response?.status === 401) {
      ElMessage.error(t('auth.loginFailed'))
    } else {
      ElMessage.error(t('execution.fetchTestcasesFailed') + ': ' + (error.response?.data?.detail || error.message))
    }
    filteredTestcases.value = []
  } finally {
    loadingTestcases.value = false
  }
}

// 处理项目选择变化
const handleProjectChange = (selectedProjects) => {
  // 清空已选择的测试用例
  newPlanForm.testcases = []
  
  // 加载新项目的测试用例
  if (selectedProjects && selectedProjects.length > 0) {
    loadTestcasesByProjects(selectedProjects)
  } else {
    filteredTestcases.value = []
  }
}

const testcaseSelectorList = computed(() => {
  let scopedTestcases = filteredTestcases.value
  const selection = testcaseLibrarySelection.value
  if (selection.type === 'project') {
    scopedTestcases = scopedTestcases.filter(item => String(item.project_id) === String(selection.projectId))
  } else if (selection.type === 'module') {
    const moduleIds = new Set(selection.moduleIds.map(String))
    scopedTestcases = scopedTestcases.filter(item => moduleIds.has(String(item.module_id)))
  } else if (selection.type === 'unassigned') {
    scopedTestcases = scopedTestcases.filter(item => !item.module_id)
  }

  return scopedTestcases.filter(item => {
    const keyword = testcaseSelectorFilters.keyword.trim().toLowerCase()
    const matchKeyword = !keyword || item.title?.toLowerCase().includes(keyword)
    const matchPriority = !testcaseSelectorFilters.priority || item.priority === testcaseSelectorFilters.priority
    const matchType = !testcaseSelectorFilters.test_type || item.test_type === testcaseSelectorFilters.test_type
    return matchKeyword && matchPriority && matchType
  })
})

const filteredTestcaseLibraryTree = computed(() => {
  const keyword = testcaseLibrarySearch.value.trim().toLowerCase()
  if (!keyword) return testcaseSelectorModuleTrees.value

  const filterModules = (nodes) => nodes.reduce((matches, item) => {
    const children = filterModules(item.children || [])
    if (item.label.toLowerCase().includes(keyword) || children.length) {
      matches.push({ ...item, children })
    }
    return matches
  }, [])

  return testcaseSelectorModuleTrees.value.map(project => ({
    ...project,
    children: filterModules(project.children)
  })).filter(project => project.children.length)
})

const buildTestcaseLibraryTree = (projectsList, modulesByProject, testcaseList) => {
  const buildModuleNodes = (nodes, projectId) => nodes.map(module => {
    const children = buildModuleNodes(module.children || [], projectId)
    const descendantIds = [module.id, ...children.flatMap(child => child.moduleIds)]
    return {
      id: `module-${projectId}-${module.id}`,
      type: 'module',
      label: module.name,
      count: testcaseList.filter(item => String(item.project_id) === String(projectId) && descendantIds.includes(item.module_id)).length,
      moduleIds: descendantIds,
      children
    }
  })

  return projectsList.map(project => {
    const projectCases = testcaseList.filter(item => String(item.project_id) === String(project.id))
    const moduleNodes = buildModuleNodes(modulesByProject[project.id] || [], project.id)
    const projectNode = {
      id: `project-${project.id}`,
      type: 'project',
      projectId: project.id,
      label: project.name,
      count: projectCases.length,
      children: [
        ...moduleNodes,
        {
          id: `unassigned-${project.id}`,
          type: 'unassigned',
          projectId: project.id,
          label: t('testcase.noModule'),
          count: projectCases.filter(item => !item.module_id).length,
          children: []
        }
      ]
    }
    return projectNode
  })
}

const selectTestcaseLibraryNode = (data) => {
  const selectedNode = data.type === 'module'
    ? findTestcaseModuleNode(testcaseSelectorModuleTrees.value, data.id)
    : null
  testcaseLibrarySelection.value = {
    id: data.type === 'all' ? '__all__' : data.id,
    type: data.type,
    projectId: data.projectId,
    moduleIds: selectedNode?.moduleIds || []
  }
}

const findTestcaseModuleNode = (nodes, id) => {
  for (const node of nodes) {
    if (node.id === id) return node
    const found = findTestcaseModuleNode(node.children || [], id)
    if (found) return found
  }
  return null
}

const getCurrentPlanForm = () => (
  testcaseSelectorMode.value === 'edit' ? editPlanForm : newPlanForm
)

const syncDialogTableSelection = async () => {
  await nextTick()
  if (!testcaseSelectorTableRef.value) return
  isSyncingTestcaseSelectorSelection.value = true
  try {
    testcaseSelectorTableRef.value.clearSelection()
    testcaseSelectorList.value.forEach(item => {
      if (testcaseTempSelectedIds.value.includes(item.id)) {
        testcaseSelectorTableRef.value.toggleRowSelection(item, true)
      }
    })
    await nextTick()
  } finally {
    isSyncingTestcaseSelectorSelection.value = false
  }
}

const openTestcaseSelector = async (mode) => {
  testcaseSelectorMode.value = mode
  const currentForm = getCurrentPlanForm()
  if (!currentForm.projects || currentForm.projects.length === 0) {
    ElMessage.warning(t('execution.selectProjectBeforeOpenTestcases'))
    return
  }

  await loadTestcasesByProjects(currentForm.projects)
  const selectedProjects = projects.value.filter(project => currentForm.projects.map(String).includes(String(project.id)))
  let moduleResponses
  try {
    moduleResponses = await Promise.all(selectedProjects.map(project => api.get('/testcases/modules/', { params: { project: project.id } })))
  } catch (error) {
    ElMessage.error(t('testcase.fetchModulesFailed'))
    return
  }
  const modulesByProject = Object.fromEntries(selectedProjects.map((project, index) => [project.id, moduleResponses[index].data || []]))
  testcaseSelectorModuleTrees.value = buildTestcaseLibraryTree(selectedProjects, modulesByProject, filteredTestcases.value)
  testcaseLibrarySelection.value = { id: '__all__', type: 'all' }
  testcaseLibrarySearch.value = ''

  testcaseTempSelectedIds.value = [...currentForm.testcases]
  testcaseSelectorVisible.value = true
  await syncDialogTableSelection()
}

const handleTestcaseSelectorSelectionChange = (selection) => {
  if (isSyncingTestcaseSelectorSelection.value) {
    return
  }
  const visibleIds = testcaseSelectorList.value.map(item => item.id)
  const hiddenSelectedIds = testcaseTempSelectedIds.value.filter(id => !visibleIds.includes(id))
  testcaseTempSelectedIds.value = [
    ...hiddenSelectedIds,
    ...selection.map(item => item.id)
  ]
}

const confirmTestcaseSelection = () => {
  const currentForm = getCurrentPlanForm()
  currentForm.testcases = [...new Set(testcaseTempSelectedIds.value)]
  testcaseSelectorVisible.value = false
  nextTick(() => {
    const formRef = testcaseSelectorMode.value === 'edit' ? editPlanFormRef.value : planFormRef.value
    formRef?.clearValidate('testcases')
  })
}

const resetTestcaseSelectorFilters = async () => {
  testcaseSelectorFilters.keyword = ''
  testcaseSelectorFilters.priority = ''
  testcaseSelectorFilters.test_type = ''
  await syncDialogTableSelection()
}

const getTestcasePriorityText = (priority) => {
  const textMap = {
    low: t('testcase.low'),
    medium: t('testcase.medium'),
    high: t('testcase.high'),
    critical: t('testcase.critical')
  }
  return textMap[priority] || priority
}

const getTestcaseTypeText = (type) => {
  const textMap = {
    functional: t('testcase.functional'),
    integration: t('testcase.integration'),
    api: t('testcase.api'),
    ui: t('testcase.ui'),
    performance: t('testcase.performance'),
    security: t('testcase.security')
  }
  return textMap[type] || type
}

const createPlan = async () => {
  try {
    await planFormRef.value.validate()
    creating.value = true

    await api.post('/executions/plans/', newPlanForm)
    ElMessage.success(t('execution.createSuccess'))
    isCreatePlanDialogOpen.value = false
    resetPlanForm()
    fetchTestPlans()
  } catch (error) {
    if (error.name !== 'ValidateError') {
      ElMessage.error(t('execution.createFailed'))
    }
  } finally {
    creating.value = false
  }
}

const viewPlan = (id) => {
  router.push(`/ai-generation/executions/${id}`)
}

const editPlan = async (plan) => {
  try {
    // 获取完整的测试计划详情
    const response = await api.get(`/executions/plans/${plan.id}/`)
    const planDetail = response.data

    // 设置当前编辑的计划
    currentEditingPlan.value = planDetail

    // 填充编辑表单数据
    Object.assign(editPlanForm, {
      id: planDetail.id,
      name: planDetail.name,
      description: planDetail.description || '',
      projects: planDetail.projects?.map(p => {
        // 如果是字符串，需要找到对应的项目ID
        const project = projects.value.find(proj => proj.name === p)
        return project ? project.id : p
      }) || [],
      version: planDetail.version ? versions.value.find(v => v.name === planDetail.version)?.id : null,
      testcases: planDetail.testcases?.map(tc => tc.id) || [],
      assignees: planDetail.assignees || [],
      is_active: planDetail.is_active
    })

    if (editPlanForm.projects.length > 0) {
      await loadTestcasesByProjects(editPlanForm.projects)
    }

    isEditPlanDialogOpen.value = true
  } catch (error) {
    ElMessage.error(t('execution.fetchDetailFailed'))
  }
}

const updatePlan = async () => {
  try {
    await editPlanFormRef.value.validate()
    updating.value = true

    const updateData = {
      name: editPlanForm.name,
      description: editPlanForm.description,
      projects: editPlanForm.projects,
      version: editPlanForm.version,
      testcases: editPlanForm.testcases,
      assignees: editPlanForm.assignees,
      is_active: editPlanForm.is_active
    }

    await api.put(`/executions/plans/${editPlanForm.id}/`, updateData)
    ElMessage.success(t('execution.updateSuccess'))
    isEditPlanDialogOpen.value = false
    resetEditForm()
    fetchTestPlans()
  } catch (error) {
    if (error.name !== 'ValidateError') {
      ElMessage.error(t('execution.updateFailed'))
    }
  } finally {
    updating.value = false
  }
}

const resetEditForm = () => {
  Object.assign(editPlanForm, {
    id: null,
    name: '',
    description: '',
    projects: [],
    version: null,
    testcases: [],
    assignees: [],
    is_active: true
  })
  currentEditingPlan.value = null
  editPlanFormRef.value?.resetFields()
}

const togglePlanStatus = async (plan) => {
  try {
    const action = plan.is_active ? t('execution.closePlan') : t('execution.activatePlan')
    await ElMessageBox.confirm(t('execution.toggleStatusConfirm', { action }), t('common.confirm'), {
      type: 'warning'
    })

    await api.patch(`/executions/plans/${plan.id}/`, {
      is_active: !plan.is_active
    })

    ElMessage.success(t('execution.toggleStatusSuccess', { action }))
    fetchTestPlans()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('execution.toggleStatusFailed'))
    }
  }
}

const openCreatePlanDialog = () => {
  resetPlanForm()
  isCreatePlanDialogOpen.value = true
}

const resetPlanForm = () => {
  Object.assign(newPlanForm, {
    name: '',
    description: '',
    projects: [], // 改为数组
    version: null,
    testcases: [],
    assignees: []
  })
  filteredTestcases.value = [] // 清空过滤后的测试用例
  loadingTestcases.value = false // 重置加载状态
  planFormRef.value?.resetFields()
}

const applyFilters = () => {
  currentPage.value = 1
  fetchTestPlans()
}

const resetFilters = () => {
  Object.assign(filters, {
    project: null,
    is_active: null
  })
  currentPage.value = 1
  fetchTestPlans()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchTestPlans()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchTestPlans()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedPlans.value = selection
}

// 获取序号
const getSerialNumber = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 批量删除
const batchDeletePlans = async () => {
  if (selectedPlans.value.length === 0) {
    ElMessage.warning(t('execution.selectFirst'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('execution.batchDeleteConfirm', { count: selectedPlans.value.length }),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    isDeleting.value = true
    let successCount = 0
    let failCount = 0

    for (const plan of selectedPlans.value) {
      try {
        await api.delete(`/executions/plans/${plan.id}/`)
        successCount++
      } catch (error) {
        console.error(`删除测试计划 ${plan.id} 失败:`, error)
        failCount++
      }
    }

    if (successCount > 0) {
      if (failCount > 0) {
        ElMessage.success(t('execution.batchDeletePartialSuccess', { successCount, failCount }))
      } else {
        ElMessage.success(t('execution.batchDeleteSuccess', { successCount }))
      }
    } else {
      ElMessage.error(t('execution.batchDeleteFailed'))
    }

    selectedPlans.value = []
    fetchTestPlans()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error(t('execution.batchDeleteFailed'))
    }
  } finally {
    isDeleting.value = false
  }
}

// 监听项目选择变化
watch(
  () => newPlanForm.projects,
  (newProjects) => {
    // 清空已选择的测试用例
    newPlanForm.testcases = []
    
    // 加载新项目的测试用例
    if (newProjects && newProjects.length > 0) {
      loadTestcasesByProjects(newProjects)
    } else {
      filteredTestcases.value = []
    }
  },
  { deep: true }
)

watch(
  () => editPlanForm.projects,
  (newProjects, oldProjects) => {
    if (!isEditPlanDialogOpen.value) return
    if (JSON.stringify(newProjects || []) === JSON.stringify(oldProjects || [])) return

    editPlanForm.testcases = []
    if (newProjects && newProjects.length > 0) {
      loadTestcasesByProjects(newProjects)
    } else {
      filteredTestcases.value = []
    }
  },
  { deep: true }
)

watch(testcaseSelectorList, () => {
  if (testcaseSelectorVisible.value) {
    syncDialogTableSelection()
  }
})

onMounted(() => {
  fetchTestPlans()
  fetchBasicData()
})
</script>

<style scoped>
.execution-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.testcase-picker-trigger {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.testcase-selection-tip {
  color: #606266;
  font-size: 14px;
}

.testcase-selector-container {
  height: min(68vh, 620px);
  min-height: 420px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.testcase-library-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
}

.testcase-library-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-bottom: 1px solid #e4e7ed;
}

.testcase-library-tree {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px;
}

.testcase-library-node {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  height: 32px;
  gap: 8px;
  padding: 0 8px;
  border-radius: 4px;
  color: #606266;
  cursor: pointer;
}

.testcase-library-node.active {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.testcase-library-node-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.testcase-library-count {
  flex: 0 0 auto;
  min-width: 24px;
  text-align: right;
  color: #909399;
  font-size: 12px;
}

.testcase-library-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  padding: 12px;
}

.testcase-search-bar {
  flex: 0 0 auto;
  min-width: max-content;
  padding: 10px 12px 0;
  background: #f8f9fa;
  border-radius: 4px;
}

.testcase-search-bar :deep(.el-form--inline) {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
}

.testcase-search-bar :deep(.el-form-item) {
  flex: 0 0 auto;
  margin-right: 0;
  margin-bottom: 10px;
}

.testcase-search-bar :deep(.el-form-item__content) {
  flex-wrap: nowrap;
}

.testcase-selector-table {
  flex: 1;
  min-height: 0;
  padding-top: 12px;
}

.testcase-selector-table :deep(.el-table) {
  height: 100%;
}

.testcase-selector-dialog :deep(.el-dialog__body) {
  padding-top: 12px;
  padding-bottom: 12px;
}

@media (max-width: 760px) {
  .testcase-selector-container {
    height: 70vh;
    min-height: 0;
  }

  .testcase-library-tree {
    min-height: 0;
  }

  .testcase-library-list {
    overflow-x: auto;
  }
}

.priority-tag.low {
  color: #67c23a;
}

.priority-tag.medium {
  color: #e6a23c;
}

.priority-tag.high,
.priority-tag.critical {
  color: #f56c6c;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 操作列：固定右列，按钮强制单行不换行（列宽已留足空间） */
:deep(.action-col .cell) {
  white-space: nowrap;
}
</style>
