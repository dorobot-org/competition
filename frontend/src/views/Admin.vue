<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'
const router = useRouter()
const authStore = useAuthStore()

const users = ref([])
const userCount = ref({ count: 0, max: 15 })
const loading = ref(false)
const showModal = ref(false)
const modalMode = ref('add') // 'add' or 'edit'
const editingUser = ref(null)
const error = ref('')
const success = ref('')

const formData = ref({
  username: '',
  password: '',
  email: '',
  phone: '',
  target_url: '',
  is_admin: false,
  instance_id: '',
  instance_uuid: '',
  bearer_token: ''
})

const canAddMore = computed(() => userCount.value.count < userCount.value.max)

async function fetchUsers() {
  loading.value = true
  try {
    const response = await axios.get(`${API_URL}/users`, {
      headers: authStore.getAuthHeader()
    })
    users.value = response.data
  } catch (err) {
    error.value = 'Failed to fetch users'
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

function openAddModal() {
  if (!canAddMore.value) {
    error.value = `Maximum user limit reached (${userCount.value.max} users)`
    setTimeout(() => error.value = '', 3000)
    return
  }
  modalMode.value = 'add'
  formData.value = {
    username: '',
    password: '',
    email: '',
    phone: '',
    target_url: 'https://docs.swanlab.cn/guide_cloud/general/quick-start.html',
    is_admin: false,
    instance_id: '',
    instance_uuid: '',
    bearer_token: ''
  }
  showModal.value = true
  error.value = ''
}

function openEditModal(user) {
  modalMode.value = 'edit'
  editingUser.value = user
  formData.value = {
    username: user.username,
    password: '',
    email: user.email || '',
    phone: user.phone || '',
    target_url: user.target_url,
    is_admin: user.is_admin,
    instance_id: user.instance_id || '',
    instance_uuid: user.instance_uuid || '',
    bearer_token: user.bearer_token || ''
  }
  showModal.value = true
  error.value = ''
}

function closeModal() {
  showModal.value = false
  editingUser.value = null
  error.value = ''
}

async function saveUser() {
  if (!formData.value.username) {
    error.value = 'Username is required'
    return
  }
  if (modalMode.value === 'add' && !formData.value.password) {
    error.value = 'Password is required'
    return
  }
  if (!formData.value.target_url) {
    error.value = 'Target URL is required'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const payload = {
      ...formData.value,
      instance_id: formData.value.instance_id ? parseInt(formData.value.instance_id) : null,
      instance_uuid: formData.value.instance_uuid || null,
      bearer_token: formData.value.bearer_token || null,
      email: formData.value.email || null,
      phone: formData.value.phone || null
    }

    if (modalMode.value === 'add') {
      await axios.post(`${API_URL}/users`, payload, {
        headers: authStore.getAuthHeader()
      })
      success.value = 'User created successfully'
    } else {
      const updateData = { ...payload }
      if (!updateData.password) {
        delete updateData.password
      }
      await axios.put(`${API_URL}/users/${editingUser.value.id}`, updateData, {
        headers: authStore.getAuthHeader()
      })
      success.value = 'User updated successfully'
    }
    closeModal()
    await fetchUsers()
    await fetchUserCount()
    setTimeout(() => success.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save user'
  } finally {
    loading.value = false
  }
}

async function deleteUser(user) {
  if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) {
    return
  }

  loading.value = true
  try {
    await axios.delete(`${API_URL}/users/${user.id}`, {
      headers: authStore.getAuthHeader()
    })
    success.value = 'User deleted successfully'
    await fetchUsers()
    await fetchUserCount()
    setTimeout(() => success.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete user'
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
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  fetchUsers()
  fetchUserCount()
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
          <h1>Admin Console</h1>
          <p>Manage users and permissions</p>
        </div>
      </div>
      <div class="header-right">
        <span class="user-badge">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
          {{ authStore.user?.username }}
        </span>
        <button class="portal-btn" @click="goToPortal">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14z"/>
          </svg>
          Portal
        </button>
        <button class="logout-btn" @click="handleLogout">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
          </svg>
          Logout
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
            <span class="stat-label">Your Users</span>
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
            <span class="stat-label">User Limit</span>
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
            <span class="stat-label">Active Sessions</span>
          </div>
        </div>
      </div>

      <!-- Users Table -->
      <div class="table-container">
        <div class="table-header">
          <h2>User Management</h2>
          <button class="add-btn" @click="openAddModal" :disabled="!canAddMore">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            Add User
          </button>
        </div>

        <div v-if="loading && !users.length" class="loading">
          <div class="spinner"></div>
          Loading users...
        </div>

        <div class="table-wrapper">
          <table v-if="users.length" class="users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Instance</th>
                <th>Role</th>
                <th>State</th>
                <th>Last Login</th>
                <th>Actions</th>
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
                  <span v-else class="no-instance">Not configured</span>
                </td>
                <td>
                  <span :class="['role-badge', user.is_admin ? 'admin' : 'user']">
                    {{ user.is_admin ? 'Admin' : 'User' }}
                  </span>
                </td>
                <td>
                  <span :class="['state-badge', user.state]">
                    {{ user.state }}
                  </span>
                </td>
                <td>{{ formatDate(user.last_login) }}</td>
                <td class="actions-cell">
                  <button class="action-btn edit" @click="openEditModal(user)" title="Edit">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                  </button>
                  <button
                    class="action-btn delete"
                    @click="deleteUser(user)"
                    :disabled="user.id === authStore.user?.id || user.is_admin"
                    title="Delete"
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
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ modalMode === 'add' ? 'Add New User' : 'Edit User' }}</h3>
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
              <label>Username *</label>
              <input v-model="formData.username" type="text" placeholder="Enter username" />
            </div>
            <div class="form-group">
              <label>Password {{ modalMode === 'edit' ? '(leave blank to keep)' : '*' }}</label>
              <input v-model="formData.password" type="password" placeholder="Enter password" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Email</label>
              <input v-model="formData.email" type="email" placeholder="user@example.com" />
            </div>
            <div class="form-group">
              <label>Phone</label>
              <input v-model="formData.phone" type="tel" placeholder="Phone number" />
            </div>
          </div>

          <div class="form-group">
            <label>Target URL *</label>
            <input v-model="formData.target_url" type="url" placeholder="https://example.com" />
          </div>

          <div class="form-section">
            <h4>GPU Instance Configuration</h4>
            <div class="form-row">
              <div class="form-group">
                <label>Instance ID</label>
                <input v-model="formData.instance_id" type="number" placeholder="e.g. 7764" />
              </div>
              <div class="form-group">
                <label>Instance UUID</label>
                <input v-model="formData.instance_uuid" type="text" placeholder="e.g. gghcmwa6-emgm7485" />
              </div>
            </div>
            <div class="form-group">
              <label>Bearer Token (optional)</label>
              <textarea v-model="formData.bearer_token" placeholder="GPUFree API bearer token" rows="2"></textarea>
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="formData.is_admin" type="checkbox" />
              <span class="checkmark"></span>
              Administrator privileges
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="closeModal">Cancel</button>
            <button type="submit" class="save-btn" :disabled="loading">
              {{ loading ? 'Saving...' : 'Save User' }}
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

.portal-btn:hover,
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

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
.modal-form textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
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
