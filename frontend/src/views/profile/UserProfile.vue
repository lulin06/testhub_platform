<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ $t('profile.title') }}</h1>
    </div>

    <div class="card-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="$t('profile.basicInfo')" name="basic">
          <el-form v-if="userStore.user" :model="profileForm" label-width="100px">
            <el-form-item :label="$t('profile.username')" prop="username">
              <el-input v-model="profileForm.username" maxlength="20" />
            </el-form-item>
            <el-form-item :label="$t('profile.email')">
              <el-input :model-value="userStore.user.email" disabled />
            </el-form-item>
            <el-form-item :label="$t('profile.name')">
              <el-input v-model="profileForm.first_name" />
            </el-form-item>
            <el-form-item :label="$t('profile.department')">
              <el-input v-model="profileForm.department" />
            </el-form-item>
            <el-form-item :label="$t('profile.position')">
              <el-input v-model="profileForm.position" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="profileSubmitting" @click="submitProfile">
                {{ $t('common.save') }}
              </el-button>
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
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api from '@/utils/api'

const userStore = useUserStore()
const activeTab = ref('basic')
const passwordFormRef = ref()
const passwordSubmitting = ref(false)
const profileSubmitting = ref(false)
const profileForm = reactive({ username: '', first_name: '', department: '', position: '' })
const passwordForm = reactive({ current_password: '', new_password: '', confirm_password: '' })
watch(() => userStore.user, (user) => {
  if (!user) return
  Object.assign(profileForm, {
    username: user.username || '',
    first_name: user.first_name || '',
    department: user.department || '',
    position: user.position || ''
  })
}, { immediate: true })
const passwordRules = {
  current_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '新密码至少 6 位', trigger: 'blur' }],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: (_rule, value, callback) => value !== passwordForm.new_password ? callback(new Error('两次输入的新密码不一致')) : callback(), trigger: 'blur' }
  ]
}

async function submitProfile() {
  profileSubmitting.value = true
  try {
    const response = await api.patch('/auth/profile/', profileForm)
    userStore.user = response.data
    localStorage.setItem('user', JSON.stringify(response.data))
    ElMessage.success('个人信息已保存')
  } catch (error) {
    const data = error.response?.data || {}
    const message = data.username?.[0] || data.detail || data.error || '个人信息保存失败'
    ElMessage.error(message)
  } finally {
    profileSubmitting.value = false
  }
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
