<template>
  <div class="detail-page">
    <div class="detail-top">
      <n-button text @click="$router.push('/lab')">← 返回模型工厂</n-button>
    </div>

    <div v-if="!task" class="loading-state">⏳ 加载中...</div>

    <template v-else>
      <!-- Header -->
      <div class="detail-hero">
        <div class="dh-left">
          <span class="dh-icon">🧠</span>
          <div>
            <h1>{{ task.name }}</h1>
            <p>{{ task.base_model }} · {{ task.method?.toUpperCase() }} · {{ task.duration_seconds || 0 }}秒</p>
          </div>
        </div>
        <div class="dh-right">
          <n-tag :type="statusTagType(task.status)" size="large">{{ statusLabel(task.status) }}</n-tag>
          <n-button size="small" @click="fetchAll">🔄 刷新</n-button>
        </div>
      </div>

      <!-- Loss Chart -->
      <div class="section-card" v-if="task.loss_history">
        <h3>📉 训练 Loss 曲线</h3>
        <div class="loss-chart-container">
          <div class="loss-chart">
            <div v-for="(l,i) in task.loss_history" :key="i" class="loss-bar"
              :style="{height:Math.max(1,Math.min(120,(4-l)*30))+'px',opacity:0.5+(i/task.loss_history.length)*0.5}"
              :title="'Step '+i+': '+l" />
          </div>
          <div class="loss-axis">
            <span>Step 0</span>
            <span>{{ task.loss_history.length }} steps</span>
          </div>
        </div>
        <div class="loss-stats">
          <div class="ls-item"><div class="ls-v">{{ task.loss_history[0] }}</div><div class="ls-l">初始Loss</div></div>
          <div class="ls-item"><div class="ls-v green">{{ task.loss_history[task.loss_history.length-1] }}</div><div class="ls-l">最终Loss</div></div>
          <div class="ls-item"><div class="ls-v amber">{{ (task.loss_history[0] - task.loss_history[task.loss_history.length-1]).toFixed(2) }}</div><div class="ls-l">Loss下降</div></div>
        </div>
      </div>

      <!-- Metrics -->
      <div class="section-card" v-if="task.eval_metrics">
        <h3>📊 评估指标</h3>
        <div class="metrics-row">
          <div class="metric-card blue">
            <div class="mc-ring">
              <svg viewBox="0 0 100 100" width="80" height="80">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" stroke-width="8"/>
                <circle cx="50" cy="50" r="42" fill="none" stroke="#3b82f6" stroke-width="8"
                  :stroke-dasharray="264" :stroke-dashoffset="264*(1-task.eval_metrics.bleu)" stroke-linecap="round" transform="rotate(-90 50 50)"/>
              </svg>
            </div>
            <div class="mc-val">{{ task.eval_metrics.bleu }}</div>
            <div class="mc-lbl">BLEU Score</div>
          </div>
          <div class="metric-card green">
            <div class="mc-ring">
              <svg viewBox="0 0 100 100" width="80" height="80">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" stroke-width="8"/>
                <circle cx="50" cy="50" r="42" fill="none" stroke="#22c55e" stroke-width="8"
                  :stroke-dasharray="264" :stroke-dashoffset="264*(1-task.eval_metrics.rouge_l)" stroke-linecap="round" transform="rotate(-90 50 50)"/>
              </svg>
            </div>
            <div class="mc-val">{{ task.eval_metrics.rouge_l }}</div>
            <div class="mc-lbl">ROUGE-L</div>
          </div>
          <div class="metric-card amber">
            <div class="mc-ring">
              <svg viewBox="0 0 100 100" width="80" height="80">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" stroke-width="8"/>
                <circle cx="50" cy="50" r="42" fill="none" stroke="#f59e0b" stroke-width="8"
                  :stroke-dasharray="264" :stroke-dashoffset="264*(1-task.eval_metrics.human_score/5)" stroke-linecap="round" transform="rotate(-90 50 50)"/>
              </svg>
            </div>
            <div class="mc-val">{{ task.eval_metrics.human_score }}<span class="mc-unit">/5</span></div>
            <div class="mc-lbl">人工评分</div>
          </div>
        </div>
      </div>

      <!-- Models -->
      <div class="section-card">
        <div class="section-header">
          <h3>🧬 模型版本 ({{ models.length }})</h3>
          <div style="display:flex;gap:8px">
            <n-button size="small" @click="fetchModels">🔄 刷新</n-button>
            <n-button size="small" type="primary" @click="showFromHub=true" secondary>📥 从数据中枢导入</n-button>
          </div>
        </div>
        <div v-if="models.length" class="models-list">
          <div v-for="m in models" :key="m.id" class="model-card">
            <div class="md-left">
              <span class="md-ver">v{{ m.version_number }}</span>
              <div>
                <div class="md-name">{{ m.model_name }}</div>
                <div class="md-meta">{{ m.size_mb }}MB · {{ m.file_path }}</div>
              </div>
            </div>
            <div class="md-right">
              <n-tag v-if="m.is_deployed" type="success" size="small">已部署</n-tag>
              <n-tag v-else size="small">未部署</n-tag>
              <n-button v-if="!m.is_deployed" size="tiny" type="primary" @click="deployModel(m.id)" :loading="deployingId===m.id">部署</n-button>
              <n-button v-if="m.is_deployed" size="tiny" @click="testModel(m.id)">推理测试</n-button>
            </div>
          </div>
        </div>
        <div v-else class="no-data">暂无模型版本</div>
      </div>

      <!-- A/B Test -->
      <div class="section-card" v-if="task.status==='completed'">
        <h3>🔬 A/B 对比测试</h3>
        <p class="ab-desc">输入测试提示词，对比基座模型与微调模型的输出差异</p>
        <div class="ab-input-row">
          <n-input v-model:value="abPrompt" type="textarea" placeholder="输入测试提示词，如：能便宜点吗？" :autosize="{minRows:2,maxRows:3}" />
          <n-button type="primary" size="large" @click="doABTest" :loading="abLoading" class="ab-run-btn">
            {{ abLoading ? '对比中…' : '🔬 运行对比' }}
          </n-button>
        </div>

        <div v-if="abResults.length" class="ab-results">
          <div v-for="(ab,i) in abResults" :key="i" class="ab-card">
            <div class="ab-prompt-text">💬 {{ab.prompt}}</div>
            <div class="ab-compare">
              <div class="ab-col">
                <div class="ab-col-header">🧬 基础模型</div>
                <div class="ab-col-body">{{ab.base_response?.slice(0,400)||'-'}}</div>
              </div>
              <div class="ab-col" :class="{winner:ab.winner==='finetuned'}">
                <div class="ab-col-header">🧠 微调模型 {{ab.winner==='finetuned'?'🏆':''}}</div>
                <div class="ab-col-body">{{ab.finetuned_response?.slice(0,400)||'-'}}</div>
              </div>
            </div>
            <div v-if="ab.winner" class="ab-verdict" :class="ab.winner">
              {{ ab.winner==='finetuned' ? '✅ 微调模型胜出' : ab.winner==='base' ? '🔵 基础模型胜出' : '⚖️ 平局' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Model Inference Modal -->
      <n-modal v-model:show="showInference" title="模型推理测试" preset="card" style="width:600px">
        <template v-if="infResult">
          <n-tag type="success" size="small" style="margin-bottom:12px">{{ infResult.model }}</n-tag>
          <div class="inf-response">{{ infResult.response }}</div>
        </template>
      </n-modal>

      <!-- Import from DataHub Modal -->
      <n-modal v-model:show="showFromHub" title="从数据中枢导入数据集" preset="card" style="width:700px">
        <div v-if="hubLoading" style="text-align:center;padding:40px">⏳ 加载数据中枢...</div>
        <template v-else>
          <div v-if="hubDatasets.length" class="hub-list">
            <div v-for="ds in hubDatasets" :key="ds.id" class="hub-card">
              <div class="hub-info">
                <span class="hub-icon">{{ ds.source==='客服助手'?'💬':'📊' }}</span>
                <div>
                  <div class="hub-name">{{ ds.name }}</div>
                  <div class="hub-meta">{{ ds.item_count }}条 · {{ ds.source }} · {{ ds.status }}</div>
                </div>
              </div>
              <n-button size="tiny" type="primary" @click="importFromHub(ds.id,ds.name)" :loading="importingId===ds.id">导入训练</n-button>
            </div>
          </div>
          <div v-else class="no-data">数据中枢暂无可用数据集</div>
        </template>
      </n-modal>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'

const route = useRoute(); const msg = useMessage()
const task = ref<any>(null)
const models = ref<any[]>([])
const abPrompt = ref(''); const abLoading = ref(false); const abResults = ref<any[]>([])
const deployingId = ref('')

// Inference
const showInference = ref(false); const infResult = ref<any>(null)

// DataHub import
const showFromHub = ref(false); const hubLoading = ref(false)
const hubDatasets = ref<any[]>([]); const importingId = ref('')

const statusLabel=(s:string)=>({created:'已创建',running:'训练中',completed:'已完成',failed:'失败'}[s]||s)
const statusTagType=(s:string)=>({created:'default',running:'info',completed:'success',failed:'error'}[s]||'default') as any

async function fetchAll(){
  await Promise.all([fetchTask(),fetchModels()])
}

async function fetchTask(){
  const id = route.params.id as string; if(!id) return
  try{const r=await apiClient.get('/finetune/tasks/'+id);task.value=r.data}catch{}
}

async function fetchModels(){
  const id = route.params.id as string; if(!id) return
  try{const r=await apiClient.get('/finetune/tasks/'+id+'/models');models.value=r.data}catch{}
}

async function deployModel(modelId:string){
  deployingId.value=modelId
  try{await apiClient.patch('/finetune/models/'+modelId+'/deploy');msg.success('模型已部署');fetchModels()}catch{msg.error('部署失败')}
  finally{deployingId.value=''}
}

async function testModel(modelId:string){
  try{
    const r=await apiClient.post('/finetune/models/'+modelId+'/proxy',{message:'退货怎么操作？'})
    infResult.value=r.data; showInference.value=true
  }catch{msg.error('推理失败')}
}

async function doABTest(){
  if(!abPrompt.value||!task.value)return; abLoading.value=true
  try{
    const r=await apiClient.post('/finetune/tasks/'+task.value.id+'/abtests',{prompt:abPrompt.value})
    abResults.value.unshift(r.data); abPrompt.value=''; msg.success('A/B 对比完成')
  }catch{msg.error('对比失败')}
  finally{abLoading.value=false}
}

async function loadHubDatasets(){
  showFromHub.value=true; hubLoading.value=true
  try{const r=await apiClient.get('/data/datasets',{baseURL: import.meta.env.VITE_DATAHUB_API || 'http://localhost:8606/api'});hubDatasets.value=r.data.filter((d:any)=>d.status==='ready')}catch{msg.error('加载数据中枢失败')}
  finally{hubLoading.value=false}
}

async function importFromHub(dsId:string,dsName:string){
  importingId.value=dsId
  try{
    await apiClient.post('/finetune/tasks/from-dataset/'+dsId,{
      name:dsName+'-微调版',base_model:'deepseek-chat',method:'qlora',learning_rate:0.0002,epochs:3
    })
    msg.success('微调任务创建成功'); showFromHub.value=false; fetchAll()
  }catch{msg.error('创建失败')}
  finally{importingId.value=''}
}

onMounted(async()=>{
  await fetchAll()
  // Also load A/B tests
  const id = route.params.id as string
  if(id){try{const r=await apiClient.get('/finetune/tasks/'+id+'/abtests');abResults.value=r.data}catch{}}
})
</script>

<style scoped>
.detail-page{padding:32px 40px;max-width:1100px;height:100%;overflow-y:auto}
.detail-top{margin-bottom:20px}

.detail-hero{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}
.dh-left{display:flex;align-items:center;gap:14px}
.dh-icon{font-size:36px}
.dh-left h1{font-size:24px;font-weight:800;color:#0f172a;margin:0 0 4px}
.dh-left p{color:#64748b;font-size:14px;margin:0}
.dh-right{display:flex;align-items:center;gap:10px}

/* Section cards */
.section-card{background:#fff;border-radius:16px;border:1px solid #e2e8f0;padding:24px;margin-bottom:20px}
.section-card h3{margin:0 0 16px;font-size:16px;color:#1e293b}
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.section-header h3{margin:0}

/* Loss chart */
.loss-chart-container{margin-bottom:16px}
.loss-chart{display:flex;align-items:flex-end;gap:1px;height:120px;background:#f8fafc;border-radius:12px;padding:12px 16px}
.loss-bar{width:4px;background:linear-gradient(180deg,#f59e0b,#d97706);border-radius:2px;min-height:1px;flex-shrink:0;transition:opacity .3s}
.loss-axis{display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-top:6px}
.loss-stats{display:flex;gap:12px}
.ls-item{flex:1;text-align:center;padding:12px;background:#f8fafc;border-radius:10px}
.ls-v{font-size:22px;font-weight:800;color:#f59e0b}.ls-v.green{color:#22c55e}.ls-v.amber{color:#f59e0b}
.ls-l{font-size:11px;color:#94a3b8;margin-top:2px}

/* Metrics */
.metrics-row{display:flex;gap:16px}
.metric-card{flex:1;text-align:center;padding:24px 16px;background:#f8fafc;border-radius:14px}
.metric-card.blue .mc-val{color:#3b82f6}.metric-card.green .mc-val{color:#22c55e}.metric-card.amber .mc-val{color:#f59e0b}
.mc-ring{margin-bottom:8px}
.mc-val{font-size:36px;font-weight:800}.mc-unit{font-size:16px;font-weight:500;color:#94a3b8}
.mc-lbl{font-size:12px;color:#94a3b8;margin-top:4px}

/* Models */
.models-list{display:flex;flex-direction:column;gap:8px}
.model-card{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0}
.md-left{display:flex;align-items:center;gap:10px}
.md-ver{font-size:13px;font-weight:800;color:#f59e0b;min-width:30px}
.md-name{font-size:14px;font-weight:600;color:#1e293b}
.md-meta{font-size:11px;color:#94a3b8}
.md-right{display:flex;align-items:center;gap:6px}

/* A/B */
.ab-desc{font-size:13px;color:#94a3b8;margin:0 0 12px}
.ab-input-row{display:flex;gap:10px;align-items:flex-start;margin-bottom:16px}
.ab-input-row .n-input{flex:1}
.ab-run-btn{flex-shrink:0;border-radius:12px!important;background:linear-gradient(135deg,#f59e0b,#d97706)!important;border:none!important;font-weight:700!important}
.ab-results{display:flex;flex-direction:column;gap:14px}
.ab-card{background:#f8fafc;border-radius:14px;padding:16px}
.ab-prompt-text{font-size:13px;font-weight:600;color:#475569;margin-bottom:10px}
.ab-compare{display:flex;gap:10px}
.ab-col{flex:1;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0}
.ab-col.winner{border-color:#f59e0b;box-shadow:0 0 0 1px rgba(245,158,11,.2)}
.ab-col-header{font-size:12px;font-weight:700;color:#64748b;padding:8px 12px;background:#f1f5f9;text-align:center}
.ab-col.winner .ab-col-header{background:#fffbeb;color:#b45309}
.ab-col-body{padding:12px;font-size:13px;color:#334155;line-height:1.6;white-space:pre-wrap;max-height:180px;overflow-y:auto}
.ab-verdict{margin-top:10px;text-align:center;font-size:13px;font-weight:700;padding:6px 12px;border-radius:8px}
.ab-verdict.finetuned{background:#ecfdf5;color:#059669}
.ab-verdict.base{background:#eff6ff;color:#2563eb}
.ab-verdict.tie{background:#f1f5f9;color:#64748b}

/* Hub import */
.hub-list{display:flex;flex-direction:column;gap:8px;max-height:400px;overflow-y:auto}
.hub-card{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0}
.hub-info{display:flex;align-items:center;gap:10px}
.hub-icon{font-size:24px}.hub-name{font-size:14px;font-weight:600;color:#1e293b}.hub-meta{font-size:11px;color:#94a3b8}

/* Inference */
.inf-response{font-size:14px;color:#334155;line-height:1.7;white-space:pre-wrap;padding:16px;background:#fffbeb;border-radius:12px;max-height:400px;overflow-y:auto}

.loading-state{text-align:center;padding:80px;color:#94a3b8;font-size:18px}
.no-data{text-align:center;color:#94a3b8;font-size:13px;padding:16px}

[data-theme="dark"] .dh-left h1{color:#f1f5f9}
[data-theme="dark"] .section-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .section-card h3{color:#e2e8f0}
[data-theme="dark"] .loss-chart,.loss-stats .ls-item,.metric-card,.models-list .model-card,.ab-card,.hub-card{background:#252530;border-color:#2d2d3d}
[data-theme="dark"] .md-name{color:#e2e8f0}
[data-theme="dark"] .inf-response{background:#2d2508}
</style>
