import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/authApi', () => ({
  authApi: {
    accountLogin: vi.fn(),
    phoneLogin: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
  },
}))

const routes = [
  {
    path: '/',
    name: 'home',
    component: { template: '<div>Home</div>' },
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: { template: '<div>Login</div>' },
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: { template: '<div>Register</div>' },
    meta: { guest: true },
  },
]

function createTestRouter() {
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }
    if (to.meta.guest && authStore.isAuthenticated) {
      return next({ name: 'home' })
    }
    next()
  })

  return router
}

describe('router guards', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('redirects unauthenticated user from / to /login', async () => {
    const router = createTestRouter()
    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/')
  })

  it('allows unauthenticated user to access /login', async () => {
    const router = createTestRouter()
    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
  })

  it('redirects authenticated user from /login to /', async () => {
    const authStore = useAuthStore()
    authStore.setTokens({ accessToken: 'test-at', refreshToken: 'test-rt', expiresIn: 7200 }, true)

    const router = createTestRouter()
    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('home')
  })

  it('allows unauthenticated user to access guest routes', async () => {
    // 确保未登录状态
    const authStore = useAuthStore()
    authStore.clearTokens()

    const router = createTestRouter()
    // /register 是 guest 路由，未登录用户可以访问
    await router.push('/register')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('register')
  })
})
