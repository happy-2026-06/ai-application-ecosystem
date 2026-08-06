<template>
  <div class="apage">
    <div class="atop"><h2>系统仪表盘</h2></div>
    <n-grid cols="4" x-gap="12" style="margin-bottom:20px;">
      <n-gi v-for="s in cards" :key="s.label"><n-card size="small" class="stat-card"><n-statistic :label="s.label" :value="s.value" /></n-card></n-gi>
    </n-grid>
    <n-grid cols="3" x-gap="12" style="margin-bottom:20px;">
      <n-gi><n-card size="small" title="知识库" class="kb-card"><n-statistic label="文档总数" :value="dash?.total_documents||0" /><n-statistic label="总片段数" :value="dash?.total_chunks||0" /></n-card></n-gi>
      <n-gi><n-card size="small" title="反馈" class="pos-card"><n-statistic label="👍 好评" :value="dash?.feedback?.positive||0" /></n-card></n-gi>
      <n-gi><n-card size="small" title="反馈" class="neg-card"><n-statistic label="👎 差评" :value="dash?.feedback?.negative||0" /></n-card></n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '../api/client'
import { useMessage } from 'naive-ui'
const message=useMessage(); const dash=ref<any>(null)
const cards=computed(()=>[{label:'总用户',value:dash.value?.total_users||0},{label:'活跃用户',value:dash.value?.active_users||0},{label:'总会话',value:dash.value?.total_sessions||0},{label:'总消息',value:dash.value?.total_messages||0}])
onMounted(async()=>{try{const r=await apiClient.get('/admin/dashboard');dash.value=r.data}catch{message.error('加载失败')}})
</script>

<style scoped>
.apage { padding:28px 32px; max-width:1000px; overflow-y:auto; height:100%; }
.atop { margin-bottom:20px; } .atop h2 { margin:0; font-size:22px; color:#0F172A; }
.stat-card { background:linear-gradient(135deg,#F8FAFC,#EFF6FF) !important; border:1px solid #E2E8F0 !important; border-radius:10px !important; }
.kb-card { border-radius:10px !important; }
.pos-card { background:#ECFDF5 !important; border-radius:10px !important; }
.neg-card { background:#FEF2F2 !important; border-radius:10px !important; }
[data-theme="dark"] .atop h2 { color: #E2E8F0; }
[data-theme="dark"] .stat-card { background:linear-gradient(135deg,#1E293B,#1E3A5F) !important; border-color:#334155 !important; }
[data-theme="dark"] .pos-card { background:rgba(16,185,129,.1) !important; }
[data-theme="dark"] .neg-card { background:rgba(239,68,68,.1) !important; }
</style>
