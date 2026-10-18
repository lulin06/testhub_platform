<template>
  <el-dialog v-model="dialogVisible" :title="$t('uiAutomation.replay.title')" width="760px" :close-on-click-modal="false" destroy-on-close>
    <div v-if="script" class="replay-header">
      <span>{{ $t('uiAutomation.replay.currentScript') }}</span>
      <el-tag :type="statusType">{{ statusText }}</el-tag>
      <div class="replay-actions">
        <el-select v-model="form.browser" size="small" style="width: 150px">
          <el-option label="Chromium" value="chromium" />
        </el-select>
        <el-checkbox v-model="form.headless">{{ $t('uiAutomation.replay.headless') }}</el-checkbox>
        <el-button type="primary" size="small" :loading="running" :disabled="running" @click="run">
          <el-icon><VideoPlay /></el-icon>{{ $t('uiAutomation.common.run') }}
        </el-button>
      </div>
    </div>
    <el-input v-model="form.base_url" :placeholder="$t('uiAutomation.replay.baseUrlPlaceholder')" class="base-url" />
    <div class="log-title"><span>{{ $t('uiAutomation.replay.executionLogs') }}</span><el-button text size="small" @click="logs = ''">{{ $t('uiAutomation.replay.clear') }}</el-button></div>
    <pre class="log-panel">{{ logs || $t('uiAutomation.replay.emptyLogs') }}</pre>
    <el-alert v-if="errorMessage" :title="errorMessage" type="error" :closable="false" />
    <template #footer>
      <el-button v-if="running" type="danger" plain @click="abort">{{ $t('uiAutomation.common.stop') }}</el-button>
      <el-button @click="close">{{ $t('uiAutomation.common.close') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { abortTestScriptExecution, getTestExecutionLogs, runRecordedScript, runUnsavedRecordedScript } from '@/api/ui_automation'

const props = defineProps({ visible: Boolean, script: { type: Object, default: null } })
const emit = defineEmits(['update:visible', 'started'])
const { t } = useI18n()
const dialogVisible = computed({ get: () => props.visible, set: value => emit('update:visible', value) })
const form = reactive({ browser: 'chromium', headless: true, base_url: '' })
const executionId = ref(null)
const status = ref('IDLE')
const logs = ref('')
const errorMessage = ref('')
const submitting = ref(false)
const running = computed(() => submitting.value || Boolean(executionId.value && ['PENDING', 'RUNNING'].includes(status.value)))
let timer = null

const statusType = computed(() => ({ SUCCESS: 'success', FAILED: 'danger', ABORTED: 'info', RUNNING: 'warning' }[status.value] || 'info'))
const statusText = computed(() => ({ IDLE: t('uiAutomation.status.ready'), PENDING: t('uiAutomation.status.pending'), RUNNING: t('uiAutomation.status.running'), SUCCESS: t('uiAutomation.status.success'), FAILED: t('uiAutomation.status.failed'), ABORTED: t('uiAutomation.status.aborted') }[status.value] || status.value))
watch(() => props.visible, value => { if (value) reset() })
watch(executionId, value => { if (value) poll() })

const reset = () => {
  stopPolling()
  executionId.value = null
  status.value = 'IDLE'
  submitting.value = false
  logs.value = ''
  errorMessage.value = ''
  form.browser = 'chromium'
  form.headless = true
  form.base_url = props.script?.start_url || ''
}

const run = async () => {
  if (!props.script || running.value) return
  errorMessage.value = ''
  submitting.value = true
  try {
    const response = props.script.id
      ? await runRecordedScript(props.script.id, form)
      : await runUnsavedRecordedScript({
          ...form,
          project: props.script.project_id || props.script.project?.id,
          content: props.script.content,
          start_url: props.script.start_url || ''
        })
    executionId.value = response.data.id
    status.value = response.data.status || 'PENDING'
    emit('started', response.data)
  } catch (error) {
    errorMessage.value = error.response?.data?.error || t('uiAutomation.replay.runFailed')
  } finally {
    submitting.value = false
  }
}

const poll = () => {
  stopPolling()
  const fetchLogs = async () => {
    if (!executionId.value) return
    try {
      const response = await getTestExecutionLogs(executionId.value)
      status.value = response.data.status
      logs.value = response.data.logs || ''
      errorMessage.value = response.data.error_message || ''
      if (!['PENDING', 'RUNNING'].includes(status.value)) stopPolling()
    } catch (error) { errorMessage.value = error.response?.data?.error || t('uiAutomation.replay.logsFailed') }
  }
  fetchLogs()
  timer = window.setInterval(fetchLogs, 1500)
}

const abort = async () => {
  if (!executionId.value) return
  try { await abortTestScriptExecution(executionId.value); status.value = 'ABORTED'; stopPolling(); ElMessage.success(t('uiAutomation.replay.abortSuccess')) } catch (error) { errorMessage.value = error.response?.data?.error || t('uiAutomation.replay.abortFailed') }
}
const stopPolling = () => { if (timer) { window.clearInterval(timer); timer = null } }
const close = () => { stopPolling(); dialogVisible.value = false }
onBeforeUnmount(stopPolling)
</script>

<style scoped>
.replay-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; color: #4d5562; }
.replay-actions { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.base-url { margin-bottom: 16px; }
.log-title { display: flex; justify-content: space-between; align-items: center; padding: 9px 12px; color: #5a626e; border: 1px solid #e8eaee; border-bottom: 0; background: #f8fafb; }
.log-panel { height: 300px; margin: 0 0 14px; padding: 15px; overflow: auto; border-radius: 0 0 6px 6px; background: var(--el-bg-color-page); color: var(--el-text-color-primary); border: 1px solid var(--el-border-color); font: 13px/1.65 Monaco, Consolas, monospace; white-space: pre-wrap; }
</style>
