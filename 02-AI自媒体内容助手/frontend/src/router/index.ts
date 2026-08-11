import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  // Auth pages (no layout)
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('../views/ForgotPasswordView.vue'), meta: { guest: true } },

  // App pages (with top nav layout)
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', name: 'DashboardHome', component: () => import('../views/DashboardHome.vue') },
      { path: 'studio', name: 'ContentStudio', component: () => import('../views/ContentStudio.vue') },
      { path: 'studio/:sessionId', name: 'ContentStudioSession', component: () => import('../views/ContentStudio.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
      { path: 'admin/users', name: 'AdminUsers', component: () => import('../views/AdminUsersView.vue'), meta: { requiresAdmin: true } },
      { path: 'admin/dashboard', name: 'AdminDashboard', component: () => import('../views/AdminDashboardView.vue'), meta: { requiresAdmin: true } },
    ],
  },
  // 404 catch-all
  { path: '/:pathMatch(.*)*', redirect: '/home' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  // Redirect to login if not authenticated
  if (!to.meta.guest && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Redirect to chat if already logged in and visiting guest pages
  if (to.meta.guest && authStore.isLoggedIn) {
    next({ name: 'DashboardHome' })
    return
  }

  // Admin check
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'DashboardHome' })
    return
  }

  next()
})

export default router
