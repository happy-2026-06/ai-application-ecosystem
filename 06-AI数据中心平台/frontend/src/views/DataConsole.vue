<template>
  <div class="dc-page">
    <div class="dc-hero">
      <div><h1>数据控制台</h1><p>数据采集 · 智能清洗 · AI标注 · 版本管理 · 质量分析</p></div>
      <div class="dc-hero-right">
        <n-button size="large" @click="showIngest=true" secondary>📥 接收跨系统数据</n-button>
        <n-button type="primary" size="large" @click="showCreate=true">+ 新建数据集</n-button>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-row" v-if="stats">
      <div class="st-card"><div class="st-v">{{stats.total_datasets}}</div><div class="st-l">数据集</div></div>
      <div class="st-card"><div class="st-v">{{stats.total_items}}</div><div class="st-l">数据条目</div></div>
      <div class="st-card"><div class="st-v">{{stats.ai_annotated}}</div><div class="st-l">AI标注</div></div>
      <div class="st-card"><div class="st-v">{{stats.human_verified}}</div><div class="st-l">人工校验</div></div>
    </div>

    <!-- Datasets -->
    <h2 style="margin:24px 0 12px;font-size:18px;color:#1e293b;">📁 数据集列表</h2>
    <div class="ds-grid" v-if="datasets.length">
      <div v-for="d in datasets" :key="d.id" class="ds-card" @click="goDetail(d.id)">
        <div class="ds-header">
          <span class="ds-icon">{{ sourceIcon(d.source) }}</span>
          <n-tag :type="statusType(d.status)" size="small">{{ statusLabel(d.status) }}</n-tag>
        </div>
        <div class="ds-name">{{d.name}}</div>
        <div class="ds-desc">{{d.description||'暂无描述'}}</div>
        <div class="ds-meta">
          <span>📝 {{d.item_count}}条</span>
          <span>来源: {{d.source}}</span>
        </div>
      </div>
    </div>
    <div v-else class="empty"><span>📭</span><p>还没有数据集，点击"接收跨系统数据"试试</p></div>

    <!-- Cross-System Ingest Modal -->
    <n-modal v-model:show="showIngest" title="📥 接收跨系统数据" style="width:600px">
      <div class="modal-form">
        <n-form :model="ig" label-placement="top">
          <n-form-item label="来源系统">
            <n-select v-model:value="ig.source" :options="sourceOptions" placeholder="选择数据来源系统"/>
          </n-form-item>
          <n-form-item label="数据类型">
            <n-select v-model:value="ig.dataType" :options="[{label:'对话记录 (chat_qa)',value:'chat_qa'},{label:'训练数据 (training)',value:'training'},{label:'内容生成 (content)',value:'content'},{label:'原始文本 (text)',value:'text'}]"/>
          </n-form-item>
          <n-form-item label="数据集名称">
            <n-input v-model:value="ig.datasetName" placeholder="如：客服对话语料、话术训练数据"/>
          </n-form-item>
          <n-form-item label="数据内容（每行一条）">
            <n-input v-model:value="ig.texts" type="textarea" :autosize="{minRows:5,maxRows:15}" placeholder="Q: 退货怎么操作？&#10;A: 7天无理由退货，请在线申请&#10;&#10;Q: 多久发货？&#10;A: 24小时内发货"/>
          </n-form-item>
        </n-form>
        <n-button type="primary" block @click="doIngest" :loading="ingesting" size="large" style="margin-top:12px;background:linear-gradient(135deg,#f59e0b,#d97706);border:none">
          {{ ingesting ? '接入中…' : '📥 接入数据' }}
        </n-button>
      </div>
    </n-modal>

    <!-- Create Modal -->
    <n-modal v-model:show="showCreate" title="新建数据集">
      <div style="padding:16px">
        <n-form ref="cf" :model="cd" :rules="cr" label-placement="top">
          <n-form-item label="数据集名称" path="name"><n-input v-model:value="cd.name" placeholder="如：京东客服对话语料"/></n-form-item>
          <n-form-item label="描述" path="desc"><n-input v-model:value="cd.desc" type="textarea" placeholder="描述数据集的内容和用途"/></n-form-item>
          <n-form-item label="来源" path="source"><n-select v-model:value="cd.source" :options="[{label:'手动上传',value:'upload'},{label:'API导入',value:'api'},{label:'爬虫采集',value:'crawl'}]"/></n-form-item>
        </n-form>
        <n-button type="primary" block @click="doCreate" :loading="creating" style="margin-top:12px">创建数据集</n-button>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { dataApi, type DataSet, type DashboardStats } from '../api/data'
const router = useRouter(); const msg = useMessage()
const stats = ref<DashboardStats|null>(null); const datasets = ref<DataSet[]>([])
const showCreate = ref(false); const creating = ref(false)
const showIngest = ref(false); const ingesting = ref(false)
const cd = ref({name:'',desc:'',source:'upload'})
const cr = {name:[{required:true,message:'请输入名称'}]}
const ig = ref({source:'客服助手',dataType:'chat_qa',datasetName:'',texts:''})

const sourceOptions = [
  {label:'💬 智能客服助手',value:'客服助手'},
  {label:'✍️ 灵笔内容引擎',value:'灵笔引擎'},
  {label:'🎬 视界短视频工坊',value:'视界工坊'},
  {label:'🖼️ 图库资产管家',value:'图库管家'},
  {label:'🎯 话术对战教练',value:'话术教练'},
  {label:'🤖 智能运营引擎',value:'运营引擎'},
]

function sourceIcon(s:string){const m:Record<string,string>={rag客服:'💬',客服助手:'💬',灵笔引擎:'✍️',视界工坊:'🎬',图库管家:'🖼️',话术教练:'🎯',运营引擎:'🤖',upload:'📤',api:'🔗',crawl:'🕷️',test:'🧪'};return m[s]||'📊'}
const statusType=(s:string)=>s==='ready'?'success':s==='archived'?'default':s==='raw'?'warning':'info'
const statusLabel=(s:string)=>({raw:'原始',cleaning:'清洗中',annotating:'标注中',ready:'就绪',archived:'已归档'})[s]||s
function goDetail(id:string){router.push('/data/datasets/'+id)}

async function doCreate(){
  try{await dataApi.createDataset({name:cd.value.name,description:cd.value.desc,source:cd.value.source});showCreate.value=false;msg.success('创建成功');loadData()}
  catch{msg.error('创建失败')}
}

async function doIngest(){
  if(!ig.value.texts.trim()){msg.warning('请输入数据内容');return}
  ingesting.value=true
  try{
    const texts = ig.value.texts.split('\n').filter(t=>t.trim())
    const r = await dataApi.ingestExternal(
      ig.value.source,
      ig.value.dataType,
      texts,
      ig.value.datasetName || `来自${ig.value.source}的数据`
    )
    msg.success(`成功接入 ${r.data.count} 条数据`)
    showIngest.value=false; ig.value.texts=''; ig.value.datasetName=''
    loadData()
  }catch{msg.error('接入失败，请检查数据格式')}
  finally{ingesting.value=false}
}

async function loadData(){
  try{
    const [sr,dr]=await Promise.all([dataApi.dashboard(),dataApi.listDatasets()])
    stats.value=sr.data; datasets.value=dr.data.filter((d:DataSet)=>d.status!=='archived')
  }catch{}
}
onMounted(loadData)
</script>

<style scoped>
.dc-page{padding:32px 40px;max-width:1200px;margin:0 auto}
.dc-hero{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
.dc-hero h1{font-size:26px;font-weight:800;color:#0c4a6e;margin:0 0 4px}
.dc-hero p{color:#64748b;font-size:14px;margin:0}
.dc-hero-right{display:flex;gap:10px}
.stats-row{display:flex;gap:16px;margin-bottom:16px}
.st-card{flex:1;background:#fff;padding:20px;border-radius:16px;border:1px solid #e2e8f0;text-align:center}
.st-v{font-size:32px;font-weight:800;color:#0ea5e9}.st-l{font-size:12px;color:#94a3b8;margin-top:4px}
.ds-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.ds-card{padding:20px;background:#fff;border-radius:16px;border:1px solid #e2e8f0;cursor:pointer;transition:all .15s}
.ds-card:hover{border-color:#7dd3fc;box-shadow:0 4px 16px rgba(14,165,233,.06);transform:translateY(-2px)}
.ds-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.ds-icon{font-size:28px}.ds-name{font-size:16px;font-weight:700;color:#1e293b;margin-bottom:6px}
.ds-desc{font-size:13px;color:#94a3b8;margin-bottom:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ds-meta{display:flex;gap:16px;font-size:12px;color:#64748b}
.empty{text-align:center;padding:60px 20px;color:#94a3b8}.empty span{font-size:48px;display:block;margin-bottom:8px}
.modal-form{padding:8px 0}
</style>
