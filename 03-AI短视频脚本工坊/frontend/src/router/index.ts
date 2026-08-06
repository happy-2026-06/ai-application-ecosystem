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
      { path: '', redirect: '/studio' },
      { path: 'studio', name: 'ScriptStudio', component: () => import('../views/ScriptStudio.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
      { path: 'admin/users', name: 'AdminUsers', component: () => import('../views/AdminUsersView.vue'), meta: { requiresAdmin: true } },
      { path: 'admin/dashboard', name: 'AdminDashboard', component: () => import('../views/AdminDashboardView.vue'), meta: { requiresAdmin: true } },
      { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFoundView.vue') },
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
    next({ name: 'ScriptStudio' })
    return
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'ScriptStudio' })
    return
  }
  next()
})

export default router
