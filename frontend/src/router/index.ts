import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const MainLayout = () => import('@/components/MainLayout.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/HomeView.vue'),
      },
      {
        path: 'skills',
        name: 'skills',
        component: () => import('@/views/SkillsView.vue'),
        meta: { title: 'Skills' },
      },
      {
        path: 'agents',
        name: 'agents',
        component: () => import('@/views/AgentsView.vue'),
        meta: { title: '代理管理中心' },
      },
      {
        path: 'mcp',
        name: 'mcp-square',
        component: () => import('@/views/McpSquareView.vue'),
        meta: { title: 'MCP 广场' },
      },
      {
        path: 'mcp/:id',
        name: 'mcp-detail',
        component: () => import('@/views/McpDetailView.vue'),
        meta: { title: 'MCP 详情' },
      },
    ],
  },
  {
    path: '/login',
    component: () => import('@/components/auth/AuthLayout.vue'),
    children: [
      {
        path: '',
        name: 'login',
        component: () => import('@/views/LoginView.vue'),
        meta: { title: '登录', guest: true },
      },
    ],
  },
  {
    path: '/register',
    component: () => import('@/components/auth/AuthLayout.vue'),
    children: [
      {
        path: '',
        name: 'register',
        component: () => import('@/views/RegisterView.vue'),
        meta: { title: '注册', guest: true },
      },
      {
        path: 'email',
        name: 'register-email',
        component: () => import('@/views/EmailRegisterView.vue'),
        meta: { title: '邮箱注册', guest: true },
      },
    ],
  },
  {
    path: '/oauth/callback',
    name: 'oauth-callback',
    component: () => import('@/views/OAuthCallbackView.vue'),
    meta: { title: '第三方登录', guest: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫
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

export default router
