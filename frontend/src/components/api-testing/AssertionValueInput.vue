<template>
  <div class="assertion-value-input">
    <el-input v-model="value" :placeholder="$t(placeholder)" size="small">
      <template v-if="showHelpers" #append>
        <el-button
          size="small"
          :icon="MagicStick"
          :title="$t('apiTesting.interface.referDataFactory')"
          @click="$emit('data-factory', { assertion, field, index })"
        />
      </template>
    </el-input>
    <el-tooltip
      v-if="showHelpers"
      :content="$t('apiTesting.interface.insertDynamicVariable')"
      placement="top"
    >
      <el-button
        size="small"
        class="variable-helper-btn"
        @click="$emit('variable-helper', { assertion, field, index })"
      >
        <el-icon><MagicStick /></el-icon>
      </el-button>
    </el-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { default: '' },
  assertion: { type: Object, required: true },
  field: { type: String, required: true },
  index: { type: Number, required: true },
  placeholder: { type: String, required: true },
  showHelpers: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'data-factory', 'variable-helper'])
const value = computed({
  get: () => props.modelValue,
  set: nextValue => emit('update:modelValue', nextValue)
})
</script>

<style scoped>
.assertion-value-input {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 5px;
}

.assertion-value-input .el-input {
  flex: 1;
}
</style>

