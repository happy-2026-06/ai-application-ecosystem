<template>
  <div class="apage">
    <div class="atop"><h2>用户管理</h2><n-button @click="$router.push('/admin/dashboard')">📊 仪表盘</n-button></div>
    <n-card>
      <n-data-table :columns="cols" :data="users" :loading="loading" :pagination="{pageSize:10}" :row-key="(r:any)=>r.id" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useMessage, NTag, NButton } from 'naive-ui'
import apiClient from '../api/client'
const message=useMessage(); const users=ref<any[]>([]); const loading=ref(false)
const cols=[{title:'用户名',key:'username'},{title:'邮箱',key:'email',ellipsis:{tooltip:true}},{title:'角色',key:'role',width:80,render(r:any){return h(NTag,{type:r.role==='admin'?'warning':'info'},{default:()=>r.role==='admin'?'管理员':'用户'})}},{title:'状态',key:'is_active',width:80,render(r:any){return h(NTag,{type:r.is_active?'success':'error'},{default:()=>r.is_active?'正常':'禁用'})}},{title:'操作',key:'act',width:80,render(r:any){return h(NButton,{size:'small',type:r.is_active?'error':'success',onClick:()=>toggle(r)},{default:()=>r.is_active?'禁用':'启用'})}}]
async function load(){loading.value=true;try{const r=await apiClient.get('/admin/users');users.value=r.data}catch{message.error('加载失败')}finally{loading.value=false}}
async function toggle(u:any){try{await apiClient.patch(`/admin/users/${u.id}`,{is_active:!u.is_active});message.success(u.is_active?'已禁用':'已启用');await load()}catch{message.error('操作失败')}}
onMounted(load)
</script>

<style scoped>
.apage { padding:28px 32px; max-width:1000px; overflow-y:auto; height:100%; }
.atop { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.atop h2 { margin:0; font-size:22px; color: #1A0F2E; }

[data-theme="dark"] .atop h2 { color: #eee; }
</style>
