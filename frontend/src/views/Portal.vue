<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { API_URL } from '../config'
import axios from 'axios'
const router = useRouter()
const authStore = useAuthStore()

const targetUrl = ref('')
const userState = ref('inactive')
const loading = ref(false)
const actionLoading = ref(false)
const showIframe = ref(false)
const pollingStatus = ref(false)
const statusMessage = ref('')
const pollingInterval = ref(null)
const currentTime = ref('')
const timeInterval = ref(null)
const heartbeatInterval = ref(null)
const HEARTBEAT_INTERVAL = 30000  // Send heartbeat every 30 seconds

// Heartbeat functions for inactivity detection
async function sendHeartbeat() {
  try {
    await axios.post(`${API_URL}/portal/heartbeat`, {}, {
      headers: authStore.getAuthHeader()
    })
  } catch (err) {
    console.error('Failed to send heartbeat')
  }
}

function startHeartbeat() {
  // Send immediately, then every 30 seconds
  sendHeartbeat()
  heartbeatInterval.value = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL)
}

function stopHeartbeat() {
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value)
    heartbeatInterval.value = null
  }
}

const isActive = computed(() => userState.value === 'active')
const isPolling = computed(() => pollingStatus.value)
const hasInstance = computed(() => authStore.user?.instance_id != null)

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

async function fetchTargetUrl() {
  loading.value = true
  try {
    const response = await axios.get(`${API_URL}/portal/target-url`, {
      headers: authStore.getAuthHeader()
    })
    targetUrl.value = response.data.target_url
    userState.value = response.data.state

    if (userState.value === 'active') {
      showIframe.value = true
      // Start heartbeat if already active (e.g., page refresh)
      startHeartbeat()
    }
  } catch (err) {
    console.error('Failed to load portal information')
  } finally {
    loading.value = false
  }
}

async function queryInstanceStatus() {
  try {
    const response = await axios.get(`${API_URL}/portal/query-instance`, {
      headers: authStore.getAuthHeader()
    })
    return response.data
  } catch (err) {
    console.error('Failed to query instance status')
    return null
  }
}

async function handleStart() {
  actionLoading.value = true
  statusMessage.value = '正在发送启动请求...'

  try {
    const response = await axios.post(
      `${API_URL}/portal/action`,
      { action: 'start' },
      { headers: authStore.getAuthHeader() }
    )

    if (response.data.success) {
      // Start polling for instance status
      startPolling()
    }
  } catch (err) {
    console.error('Failed to start session')
    statusMessage.value = ''
  } finally {
    actionLoading.value = false
  }
}

function startPolling() {
  pollingStatus.value = true
  statusMessage.value = '等待实例启动中...'

  // Check status immediately, then every 5 seconds
  checkInstanceStatus()

  pollingInterval.value = setInterval(() => {
    checkInstanceStatus()
  }, 5000)
}

async function checkInstanceStatus() {
  const result = await queryInstanceStatus()

  if (result) {
    // Status 3 = running, Status 5 = stopped
    if (result.is_running) {
      // Instance is running, stop polling and show iframe
      stopPolling()
      userState.value = 'active'
      targetUrl.value = result.target_url
      showIframe.value = true
      statusMessage.value = ''
      // Start sending heartbeats for inactivity detection
      startHeartbeat()
    } else {
      // Still waiting, update message
      statusMessage.value = '实例启动中，5秒后再次检查...'
    }
  }
}

function stopPolling() {
  pollingStatus.value = false
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

async function handleStop() {
  actionLoading.value = true
  statusMessage.value = '正在停止实例...'

  try {
    const response = await axios.post(
      `${API_URL}/portal/action`,
      { action: 'stop' },
      { headers: authStore.getAuthHeader() }
    )

    if (response.data.success) {
      stopHeartbeat()
      userState.value = 'inactive'
      showIframe.value = false
      statusMessage.value = ''
    }
  } catch (err) {
    console.error('Failed to stop session')
  } finally {
    actionLoading.value = false
  }
}

function handleLogout() {
  stopHeartbeat()
  authStore.logout()
  router.push('/login')
}

function goToAdmin() {
  router.push('/admin')
}

onMounted(() => {
  fetchTargetUrl()
  updateTime()
  timeInterval.value = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  stopPolling()
  stopHeartbeat()
  if (timeInterval.value) {
    clearInterval(timeInterval.value)
  }
})
</script>

<template>
  <div class="portal-container">
    <!-- Header Bar -->
    <header class="header">
      <div class="header-left">
        <div class="logo-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <span class="app-title">第五届"海淀工匠杯"职工职业技能大赛</span>
        <span class="divider"></span>
        <span class="username">{{ authStore.user?.username }}</span>
        <template v-if="showIframe">
          <span class="divider"></span>
          <span class="current-time">{{ currentTime }}</span>
        </template>
      </div>

      <div class="header-right">
        <!-- No instance warning -->
        <div v-if="!hasInstance" class="status-display warning">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          未分配GPU实例
        </div>

        <!-- Status display -->
        <div v-else-if="actionLoading || isPolling" class="status-display starting">
          <span class="spinner-small"></span>
          {{ statusMessage }}
        </div>

        <!-- Start/Stop Buttons (only show when instance is assigned) -->
        <template v-if="hasInstance">
          <button
            class="header-btn start-btn"
            @click="handleStart"
            :disabled="actionLoading || isActive || isPolling"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
            启动
          </button>

          <button
            class="header-btn stop-btn"
            @click="handleStop"
            :disabled="actionLoading || !isActive || isPolling"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 6h12v12H6z"/>
            </svg>
            停止
          </button>
        </template>

        <span class="divider"></span>

        <!-- Admin Button -->
        <button v-if="authStore.isAdmin" class="header-btn admin-btn" @click="goToAdmin">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
          </svg>
          管理
        </button>

        <!-- Logout Button -->
        <button class="header-btn logout-btn" @click="handleLogout">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
          </svg>
          退出
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Welcome Screen (before start) -->
      <div v-if="!showIframe" class="welcome-screen">
        <div class="welcome-content">
          <!-- No instance assigned -->
          <template v-if="!hasInstance">
            <div class="welcome-icon warning-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
            </div>
            <h2>未分配GPU实例</h2>
            <p>请联系管理员为您分配GPU实例后再开始比赛</p>
          </template>
          <!-- Has instance -->
          <template v-else>
            <div class="welcome-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
            <h2 v-if="isPolling">正在启动...</h2>
            <h2 v-else>准备就绪</h2>
            <p v-if="isPolling">{{ statusMessage }}</p>
            <p v-else>点击上方"启动"按钮开始您的比赛</p>
          </template>
        </div>
      </div>

      <!-- Iframe Content -->
      <iframe
        v-if="showIframe"
        :src="targetUrl"
        frameborder="0"
        class="content-iframe"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
      ></iframe>
    </main>
  </div>
</template>

<style scoped>
.portal-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0f172a;
}

.header {
  background: #1e293b;
  padding: 0 20px;
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #334155;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 18px;
  height: 18px;
  color: white;
}

.app-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.divider {
  width: 1px;
  height: 24px;
  background: #475569;
  margin: 0 4px;
}

.username {
  font-size: 14px;
  color: #94a3b8;
}

.current-time {
  font-size: 14px;
  color: #94a3b8;
  font-family: 'Courier New', monospace;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.status-display.starting {
  background: #3b82f6;
  color: white;
}

.status-display.warning {
  background: #f59e0b;
  color: white;
}

.status-display.warning svg {
  width: 16px;
  height: 16px;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.header-btn svg {
  width: 16px;
  height: 16px;
}

.start-btn {
  background: #10b981;
  color: white;
}

.start-btn:hover:not(:disabled) {
  background: #059669;
}

.stop-btn {
  background: #ef4444;
  color: white;
}

.stop-btn:hover:not(:disabled) {
  background: #dc2626;
}

.admin-btn {
  background: #475569;
  color: #e2e8f0;
}

.admin-btn:hover {
  background: #64748b;
}

.logout-btn {
  background: transparent;
  color: #94a3b8;
  border: 1px solid #475569;
}

.logout-btn:hover {
  background: #334155;
  color: #e2e8f0;
}

.header-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}

.welcome-content {
  text-align: center;
  color: #e2e8f0;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.welcome-icon svg {
  width: 40px;
  height: 40px;
  color: white;
}

.welcome-icon.warning-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.welcome-content h2 {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 12px;
}

.welcome-content p {
  font-size: 16px;
  color: #94a3b8;
  margin: 0;
}

.content-iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}
</style>
