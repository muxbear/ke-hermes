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
        redirect: '/overview',
      },
      {
        path: 'chat',
        name: 'chat',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '对话' },
      },
      {
        path: 'overview',
        name: 'overview',
        component: () => import('@/views/OverviewView.vue'),
        meta: { title: '概览' },
      },
      {
        path: 'skills',
        name: 'skills',
        component: () => import('@/views/SkillsView.vue'),
        meta: { title: 'Skills' },
      },
      {
        path: 'tools',
        name: 'tools',
        component: () => import('@/views/ToolsView.vue'),
        meta: { title: 'Tools' },
      },
      {
        path: 'agents',
        name: 'agents',
        component: () => import('@/views/AgentsView.vue'),
        meta: { title: '代理管理中心' },
      },
      {
        path: 'models',
        name: 'models',
        component: () => import('@/views/ModelsView.vue'),
        meta: { title: '模型' },
      },
      {
        path: 'scheduled-tasks',
        name: 'scheduled-tasks',
        component: () => import('@/views/ScheduledTasksView.vue'),
        meta: { title: '定时任务' },
      },
      {
        path: 'knowledge-base',
        name: 'knowledge-base',
        component: () => import('@/views/KnowledgeBaseView.vue'),
        meta: { title: '知识库' },
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
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/AdminView.vue'),
        meta: { title: '后台管理' },
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('@/views/UserManagementView.vue'),
        meta: { title: '人员管理' },
      },
      {
        path: 'admin/rbac',
        name: 'admin-rbac',
        component: () => import('@/views/RbacView.vue'),
        meta: { title: '角色权限' },
      },
      {
        path: 'admin/menu-config',
        name: 'admin-menu-config',
        component: () => import('@/views/MenuConfigView.vue'),
        meta: { title: '菜单配置' },
      },
      {
        path: 'admin/org',
        name: 'admin-org',
        component: () => import('@/views/OrgDeptView.vue'),
        meta: { title: '机构部门' },
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
