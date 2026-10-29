<template>
  <div class="test-sets-page">
    <div class="page-header">
      <h2>测试套件</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新建测试套
      </el-button>
    </div>

    <div v-loading="loading" class="sets-grid">
      <div v-for="ts in testSets" :key="ts.id" class="set-card">
        <div class="set-card-head">
          <el-icon class="set-icon"><Files /></el-icon>
          <div class="set-title">
            <div class="name">{{ ts.name }}</div>
            <div class="desc">{{ ts.description || '暂无描述' }}</div>
          </div>
        </div>
        <div class="set-meta">
          <span>用例数：{{ ts.suites?.length || 0 }}</span>
          <span v-if="ts.cron">定时：{{ ts.cron }}</span>
        </div>
        <div class="set-actions">
          <el-button size="small" @click="openPicker(ts)">选择用例</el-button>
          <el-button size="small" type="success" :loading="runningSetId===ts.id" @click="runSet(ts)">运行</el-button>
          <el-button size="small" @click="editSet(ts)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteSet(ts)">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!loading && testSets.length === 0" description="还没有测试套件，点右上角新建" />
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingSet.id ? '编辑测试套' : '新建测试套'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如 P0 每日回归" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="定时cron">
          <el-input v-model="form.cron" placeholder="如 0 0 * * *（每天0点）" />
        </el-form-item>
        <el-form-item label="启用定时">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSet">保存</el-button>
      </template>
    </el-dialog>

    <!-- 选择用例对话框 -->
    <el-dialog v-model="pickerVisible" title="选择场景用例" width="700px" top="5vh">
      <el-tree
        ref="pickerTreeRef"
        :data="suiteTree"
        :props="{ label: 'name', children: 'children' }"
        show-checkbox
        node-key="id"
        default-expand-all
      />
      <template #footer>
        <span style="margin-right:auto">已选 {{ checkedCount }} 条</span>
        <el-button @click="pickerVisible = false">取消</el-button>
        <el-button type="primary" @click="savePicked">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Files } from '@element-plus/icons-vue'
import api from '@/utils/api'

const testSets = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const pickerVisible = ref(false)
const editingSet = ref({})
const form = ref({ name: '', description: '', cron: '', enabled: false })
const currentSet = ref(null)
const allSuites = ref([])
const runningSetId = ref(null)
const pickerTreeRef = ref(null)

const loadSets = async () => {
  loading.value = true
  try {
    const res = await api.get('/api-testing/test-sets/')
    testSets.value = res.data.results || res.data
  } catch (e) {
    ElMessage.error('加载测试套失败')
  } finally {
    loading.value = false
  }
}

const loadAllSuites = async () => {
  try {
    let url = '/api-testing/test-suites/?page_size=200'
    let all = []
    while (url) {
      const res = await api.get(url)
      all = all.concat(res.data.results || res.data)
      let next = res.data.next
      if (next) next = next.replace(/^https?:\/\/[^/]+/, '').replace(/^\/api/, '')
      url = next
    }
    allSuites.value = all
  } catch (e) {
    ElMessage.error('加载场景用例失败')
  }
}

const suiteTree = computed(() => {
  const root = []
  const map = {}
  const ensure = (parts) => {
    let cur = root
    let p = ''
    for (const x of parts) {
      p = p ? p + '/' + x : x
      if (!map[p]) {
        map[p] = { id: 'f-' + p, name: x, children: [] }
        cur.push(map[p])
      }
      cur = map[p].children
    }
    return cur
  }
  for (const s of allSuites.value) {
    const bucket = ensure((s.folder || '未分组').split('/'))
    bucket.push({ id: s.id, name: s.name })
  }
  return root
})

const openCreate = () => {
  editingSet.value = {}
  form.value = { name: '', description: '', cron: '', enabled: false }
  dialogVisible.value = true
}

const editSet = (ts) => {
  editingSet.value = ts
  form.value = { name: ts.name, description: ts.description, cron: ts.cron, enabled: ts.enabled }
  dialogVisible.value = true
}

const saveSet = async () => {
  if (!form.value.name) return ElMessage.warning('请填名称')
  const body = { ...form.value, project: 1 }
  try {
    if (editingSet.value.id) {
      await api.put(`/api-testing/test-sets/${editingSet.value.id}/`, body)
    } else {
      await api.post('/api-testing/test-sets/', body)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    loadSets()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const deleteSet = async (ts) => {
  await ElMessageBox.confirm(`删除测试套「${ts.name}」？`, '确认', { type: 'warning' })
  await api.delete(`/api-testing/test-sets/${ts.id}/`)
  ElMessage.success('已删除')
  loadSets()
}

const openPicker = async (ts) => {
  currentSet.value = ts
  pickerVisible.value = true
  await nextTick()
  // 勾选已有的 suite
  const existingIds = (ts.suites || []).map(s => s.id)
  pickerTreeRef.value?.setCheckedKeys(existingIds)
}

const checkedCount = computed(() => {
  if (!pickerTreeRef.value) return 0
  return pickerTreeRef.value.getCheckedNodes().filter(n => !n.children).length
})

const savePicked = async () => {
  const nodes = pickerTreeRef.value.getCheckedNodes().filter(n => !n.children)
  const suiteIds = nodes.map(n => n.id)
  try {
    await api.patch(`/api-testing/test-sets/${currentSet.value.id}/`, { suite_ids: suiteIds })
    ElMessage.success(`已加入 ${suiteIds.length} 个用例`)
    pickerVisible.value = false
    loadSets()
  } catch (e) {
    ElMessage.error('保存用例失败')
  }
}

const runSet = async (ts) => {
  runningSetId.value = ts.id
  try {
    const res = await api.post(`/api-testing/test-sets/${ts.id}/execute/`)
    const results = res.data.results || []
    const failed = results.filter(r => r.status !== 'COMPLETED').length
    if (results.length === 0) {
      ElMessage.warning('测试套中没有可运行的场景用例')
    } else if (failed > 0) {
      ElMessage.error(`执行完成：${results.length - failed}/${results.length} 通过，${failed} 个失败`)
    } else {
      ElMessage.success(`执行完成：${results.length}/${results.length} 通过`)
    }
  } catch (e) {
    ElMessage.error('运行失败')
  } finally {
    runningSetId.value = null
  }
}

import { nextTick } from 'vue'
onMounted(() => { loadSets(); loadAllSuites() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.sets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.set-card { border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; }
.set-card-head { display: flex; gap: 10px; align-items: flex-start; }
.set-icon { font-size: 28px; color: #409eff; }
.set-title { flex: 1; }
.set-title .name { font-weight: 600; }
.set-title .desc { font-size: 12px; color: #909399; margin-top: 4px; }
.set-meta { font-size: 12px; color: #606266; margin: 10px 0; display: flex; gap: 12px; }
.set-actions { display: flex; gap: 6px; flex-wrap: wrap; }
</style>
