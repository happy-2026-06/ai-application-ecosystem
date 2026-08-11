<template>
  <div class="apage">
    <div class="atop"><h2>系统仪表盘</h2></div>

    <!-- Stats -->
    <n-grid cols="4" x-gap="12" style="margin-bottom:20px">
      <n-gi v-for="s in statsCards" :key="s.label">
        <div class="stat-card" :style="{borderTop:'3px solid '+s.color}">
          <div class="stat-icon">{{s.icon}}</div>
          <n-statistic :label="s.label">
            <template #value><span :style="{color:s.color}">{{s.value}}</span></template>
          </n-statistic>
        </div>
      </n-gi>
    </n-grid>

    <!-- Detail row -->
    <n-grid cols="3" x-gap="12" style="margin-bottom:20px">
      <n-gi>
        <div class="detail-card">
          <h3>🤖 Agent 集群</h3>
          <div class="dc-row"><span>Agent 总数</span><strong>{{dash?.total_agents||0}}</strong></div>
          <div class="dc-row"><span>在线</span><strong class="green">{{dash?.online_agents||0}}</strong></div>
          <div class="dc-row"><span>离线</span><strong class="red">{{(dash?.total_agents||0)-(dash?.online_agents||0)}}</strong></div>
        </div>
      </n-gi>
      <n-gi>
        <div class="detail-card">
          <h3>📋 任务概览</h3>
          <div class="dc-row"><span>总任务</span><strong>{{dash?.total_tasks||0}}</strong></div>
          <div class="dc-row"><span>已完成</span><strong class="green">{{dash?.completed_tasks||0}}</strong></div>
          <div class="dc-row"><span>失败</span><strong class="red">{{dash?.failed_tasks||0}}</strong></div>
        </div>
      </n-gi>
      <n-gi>
        <div class="detail-card">
          <h3>👥 用户</h3>
          <div class="dc-row"><span>总用户</span><strong>{{dash?.total_users||0}}</strong></div>
          <div class="dc-row"><span>活跃</span><strong class="green">{{dash?.active_users||0}}</strong></div>
        </div>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '../api/client'
import { useMessage } from 'naive-ui'
const message=useMessage(); const dash=ref<any>(null)
const statsCards=computed(()=>[
  {label:'总用户',value:dash.value?.total_users||0,icon:'👥',color:'#7c3aed'},
  {label:'活跃用户',value:dash.value?.active_users||0,icon:'🟢',color:'#22c55e'},
  {label:'Agent数',value:dash.value?.total_agents||0,icon:'🤖',color:'#3b82f6'},
  {label:'总任务',value:dash.value?.total_tasks||0,icon:'📋',color:'#f59e0b'},
])
onMounted(async()=>{try{const r=await apiClient.get('/admin/dashboard');dash.value=r.data}catch{message.error('加载失败')}})
</script>

<style scoped>
.apage{padding:28px 40px;max-width:1100px;overflow-y:auto;height:100%}
.atop{margin-bottom:24px}.atop h2{margin:0;font-size:22px;color:#0f172a}

.stat-card{background:#fff;border-radius:14px;padding:20px 24px;border:1px solid #e2e8f0}
.stat-icon{font-size:24px;margin-bottom:8px}

.detail-card{background:#fff;border-radius:14px;padding:20px 24px;border:1px solid #e2e8f0}
.detail-card h3{font-size:15px;font-weight:700;color:#1e293b;margin:0 0 14px}
.dc-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:14px}
.dc-row:last-child{border-bottom:none}
.dc-row span{color:#64748b}.dc-row strong{color:#1e293b;font-size:20px}
.dc-row strong.green{color:#22c55e}.dc-row strong.red{color:#ef4444}

[data-theme="dark"] .atop h2{color:#f1f5f9}
[data-theme="dark"] .stat-card,[data-theme="dark"] .detail-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .dc-row{border-bottom-color:#2d2d3d}
[data-theme="dark"] .dc-row span{color:#94a3b8}.dc-row strong{color:#e2e8f0}
</style>
