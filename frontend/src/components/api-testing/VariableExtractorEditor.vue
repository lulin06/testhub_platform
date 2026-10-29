<template>
  <div class="extractors-editor" :class="{ compact }">
    <div class="extractors-header">
      <span v-if="showTitle">{{ $t('apiTesting.interface.variableExtraction') }}</span>
      <el-button size="small" type="primary" @click="addExtractor">
        <el-icon><Plus /></el-icon>
        {{ $t('apiTesting.interface.addExtractor') }}
      </el-button>
    </div>

    <div v-if="extractors.length" class="extractors-list">
      <div v-for="(extractor, index) in extractors" :key="index" class="extractor-row">
        <el-input v-model="extractor.name" size="small" :placeholder="$t('apiTesting.interface.variableName')" />
        <el-select v-model="extractor.source" size="small" class="extractor-source">
          <el-option :label="$t('apiTesting.interface.responseBody')" value="body" />
        </el-select>
        <el-select v-model="extractor.type" size="small" class="extractor-type">
          <el-option label="JSONPath" value="json_path" />
        </el-select>
        <el-input
          v-model="extractor.expression"
          size="small"
          class="extractor-expression"
          :placeholder="$t('apiTesting.interface.jsonPathExtractorPlaceholder')"
        />
        <el-input
          v-model="extractor.default_value"
          size="small"
          class="extractor-default"
          :placeholder="$t('apiTesting.interface.defaultValue')"
        />
        <el-button size="small" type="danger" :icon="Delete" circle @click="removeExtractor(index)" />
      </div>
    </div>
    <el-empty
      v-else
      :description="$t('apiTesting.interface.noExtractors')"
      :image-size="64"
    />

    <div v-if="results?.length" class="extraction-results">
      <strong>{{ $t('apiTesting.interface.extractionResults') }}</strong>
      <div v-for="(result, index) in results" :key="`${result.name}-${index}`" class="extraction-result-row">
        <span>{{ result.name }}</span>
        <el-tag :type="result.success ? 'success' : 'danger'" size="small">
          {{ result.success ? formatValue(result.value) : result.error }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Delete, Plus } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  results: {
    type: Array,
    default: () => []
  },
  compact: {
    type: Boolean,
    default: false
  },
  showTitle: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])
const extractors = computed({
  get: () => props.modelValue || [],
  set: value => emit('update:modelValue', value)
})

const addExtractor = () => {
  emit('update:modelValue', [
    ...extractors.value,
    { name: '', source: 'body', type: 'json_path', expression: '', default_value: '', enabled: true }
  ])
}

const removeExtractor = index => {
  emit('update:modelValue', extractors.value.filter((_, itemIndex) => itemIndex !== index))
}

const formatValue = value => (
  typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '')
)
</script>

<style scoped>
.extractors-editor {
  padding: 20px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
}

.extractors-editor.compact {
  padding: 0;
  background: transparent;
  border: 0;
}

.extractors-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  font-weight: 600;
}

.extractor-row {
  display: grid;
  grid-template-columns: minmax(90px, 1fr) 90px 96px minmax(150px, 1.7fr) minmax(96px, 1fr) 36px;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.extractor-source,
.extractor-type,
.extractor-expression,
.extractor-default {
  width: 100%;
  min-width: 0;
}

.extractor-row :deep(.el-input),
.extractor-row :deep(.el-select) {
  min-width: 0;
}

.extraction-results {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid #e4e7ed;
}

.extraction-result-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.extraction-result-row > span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.extraction-result-row :deep(.el-tag) {
  justify-self: end;
  max-width: min(70%, 420px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .extractor-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
