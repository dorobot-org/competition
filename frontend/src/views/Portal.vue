<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'
const router = useRouter()
const authStore = useAuthStore()

const targetUrl = ref('')
const userState = ref('inactive')
const loading = ref(false)
const actionLoading = ref(false)
const showIframe = ref(false)
const countdown = ref(0)
const countdownInterval = ref(null)

const isActive = computed(() => userState.value === 'active')

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
    }
  } catch (err) {
    console.error('Failed to load portal information')
  } finally {
    loading.value = false
  }
}

async function handleStart() {
  actionLoading.value = true
  try {
    const response = await axios.post(
      `${API_URL}/portal/action`,
      { action: 'start' },
      { headers: authStore.getAuthHeader() }
    )

    if (response.data.success) {
      userState.value = 'active'
      startCountdown()
    }
  } catch (err) {
    console.error('Failed to start session')
  } finally {
    actionLoading.value = false
  }
}

async function handleStop() {
  actionLoading.value = true
  try {
    const response = await axios.post(
      `${API_URL}/portal/action`,
      { action: 'stop' },
      { headers: authStore.getAuthHeader() }
    )

    if (response.data.success) {
      userState.value = 'inactive'
      showIframe.value = false
    }
  } catch (err) {
    console.error('Failed to stop session')
  } finally {
    actionLoading.value = false
  }
}

function startCountdown() {
  countdown.value = 5
  countdownInterval.value = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownInterval.value)
      showIframe.value = true
    }
  }, 1000)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function goToAdmin() {
  router.push('/admin')
}

onMounted(() => {
  fetchTargetUrl()
})

onUnmounted(() => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
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
        <span class="app-title">User Portal</span>
        <span class="divider"></span>
        <span class="username">{{ authStore.user?.username }}</span>
      </div>

      <div class="header-right">
        <!-- Countdown display -->
        <div v-if="countdown > 0" class="countdown-display">
          Loading in {{ countdown }}s...
        </div>

        <!-- Start/Stop Buttons -->
        <button
          class="header-btn start-btn"
          @click="handleStart"
          :disabled="actionLoading || isActive || countdown > 0"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
          Start
        </button>

        <button
          class="header-btn stop-btn"
          @click="handleStop"
          :disabled="actionLoading || !isActive"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h12v12H6z"/>
          </svg>
          Stop
        </button>

        <span class="divider"></span>

        <!-- Admin Button -->
        <button v-if="authStore.isAdmin" class="header-btn admin-btn" @click="goToAdmin">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
          </svg>
          Admin
        </button>

        <!-- Logout Button -->
        <button class="header-btn logout-btn" @click="handleLogout">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
          </svg>
          Logout
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Welcome Screen (before start) -->
      <div v-if="!showIframe" class="welcome-screen">
        <div class="welcome-content">
          <div class="welcome-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
          <h2 v-if="countdown > 0">Starting Session...</h2>
          <h2 v-else>Ready to Start</h2>
          <p v-if="countdown > 0">Redirecting in {{ countdown }} seconds</p>
          <p v-else>Click the Start button above to begin your session</p>
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

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.countdown-display {
  padding: 6px 14px;
  background: #7c3aed;
  color: white;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
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
