import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type LoginRequest, type RegisterRequest } from '../api/auth'

export interface UserInfo {
  id: string
  username: string
  email?: string
  display_name?: string
  role: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>('')
  const refreshToken = ref<string>('')
  const user = ref<UserInfo | null>(null)
  const isDarkMode = ref<boolean>(false)
  const avatar = ref<string>('🐱')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(access: string, refresh: string) {
    token.value = access
    refreshToken.value = refresh
  }

  async function login(data: LoginRequest): Promise<boolean> {
    try {
      const res = await authApi.login(data)
      const d = res.data
      token.value = d.access_token
      refreshToken.value = d.refresh_token
      user.value = d.user
      return true
    } catch {
      return false
    }
  }

  async function register(data: RegisterRequest): Promise<boolean> {
    try {
      await authApi.register(data)
      return true
    } catch {
      return false
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
  }

  async function changePassword(oldPwd: string, newPwd: string): Promise<boolean> {
    try {
      await authApi.changePassword(oldPwd, newPwd)
      return true
    } catch {
      return false
    }
  }

  async function updateProfile(displayName: string): Promise<boolean> {
    try {
      const { default: apiClient } = await import('../api/client')
      await apiClient.patch('/auth/profile', { display_name: displayName })
      const meRes = await apiClient.get('/auth/me')
      if (meRes.data) {
        user.value = meRes.data
      }
      return true
    } catch (e: any) {
      console.error('[updateProfile] Error:', e?.response?.status, e?.response?.data || e?.message)
      return false
    }
  }

  function setAvatar(emoji: string) { avatar.value = emoji }
  function toggleDarkMode() { isDarkMode.value = !isDarkMode.value }

  return {
    token, refreshToken, user, isDarkMode, avatar,
    isLoggedIn, isAdmin,
    setTokens, login, register, logout, changePassword,
    updateProfile, setAvatar, toggleDarkMode,
  }
}, {
  persist: {
    key: 'asset-auth',
    storage: localStorage,
    pick: ['token', 'refreshToken', 'user', 'isDarkMode', 'avatar'],
  },
})
