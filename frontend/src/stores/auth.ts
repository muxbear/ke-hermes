import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AuthTokens, UserInfo } from '@/types/auth'
import { authApi } from '@/services/authApi'
import { clearTokensFromStorage } from '@/services/request'

const TOKEN_STORAGE_KEY = 'auth_tokens'
const USER_STORAGE_KEY = 'auth_user'
const REMEMBERED_ACCOUNT_KEY = 'remembered_account'

export const useAuthStore = defineStore('auth', () => {
  // ---- State ----
  const tokens = ref<AuthTokens | null>(loadTokens())
  const user = ref<UserInfo | null>(loadUser())
  const loginLoading = ref(false)
  const loginError = ref<string | null>(null)
  const agreedProtocolVersion = ref<string | null>(null)

  // ---- Getters ----
  const isAuthenticated = computed(() => !!tokens.value?.accessToken)
  const accessToken = computed(() => tokens.value?.accessToken ?? '')
  const refreshTokenValue = computed(() => tokens.value?.refreshToken ?? '')
  const isLoginLoading = computed(() => loginLoading.value)

  // ---- Token 持久化（始终使用 sessionStorage，关闭浏览器即清除）----
  function loadTokens(): AuthTokens | null {
    try {
      const raw = sessionStorage.getItem(TOKEN_STORAGE_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  function loadUser(): UserInfo | null {
    try {
      const raw = sessionStorage.getItem(USER_STORAGE_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  function persistTokens() {
    if (!tokens.value) return
    sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens.value))
  }

  function persistUser() {
    if (!user.value) return
    sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user.value))
  }

  function setTokens(t: AuthTokens) {
    tokens.value = t
    persistTokens()
  }

  function setUser(u: UserInfo) {
    user.value = u
    persistUser()
  }

  function saveRememberedAccount(account: string) {
    localStorage.setItem(REMEMBERED_ACCOUNT_KEY, account)
  }

  function loadRememberedAccount(): string | null {
    return localStorage.getItem(REMEMBERED_ACCOUNT_KEY)
  }

  function clearRememberedAccount() {
    localStorage.removeItem(REMEMBERED_ACCOUNT_KEY)
  }

  function clearTokens() {
    tokens.value = null
    user.value = null
    sessionStorage.removeItem(USER_STORAGE_KEY)
    clearRememberedAccount()
    clearTokensFromStorage()
  }

  // ---- Token 刷新去重锁 ----
  let refreshPromise: Promise<string> | null = null

  async function refreshAccessToken(): Promise<string> {
    if (refreshPromise) return refreshPromise

    refreshPromise = (async () => {
      try {
        const res = await authApi.refreshToken(refreshTokenValue.value)
        const data = res.data.data
        setTokens(data.tokens)
        if (data.user) {
          setUser(data.user)
        }
        return data.tokens.accessToken
      } catch {
        clearTokens()
        throw new Error('refresh-failed')
      } finally {
        refreshPromise = null
      }
    })()

    return refreshPromise
  }

  // ---- Actions ----
  async function loginWithPassword(payload: {
    account: string
    password: string
    rememberMe: boolean
  }) {
    loginLoading.value = true
    loginError.value = null
    try {
      const res = await authApi.accountLogin({
        account: payload.account,
        password: payload.password,
      })
      const { tokens: t, user: u } = res.data.data
      setTokens(t)
      setUser(u)
      if (payload.rememberMe) {
        saveRememberedAccount(payload.account)
      } else {
        clearRememberedAccount()
      }
    } catch (err) {
      loginError.value = err instanceof Error ? err.message : '登录失败'
      throw err
    } finally {
      loginLoading.value = false
    }
  }

  async function loginWithPhone(payload: { phone: string; smsCode: string }) {
    loginLoading.value = true
    loginError.value = null
    try {
      const res = await authApi.phoneLogin(payload)
      const { tokens: t, user: u } = res.data.data
      setTokens(t)
      setUser(u)
    } catch (err) {
      loginError.value = err instanceof Error ? err.message : '登录失败'
      throw err
    } finally {
      loginLoading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // 即使后端退出失败也清除本地状态
    }
    clearTokens()
  }

  function agreeProtocol(version: string) {
    agreedProtocolVersion.value = version
  }

  return {
    tokens,
    user,
    loginLoading,
    loginError,
    agreedProtocolVersion,
    isAuthenticated,
    accessToken,
    refreshToken: refreshTokenValue,
    isLoginLoading,
    setTokens,
    clearTokens,
    refreshAccessToken,
    loginWithPassword,
    loginWithPhone,
    logout,
    agreeProtocol,
    loadRememberedAccount,
    clearRememberedAccount,
  }
})
