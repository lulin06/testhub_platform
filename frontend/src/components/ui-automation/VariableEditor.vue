<template>
  <div class="ui-variable-editor">
    <div class="variable-toolbar">
      <p>{{ t('uiAutomation.variables.hint') }}</p>
      <el-button type="primary" plain :icon="Plus" @click="add">{{ t('uiAutomation.variables.add') }}</el-button>
    </div>
    <el-empty v-if="!modelValue.length" :description="t('uiAutomation.variables.empty')" :image-size="70" />
    <div class="variable-list">
      <div v-for="(row, index) in modelValue" :key="index" class="variable-row">
        <el-input v-model="row.name" class="variable-name" :placeholder="t('uiAutomation.variables.name')" :aria-label="t('uiAutomation.variables.name')" />
        <el-select v-model="row.type" :aria-label="t('uiAutomation.variables.type')" @change="resetValue(row)">
          <el-option v-for="type in types" :key="type" :label="type" :value="type" />
        </el-select>
        <el-input v-model="row.value" class="variable-value" :placeholder="t('uiAutomation.variables.value')" :aria-label="t('uiAutomation.variables.value')" />
        <el-input v-model="row.description" :placeholder="t('uiAutomation.variables.description')" :aria-label="t('uiAutomation.variables.description')" />
        <el-button text type="danger" @click="remove(index)">{{ t('uiAutomation.variables.remove') }}</el-button>
      </div>
    </div>
    <div class="syntax-guide">
      <span>{{ t('uiAutomation.variables.syntax') }}</span>
      <code v-pre>{{user.name}}</code>
      <code v-pre>{{items[0].id}}</code>
      <code>${random_string(8)}</code>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
const { t } = useI18n()
const props = defineProps({ modelValue: { type: Array, required: true } })
const emit = defineEmits(['update:modelValue'])
const types = ['string', 'number', 'boolean', 'array', 'object']
const resetValue = row => {
  row.value = { string: '', number: '0', boolean: 'false', array: '[]', object: '{}' }[row.type]
  delete row._originalValue
}
const add = () => emit('update:modelValue', [...props.modelValue, { name: '', type: 'string', value: '', description: '' }])
const remove = index => emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
</script>

<style scoped>
.variable-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin: 12px 0; }
.variable-toolbar p { margin: 0; color: var(--el-text-color-secondary); font-size: 13px; line-height: 1.6; }
.variable-list { overflow-x: auto; }
.variable-row { display: grid; grid-template-columns: minmax(130px, 1.2fr) minmax(100px, .9fr) minmax(150px, 1.3fr) minmax(150px, 1.3fr) auto; gap: 8px; align-items: center; min-width: 650px; margin-bottom: 10px; }
.variable-row > * { min-width: 0; }
.variable-row .el-select { width: 100%; }
.variable-row .el-button { margin: 0; padding: 8px; }
.syntax-guide { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 12px; color: var(--el-text-color-secondary); padding: 4px 0; }
.syntax-guide code { background: var(--el-fill-color-light); border-radius: 4px; padding: 3px 6px; overflow-wrap: anywhere; }
@media (max-width: 700px) {
  .variable-toolbar { align-items: flex-start; gap: 10px; }
}
</style>
