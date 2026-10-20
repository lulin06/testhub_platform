<template>
  <div class="structured-step-editor">
    <div v-if="showToolbar" class="steps-toolbar">
      <span>{{ title }} ({{ modelValue.length }})</span>
      <el-button size="small" @click="addStep">添加步骤</el-button>
    </div>
    <draggable v-model="localSteps" item-key="id" handle=".drag-handle" @change="emitSteps">
      <template #item="{ element, index }">
        <section class="step-row" :class="{ expanded: element.expanded }">
          <header class="step-header">
            <el-icon class="drag-handle"><Rank /></el-icon>
            <span class="step-number">{{ index + 1 }}</span>
            <el-select v-model="element.action_type" size="small" @change="onActionChange(element)">
              <el-option v-for="action in actions" :key="action.value" :label="action.label" :value="action.value" />
            </el-select>
            <el-select v-if="needsElement(element) && pages.length" v-model="element.element_page" size="small" clearable placeholder="所属页面" @change="onPageChange(element)">
              <el-option v-for="page in pages" :key="page.id" :label="page.name" :value="page.name" />
            </el-select>
            <el-select v-if="needsElement(element)" v-model="element.element_id" size="small" filterable clearable placeholder="选择元素" @change="onElementChange(element)">
              <el-option v-for="item in getElementsForStep(element)" :key="item.id" :label="elementOptionLabel(item)" :value="item.id" />
            </el-select>
            <el-button text @click="element.expanded = !element.expanded; emitSteps()" :aria-label="element.expanded ? '折叠步骤' : '展开步骤'">
              <el-icon><ArrowUp v-if="element.expanded" /><ArrowDown v-else /></el-icon>
            </el-button>
            <el-button text type="danger" @click="removeStep(index)">删除</el-button>
          </header>
          <div v-if="element.expanded" class="step-content">
          <div v-if="needsElement(element)" class="step-field locator-field">
            <el-select v-model="element.locator_strategy" size="small" placeholder="定位策略" :disabled="hasElement(element)" @change="onLocatorChange(element)">
              <el-option v-for="strategy in strategies" :key="strategy" :label="strategy" :value="strategy" />
            </el-select>
            <el-input v-model="element.locator_value" size="small" placeholder="定位器" :disabled="hasElement(element)" @input="emitSteps" />
            <el-input v-if="element.locator_strategy === 'role'" v-model="element.locator_name" size="small" placeholder="名称（可选）" :disabled="hasElement(element)" @input="onLocatorNameInput(element)" />
          </div>
          <div v-if="element.action_type === 'setVariable'" class="step-field variable-set-field">
            <el-input v-model="element.input_value" size="small" placeholder="变量名" @input="emitSteps" />
            <el-input v-model="element.assert_value" size="small" placeholder="变量值" @input="emitSteps" />
          </div>
          <div v-else-if="element.action_type === 'getText'" class="step-field">
            <el-input v-model="element.assert_value" size="small" placeholder="保存到临时变量（可选）" @input="emitSteps" />
          </div>
          <div v-else-if="needsInput(element.action_type)" class="step-field">
            <el-input v-model="element.input_value" size="small" :placeholder="element.action_type === 'navigate' ? 'URL' : '输入值'" @input="emitSteps">
              <template v-if="helperActions" #append><el-button class="data-factory-button" size="small" :icon="MagicStick" title="选择数据工厂数据" @click="emit('helper', { step: element, field: 'input_value' })" /></template>
            </el-input>
            <el-button v-if="helperActions && element.action_type !== 'switchTab'" class="variable-helper-button" size="small" @click="emit('variable', { step: element, field: 'input_value' })"><el-icon><MagicStick /></el-icon></el-button>
          </div>
          <div v-if="['wait', 'waitFor'].includes(element.action_type)" class="step-field">
            <el-input-number v-model="element.wait_time" :min="100" :max="30000" :step="100" size="small" @change="emitSteps" />
          </div>
          <div v-if="element.action_type === 'assert'" class="step-field">
            <el-select v-model="element.assert_type" size="small" @change="emitSteps">
              <el-option label="文本包含" value="textContains" /><el-option label="文本相等" value="textEquals" />
              <el-option label="元素可见" value="isVisible" /><el-option label="元素存在" value="exists" />
              <el-option label="URL包含" value="urlContains" />
            </el-select>
            <el-input v-model="element.assert_value" size="small" placeholder="断言值" @input="emitSteps">
              <template v-if="helperActions" #append><el-button class="data-factory-button" size="small" :icon="MagicStick" title="选择数据工厂数据" @click="emit('helper', { step: element, field: 'assert_value' })" /></template>
            </el-input>
            <el-button v-if="helperActions" class="variable-helper-button" size="small" @click="emit('variable', { step: element, field: 'assert_value' })"><el-icon><MagicStick /></el-icon></el-button>
          </div>
          <div class="step-field description-field">
            <el-input v-model="element.description" size="small" placeholder="步骤描述" @input="emitSteps" />
          </div>
          </div>
        </section>
      </template>
    </draggable>
    <el-empty v-if="!modelValue.length" description="暂无步骤" :image-size="48" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import draggable from 'vuedraggable'
import { Rank, MagicStick, ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  elements: { type: Array, default: () => [] },
  pages: { type: Array, default: () => [] },
  title: { type: String, default: '结构化步骤' },
  helperActions: { type: Boolean, default: false },
  showToolbar: { type: Boolean, default: true }
})
const emit = defineEmits(['update:modelValue', 'change', 'helper', 'variable'])
// 与后端 LocatorStrategy 名称保持一致，保证步骤编辑和代码生成使用同一套值。
const strategies = ['role', 'label', 'placeholder', 'text', 'test-id', 'title', 'alt-text', 'css', 'xpath']
const actions = [
  { value: 'click', label: '点击' }, { value: 'fill', label: '输入文本' }, { value: 'press', label: '按键' },
  { value: 'select', label: '选择选项' }, { value: 'check', label: '勾选' }, { value: 'uncheck', label: '取消勾选' },
  { value: 'hover', label: '悬停' }, { value: 'getText', label: '获取文本' }, { value: 'waitFor', label: '等待元素' },
  { value: 'scroll', label: '滚动' }, { value: 'screenshot', label: '截图' }, { value: 'assert', label: '断言' },
  { value: 'wait', label: '等待' }, { value: 'switchTab', label: '切换标签页' }, { value: 'navigate', label: '跳转URL' },
  { value: 'setVariable', label: '设置临时变量' }
]
// 使用 computed 代理 v-model，让拖拽排序和字段修改统一向父组件同步。
const localSteps = computed({
  get: () => props.modelValue,
  set: value => { emit('update:modelValue', value); emit('change', value) }
})
const emitSteps = () => { emit('update:modelValue', props.modelValue); emit('change', props.modelValue) }
const addStep = () => localSteps.value = [...localSteps.value, {
  id: `new-${Date.now()}-${Math.random()}`, action_type: 'click', element_id: '', element_page: '', locator_strategy: 'role', locator_value: '',
  locator_name: '', locator_options: {}, locator_options_json: '{}', input_value: '', wait_time: 1000, assert_type: 'textContains', assert_value: '', description: ''
}]
const removeStep = index => { localSteps.value = localSteps.value.filter((_, i) => i !== index) }
const needsInput = action => ['fill', 'press', 'select', 'switchTab', 'navigate'].includes(action)
const needsElement = step => !['wait', 'switchTab', 'screenshot', 'navigate', 'setVariable'].includes(step.action_type) && !(step.action_type === 'assert' && step.assert_type === 'urlContains')
const hasElement = step => Boolean(step.element_id)
const locatorOptionsText = options => JSON.stringify(options || {})
const getElementsForStep = step => step.element_page ? props.elements.filter(item => item.page === step.element_page) : props.elements
const elementOptionLabel = item => {
  const strategy = item.locator_strategy?.name || item.locator_strategy || ''
  return `${item.name} (${strategy ? `${strategy}=` : ''}${item.locator_value})`
}
const onPageChange = step => {
  const selected = props.elements.find(item => item.id === step.element_id)
  if (selected && selected.page !== step.element_page) {
    step.element_id = ''
    step.locator_strategy = 'role'
    step.locator_value = ''
    step.locator_name = ''
    step.locator_options = {}
    step.locator_options_json = '{}'
  }
  emitSteps()
}
const onActionChange = step => {
  if (!['fill', 'press', 'select', 'navigate', 'switchTab', 'setVariable'].includes(step.action_type)) step.input_value = ''
  if (!['wait', 'waitFor'].includes(step.action_type)) step.wait_time = 1000
  if (step.action_type !== 'assert') { step.assert_type = 'textContains'; step.assert_value = '' }
  if (!needsElement(step)) { step.element_id = ''; step.element_page = '' }
  emitSteps()
}
const onLocatorChange = step => {
  if (!['role', 'label', 'placeholder'].includes(step.locator_strategy)) {
    step.locator_name = ''
    if (step.locator_options?.name) {
      const { name, ...options } = step.locator_options
      step.locator_options = options
      step.locator_options_json = locatorOptionsText(options)
    }
  }
  if (!hasElement(step)) {
    step.locator_options = {}
    step.locator_options_json = '{}'
  }
  emitSteps()
}
const onLocatorNameInput = step => {
  const options = { ...(step.locator_options || {}) }
  if (step.locator_name) options.name = step.locator_name
  else delete options.name
  step.locator_options = options
  step.locator_options_json = locatorOptionsText(options)
  emitSteps()
}
// 选择元素后回填其页面、定位器及可读描述，避免用户重复录入。
const onElementChange = step => {
  const selected = props.elements.find(item => item.id === step.element_id)
  if (selected) {
    step.locator_value = selected.locator_value
    step.locator_strategy = selected.locator_strategy?.name?.toLowerCase() || step.locator_strategy
    step.locator_options = { ...(selected.locator_options || {}) }
    step.locator_options_json = locatorOptionsText(step.locator_options)
    step.locator_name = step.locator_options.name || ''
    step.element_page = selected.page || ''
    step.description ||= `${actions.find(item => item.value === step.action_type)?.label || ''}“${selected.name}”`
  } else {
    step.locator_strategy = 'role'
    step.locator_value = ''
    step.locator_name = ''
    step.locator_options = {}
    step.locator_options_json = '{}'
  }
  emitSteps()
}
</script>

<style scoped>
.structured-step-editor { height: 100%; overflow: auto; padding: 10px; }
.steps-toolbar, .step-header, .step-field { display: flex; align-items: center; gap: 8px; }
.steps-toolbar { justify-content: space-between; margin-bottom: 10px; font-weight: 600; }
.step-row { border: 1px solid var(--el-border-color); border-radius: 4px; padding: 9px; margin-bottom: 8px; display: grid; gap: 8px; }
.step-row.expanded { border-color: var(--el-color-primary-light-5); }
.step-header { min-width: 0; }
.step-header > .el-select { min-width: 105px; }
.step-header > .el-select:nth-of-type(2) { min-width: 150px; }
.step-content { display: grid; gap: 8px; min-width: 0; }
.step-field > .el-input { flex: 1; min-width: 0; }
.variable-set-field > .el-input { flex: 1 1 0; min-width: 0; }
.variable-set-field :deep(.el-input__inner) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.step-field :deep(.data-factory-button) { background-color: #409eff !important; border-color: #409eff !important; color: white !important; }
.step-field :deep(.data-factory-button:hover) { background-color: #66b1ff !important; border-color: #66b1ff !important; }
.step-field > .variable-helper-button { flex: 0 0 auto; background-color: #67c23a; border-color: #67c23a; color: white; }
.step-field > .variable-helper-button:hover { background-color: #5daf34; border-color: #5daf34; }
.locator-field > .el-select, .locator-field > .el-input { flex: 1 1 0; width: 0; min-width: 0; }
.description-field { width: 100%; }
.drag-handle { cursor: grab; color: var(--el-text-color-secondary); }
.step-number { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; flex: 0 0 24px; border-radius: 50%; background: #409eff; color: #fff; font-weight: 600; }
@media (max-width: 760px) {
  .step-header { flex-wrap: wrap; }
  .step-header > .el-select { flex: 1 1 140px; }
  .locator-field { flex-wrap: wrap; }
  .locator-field > .el-select, .locator-field > .el-input { flex: 1 1 0; width: 0; }
}
</style>
