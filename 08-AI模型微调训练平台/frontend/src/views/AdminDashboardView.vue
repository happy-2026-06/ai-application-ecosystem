<template>
  <div class="apage">
    <div class="atop"><h2>系统仪表盘</h2></div>

    <!-- Stats cards -->
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
          <h3>🔬 微调训练</h3>
          <div class="dc-row"><span>总任务数</span><strong>{{dash?.total_tasks||0}}</strong></div>
          <div class="dc-row"><span>运行中</span><strong class="blue">{{dash?.running_tasks||0}}</strong></div>
          <div class="dc-row"><span>已完成</span><strong class="green">{{dash?.completed_tasks||0}}</strong></div>
        </div>
      </n-gi>
      <n-gi>
        <div class="detail-card">
          <h3>🧠 模型仓库</h3>
          <div class="dc-row"><span>模型版本</span><strong>{{dash?.total_models||0}}</strong></div>
          <div class="dc-row"><span>已部署</span><strong class="purple">{{dash?.deployed_models||0}}</strong></div>
        </div>
      </n-gi>
      <n-gi>
        <div class="detail-card recent">
          <h3>📋 最近任务</h3>
          <div v-if="dash?.recent_tasks?.length">
            <div v-for="(t,i) in dash.recent_tasks.slice(0,5)" :key="t.id||i" class="recent-item">
              <span class="ri-name">{{t.name}}</span>
              <n-tag :type="t.status==='completed'?'success':t.status==='running'?'info':'default'" size="tiny">{{t.status}}</n-tag>
            </div>
          </div>
          <div v-else class="no-data">暂无任务</div>
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
  {label:'总用户',value:dash.value?.total_users||0,icon:'👥',color:'#f59e0b'},
  {label:'活跃用户',value:dash.value?.active_users||0,icon:'🟢',color:'#22c55e'},
  {label:'总会话',value:dash.value?.total_sessions||0,icon:'💬',color:'#3b82f6'},
  {label:'总消息',value:dash.value?.total_messages||0,icon:'📝',color:'#8b5cf6'},
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
.dc-row span{color:#64748b}.dc-row strong{color:#1e293b;font-size:20px}.dc-row strong.blue{color:#3b82f6}.dc-row strong.green{color:#22c55e}.dc-row strong.purple{color:#8b5cf6}

.recent-item{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f1f5f9}
.recent-item:last-child{border-bottom:none}
.ri-name{font-size:13px;color:#475569;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;margin-right:8px}
.no-data{text-align:center;color:#94a3b8;padding:16px;font-size:13px}

[data-theme="dark"] .atop h2{color:#f1f5f9}
[data-theme="dark"] .stat-card,[data-theme="dark"] .detail-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .dc-row{border-bottom-color:#2d2d3d}
[data-theme="dark"] .dc-row span{color:#94a3b8}.dc-row strong{color:#e2e8f0}
[data-theme="dark"] .recent-item{border-bottom-color:#2d2d3d}
</style>
