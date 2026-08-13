import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('../views/ForgotPasswordView.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      { path: '', redirect: '/data' },
      { path: 'data', name: 'DataConsole', component: () => import('../views/DataConsole.vue') },
      { path: 'data/datasets', name: 'DataSetList', component: () => import('../views/DataSetList.vue') },
      { path: 'data/datasets/:id', name: 'DataSetDetail', component: () => import('../views/DataSetDetail.vue') },
      { path: 'data/quality', name: 'QualityReport', component: () => import('../views/QualityReport.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
      { path: 'admin/users', name: 'AdminUsers', component: () => import('../views/AdminUsersView.vue'), meta: { requiresAdmin: true } },
      { path: 'admin/dashboard', name: 'AdminDashboard', component: () => import('../views/AdminDashboardView.vue'), meta: { requiresAdmin: true } },
    ],
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (!to.meta.guest && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  if (to.meta.guest && authStore.isLoggedIn) {
    next({ name: 'DataConsole' })
    return
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'DataConsole' })
    return
  }
  next()
})

export default router
