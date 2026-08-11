<template>
  <div class="lab-page">
    <!-- Hero section -->
    <div class="lab-hero">
      <div class="hero-content">
        <h1>模型工厂</h1>
        <p>QLoRA 低显存微调 · 实时 Loss 可视化 · A/B 对比评估 · 一键部署推理 API</p>
      </div>
    </div>

    <!-- Stats row -->
    <div class="stats-row" v-if="stats">
      <div class="st-card">
        <div class="st-icon-wrap amber"><span>🧪</span></div>
        <div class="st-v">{{stats.total_tasks}}</div>
        <div class="st-l">任务总数</div>
      </div>
      <div class="st-card">
        <div class="st-icon-wrap green"><span>✅</span></div>
        <div class="st-v green">{{stats.completed_tasks}}</div>
        <div class="st-l">已完成</div>
      </div>
      <div class="st-card">
        <div class="st-icon-wrap blue"><span>🧠</span></div>
        <div class="st-v">{{stats.total_models}}</div>
        <div class="st-l">模型版本</div>
      </div>
      <div class="st-card">
        <div class="st-icon-wrap purple"><span>🚀</span></div>
        <div class="st-v purple">{{stats.deployed_models}}</div>
        <div class="st-l">已部署</div>
      </div>
    </div>

    <!-- Section header -->
    <div class="section-header">
      <h2>🧪 微调任务</h2>
      <n-button type="primary" size="large" @click="showCreate=true" class="create-btn">
        + 新建任务
      </n-button>
    </div>

    <!-- Task grid -->
    <div class="task-grid" v-if="tasks.length">
      <div v-for="t in tasks" :key="t.id" class="task-card" @click="selectTask(t)">
        <div class="tk-header">
          <span class="tk-name">{{t.name}}</span>
          <n-tag :type="statusTagType(t.status)" size="small" round>{{statusLabel(t.status)}}</n-tag>
        </div>
        <div class="tk-meta">
          <span class="tk-meta-item">🧬 {{t.base_model}}</span>
          <span class="tk-meta-item">⚙️ {{t.method?.toUpperCase()}}</span>
          <span class="tk-meta-item">⏱ {{t.duration_seconds||0}}s</span>
        </div>
        <div v-if="t.eval_metrics" class="tk-metrics">
          <div class="metric-badge">
            <span class="metric-label">BLEU</span>
            <span class="metric-value">{{t.eval_metrics.bleu}}</span>
          </div>
          <div class="metric-badge">
            <span class="metric-label">ROUGE-L</span>
            <span class="metric-value">{{t.eval_metrics.rouge_l}}</span>
          </div>
          <div class="metric-badge highlight">
            <span class="metric-label">人工评分</span>
            <span class="metric-value">{{t.eval_metrics.human_score}}</span>
          </div>
        </div>
        <!-- Mini loss chart -->
        <div v-if="t.loss_history" class="tk-chart">
          <div class="chart-label">Loss ↓</div>
          <div class="chart-bars">
            <div v-for="(l,i) in t.loss_history.slice(-60)" :key="i" class="tk-bar"
              :style="{height:Math.max(2,Math.min(30,(4-l)*8))+'px'}"
              :title="'Step '+(t.loss_history.length-60+i)+': '+l" />
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <span class="empty-icon">🧪</span>
      <h3>暂无微调任务</h3>
      <p>点击「新建任务」开始你的第一个模型微调</p>
    </div>

    <!-- New Task Modal -->
    <n-modal v-model:show="showCreate" title="新建微调任务" preset="card" style="width:560px" :bordered="false">
      <div class="modal-form">
        <n-form :model="tf" label-placement="top" size="large">
          <n-form-item label="任务名称">
            <n-input v-model:value="tf.name" placeholder="如：客服对话模型 v2" />
          </n-form-item>
          <n-form-item label="基座模型">
            <n-select v-model:value="tf.base" :options="[
              {label:'DeepSeek-Chat',value:'deepseek-chat'},
              {label:'Qwen2.5-7B',value:'qwen2.5-7b'},
              {label:'Qwen2.5-14B',value:'qwen2.5-14b'},
              {label:'Llama-3-8B',value:'llama-3-8b'},
            ]"/>
          </n-form-item>
          <n-form-item label="微调方法">
            <n-select v-model:value="tf.method" :options="[
              {label:'QLoRA (低显存推荐)',value:'qlora'},
              {label:'LoRA',value:'lora'},
              {label:'全量微调 (需大显存)',value:'full'},
            ]"/>
          </n-form-item>
          <n-grid cols="2" x-gap="12">
            <n-gi>
              <n-form-item label="学习率"><n-input-number v-model:value="tf.lr" :step="0.0001" :min="0.00001" :max="0.01" /></n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="训练轮数"><n-input-number v-model:value="tf.epochs" :min="1" :max="20" /></n-form-item>
            </n-gi>
          </n-grid>
        </n-form>
        <n-button type="primary" block size="large" @click="doCreate" :loading="creating" class="create-submit-btn">
          {{ creating ? '微调训练中…' : '🚀 开始微调' }}
        </n-button>
      </div>
    </n-modal>

    <!-- Task Detail + A/B Test Modal -->
    <n-modal v-model:show="showDetail" :title="selTask?.name" preset="card" style="width:960px;max-width:95vw" :bordered="false">
      <div v-if="selTask" class="detail-panel">
        <!-- Task info -->
        <div class="detail-info">
          <n-tag :type="statusTagType(selTask.status)" size="medium">{{statusLabel(selTask.status)}}</n-tag>
          <span class="detail-meta">{{selTask.base_model}} · {{selTask.method?.toUpperCase()}} · {{selTask.duration_seconds||0}}秒</span>
        </div>

        <!-- Loss chart (full) -->
        <div v-if="selTask.loss_history" class="detail-chart">
          <h3>📉 训练 Loss 曲线</h3>
          <div class="full-chart">
            <div v-for="(l,i) in selTask.loss_history" :key="i" class="full-chart-bar"
              :style="{height:Math.max(1,Math.min(80,(4-l)*20))+'px'}"
              :title="'Step '+i+': '+l" />
          </div>
          <div class="chart-axis">
            <span>Step 0</span>
            <span>Step {{selTask.loss_history.length}}</span>
          </div>
        </div>

        <!-- Eval metrics -->
        <div v-if="selTask.eval_metrics" class="detail-metrics">
          <h3>📊 评估指标</h3>
          <div class="metrics-grid">
            <div class="m-card"><div class="m-val blue">{{selTask.eval_metrics.bleu}}</div><div class="m-lbl">BLEU Score</div></div>
            <div class="m-card"><div class="m-val green">{{selTask.eval_metrics.rouge_l}}</div><div class="m-lbl">ROUGE-L</div></div>
            <div class="m-card"><div class="m-val amber">{{selTask.eval_metrics.human_score}}</div><div class="m-lbl">人工评分 /5</div></div>
          </div>
        </div>

        <!-- A/B Test section -->
        <div v-if="selTask.status==='completed'" class="ab-section">
          <h3>🔬 A/B 对比测试</h3>
          <p class="ab-desc">输入测试提示词，对比基座模型与微调模型的输出差异</p>
          <div class="ab-input-row">
            <n-input v-model:value="abPrompt" type="textarea" placeholder="输入测试提示词，如：如何向客户推荐我们的新产品？" :autosize="{minRows:2,maxRows:4}" />
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
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'
const router = useRouter(); const msg = useMessage()
const stats = ref<any>(null); const tasks = ref<any[]>([]); const showCreate = ref(false); const creating = ref(false)
const tf = ref({name:'',base:'deepseek-chat',method:'qlora',lr:0.0002,epochs:3})
const showDetail = ref(false); const selTask = ref<any>(null); const abPrompt = ref(''); const abLoading = ref(false); const abResults = ref<any[]>([])

const statusLabel=(s:string)=>({created:'已创建',running:'训练中',completed:'已完成',failed:'失败'}[s]||s)
const statusTagType=(s:string)=>({created:'default',running:'info',completed:'success',failed:'error'}[s]||'default') as any

async function loadData(){
  try{
    const [r,t] = await Promise.all([
      apiClient.get('/finetune/dashboard'),
      apiClient.get('/finetune/tasks')
    ])
    stats.value = r.data; tasks.value = t.data
  }catch{}
}

async function doCreate(){
  if(!tf.value.name.trim()){msg.warning('请输入任务名称');return}
  creating.value=true
  try{
    await apiClient.post('/finetune/tasks',{
      name:tf.value.name,base_model:tf.value.base,method:tf.value.method,
      learning_rate:tf.value.lr,epochs:tf.value.epochs
    })
    showCreate.value=false; msg.success('微调任务创建成功，训练已开始')
    tf.value.name=''; loadData()
  }catch{msg.error('创建失败')}
  finally{creating.value=false}
}

async function selectTask(t:any){
  router.push('/lab/tasks/'+t.id)
}

async function doABTest(){
  if(!abPrompt.value||!selTask.value)return; abLoading.value=true
  try{
    const r=await apiClient.post('/finetune/tasks/'+selTask.value.id+'/abtests',{prompt:abPrompt.value})
    abResults.value.unshift(r.data); abPrompt.value=''; msg.success('A/B 对比完成')
  }catch{msg.error('对比失败')}
  finally{abLoading.value=false}
}

onMounted(loadData)
</script>

<style scoped>
.lab-page{padding:32px 40px;max-width:1280px;margin:0 auto;height:100%;overflow-y:auto}

/* Hero */
.lab-hero{margin-bottom:28px}
.lab-hero h1{font-size:26px;font-weight:800;color:#0f172a;margin:0 0 6px}
.lab-hero p{color:#64748b;font-size:14px;margin:0}

/* Stats */
.stats-row{display:flex;gap:16px;margin-bottom:32px}
.st-card{flex:1;background:#fff;padding:24px;border-radius:16px;border:1px solid #e2e8f0;text-align:center;transition:all .2s}
.st-card:hover{border-color:#fcd34d;box-shadow:0 4px 20px rgba(245,158,11,.06);transform:translateY(-2px)}
.st-icon-wrap{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;margin:0 auto 12px}
.st-icon-wrap.amber{background:#fffbeb}.st-icon-wrap.green{background:#ecfdf5}
.st-icon-wrap.blue{background:#eff6ff}.st-icon-wrap.purple{background:#f5f3ff}
.st-v{font-size:32px;font-weight:800;color:#f59e0b;line-height:1}.st-v.green{color:#22c55e}.st-v.purple{color:#8b5cf6}
.st-l{font-size:12px;color:#94a3b8;margin-top:6px}

/* Section header */
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.section-header h2{font-size:17px;font-weight:700;color:#1e293b;margin:0}
.create-btn{height:42px!important;font-weight:700!important;border-radius:12px!important;background:linear-gradient(135deg,#f59e0b,#d97706)!important;border:none!important;box-shadow:0 4px 16px rgba(245,158,11,.2)}
.create-btn:hover{transform:translateY(-1px);box-shadow:0 8px 24px rgba(245,158,11,.35)!important}

/* Task grid */
.task-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.task-card{padding:20px 24px;background:#fff;border-radius:16px;border:1px solid #e2e8f0;cursor:pointer;transition:all .2s}
.task-card:hover{border-color:#fcd34d;box-shadow:0 6px 24px rgba(245,158,11,.08);transform:translateY(-2px)}
.tk-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.tk-name{font-size:15px;font-weight:700;color:#1e293b}
.tk-meta{display:flex;gap:12px;margin-bottom:8px;flex-wrap:wrap}
.tk-meta-item{font-size:12px;color:#94a3b8;background:#f8fafc;padding:2px 8px;border-radius:6px}
.tk-metrics{display:flex;gap:8px;margin-bottom:10px}
.metric-badge{text-align:center;padding:6px 10px;background:#f8fafc;border-radius:8px;min-width:70px}
.metric-badge.highlight{background:#fffbeb}
.metric-label{display:block;font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px}
.metric-value{font-size:18px;font-weight:800;color:#1e293b}
.tk-chart{display:flex;align-items:center;gap:8px}
.chart-label{font-size:10px;color:#94a3b8;white-space:nowrap}
.chart-bars{display:flex;align-items:flex-end;gap:1px;flex:1;height:30px}
.tk-bar{width:3px;background:linear-gradient(180deg,#f59e0b,#fbbf24);border-radius:1px;min-height:2px}

/* Empty */
.empty-state{text-align:center;padding:80px 20px}
.empty-icon{font-size:64px;display:block;margin-bottom:16px}
.empty-state h3{font-size:18px;color:#475569;margin:0 0 8px}
.empty-state p{color:#94a3b8;margin:0}

/* Modal */
.modal-form{padding:8px 0}
.create-submit-btn{height:50px!important;font-size:16px!important;font-weight:700!important;border-radius:14px!important;background:linear-gradient(135deg,#f59e0b,#d97706)!important;border:none!important;margin-top:16px;box-shadow:0 4px 16px rgba(245,158,11,.2)}

/* Detail Panel */
.detail-panel{padding:8px 0}
.detail-info{display:flex;align-items:center;gap:12px;margin-bottom:24px}
.detail-meta{font-size:13px;color:#64748b}

.detail-chart h3,.detail-metrics h3,.ab-section h3{font-size:16px;color:#1e293b;margin:0 0 12px}
.full-chart{display:flex;align-items:flex-end;gap:1px;height:80px;background:#f8fafc;border-radius:12px;padding:12px;margin-bottom:8px}
.full-chart-bar{width:5px;background:linear-gradient(180deg,#f59e0b,#d97706);border-radius:2px;min-height:1px;flex-shrink:0}
.chart-axis{display:flex;justify-content:space-between;font-size:11px;color:#94a3b8}

.metrics-grid{display:flex;gap:12px;margin-bottom:28px}
.m-card{flex:1;text-align:center;padding:20px;background:#f8fafc;border-radius:14px}
.m-val{font-size:32px;font-weight:800}.m-val.blue{color:#3b82f6}.m-val.green{color:#22c55e}.m-val.amber{color:#f59e0b}
.m-lbl{font-size:12px;color:#94a3b8;margin-top:4px}

/* A/B section */
.ab-section{border-top:1px solid #e2e8f0;padding-top:24px;margin-top:8px}
.ab-desc{font-size:13px;color:#94a3b8;margin:0 0 12px}
.ab-input-row{display:flex;gap:10px;align-items:flex-start;margin-bottom:20px}
.ab-input-row .n-input{flex:1}
.ab-run-btn{flex-shrink:0;height:auto!important;min-height:42px;border-radius:12px!important;background:linear-gradient(135deg,#f59e0b,#d97706)!important;border:none!important;font-weight:700!important}

.ab-results{display:flex;flex-direction:column;gap:16px}
.ab-card{background:#f8fafc;border-radius:14px;padding:16px}
.ab-prompt-text{font-size:13px;font-weight:600;color:#475569;margin-bottom:12px}
.ab-compare{display:flex;gap:12px}
.ab-col{flex:1;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0}
.ab-col.winner{border-color:#f59e0b;box-shadow:0 0 0 1px rgba(245,158,11,.2)}
.ab-col-header{font-size:12px;font-weight:700;color:#64748b;padding:8px 12px;background:#f1f5f9;text-align:center}
.ab-col.winner .ab-col-header{background:#fffbeb;color:#b45309}
.ab-col-body{padding:12px;font-size:13px;color:#334155;line-height:1.6;white-space:pre-wrap;max-height:200px;overflow-y:auto}
.ab-verdict{margin-top:10px;text-align:center;font-size:13px;font-weight:700;padding:6px 12px;border-radius:8px}
.ab-verdict.finetuned{background:#ecfdf5;color:#059669}
.ab-verdict.base{background:#eff6ff;color:#2563eb}
.ab-verdict.tie{background:#f1f5f9;color:#64748b}
</style>
