<template>
  <div class="list-page">
    <div class="page-header">
      <div>
        <h2>📚 数据集列表</h2>
        <p>管理全部数据集 · 点击查看详情</p>
      </div>
      <n-button type="primary" @click="showCreate=true">+ 新建数据集</n-button>
    </div>

    <div class="search-bar">
      <n-input v-model:value="search" placeholder="搜索数据集名称/来源..." clearable style="max-width:320px" />
      <n-button size="small" @click="fetchList" :loading="loading">🔍 搜索</n-button>
    </div>

    <div v-if="loading" class="loading-state">⏳ 加载中...</div>
    <div v-else-if="!datasets.length" class="empty-state">暂无数据集，点击右上角新建</div>

    <div v-else class="ds-grid">
      <div v-for="ds in filtered" :key="ds.id" class="ds-card" @click="$router.push('/data/datasets/'+ds.id)">
        <div class="dc-top">
          <span class="dc-icon">{{ sourceIcon(ds.source) }}</span>
          <n-tag size="tiny" :type="statusType(ds.status)">{{ statusLabel(ds.status) }}</n-tag>
        </div>
        <div class="dc-name">{{ ds.name }}</div>
        <div class="dc-desc">{{ ds.description || '暂无描述' }}</div>
        <div class="dc-meta">
          <span>{{ ds.item_count }} 条数据</span>
          <span>·</span>
          <span>{{ ds.source }}</span>
          <span>·</span>
          <span>{{ formatDate(ds.updated_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <n-modal v-model:show="showCreate" title="新建数据集">
      <div style="padding:16px">
        <n-form label-placement="top">
          <n-form-item label="名称"><n-input v-model:value="createForm.name" placeholder="如：客服对话语料" /></n-form-item>
          <n-form-item label="描述"><n-input v-model:value="createForm.description" type="textarea" :rows="3" placeholder="数据集用途说明" /></n-form-item>
          <n-form-item label="来源">
            <n-select v-model:value="createForm.source" :options="[
              {label:'上传 upload',value:'upload'},{label:'API api',value:'api'},
              {label:'爬取 crawl',value:'crawl'},{label:'测试 test',value:'test'}]" />
          </n-form-item>
        </n-form>
        <n-button type="primary" block @click="createDataset" :loading="creating">创建</n-button>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'

const msg = useMessage()
const datasets = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const showCreate = ref(false); const creating = ref(false)
const createForm = ref({name:'',description:'',source:'upload'})

const filtered = computed(() => {
  if(!search.value) return datasets.value
  const q = search.value.toLowerCase()
  return datasets.value.filter(d =>
    (d.name||'').toLowerCase().includes(q) || (d.source||'').toLowerCase().includes(q)
  )
})

function sourceIcon(s:string){const m:Record<string,string>={客服助手:'💬',灵笔引擎:'✍️',视界工坊:'🎬',图库管家:'🖼️',话术教练:'🎯',运营引擎:'🤖',upload:'📤',api:'🔗',crawl:'🕷️',test:'🧪'};return m[s]||'📊'}
function statusType(s:string){const m:Record<string,string>={ready:'success',cleaning:'warning',annotating:'info',raw:'default',archived:'default'};return (m[s]||'info') as any}
function statusLabel(s:string){const m:Record<string,string>={raw:'原始',cleaning:'清洗中',annotating:'标注中',ready:'就绪',archived:'已归档'};return m[s]||s}
function formatDate(d:string){return d?new Date(d).toLocaleDateString('zh-CN'):''}

async function fetchList(){
  loading.value=true
  try{const r=await apiClient.get('/data/datasets',{params:{page:1,page_size:100}});datasets.value=r.data}catch{msg.error('加载数据集失败')}
  finally{loading.value=false}
}

async function createDataset(){
  if(!createForm.value.name.trim()){msg.warning('请输入名称');return}
  creating.value=true
  try{
    await apiClient.post('/data/datasets',{
      name:createForm.value.name.trim(),
      description:createForm.value.description,
      source:createForm.value.source,
    })
    msg.success('数据集已创建');showCreate.value=false
    createForm.value={name:'',description:'',source:'upload'}
    await fetchList()
  }catch{msg.error('创建失败')}
  finally{creating.value=false}
}

onMounted(fetchList)
</script>

<style scoped>
.list-page{padding:24px 32px;max-width:1200px;height:100%;overflow-y:auto}
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.page-header h2{margin:0;font-size:22px;color:#0f172a}
.page-header p{margin:4px 0 0;font-size:13px;color:#94a3b8}
.search-bar{display:flex;gap:8px;margin-bottom:20px}
.ds-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.ds-card{padding:18px;background:#fff;border-radius:14px;border:1px solid #e2e8f0;cursor:pointer;transition:all .15s}
.ds-card:hover{border-color:#bae6fd;transform:translateY(-2px);box-shadow:0 6px 20px rgba(14,165,233,.08)}
.dc-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.dc-icon{font-size:28px}
.dc-name{font-size:16px;font-weight:700;color:#1e293b;margin-bottom:6px}
.dc-desc{font-size:12px;color:#94a3b8;margin-bottom:10px;height:32px;overflow:hidden}
.dc-meta{font-size:11px;color:#64748b}
.loading-state{text-align:center;padding:60px;color:#94a3b8;font-size:18px}
.empty-state{text-align:center;padding:60px;color:#94a3b8}
[data-theme="dark"] .page-header h2{color:#f1f5f9}
[data-theme="dark"] .ds-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .dc-name{color:#e2e8f0}
</style>
