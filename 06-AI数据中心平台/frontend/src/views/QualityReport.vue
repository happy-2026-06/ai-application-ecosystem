<template>
  <div class="quality-page">
    <div class="page-header">
      <div>
        <h2>📊 质量报告仪表盘</h2>
        <p>全局数据质量总览 · 各数据集质量排名</p>
      </div>
      <n-button @click="fetchAll" :loading="loading">🔄 刷新</n-button>
    </div>

    <!-- Global stats -->
    <div class="stat-row" v-if="dash">
      <div class="stat-card">
        <div class="sc-v">{{ dash.total_datasets }}</div>
        <div class="sc-l">数据集总数</div>
      </div>
      <div class="stat-card">
        <div class="sc-v">{{ dash.total_items }}</div>
        <div class="sc-l">数据条目</div>
      </div>
      <div class="stat-card">
        <div class="sc-v green">{{ dash.ai_annotated }}</div>
        <div class="sc-l">AI 已标注</div>
      </div>
      <div class="stat-card">
        <div class="sc-v amber">{{ dash.human_verified }}</div>
        <div class="sc-l">人工已验证</div>
      </div>
      <div class="stat-card">
        <div class="sc-v highlight">{{ dash.avg_quality_score }}</div>
        <div class="sc-l">平均质量分</div>
      </div>
    </div>

    <!-- Per-dataset quality ranking -->
    <div class="rank-panel">
      <div class="panel-title">📈 数据集质量排名</div>
      <div v-if="loading" class="loading-state">⏳ 加载中...</div>
      <div v-else-if="!qualityList.length" class="empty-state">暂无质量数据 — 先去数据集详情页生成质量报告</div>
      <div v-else class="rank-list">
        <div v-for="(q,i) in qualityList" :key="q.dataset_id" class="rank-item" @click="$router.push('/data/datasets/'+q.dataset_id)">
          <span class="ri-rank" :class="{top:i<3}">#{{ i+1 }}</span>
          <div class="ri-main">
            <div class="ri-name">{{ q.dataset_name }}</div>
            <div class="ri-sub">{{ q.total_items }}条 · 标注{{ q.annotated_items }} · 验证{{ q.verified_items }}</div>
          </div>
          <div class="ri-progress">
            <div class="rp-track"><div class="rp-fill" :style="{width:(q.quality_score||0)+'%'}" :class="{high:q.quality_score>=70,mid:q.quality_score>=40&&q.quality_score<70,low:q.quality_score<40}"/></div>
          </div>
          <span class="ri-score" :class="{high:q.quality_score>=70,mid:q.quality_score>=40&&q.quality_score<70,low:q.quality_score<40}">{{ q.quality_score }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'

const msg = useMessage()
const dash = ref<any>(null)
const qualityList = ref<any[]>([])
const loading = ref(false)

async function fetchAll(){
  loading.value=true
  try{
    const [dashR, listR] = await Promise.all([
      apiClient.get('/data/dashboard'),
      apiClient.get('/data/datasets',{params:{page:1,page_size:100}}),
    ])
    dash.value=dashR.data
    const datasets = listR.data || []
    // Fetch quality report for each dataset (skip failures gracefully)
    const results = await Promise.allSettled(
      datasets.map((d:any)=>apiClient.get('/data/datasets/'+d.id+'/quality'))
    )
    qualityList.value = results
      .map((r:any,i:number)=>r.status==='fulfilled'?r.value.data:null)
      .filter(Boolean)
      .sort((a:any,b:any)=>(b.quality_score||0)-(a.quality_score||0))
  }catch{msg.error('加载质量数据失败')}
  finally{loading.value=false}
}

onMounted(fetchAll)
</script>

<style scoped>
.quality-page{padding:24px 32px;max-width:1200px;height:100%;overflow-y:auto}
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.page-header h2{margin:0;font-size:22px;color:#0f172a}
.page-header p{margin:4px 0 0;font-size:13px;color:#94a3b8}
.stat-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}
.stat-card{padding:18px;background:#fff;border-radius:14px;border:1px solid #e2e8f0;text-align:center}
.sc-v{font-size:26px;font-weight:800;color:#0ea5e9}
.sc-v.green{color:#22c55e}.sc-v.amber{color:#f59e0b}.sc-v.highlight{color:#0ea5e9}
.sc-l{font-size:12px;color:#94a3b8;margin-top:4px}
.rank-panel{background:#fff;border-radius:14px;border:1px solid #e2e8f0;overflow:hidden}
.panel-title{padding:14px 18px;font-size:15px;font-weight:700;color:#1e293b;border-bottom:1px solid #f1f5f9}
.rank-list{padding:6px 18px}
.rank-item{display:flex;align-items:center;gap:14px;padding:12px 0;border-bottom:1px solid #f1f5f9;cursor:pointer}
.rank-item:last-child{border-bottom:none}
.rank-item:hover{background:#f8fafc}
.ri-rank{font-size:14px;font-weight:800;color:#94a3b8;min-width:34px}
.ri-rank.top{color:#f59e0b}
.ri-main{flex:1;min-width:0}
.ri-name{font-size:14px;font-weight:600;color:#334155}
.ri-sub{font-size:11px;color:#94a3b8;margin-top:2px}
.ri-progress{width:180px}
.rp-track{height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.rp-fill{height:100%;border-radius:4px;transition:width .4s}
.rp-fill.high{background:#22c55e}.rp-fill.mid{background:#f59e0b}.rp-fill.low{background:#ef4444}
.ri-score{font-size:16px;font-weight:800;min-width:44px;text-align:right}
.ri-score.high{color:#22c55e}.ri-score.mid{color:#f59e0b}.ri-score.low{color:#ef4444}
.loading-state{text-align:center;padding:60px;color:#94a3b8;font-size:18px}
.empty-state{text-align:center;padding:60px;color:#94a3b8}
[data-theme="dark"] .page-header h2{color:#f1f5f9}
[data-theme="dark"] .stat-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .rank-panel{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .panel-title{color:#e2e8f0;border-bottom-color:#2d2d3d}
[data-theme="dark"] .rank-item{border-bottom-color:#2d2d3d}
[data-theme="dark"] .rank-item:hover{background:#252530}
[data-theme="dark"] .ri-name{color:#cbd5e1}
[data-theme="dark"] .rp-track{background:#2d2d3d}
</style>
