<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'
const router = useRouter()
const authStore = useAuthStore()

const users = ref([])
const userCount = ref({ count: 0, max: 15 })
const availableInstances = ref([])
const loading = ref(false)
const showModal = ref(false)
const modalMode = ref('add') // 'add' or 'edit'
const editingUser = ref(null)
const error = ref('')
const success = ref('')
const defaultPassword = ref('')
const originalPassword = ref('')  // Track original password to detect changes

const formData = ref({
  username: '',
  password: '',
  email: '',
  phone: '',
  target_url: '',
  is_admin: false,
  bearer_token: '',
  gpu_instance_id: null
})

const canAddMore = computed(() => userCount.value.count < userCount.value.max && availableInstances.value.length > 0)

// Generate random 8-digit password
function generatePassword() {
  return Math.floor(10000000 + Math.random() * 90000000).toString()
}

// Watch phone field to suggest password and email
watch(() => formData.value.phone, (newPhone) => {
  if (newPhone) {
    // Suggest password for add mode
    if (modalMode.value === 'add' && !formData.value.password) {
      defaultPassword.value = generatePassword()
      formData.value.password = defaultPassword.value
    }
    // Suggest email based on phone
    if (!formData.value.email) {
      formData.value.email = `${newPhone}@example.com`
    }
  }
})

async function fetchUsers() {
  loading.value = true
  try {
    const response = await axios.get(`${API_URL}/users`, {
      headers: authStore.getAuthHeader()
    })
    users.value = response.data
  } catch (err) {
    error.value = '获取用户列表失败'
  } finally {
    loading.value = false
  }
}

async function fetchUserCount() {
  try {
    const response = await axios.get(`${API_URL}/users/count`, {
      headers: authStore.getAuthHeader()
    })
    userCount.value = response.data
  } catch (err) {
    console.error('Failed to fetch user count')
  }
}

async function fetchAvailableInstances() {
  try {
    const response = await axios.get(`${API_URL}/instances/available`, {
      headers: authStore.getAuthHeader()
    })
    availableInstances.value = response.data
  } catch (err) {
    console.error('Failed to fetch available instances')
  }
}

function goToInstances() {
  router.push('/instances')
}

function openAddModal() {
  if (availableInstances.value.length <= 0) {
    error.value = '没有可用的GPU实例，请先添加实例'
    setTimeout(() => error.value = '', 3000)
    return
  }
  if (!canAddMore.value) {
    error.value = `已达到用户上限（最多 ${userCount.value.max} 个用户）`
    setTimeout(() => error.value = '', 3000)
    return
  }
  modalMode.value = 'add'
  defaultPassword.value = ''
  formData.value = {
    username: '',
    password: '',
    email: '',
    phone: '',
    target_url: '',
    is_admin: false,
    bearer_token: '',
    gpu_instance_id: null
  }
  showModal.value = true
  error.value = ''
}

function openEditModal(user) {
  modalMode.value = 'edit'
  editingUser.value = user
  defaultPassword.value = ''
  originalPassword.value = user.plain_password || ''  // Store original to detect changes
  formData.value = {
    username: user.username,
    password: user.plain_password || '',  // Show plaintext password from DB
    email: user.email || '',
    phone: user.phone || '',
    target_url: user.target_url,
    is_admin: user.is_admin,
    bearer_token: user.bearer_token || '',
    gpu_instance_id: null
  }
  showModal.value = true
  error.value = ''
}

// Watch GPU instance selection to auto-fill URL
watch(() => formData.value.gpu_instance_id, (newId) => {
  if (modalMode.value === 'add' && newId) {
    const instance = availableInstances.value.find(i => i.id === newId)
    if (instance && instance.vnc_url) {
      formData.value.target_url = instance.vnc_url
    }
  }
})

function closeModal() {
  showModal.value = false
  editingUser.value = null
  error.value = ''
}

async function saveUser() {
  // Validate required fields for add mode
  if (modalMode.value === 'add') {
    if (!formData.value.username) {
      error.value = '用户名为必填项'
      return
    }
    if (!formData.value.phone) {
      error.value = '手机号为必填项'
      return
    }
    if (!formData.value.password) {
      error.value = '密码为必填项'
      return
    }
  }

  loading.value = true
  error.value = ''

  try {
    const payload = {
      ...formData.value,
      bearer_token: formData.value.bearer_token || null,
      email: formData.value.email || null,
      phone: formData.value.phone || null
    }

    if (modalMode.value === 'add') {
      await axios.post(`${API_URL}/users`, payload, {
        headers: authStore.getAuthHeader()
      })
      success.value = '用户创建成功'
    } else {
      const updateData = { ...payload }
      // Only send password if it was actually changed from original
      if (updateData.password === originalPassword.value) {
        delete updateData.password
      }
      await axios.put(`${API_URL}/users/${editingUser.value.id}`, updateData, {
        headers: authStore.getAuthHeader()
      })
      success.value = '用户更新成功'
    }
    closeModal()
    await fetchUsers()
    await fetchUserCount()
    await fetchAvailableInstances()
    setTimeout(() => success.value = '', 3000)
  } catch (err) {
    console.error('Save user error:', err.response?.data || err)
    error.value = err.response?.data?.detail || '保存用户失败'
    // Scroll modal to top to show error
    const modal = document.querySelector('.modal')
    if (modal) modal.scrollTop = 0
  } finally {
    loading.value = false
  }
}

async function deleteUser(user) {
  if (!confirm(`确定要删除用户 "${user.username}" 吗？`)) {
    return
  }

  loading.value = true
  try {
    await axios.delete(`${API_URL}/users/${user.id}`, {
      headers: authStore.getAuthHeader()
    })
    success.value = '用户删除成功'
    await fetchUsers()
    await fetchUserCount()
    await fetchAvailableInstances()
    setTimeout(() => success.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || '删除用户失败'
    setTimeout(() => error.value = '', 3000)
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function goToPortal() {
  router.push('/portal')
}

function formatDate(dateString) {
  if (!dateString) return '从未'
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchUsers()
  fetchUserCount()
  fetchAvailableInstances()
})
</script>

<template>
  <div class="admin-container">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <div class="logo-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <div>
          <h1>管理控制台</h1>
          <p>海淀工匠杯预赛用户管理</p>
        </div>
      </div>
      <div class="header-right">
        <span class="user-badge">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
          {{ authStore.user?.username }}
        </span>
        <button class="nav-btn" @click="goToInstances">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 8h-3V6c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10h20V10c0-1.1-.9-2-2-2zM9 6h6v2H9V6zm11 12H4v-6h16v6z"/>
          </svg>
          GPU实例
        </button>
        <button class="portal-btn" @click="goToPortal">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14z"/>
          </svg>
          比赛页面
        </button>
        <button class="logout-btn" @click="handleLogout">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
          </svg>
          退出
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Alerts -->
      <div v-if="success" class="alert success">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
        {{ success }}
      </div>

      <div v-if="error && !showModal" class="alert error">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        {{ error }}
      </div>

      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon users">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ users.filter(u => !u.is_admin).length }}</span>
            <span class="stat-label">选手数量</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon limit">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14h-2V7h2v10z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ userCount.count }} / {{ userCount.max }}</span>
            <span class="stat-label">用户上限</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon active">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ users.filter(u => u.state === 'active').length }}</span>
            <span class="stat-label">活跃会话</span>
          </div>
        </div>
        <div class="stat-card gpu-card" @click="goToInstances" style="cursor: pointer;">
          <div class="stat-icon gpu">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 8h-3V6c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10h20V10c0-1.1-.9-2-2-2zM9 6h6v2H9V6zm11 12H4v-6h16v6z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ availableInstances.length }}</span>
            <span class="stat-label">可用GPU实例</span>
          </div>
          <span class="manage-link">管理 &rarr;</span>
        </div>
      </div>

      <!-- Users Table -->
      <div class="table-container">
        <div class="table-header">
          <h2>用户管理</h2>
          <button class="add-btn" @click="openAddModal" :disabled="!canAddMore">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            添加用户
          </button>
        </div>

        <div v-if="loading && !users.length" class="loading">
          <div class="spinner"></div>
          加载中...
        </div>

        <div class="table-wrapper">
          <table v-if="users.length" class="users-table">
            <thead>
              <tr>
                <th>用户名</th>
                <th>邮箱</th>
                <th>手机号</th>
                <th>实例</th>
                <th>角色</th>
                <th>状态</th>
                <th>最后登录</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td class="username-cell">
                  <div class="user-avatar">{{ user.username[0].toUpperCase() }}</div>
                  {{ user.username }}
                </td>
                <td>{{ user.email || '-' }}</td>
                <td>{{ user.phone || '-' }}</td>
                <td class="instance-cell">
                  <span v-if="user.instance_id" class="instance-badge">
                    {{ user.instance_id }}
                  </span>
                  <span v-else class="no-instance">未配置</span>
                </td>
                <td>
                  <span :class="['role-badge', user.is_admin ? 'admin' : 'user']">
                    {{ user.is_admin ? '管理员' : '选手' }}
                  </span>
                </td>
                <td>
                  <span :class="['state-badge', user.state]">
                    {{ user.state === 'active' ? '在线' : '离线' }}
                  </span>
                </td>
                <td>{{ formatDate(user.last_login) }}</td>
                <td class="actions-cell">
                  <button class="action-btn edit" @click="openEditModal(user)" title="编辑">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                  </button>
                  <button
                    class="action-btn delete"
                    @click="deleteUser(user)"
                    :disabled="user.id === authStore.user?.id || user.is_admin"
                    title="删除"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ modalMode === 'add' ? '添加新用户' : '编辑用户' }}</h3>
          <button class="close-btn" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <div v-if="error" class="modal-error">
          {{ error }}
        </div>

        <form @submit.prevent="saveUser" class="modal-form">
          <div class="form-row">
            <div class="form-group">
              <label>用户名 *</label>
              <input v-model="formData.username" type="text" placeholder="输入用户名" />
            </div>
            <div class="form-group">
              <label>手机号 *</label>
              <input v-model="formData.phone" type="tel" placeholder="输入手机号" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>密码{{ modalMode === 'add' ? ' *' : '' }}</label>
              <input v-model="formData.password" type="text" :placeholder="modalMode === 'add' ? '输入手机号后自动生成' : '修改后保存生效'" />
              <span v-if="modalMode === 'add' && defaultPassword" class="password-hint">
                建议密码: {{ defaultPassword }}
              </span>
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input v-model="formData.email" type="email" :placeholder="formData.phone ? formData.phone + '@example.com' : 'user@example.com'" />
              <span v-if="!formData.email && formData.phone" class="hint">建议: {{ formData.phone }}@example.com</span>
            </div>
          </div>

          <div class="form-group">
            <label>目标URL{{ modalMode === 'add' ? '（由实例自动填充）' : '' }}</label>
            <input
              v-model="formData.target_url"
              type="url"
              :placeholder="modalMode === 'add' ? '选择GPU实例后自动填充' : 'https://example.com'"
              :readonly="modalMode === 'add'"
              :class="{ 'readonly-input': modalMode === 'add' }"
            />
          </div>

          <div class="form-section">
            <h4>GPU 实例配置</h4>
            <!-- Show instance info as read-only in edit mode -->
            <div v-if="modalMode === 'edit'" class="form-row">
              <div class="form-group">
                <label>实例ID（不可修改）</label>
                <div class="readonly-field">
                  <span v-if="editingUser?.instance_id" class="instance-badge">{{ editingUser.instance_id }}</span>
                  <span v-else class="no-instance">未分配</span>
                </div>
              </div>
              <div class="form-group">
                <label>实例UUID</label>
                <div class="readonly-field">
                  <span v-if="editingUser?.instance_uuid" class="uuid-text">{{ editingUser.instance_uuid }}</span>
                  <span v-else class="no-instance">未分配</span>
                </div>
              </div>
            </div>
            <!-- Show dropdown for add mode -->
            <div v-else class="form-group">
              <label>选择GPU实例 *</label>
              <select v-model="formData.gpu_instance_id" class="instance-select">
                <option :value="null" disabled>请选择GPU实例</option>
                <option v-for="inst in availableInstances" :key="inst.id" :value="inst.id">
                  {{ inst.nickname }} (ID: {{ inst.instance_id }})
                </option>
              </select>
              <span class="hint">选择后将自动填充目标URL</span>
            </div>
            <div class="form-group">
              <label>Bearer Token（可选）</label>
              <textarea v-model="formData.bearer_token" placeholder="GPUFree API bearer token" rows="2"></textarea>
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label" :class="{ disabled: modalMode === 'edit' }">
              <input v-model="formData.is_admin" type="checkbox" :disabled="modalMode === 'edit'" />
              <span class="checkmark"></span>
              管理员权限 {{ modalMode === 'edit' ? '（不可修改）' : '' }}
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="closeModal">取消</button>
            <button type="submit" class="save-btn" :disabled="loading">
              {{ loading ? '保存中...' : '保存用户' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: #f1f5f9;
}

.header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 28px;
  height: 28px;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.header-left p {
  font-size: 14px;
  opacity: 0.8;
  margin: 4px 0 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 14px;
}

.user-badge svg {
  width: 20px;
  height: 20px;
}

.nav-btn,
.portal-btn,
.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-btn:hover,
.portal-btn:hover,
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.nav-btn svg,
.portal-btn svg,
.logout-btn svg {
  width: 18px;
  height: 18px;
}

.main-content {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  font-weight: 500;
}

.alert.success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.alert.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.alert svg {
  width: 20px;
  height: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.users {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.limit {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stat-icon.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stat-icon.gpu {
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
}

.gpu-card {
  position: relative;
}

.gpu-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.manage-link {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 13px;
  color: #8b5cf6;
  font-weight: 500;
}

.sync-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: auto;
}

.sync-btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #1e293b;
}

.sync-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sync-btn svg {
  width: 16px;
  height: 16px;
}

.sync-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
}

.table-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.table-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.add-btn svg {
  width: 20px;
  height: 20px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #64748b;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-wrapper {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
}

.users-table th,
.users-table td {
  padding: 16px 20px;
  text-align: left;
}

.users-table th {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.users-table tbody tr {
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.15s ease;
}

.users-table tbody tr:hover {
  background: #f8fafc;
}

.users-table tbody tr:last-child {
  border-bottom: none;
}

.username-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
  color: #1e293b;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.instance-cell {
  font-family: monospace;
}

.instance-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.no-instance {
  color: #9ca3af;
  font-size: 13px;
}

.role-badge,
.state-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.role-badge.admin {
  background: #fef3c7;
  color: #d97706;
}

.role-badge.user {
  background: #e0e7ff;
  color: #4f46e5;
}

.state-badge.active {
  background: #dcfce7;
  color: #166534;
}

.state-badge.inactive {
  background: #f1f5f9;
  color: #64748b;
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.edit {
  background: #e0e7ff;
  color: #4f46e5;
}

.action-btn.edit:hover {
  background: #c7d2fe;
}

.action-btn.delete {
  background: #fee2e2;
  color: #dc2626;
}

.action-btn.delete:hover:not(:disabled) {
  background: #fecaca;
}

.action-btn.delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease;
}

.close-btn:hover {
  background: #e2e8f0;
}

.close-btn svg {
  width: 20px;
  height: 20px;
  color: #64748b;
}

.modal-error {
  margin: 16px 24px 0;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

.modal-form {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-section {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin-top: 8px;
}

.form-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 16px;
}

.modal-form .form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.modal-form label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.modal-form input[type="text"],
.modal-form input[type="password"],
.modal-form input[type="email"],
.modal-form input[type="tel"],
.modal-form input[type="number"],
.modal-form input[type="url"],
.modal-form textarea {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s ease;
  width: 100%;
}

.modal-form textarea {
  resize: vertical;
  font-family: monospace;
  font-size: 12px;
}

.modal-form input:focus,
.modal-form textarea:focus,
.modal-form select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.instance-select {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s ease;
  width: 100%;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2364748b'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 20px;
}

.instance-select:hover {
  border-color: #cbd5e1;
}

.hint {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.checkbox-group {
  margin-top: 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  font-weight: 400 !important;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  accent-color: #667eea;
}

.checkbox-label.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.password-hint {
  font-size: 12px;
  color: #10b981;
  margin-top: 4px;
  font-family: monospace;
}

.readonly-input {
  background: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

.readonly-field {
  padding: 12px 16px;
  background: #f8fafc;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  min-height: 44px;
  display: flex;
  align-items: center;
}

.readonly-field .instance-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  font-family: monospace;
}

.readonly-field .uuid-text {
  font-family: monospace;
  font-size: 13px;
  color: #475569;
}

.readonly-field .no-instance {
  color: #9ca3af;
  font-size: 14px;
}

.instance-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  color: #1e40af;
  font-size: 14px;
}

.instance-hint svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.cancel-btn,
.save-btn {
  flex: 1;
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #64748b;
}

.cancel-btn:hover {
  background: #e2e8f0;
}

.save-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.save-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
