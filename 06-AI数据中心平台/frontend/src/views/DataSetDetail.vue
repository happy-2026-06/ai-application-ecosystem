<template>
  <div class="detail-page">
    <!-- Back + header -->
    <div class="detail-top">
      <n-button text @click="$router.push('/data')">← 返回控制台</n-button>
      <div class="detail-header" v-if="dataset">
        <div class="dh-left">
          <span class="dh-icon">{{ sourceIcon(dataset.source) }}</span>
          <div>
            <h2>{{ dataset.name }}</h2>
            <p>{{ dataset.description || '暂无描述' }} · {{ dataset.source }} · {{ dataset.item_count }}条</p>
          </div>
        </div>
        <div class="dh-actions">
          <n-tag :type="statusType(dataset.status)" size="medium">{{ statusLabel(dataset.status) }}</n-tag>
          <n-button size="small" @click="fetchAll" :loading="loading">🔄 刷新</n-button>
          <n-button size="small" type="primary" @click="runClean" :loading="cleaning">🧹 清洗</n-button>
          <n-button size="small" type="primary" @click="runAnnotate" :loading="annotating">🏷️ AI标注</n-button>
          <n-dropdown trigger="click" :options="exportOptions" @select="handleExport">
            <n-button size="small" type="primary" secondary>📤 导出</n-button>
          </n-dropdown>
        </div>
      </div>
    </div>

    <div v-if="!dataset" class="loading-state">⏳ 加载中...</div>

    <!-- Pipeline progress -->
    <div v-else class="pipeline-bar">
      <div class="pipe-step" :class="{done:dataset.item_count>0,active:dataset.item_count>0}">
        <span>📥</span><span>采集</span>
      </div><div class="pipe-line" :class="{done:dataset.status!=='raw'}" />
      <div class="pipe-step" :class="{done:dataset.status!=='raw',active:cleaning}">
        <span>🧹</span><span>清洗</span>
      </div><div class="pipe-line" :class="{done:dataset.status==='ready'}" />
      <div class="pipe-step" :class="{done:dataset.status==='ready',active:annotating}">
        <span>🏷️</span><span>标注</span>
      </div><div class="pipe-line" />
      <div class="pipe-step" :class="{active:showQuality}">
        <span>📊</span><span>质量报告</span>
      </div><div class="pipe-line" />
      <div class="pipe-step">
        <span>📤</span><span>导出</span>
      </div>
    </div>

    <!-- Two-column layout -->
    <div class="detail-body">
      <!-- Left: Data table -->
      <div class="detail-left">
        <div class="detail-toolbar">
          <span class="toolbar-title">📋 数据条目 ({{ totalItems }}条)</span>
          <div class="toolbar-right">
            <n-select v-model:value="categoryFilter" :options="categoryOptions" placeholder="全部" clearable size="small" style="width:110px" />
            <n-pagination v-model:page="page" :page-size="pageSize" :item-count="totalItems" @update:page="fetchAnnotations" size="small" />
          </div>
        </div>

        <div class="annotation-list">
          <div v-for="item in annotations" :key="item.id" class="annotation-card">
            <div class="an-body">
              <div class="an-text">{{ item.data_item }}</div>
            </div>
            <div class="an-meta">
              <n-tag v-if="item.label" size="tiny" round :type="labelColor(item.label)">{{ item.label }}</n-tag>
              <n-tag v-if="item.category" size="tiny" :bordered="false">{{ item.category }}</n-tag>
              <n-tag v-if="item.sentiment" size="tiny" :type="sentimentType(item.sentiment)" round>{{ sentimentEmoji(item.sentiment) }} {{ item.sentiment }}</n-tag>
              <span class="an-confidence" v-if="item.confidence">置信{{ (item.confidence*100).toFixed(0) }}%</span>
              <n-tag size="tiny" :type="item.is_verified?'success':'default'">{{ item.is_verified?'✅ 已验证':'未验证' }}</n-tag>
            </div>
          </div>
          <div v-if="annotations.length===0 && !loading" class="empty-state">暂无数据，点击"📥 接收数据"接入跨系统数据</div>
        </div>
      </div>

      <!-- Right: Quality + Versions -->
      <div class="detail-right">
        <!-- Quality Report -->
        <div class="right-panel">
          <div class="panel-header" @click="toggleQuality">
            <h3>📊 质量报告</h3>
            <n-button size="tiny" text>{{ showQuality?'收起':'展开'}}</n-button>
          </div>
          <div v-if="showQuality && quality" class="panel-body">
            <div class="q-stat-row">
              <div class="q-stat">
                <div class="qs-v">{{ quality.total_items }}</div><div class="qs-l">总条目</div>
              </div>
              <div class="q-stat">
                <div class="qs-v green">{{ quality.completeness }}%</div><div class="qs-l">完整率</div>
              </div>
              <div class="q-stat">
                <div class="qs-v amber">{{ quality.quality_score }}</div><div class="qs-l">质量分</div>
              </div>
            </div>
            <div class="q-section" v-if="quality.label_distribution && Object.keys(quality.label_distribution).length">
              <div class="q-subtitle">标签分布</div>
              <div v-for="(v,k) in quality.label_distribution" :key="k" class="q-bar-row">
                <span class="q-bar-label">{{ k }}</span>
                <div class="q-bar-track"><div class="q-bar-fill" :style="{width:(v/quality.total_items*100)+'%'}"/></div>
                <span class="q-bar-num">{{ v }}</span>
              </div>
            </div>
            <n-button size="small" @click="fetchQuality" :loading="loadingQ" block style="margin-top:12px">刷新报告</n-button>
          </div>
          <div v-else-if="showQuality && !quality" class="panel-body">
            <p class="no-data">点击刷新生成质量报告</p>
            <n-button size="small" @click="fetchQuality" :loading="loadingQ">生成报告</n-button>
          </div>
        </div>

        <!-- Version History -->
        <div class="right-panel">
          <div class="panel-header">
            <h3>📜 版本历史</h3>
            <n-button size="tiny" @click="showCreateVer=true">+ 新版本</n-button>
          </div>
          <div v-if="versions.length" class="panel-body">
            <div v-for="v in versions" :key="v.id" class="version-item">
              <span class="vi-num">v{{ v.version_number }}</span>
              <div class="vi-info">
                <div class="vi-date">{{ formatDate(v.created_at) }}</div>
                <div class="vi-log">{{ v.change_log || '快照' }}</div>
              </div>
              <span class="vi-count">{{ v.item_count }}条</span>
            </div>
          </div>
          <div v-else class="panel-body"><p class="no-data">暂无版本快照</p></div>
        </div>
      </div>
    </div>

    <!-- Create Version Modal -->
    <n-modal v-model:show="showCreateVer" title="创建版本快照">
      <div style="padding:16px">
        <n-form :model="verForm" label-placement="top">
          <n-form-item label="变更说明"><n-input v-model:value="verForm.log" type="textarea" placeholder="如：新增500条数据+清洗去重"/></n-form-item>
        </n-form>
        <n-button type="primary" block @click="createVersion" :loading="creatingVer">创建版本</n-button>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'

const route = useRoute(); const router = useRouter(); const msg = useMessage()
const dataset = ref<any>(null)
const annotations = ref<any[]>([])
const loading = ref(false); const cleaning = ref(false); const annotating = ref(false)
const page = ref(1); const pageSize = 30; const totalItems = ref(0)
const categoryFilter = ref<string|null>(null)

// Quality report
const showQuality = ref(false); const loadingQ = ref(false)
const quality = ref<any>(null)

// Versions
const versions = ref<any[]>([])
const showCreateVer = ref(false); const creatingVer = ref(false)
const verForm = ref({log:''})

const categoryOptions = [
  {label:'全部',value:null},{label:'qa',value:'qa'},{label:'content',value:'content'},
  {label:'review',value:'review'},{label:'data',value:'data'},
]

const exportOptions = [
  {label:'导出微调格式 (给⑧模型工厂)',key:'finetune'},
  {label:'导出JSON (原始数据)',key:'json'},
]

function sourceIcon(s:string){const m:Record<string,string>={客服助手:'💬',灵笔引擎:'✍️',视界工坊:'🎬',图库管家:'🖼️',话术教练:'🎯',运营引擎:'🤖',upload:'📤',api:'🔗',crawl:'🕷️',test:'🧪'};return m[s]||'📊'}
function statusType(s:string){const m:Record<string,string>={ready:'success',cleaning:'warning',annotating:'info',raw:'default',archived:'default'};return (m[s]||'info') as any}
function statusLabel(s:string){const m:Record<string,string>={raw:'原始',cleaning:'清洗中',annotating:'标注中',ready:'就绪',archived:'已归档'};return m[s]||s}
function sentimentType(s:string){return s==='positive'?'success':s==='negative'?'error':'default' as any}
function sentimentEmoji(s:string){return s==='positive'?'😊':s==='negative'?'😞':'😐'}
function labelColor(l:string){const c:Record<string,string>={用户问题:'info',价格咨询:'warning',内容创作:'success',正面评价:'success',负面评价:'error',通用数据:'default'};return c[l]||'default' as any}
function formatDate(d:string){return d?new Date(d).toLocaleDateString('zh-CN'):''}

async function fetchAll(){await Promise.all([fetchDataset(),fetchAnnotations(),fetchQuality(),fetchVersions()])}

async function fetchDataset(){
  const id = route.params.id as string; if(!id) return
  try{const r = await apiClient.get('/data/datasets/'+id);dataset.value=r.data}catch{msg.error('加载数据集失败')}
}

async function fetchAnnotations(){
  const id = route.params.id as string; if(!id) return
  loading.value=true
  try{const params:any={page:page.value,page_size:pageSize};const r=await apiClient.get('/data/datasets/'+id+'/annotations',{params});annotations.value=r.data;totalItems.value=dataset.value?.item_count||r.data.length}catch{msg.error('加载标注数据失败')}
  finally{loading.value=false}
}

async function fetchQuality(){
  const id = route.params.id as string; if(!id) return
  showQuality.value=true; loadingQ.value=true
  try{const r=await apiClient.get('/data/datasets/'+id+'/quality');quality.value=r.data}catch{msg.error('加载质量报告失败')}
  finally{loadingQ.value=false}
}

async function fetchVersions(){
  const id = route.params.id as string; if(!id) return
  try{const r=await apiClient.get('/data/datasets/'+id+'/versions');versions.value=r.data}catch{}
}

async function runClean(){
  const id = route.params.id as string
  cleaning.value=true
  try{const r=await apiClient.post('/data/datasets/'+id+'/clean',{remove_duplicates:true,remove_empty:true,normalize_text:true});msg.success(`清洗完成：${r.data.before}→${r.data.after}条`);await fetchAll()}catch{msg.error('清洗失败')}
  finally{cleaning.value=false}
}

async function runAnnotate(){
  const id = route.params.id as string
  annotating.value=true
  try{const items=annotations.value.map((a,i)=>({text:a.data_item,index:i}));if(!items.length){msg.warning('没有可标注的数据');annotating.value=false;return};const r=await apiClient.post('/data/datasets/'+id+'/annotate',{items});msg.success(`AI标注完成：${r.data.annotated||0}条`);await fetchAll()}catch{msg.error('标注失败')}
  finally{annotating.value=false}
}

async function createVersion(){
  const id = route.params.id as string
  creatingVer.value=true
  try{await apiClient.post('/data/datasets/'+id+'/versions',{change_log:verForm.value.log});msg.success('版本已创建');showCreateVer.value=false;verForm.value.log='';fetchVersions()}catch{msg.error('创建版本失败')}
  finally{creatingVer.value=false}
}

async function handleExport(key:string){
  const id = route.params.id as string
  if(key==='finetune'){
    try{
      const r=await apiClient.get('/data/datasets/'+id+'/export-for-finetune')
      msg.success(`已导出 ${r.data.item_count} 条微调数据`)
      // Open model factory in new tab
      window.open('http://localhost:3008','_blank')
    }catch{msg.error('导出失败')}
  }
}

function toggleQuality(){showQuality.value=!showQuality.value;if(showQuality.value&&!quality.value)fetchQuality()}

onMounted(()=>{fetchAll()})
</script>

<style scoped>
.detail-page{padding:24px 32px;max-width:1400px;height:100%;overflow-y:auto}
.detail-top{margin-bottom:16px}
.detail-header{display:flex;justify-content:space-between;align-items:center}
.dh-left{display:flex;align-items:center;gap:14px}
.dh-icon{font-size:36px}
.dh-left h2{margin:0;font-size:22px;color:#0f172a}
.dh-left p{margin:4px 0 0;font-size:13px;color:#94a3b8}
.dh-actions{display:flex;align-items:center;gap:8px}

/* Pipeline */
.pipeline-bar{display:flex;align-items:center;gap:0;margin-bottom:20px;padding:16px 24px;background:#fff;border-radius:14px;border:1px solid #e2e8f0}
.pipe-step{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:12px;color:#94a3b8;min-width:56px}
.pipe-step span:first-child{font-size:20px}
.pipe-step.done{color:#0ea5e9}
.pipe-step.active{color:#0ea5e9;font-weight:700}
.pipe-line{flex:1;height:3px;background:#e2e8f0;border-radius:2px;min-width:30px}
.pipe-line.done{background:#0ea5e9}

/* Body */
.detail-body{display:flex;gap:20px}
.detail-left{flex:1;min-width:0}
.detail-right{width:300px;flex-shrink:0;display:flex;flex-direction:column;gap:16px}
.detail-toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.toolbar-title{font-size:14px;font-weight:600;color:#475569}
.toolbar-right{display:flex;align-items:center;gap:10px}

.annotation-list{display:flex;flex-direction:column;gap:8px}
.annotation-card{padding:14px 18px;background:#fff;border-radius:12px;border:1px solid #e2e8f0;transition:all .15s}
.annotation-card:hover{border-color:#bae6fd}
.an-body{margin-bottom:8px}
.an-text{font-size:14px;color:#334155;line-height:1.6;white-space:pre-wrap}
.an-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.an-confidence{font-size:11px;color:#94a3b8}

/* Right panels */
.right-panel{background:#fff;border-radius:14px;border:1px solid #e2e8f0;overflow:hidden}
.panel-header{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid #f1f5f9;cursor:pointer}
.panel-header h3{margin:0;font-size:14px;color:#1e293b}
.panel-body{padding:14px 16px}
.q-stat-row{display:flex;gap:8px;margin-bottom:12px}
.q-stat{flex:1;text-align:center;padding:10px 4px;background:#f8fafc;border-radius:8px}
.qs-v{font-size:20px;font-weight:800;color:#0ea5e9}.qs-v.green{color:#22c55e}.qs-v.amber{color:#f59e0b}
.qs-l{font-size:11px;color:#94a3b8;margin-top:2px}
.q-section{margin-top:8px}
.q-subtitle{font-size:12px;font-weight:600;color:#64748b;margin-bottom:6px}
.q-bar-row{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.q-bar-label{font-size:11px;color:#64748b;width:60px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.q-bar-track{flex:1;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden}
.q-bar-fill{height:100%;background:#0ea5e9;border-radius:3px;transition:width .4s}
.q-bar-num{font-size:11px;color:#94a3b8;width:20px}

.version-item{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f1f5f9}
.version-item:last-child{border-bottom:none}
.vi-num{font-size:12px;font-weight:700;color:#0ea5e9;min-width:30px}
.vi-info{flex:1}.vi-date{font-size:11px;color:#94a3b8}.vi-log{font-size:12px;color:#475569}
.vi-count{font-size:11px;color:#94a3b8}

.loading-state{text-align:center;padding:60px;color:#94a3b8;font-size:18px}
.empty-state{text-align:center;padding:60px;color:#94a3b8}
.no-data{text-align:center;color:#94a3b8;font-size:12px;padding:8px}

[data-theme="dark"] .dh-left h2{color:#f1f5f9}
[data-theme="dark"] .pipeline-bar{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .annotation-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .an-text{color:#cbd5e1}
[data-theme="dark"] .right-panel{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .panel-header{border-bottom-color:#2d2d3d}
[data-theme="dark"] .panel-header h3{color:#e2e8f0}
[data-theme="dark"] .q-stat{background:#252530}
[data-theme="dark"] .q-bar-track{background:#2d2d3d}
[data-theme="dark"] .version-item{border-bottom-color:#2d2d3d}
</style>
