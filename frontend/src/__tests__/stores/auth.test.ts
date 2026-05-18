import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/authApi', () => ({
  authApi: {
    accountLogin: vi.fn(),
    phoneLogin: vi.fn(),
    logout: vi.fn().mockResolvedValue({ data: { code: 0, data: null } }),
    refreshToken: vi.fn(),
    getFailCount: vi.fn(),
    getPublicKey: vi.fn(),
  },
}))

vi.mock('@/services/request', () => ({
  clearTokensFromStorage: vi.fn(),
}))

function createMockAuthResponse() {
  return {
    data: {
      code: 0,
      data: {
        tokens: { accessToken: 'at-123', refreshToken: 'rt-123', expiresIn: 7200 },
        user: { id: '1', nickname: 'test', avatar: '', phone: '', email: '', workspaceId: 'ws1' },
      },
      message: 'ok',
      requestId: '1',
      timestamp: Date.now(),
    },
  }
}

import { authApi } from '@/services/authApi'

describe('authStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    sessionStorage.clear()
    vi.clearAllMocks()
    vi.mocked(authApi.logout).mockResolvedValue({ data: { code: 0, data: null } } as any)
  })

  it('isAuthenticated is false by default', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('loginWithPassword sets tokens and user on success', async () => {
    vi.mocked(authApi.accountLogin).mockResolvedValue(createMockAuthResponse() as any)
    const store = useAuthStore()

    await store.loginWithPassword({ account: 'testuser', password: 'encrypted', rememberMe: true })

    expect(store.isAuthenticated).toBe(true)
    expect(store.accessToken).toBe('at-123')
    expect(store.user?.nickname).toBe('test')
    // rememberMe=true → localStorage
    expect(JSON.parse(localStorage.getItem('auth_tokens')!).accessToken).toBe('at-123')
  })

  it('loginWithPassword sets loginError on failure', async () => {
    vi.mocked(authApi.accountLogin).mockRejectedValue(new Error('AUTH_001'))
    const store = useAuthStore()

    await expect(
      store.loginWithPassword({ account: 'bad', password: 'encrypted', rememberMe: false }),
    ).rejects.toThrow()
    expect(store.loginError).toBe('AUTH_001')
    expect(store.isAuthenticated).toBe(false)
  })

  it('rememberMe=false stores token in sessionStorage', async () => {
    vi.mocked(authApi.accountLogin).mockResolvedValue(createMockAuthResponse() as any)
    const store = useAuthStore()

    await store.loginWithPassword({ account: 'testuser', password: 'encrypted', rememberMe: false })

    // rememberMe=false → sessionStorage
    expect(JSON.parse(sessionStorage.getItem('auth_tokens')!).accessToken).toBe('at-123')
  })

  it('logout clears tokens and calls API', async () => {
    vi.mocked(authApi.accountLogin).mockResolvedValue(createMockAuthResponse() as any)
    const store = useAuthStore()

    await store.loginWithPassword({ account: 'testuser', password: 'encrypted', rememberMe: true })
    expect(store.isAuthenticated).toBe(true)

    await store.logout()
    expect(store.isAuthenticated).toBe(false)
    expect(authApi.logout).toHaveBeenCalled()
  })

  it('refreshAccessToken deduplicates concurrent calls', async () => {
    vi.mocked(authApi.accountLogin).mockResolvedValue(createMockAuthResponse() as any)
    vi.mocked(authApi.refreshToken).mockResolvedValue({
      data: { data: { tokens: { accessToken: 'new-at', refreshToken: 'new-rt', expiresIn: 7200 } } },
    } as any)

    const store = useAuthStore()
    await store.loginWithPassword({ account: 'testuser', password: 'encrypted', rememberMe: true })

    const [a, b] = await Promise.all([
      store.refreshAccessToken(),
      store.refreshAccessToken(),
    ])

    expect(a).toBe('new-at')
    expect(b).toBe('new-at')
    // 去重锁确保只调用一次
    expect(authApi.refreshToken).toHaveBeenCalledTimes(1)
  })

  it('refreshAccessToken clears tokens on failure', async () => {
    vi.mocked(authApi.accountLogin).mockResolvedValue(createMockAuthResponse() as any)
    vi.mocked(authApi.refreshToken).mockRejectedValue(new Error('refresh-failed'))
    const store = useAuthStore()

    await store.loginWithPassword({ account: 'testuser', password: 'encrypted', rememberMe: true })
    await expect(store.refreshAccessToken()).rejects.toThrow('refresh-failed')

    expect(store.isAuthenticated).toBe(false)
  })
})
