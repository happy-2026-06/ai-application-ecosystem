<template>
  <div class="apage">
    <div class="atop">
      <h2>👥 用户管理</h2>
      <div class="atop-right">
        <n-input v-model:value="searchUsername" placeholder="搜索用户名…" clearable size="small" style="width: 180px; margin-right: 8px;" @keyup.enter="loadUsers" />
        <n-button size="small" type="primary" @click="loadUsers">🔍 搜索</n-button>
      </div>
    </div>
    <n-card>
      <n-data-table
        :columns="cols" :data="users" :loading="loading"
        :pagination="{ page: currentPage, pageSize: pageSize, itemCount: totalUsers, onChange: onPageChange }"
        :row-key="(r:any) => r.id"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useMessage, NTag, NButton, NSelect } from 'naive-ui'
import apiClient from '../api/client'

const message = useMessage()
const users = ref<any[]>([])
const loading = ref(false)
const searchUsername = ref('')
const currentPage = ref(1)
const pageSize = 20
const totalUsers = ref(0)

const cols = [
  { title: '用户名', key: 'username' },
  { title: '邮箱', key: 'email', ellipsis: { tooltip: true } },
  {
    title: '角色', key: 'role', width: 100,
    render(r: any) {
      return h(NSelect, {
        value: r.role,
        size: 'tiny',
        options: [
          { label: '管理员', value: 'admin' },
          { label: '用户', value: 'user' },
        ],
        onUpdateValue: (val: string) => updateRole(r, val),
      })
    },
  },
  {
    title: '状态', key: 'is_active', width: 80,
    render(r: any) {
      return h(NTag, { type: r.is_active ? 'success' : 'error' }, { default: () => r.is_active ? '正常' : '禁用' })
    },
  },
  {
    title: '操作', key: 'act', width: 80,
    render(r: any) {
      return h(NButton, {
        size: 'small',
        type: r.is_active ? 'error' : 'success',
        onClick: () => toggle(r),
      }, { default: () => r.is_active ? '禁用' : '启用' })
    },
  },
  {
    title: '创建时间', key: 'created_at', width: 160,
    render(r: any) {
      return r.created_at ? new Date(r.created_at).toLocaleDateString('zh-CN') : '-'
    },
  },
]

async function loadUsers() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
    if (searchUsername.value) params.username = searchUsername.value
    const r = await apiClient.get('/admin/users', { params })
    users.value = r.data
    totalUsers.value = r.data.length >= pageSize ? (currentPage.value * pageSize + 1) : (currentPage.value - 1) * pageSize + r.data.length
  } catch {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number) {
  currentPage.value = page
  loadUsers()
}

async function toggle(u: any) {
  try {
    await apiClient.patch(`/admin/users/${u.id}`, { is_active: !u.is_active })
    message.success(u.is_active ? '已禁用' : '已启用')
    await loadUsers()
  } catch {
    message.error('操作失败')
  }
}

async function updateRole(u: any, newRole: string) {
  try {
    await apiClient.patch(`/admin/users/${u.id}`, { role: newRole })
    u.role = newRole
    message.success('角色已更新')
  } catch {
    message.error('更新角色失败')
  }
}

onMounted(() => loadUsers())
</script>

<style scoped>
.apage { padding: 28px 32px; max-width: 1000px; overflow-y: auto; height: 100%; }
.atop { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.atop h2 { margin: 0; font-size: 22px; font-weight: 700; color: var(--text-primary); }
.atop-right { display: flex; align-items: center; }
</style>
