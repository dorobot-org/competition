<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'
const router = useRouter()
const authStore = useAuthStore()

const instances = ref([])
const loading = ref(false)
const showModal = ref(false)
const modalMode = ref('add') // 'add' or 'edit'
const editingInstance = ref(null)
const error = ref('')
const success = ref('')

const formData = ref({
  instance_uuid: '',
  nickname: '',
  vnc_url: ''
})

async function fetchInstances() {
  loading.value = true
  try {
    const response = await axios.get(`${API_URL}/instances`, {
      headers: authStore.getAuthHeader()
    })
    instances.value = response.data
  } catch (err) {
    error.value = '获取实例列表失败'
    setTimeout(() => error.value = '', 3000)
  } finally {
    loading.value = false
  }
}

function openAddModal() {
  modalMode.value = 'add'
  formData.value = {
    instance_uuid: '',
    nickname: '',
    vnc_url: ''
  }
  showModal.value = true
  error.value = ''
}

function openEditModal(instance) {
  modalMode.value = 'edit'
  editingInstance.value = instance
  formData.value = {
    instance_uuid: instance.instance_uuid,
    nickname: instance.nickname,
    vnc_url: instance.vnc_url || ''
  }
  showModal.value = true
  error.value = ''
}

function closeModal() {
  showModal.value = false
  editingInstance.value = null
  error.value = ''
}

async function saveInstance() {
  if (!formData.value.instance_uuid) {
    error.value = '实例UUID为必填项'
    return
  }
  if (!formData.value.nickname) {
    error.value = '昵称为必填项'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const payload = {
      instance_uuid: formData.value.instance_uuid,
      nickname: formData.value.nickname,
      vnc_url: formData.value.vnc_url || null
    }

    if (modalMode.value === 'add') {
      await axios.post(`${API_URL}/instances`, payload, {
        headers: authStore.getAuthHeader()
      })
      success.value = '实例添加成功'
    } else {
      await axios.put(`${API_URL}/instances/${editingInstance.value.id}`, payload, {
        headers: authStore.getAuthHeader()
      })
      success.value = '实例更新成功'
    }
    closeModal()
    await fetchInstances()
    setTimeout(() => success.value = '', 3000)
  } catch (err) {
    console.error('Save instance error:', err.response?.data || err)
    error.value = err.response?.data?.detail || '保存实例失败'
  } finally {
    loading.value = false
  }
}

async function deleteInstance(instance) {
  if (!confirm(`确定要删除实例 "${instance.nickname}" 吗？`)) {
    return
  }

  loading.value = true
  try {
    await axios.delete(`${API_URL}/instances/${instance.id}`, {
      headers: authStore.getAuthHeader()
    })
    success.value = '实例删除成功'
    await fetchInstances()
    setTimeout(() => success.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || '删除实例失败'
    setTimeout(() => error.value = '', 5000)
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function goToAdmin() {
  router.push('/admin')
}

onMounted(() => {
  fetchInstances()
})
</script>

<template>
  <div class="instances-container">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <div class="logo-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 8h-3V6c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10h20V10c0-1.1-.9-2-2-2zM9 6h6v2H9V6zm11 12H4v-6h16v6z"/>
          </svg>
        </div>
        <div>
          <h1>GPU实例管理</h1>
          <p>手动添加和管理GPU实例</p>
        </div>
      </div>
      <div class="header-right">
        <span class="user-badge">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
          {{ authStore.user?.username }}
        </span>
        <button class="nav-btn" @click="goToAdmin">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
          </svg>
          用户管理
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

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon total">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 8h-3V6c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10h20V10c0-1.1-.9-2-2-2zM9 6h6v2H9V6zm11 12H4v-6h16v6z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ instances.length }}</span>
            <span class="stat-label">总实例数</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon available">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ instances.filter(i => !i.assigned_user_id).length }}</span>
            <span class="stat-label">可用实例</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon assigned">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ instances.filter(i => i.assigned_user_id).length }}</span>
            <span class="stat-label">已分配</span>
          </div>
        </div>
      </div>

      <!-- Instances Table -->
      <div class="table-container">
        <div class="table-header">
          <h2>实例列表</h2>
          <button class="add-btn" @click="openAddModal">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            添加实例
          </button>
        </div>

        <div v-if="loading && !instances.length" class="loading">
          <div class="spinner"></div>
          加载中...
        </div>

        <div class="table-wrapper">
          <table v-if="instances.length" class="instances-table">
            <thead>
              <tr>
                <th>昵称</th>
                <th>实例ID</th>
                <th>UUID</th>
                <th>VNC URL</th>
                <th>分配用户</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="instance in instances" :key="instance.id">
                <td class="nickname-cell">
                  <div class="instance-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 8h-3V6c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10h20V10c0-1.1-.9-2-2-2zM9 6h6v2H9V6z"/>
                    </svg>
                  </div>
                  {{ instance.nickname }}
                </td>
                <td class="mono">{{ instance.instance_id }}</td>
                <td class="mono uuid-cell">{{ instance.instance_uuid }}</td>
                <td class="url-cell">
                  <a v-if="instance.vnc_url" :href="instance.vnc_url" target="_blank" class="url-link">
                    {{ instance.vnc_url.length > 40 ? instance.vnc_url.substring(0, 40) + '...' : instance.vnc_url }}
                  </a>
                  <span v-else class="no-url">未设置</span>
                </td>
                <td>
                  <span v-if="instance.assigned_username" class="assigned-badge">
                    {{ instance.assigned_username }}
                  </span>
                  <span v-else class="available-badge">可用</span>
                </td>
                <td class="actions-cell">
                  <button class="action-btn edit" @click="openEditModal(instance)" title="编辑">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                  </button>
                  <button
                    class="action-btn delete"
                    @click="deleteInstance(instance)"
                    :disabled="instance.assigned_user_id"
                    :title="instance.assigned_user_id ? '已分配给用户，无法删除' : '删除'"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else-if="!loading" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 8h-3V6c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10h20V10c0-1.1-.9-2-2-2zM9 6h6v2H9V6zm11 12H4v-6h16v6z"/>
            </svg>
            <p>暂无GPU实例</p>
            <button class="add-btn-empty" @click="openAddModal">添加第一个实例</button>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ modalMode === 'add' ? '添加GPU实例' : '编辑GPU实例' }}</h3>
          <button class="close-btn" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <div v-if="error" class="modal-error">
          {{ error }}
        </div>

        <form @submit.prevent="saveInstance" class="modal-form">
          <div class="form-group">
            <label>实例UUID *</label>
            <input v-model="formData.instance_uuid" type="text" placeholder="例如 gghcmwa6-emgm7485" />
            <span class="hint">保存时将自动从GPUFree获取实例ID</span>
          </div>

          <div class="form-group">
            <label>昵称 *</label>
            <input v-model="formData.nickname" type="text" placeholder="例如 haidian-BOB专用2" />
          </div>

          <div class="form-group">
            <label>VNC URL（可选）</label>
            <input v-model="formData.vnc_url" type="url" placeholder="https://example.com/vnc" />
            <span class="hint">用户登录后自动跳转的目标地址</span>
          </div>

          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="closeModal">取消</button>
            <button type="submit" class="save-btn" :disabled="loading">
              {{ loading ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.instances-container {
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
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
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
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.nav-btn svg,
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

.stat-icon.total {
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
}

.stat-icon.available {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stat-icon.assigned {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
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
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
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
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-wrapper {
  overflow-x: auto;
}

.instances-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.instances-table th,
.instances-table td {
  padding: 16px 20px;
  text-align: left;
}

.instances-table th {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.instances-table tbody tr {
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.15s ease;
}

.instances-table tbody tr:hover {
  background: #f8fafc;
}

.instances-table tbody tr:last-child {
  border-bottom: none;
}

.nickname-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
  color: #1e293b;
}

.instance-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.instance-icon svg {
  width: 20px;
  height: 20px;
}

.mono {
  font-family: monospace;
  font-size: 13px;
  color: #475569;
}

.uuid-cell {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.url-cell {
  max-width: 250px;
}

.url-link {
  color: #6d28d9;
  text-decoration: none;
  font-size: 13px;
}

.url-link:hover {
  text-decoration: underline;
}

.no-url {
  color: #9ca3af;
  font-size: 13px;
}

.assigned-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #fef3c7;
  color: #d97706;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.available-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #dcfce7;
  color: #166534;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #64748b;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 20px;
}

.add-btn-empty {
  padding: 10px 24px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
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
  max-width: 500px;
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-group input {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1);
}

.hint {
  font-size: 12px;
  color: #64748b;
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
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  border: none;
  color: white;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
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
