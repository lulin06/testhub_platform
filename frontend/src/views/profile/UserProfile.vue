<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ $t('profile.title') }}</h1>
    </div>

    <div class="card-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="$t('profile.basicInfo')" name="basic">
          <el-form v-if="userStore.user" :model="userStore.user" label-width="100px">
            <el-form-item :label="$t('profile.username')">
              <el-input v-model="userStore.user.username" disabled />
            </el-form-item>
            <el-form-item :label="$t('profile.email')">
              <el-input v-model="userStore.user.email" />
            </el-form-item>
            <el-form-item :label="$t('profile.name')">
              <el-input v-model="userStore.user.first_name" />
            </el-form-item>
            <el-form-item :label="$t('profile.department')">
              <el-input v-model="userStore.user.department" />
            </el-form-item>
            <el-form-item :label="$t('profile.position')">
              <el-input v-model="userStore.user.position" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary">{{ $t('common.save') }}</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane :label="$t('profile.changePassword')" name="password">
          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="120px">
            <el-form-item :label="$t('profile.currentPassword')" prop="current_password">
              <el-input v-model="passwordForm.current_password" type="password" show-password autocomplete="current-password" />
            </el-form-item>
            <el-form-item :label="$t('profile.newPassword')" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password autocomplete="new-password" />
            </el-form-item>
            <el-form-item :label="$t('profile.confirmPassword')" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password autocomplete="new-password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordSubmitting" @click="submitPasswordChange">{{ $t('profile.changePasswordButton') }}</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const userStore = useUserStore()
const activeTab = ref('basic')
const passwordFormRef = ref()
const passwordSubmitting = ref(false)
const passwordForm = reactive({ current_password: '', new_password: '', confirm_password: '' })
const passwordRules = {
  current_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '新密码至少 6 位', trigger: 'blur' }],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: (_rule, value, callback) => value !== passwordForm.new_password ? callback(new Error('两次输入的新密码不一致')) : callback(), trigger: 'blur' }
  ]
}

async function submitPasswordChange() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return
  passwordSubmitting.value = true
  try {
    await api.post('/auth/change-password/', { ...passwordForm })
    ElMessage.success('密码修改成功，请使用新密码登录')
    Object.assign(passwordForm, { current_password: '', new_password: '', confirm_password: '' })
    passwordFormRef.value?.resetFields()
  } catch (error) {
    const data = error.response?.data || {}
    const message = typeof data === 'string' ? data : data.current_password || data.detail || data.error || data.confirm_password || '密码修改失败'
    ElMessage.error(message)
  } finally {
    passwordSubmitting.value = false
  }
}
</script>
