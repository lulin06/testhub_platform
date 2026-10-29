<template>
  <div class="assertions-editor" :class="{ compact }">
    <div class="assertions-header">
      <el-button size="small" type="primary" @click="addAssertion">
        <el-icon><Plus /></el-icon>
        {{ $t('apiTesting.interface.addAssertion') }}
      </el-button>
    </div>

    <div class="assertions-list">
      <div v-for="(assertion, index) in assertions" :key="index" class="assertion-item">
        <div class="assertion-header">
          <el-input
            v-model="assertion.name"
            :placeholder="$t('apiTesting.interface.assertionName')"
            size="small"
            class="assertion-name"
          />
          <el-button size="small" type="danger" @click="removeAssertion(index)" circle>
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>

        <div class="assertion-config">
          <el-select
            v-model="assertion.type"
            :placeholder="$t('apiTesting.interface.selectAssertionType')"
            size="small"
            @change="resetAssertion(assertion)"
          >
            <el-option :label="$t('apiTesting.interface.assertionTypes.statusCode')" value="status_code" />
            <el-option :label="$t('apiTesting.interface.assertionTypes.responseTime')" value="response_time" />
            <el-option :label="$t('apiTesting.interface.assertionTypes.contains')" value="contains" />
            <el-option :label="$t('apiTesting.interface.assertionTypes.jsonPath')" value="json_path" />
            <el-option :label="$t('apiTesting.interface.assertionTypes.header')" value="header" />
            <el-option :label="$t('apiTesting.interface.assertionTypes.equals')" value="equals" />
          </el-select>

          <div v-if="assertion.type" class="assertion-params">
            <el-input-number
              v-if="assertion.type === 'status_code'"
              v-model="assertion.expected"
              :min="100"
              :max="599"
              size="small"
              :placeholder="$t('apiTesting.interface.expectedStatusCode')"
            />
            <el-input-number
              v-else-if="assertion.type === 'response_time'"
              v-model="assertion.expected"
              :min="1"
              size="small"
              :placeholder="$t('apiTesting.interface.maxResponseTime')"
            />
            <template v-else-if="assertion.type === 'json_path'">
              <el-input
                v-model="assertion.json_path"
                :placeholder="$t('apiTesting.interface.jsonPathExample')"
                size="small"
                class="assertion-input"
              />
              <AssertionValueInput
                v-model="assertion.expected"
                :placeholder="$t('apiTesting.interface.expectedValue')"
                :show-helpers="showHelpers"
                :assertion="assertion"
                field="expected"
                :index="index"
                @data-factory="emitHelper('data-factory', $event)"
                @variable-helper="emitHelper('variable-helper', $event)"
              />
            </template>
            <template v-else-if="assertion.type === 'header'">
              <el-input
                v-model="assertion.header_name"
                :placeholder="$t('apiTesting.interface.headerNameLabel')"
                size="small"
                class="assertion-input"
              />
              <AssertionValueInput
                v-model="assertion.expected_value"
                :placeholder="$t('apiTesting.interface.expectedValue')"
                :show-helpers="showHelpers"
                :assertion="assertion"
                field="expected_value"
                :index="index"
                @data-factory="emitHelper('data-factory', $event)"
                @variable-helper="emitHelper('variable-helper', $event)"
              />
            </template>
            <AssertionValueInput
              v-else
              v-model="assertion.expected"
              :placeholder="valuePlaceholder(assertion.type)"
              :show-helpers="showHelpers"
              :assertion="assertion"
              field="expected"
              :index="index"
              @data-factory="emitHelper('data-factory', $event)"
              @variable-helper="emitHelper('variable-helper', $event)"
            />
          </div>
        </div>
      </div>

      <div v-if="assertions.length === 0" class="no-assertions">
        <p>{{ $t('apiTesting.interface.noAssertions') }}</p>
        <el-button size="small" type="primary" @click="addAssertion">
          <el-icon><Plus /></el-icon>
          {{ $t('apiTesting.interface.addFirstAssertion') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Delete, Plus } from '@element-plus/icons-vue'
import AssertionValueInput from './AssertionValueInput.vue'
import {
  createAssertion,
  normalizeAssertions,
  resetAssertionFields
} from '@/utils/assertions'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  showHelpers: {
    type: Boolean,
    default: false
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'data-factory', 'variable-helper'])
const { t } = useI18n()
const assertions = computed({
  get: () => props.modelValue || [],
  set: value => emit('update:modelValue', value)
})

const addAssertion = () => {
  emit('update:modelValue', [
    ...normalizeAssertions(assertions.value),
    createAssertion(`${t('apiTesting.interface.assertion')}${assertions.value.length + 1}`)
  ])
}

const removeAssertion = (index) => {
  emit('update:modelValue', assertions.value.filter((_, itemIndex) => itemIndex !== index))
}

const resetAssertion = assertion => resetAssertionFields(assertion)
const emitHelper = (eventName, payload) => emit(eventName, payload)

const valuePlaceholder = type => (
  type === 'contains'
    ? 'apiTesting.interface.expectedContains'
    : 'apiTesting.interface.expectedMatch'
)
</script>

<style scoped>
.assertions-editor {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.assertions-editor.compact {
  padding: 0;
  border: 0;
  background: transparent;
}

.assertions-editor.compact .assertion-item {
  padding: 14px;
}

.assertions-editor.compact .assertions-list {
  max-height: 55vh;
  overflow-y: auto;
  padding-right: 6px;
}

.assertions-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e9ecef;
}

.assertions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.assertion-item {
  padding: 24px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 10px;
}

.assertion-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.assertion-name {
  flex: 1;
  margin-right: 12px;
}

.assertion-config,
.assertion-params {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assertion-config .el-select {
  width: 200px;
}

.assertion-input {
  margin-bottom: 12px;
}

.assertion-value-input {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 5px;
}

.assertion-value-input .el-input {
  flex: 1;
}

.no-assertions {
  text-align: center;
  color: #909399;
}
</style>

