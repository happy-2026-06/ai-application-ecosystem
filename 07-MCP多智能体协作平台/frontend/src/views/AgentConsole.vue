<template>
  <div class="ac-page">
    <div class="ac-hero">
      <div><h1>智能运营引擎</h1><p>多Agent编排 · 流水线/并行/投票/辩论 · 跨系统联动 · 实时监控</p></div>
      <n-button type="primary" size="large" @click="seedAgents(); loadData()">🔧 初始化Agent</n-button>
    </div>

    <!-- Stats -->
    <div class="stats-row" v-if="stats">
      <div class="st-card"><div class="st-v">{{stats.total_agents}}</div><div class="st-l">Agent总数</div></div>
      <div class="st-card"><div class="st-v online">{{stats.online_agents}}</div><div class="st-l">在线</div></div>
      <div class="st-card"><div class="st-v">{{stats.total_tasks}}</div><div class="st-l">任务总数</div></div>
      <div class="st-card"><div class="st-v success">{{stats.completed_tasks}}</div><div class="st-l">已完成</div></div>
    </div>

    <!-- Task Templates -->
    <div class="template-row">
      <span class="template-label">⚡ 快速任务：</span>
      <n-button v-for="tpl in templates" :key="tpl.title" size="small" secondary @click="useTemplate(tpl)">{{ tpl.icon }} {{ tpl.title }}</n-button>
    </div>

    <!-- Main two-column -->
    <div style="display:flex;gap:24px;margin-top:20px">
      <!-- Left: Agents -->
      <div style="flex:1;max-width:340px">
        <h2 style="margin:0 0 12px;font-size:17px;color:#1e293b">🤖 Agent集群</h2>
        <div class="agent-list" v-if="agents.length">
          <div v-for="a in agents" :key="a.id" class="agent-card" :class="a.status">
            <div class="ag-header">
              <span class="ag-icon">{{capIcon(a.capability)}}</span>
              <n-tag :type="a.status==='online'?'success':'default'" size="tiny">{{a.status==='online'?'在线':'离线'}}</n-tag>
            </div>
            <div class="ag-name">{{a.name}}</div>
            <div class="ag-role">{{a.role}}</div>
            <div class="ag-prompt-preview">{{ getAgentPromptPreview(a.name) }}</div>
          </div>
        </div>
        <div v-else class="empty" style="padding:20px">点击右上角"初始化Agent"按钮</div>
      </div>

      <!-- Right: Tasks -->
      <div style="flex:2">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <h2 style="margin:0;font-size:17px;color:#1e293b">📋 任务列表</h2>
          <n-button size="small" type="primary" @click="showCreate=true">+ 新建任务</n-button>
        </div>

        <!-- Live execution panel (shown during SSE streaming) -->
        <div v-if="liveRunning" class="live-panel">
          <div class="live-header">
            <div class="live-pulse"/>
            <span class="live-title">⚡ 实时执行中 — {{ liveModeLabel }}</span>
            <n-tag :type="liveTask.status==='running'?'info':'success'" size="small">{{ liveTask.status==='running' ? '执行中' : '已完成' }}</n-tag>
          </div>
          <div class="live-progress">
            <div class="live-bar"><div class="live-bar-fill" :style="{width:(liveDoneCount/Math.max(liveTotalCount,1)*100)+'%'}"/></div>
            <span class="live-count">{{liveDoneCount}}/{{liveTotalCount}}</span>
          </div>
          <div class="live-timeline">
            <div v-for="(step,i) in liveSteps" :key="i" class="live-step" :class="step.status">
              <div class="ls-header">
                <span class="ls-agent">{{ step.icon }} {{ step.name || ('Agent #'+(i+1)) }}</span>
                <span class="ls-dur" v-if="step.duration_ms">{{step.duration_ms}}ms</span>
                <n-tag :type="step.status==='completed'?'success':step.status==='running'?'info':step.status==='failed'?'error':'default'" size="tiny">{{step.statusText}}</n-tag>
              </div>
              <div class="ls-preview" v-if="step.preview">{{step.preview}}</div>
            </div>
          </div>
        </div>

        <!-- Filter bar -->
        <div class="filter-bar">
          <n-input v-model:value="taskFilter" placeholder="🔍 搜索任务..." size="small" clearable style="width:200px" @update:value="onFilterChange"/>
          <n-select v-model:value="filterMode" :options="[{label:'全部模式',value:''},{label:'🔗 流水线',value:'pipeline'},{label:'⚡ 并行',value:'parallel'},{label:'🗳️ 投票',value:'vote'},{label:'💬 辩论',value:'debate'}]" size="small" style="width:130px" @update:value="onFilterChange"/>
          <n-select v-model:value="filterStatus" :options="[{label:'全部状态',value:''},{label:'✅ 已完成',value:'completed'},{label:'⏳ 执行中',value:'running'}]" size="small" style="width:130px" @update:value="onFilterChange"/>
          <span class="filter-count">{{ filteredTasks.length }} 个任务</span>
        </div>

        <div class="task-list" v-if="filteredTasks.length">
          <div v-for="t in filteredTasks" :key="t.id" class="task-card" @click="selectTask(t)" :class="{selected:selTask?.id===t.id}">
            <div class="tk-delete" @click.stop="deleteTask(t)">
              <n-button text size="tiny" type="error" :loading="deletingId===t.id">🗑</n-button>
            </div>
            <div class="tk-header">
              <span class="tk-title">{{t.title}}</span>
              <n-tag :type="t.status==='completed'?'success':t.status==='running'?'info':'default'" size="tiny">{{statusLabel(t.status)}}</n-tag>
            </div>
            <div class="tk-meta">{{modeLabel(t.mode)}} · {{formatDate(t.created_at)}}</div>
            <div class="tk-tags" v-if="getSystemTags(t).length">
              <n-tag v-for="s in getSystemTags(t)" :key="s" size="tiny" :bordered="false" round>{{ s }}</n-tag>
            </div>
            <div class="tk-result" v-if="t.result">{{t.result.slice(0,150)}}...</div>
          </div>
        </div>
        <div v-else class="empty">{{ taskFilter || filterMode || filterStatus ? '没有匹配的任务' : '暂无任务，选择一个快速模板试试' }}</div>
      </div>
    </div>

    <!-- Task Detail Modal -->
    <n-modal v-model:show="showDetail" :title="selTask?.title || '任务详情'" preset="card" style="width:800px;max-width:95vw" :bordered="false">
      <div v-if="selTask" class="detail-panel">
        <div class="dp-info">
          <n-tag :type="selTask.status==='completed'?'success':selTask.status==='running'?'info':'default'">{{statusLabel(selTask.status)}}</n-tag>
          <span class="dp-mode">{{modeLabel(selTask.mode)}} · {{formatDate(selTask.created_at)}}</span>
        </div>
        <div class="dp-desc" v-if="selTask.description">{{selTask.description}}</div>

        <!-- Cross-system links -->
        <div class="dp-systems" v-if="getSystemTags(selTask).length">
          <span class="dp-sys-label">🌐 跨系统联动：</span>
          <n-tag v-for="s in getSystemTags(selTask)" :key="s" type="success" size="small" round>{{ s }}</n-tag>
        </div>

        <!-- Execution Timeline -->
        <div class="dp-timeline" v-if="executions.length">
          <h4>⏱ 执行时间线</h4>
          <div class="tl-item" v-for="(ex,i) in executions" :key="ex.id||i" :class="ex.status">
            <div class="tl-dot" :class="ex.status"/>
            <div class="tl-content">
              <div class="tl-step">Step {{ i+1 }} - {{ ex.agent_name || 'Agent #'+(i+1) }}</div>
              <div class="tl-status">
                <n-tag :type="ex.status==='completed'?'success':ex.status==='failed'?'error':'info'" size="tiny">{{ex.status}}</n-tag>
                <span v-if="ex.duration_ms" class="tl-duration">{{ex.duration_ms}}ms</span>
              </div>
              <div class="tl-output" v-if="ex.output_data">{{ex.output_data.slice(0,300)}}</div>
            </div>
          </div>
        </div>
        <div v-else class="dp-noexec">暂无执行记录，点击"刷新"获取最新状态</div>

        <div v-if="selTask.result" class="dp-result">
          <h4>📋 汇总结果</h4>
          <div class="dp-result-text">{{selTask.result}}</div>
        </div>

        <n-button size="small" @click="fetchExecutions" :loading="loadingExec" style="margin-top:12px">🔄 刷新执行记录</n-button>
      </div>
    </n-modal>

    <!-- Create Task Modal -->
    <n-modal v-model:show="showCreate" title="新建协作任务" preset="card" style="width:560px" :bordered="false">
      <div style="padding:8px">
        <n-form :model="tf" label-placement="top">
          <n-form-item label="任务标题"><n-input v-model:value="tf.title" placeholder="如：双11大促全链路策划"/></n-form-item>
          <n-form-item label="任务描述"><n-input v-model:value="tf.desc" type="textarea" placeholder="详细描述任务内容（关键词会自动匹配外部系统）" :autosize="{minRows:2,maxRows:4}"/></n-form-item>
          <n-form-item label="执行模式">
            <n-select v-model:value="tf.mode" :options="[
              {label:'🔗 流水线 (串行) — 每个Agent输出作为下一个输入',value:'pipeline'},
              {label:'⚡ 并行 — 所有Agent同时执行',value:'parallel'},
              {label:'🗳️ 投票 — 多Agent投票决定最优结果',value:'vote'},
              {label:'💬 辩论 — Agent轮流辩论后裁判总结',value:'debate'},
            ]"/>
          </n-form-item>
          <n-form-item label="选择Agent" v-if="agents.length">
            <n-checkbox-group v-model:value="tf.agentIds">
              <n-space>
                <n-checkbox v-for="a in agents.filter(a=>a.status==='online')" :key="a.id" :value="a.id">{{capIcon(a.capability)}} {{a.name}}</n-checkbox>
              </n-space>
            </n-checkbox-group>
            <span style="font-size:11px;color:#94a3b8;margin-top:4px">不选则自动使用全部在线Agent</span>
          </n-form-item>
        </n-form>
        <n-button type="primary" block @click="doCreateStream" :loading="creating" size="large" style="margin-top:12px">⚡ 创建并实时执行 (SSE)</n-button>
        <div style="text-align:center;margin-top:6px">
          <n-button text size="tiny" @click="doCreate" :loading="creatingSilent">普通创建（后台执行）</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const msg = useMessage()
const authStore = useAuthStore()
const stats = ref<any>(null); const agents = ref<any[]>([]); const tasks = ref<any[]>([])
const showCreate = ref(false); const creating = ref(false); const creatingSilent = ref(false)
const tf = ref({title:'',desc:'',mode:'pipeline',agentIds:[] as string[]})

// Task detail
const showDetail = ref(false); const selTask = ref<any>(null)
const executions = ref<any[]>([]); const loadingExec = ref(false)
const deletingId = ref<string|null>(null)

// Task filtering
const taskFilter = ref('')
const filterMode = ref('')
const filterStatus = ref('')
const filteredTasks = computed(() => {
  let list = tasks.value
  if (taskFilter.value) {
    const q = taskFilter.value.toLowerCase()
    list = list.filter((t:any) => (t.title||'').toLowerCase().includes(q) || (t.description||'').toLowerCase().includes(q))
  }
  if (filterMode.value) list = list.filter((t:any) => t.mode === filterMode.value)
  if (filterStatus.value) list = list.filter((t:any) => t.status === filterStatus.value)
  return list
})
function onFilterChange() { /* computed auto-updates */ }

// Live execution (SSE)
const liveRunning = ref(false)
const liveSteps = ref<any[]>([])
const liveTask = ref<any>({status:'running'})
const liveDoneCount = ref(0)
const liveTotalCount = ref(0)
const liveModeLabel = ref('')

const templates = [
  {icon:'📱',title:'生成小红书种草文案',desc:'为产品写小红书爆款种草文案，适配小红书平台风格，含标题+正文+标签',mode:'pipeline'},
  {icon:'🎬',title:'策划短视频脚本',desc:'生成带货短视频分镜脚本，含开场钩子+产品展示+价格锚点+行动号召',mode:'pipeline'},
  {icon:'📊',title:'双11大促全链路策划',desc:'分析市场趋势→制定促销策略→创作营销内容→规划投放排期',mode:'pipeline'},
  {icon:'🔄',title:'多平台内容分发',desc:'同一产品信息适配小红书+抖音+公众号三种风格，多Agent并行创作',mode:'parallel'},
  {icon:'🎯',title:'竞品分析+应对策略',desc:'分析竞品优劣势→提炼我方差异化卖点→生成反击营销文案',mode:'pipeline'},
]

const capIcon=(c:string)=>({analysis:'📊',content:'✍️',decision:'🧠',execution:'⚡',general:'🔍'})[c]||'🤖'
const statusLabel=(s:string)=>({pending:'排队中',running:'执行中',completed:'已完成',failed:'失败'})[s]||s
const modeLabel=(m:string)=>({pipeline:'🔗 流水线',parallel:'⚡ 并行',vote:'🗳️ 投票',debate:'💬 辩论'})[m]||m
const formatDate=(d:string)=>{const dt=new Date(d);return `${dt.getMonth()+1}/${dt.getDate()} ${dt.getHours()}:${String(dt.getMinutes()).padStart(2,'0')}`}

// Agent prompt previews (shows each agent's specialty)
function getAgentPromptPreview(name:string):string{
  const previews:Record<string,string> = {
    '市场分析Agent':'擅长SWOT分析、竞品情报、用户画像',
    '内容创作Agent':'擅长爆款标题、种草文案、多平台适配',
    '数据决策Agent':'擅长ROI测算、风险评估、优先级排序',
    '执行调度Agent':'擅长SOP拆解、时间线规划、资源配置',
    '质量审查Agent':'擅长合规检查、事实校验、质量评分',
  }
  return previews[name] || ''
}

function getSystemTags(t:any):string[]{
  const text = `${t.title||''} ${t.description||''} ${t.result||''}`.toLowerCase()
  const tags:string[] = []
  if(text.includes('小红书')||text.includes('文案')||text.includes('种草')||text.includes('内容')||text.includes('生成')) tags.push('②灵笔引擎')
  if(text.includes('视频')||text.includes('脚本')||text.includes('分镜')||text.includes('短视频')) tags.push('③视界工坊')
  if(text.includes('图库')||text.includes('素材')||text.includes('图片')) tags.push('④图库管家')
  if(text.includes('客服')||text.includes('FAQ')||text.includes('知识库')||text.includes('咨询')) tags.push('①智能客服')
  if(text.includes('训练')||text.includes('话术')||text.includes('培训')) tags.push('⑤话术教练')
  if(text.includes('数据')||text.includes('数据集')||text.includes('查询')) tags.push('⑥数据中枢')
  return [...new Set(tags)].slice(0,3)
}

async function seedAgents(){try{await apiClient.post('/agent/agents/seed')}catch{}}
async function loadData(){
  try{const[ar,tr]=await Promise.all([apiClient.get('/agent/agents'),apiClient.get('/agent/tasks')]);agents.value=ar.data;tasks.value=tr.data.slice(0,20);stats.value={total_agents:ar.data.length,online_agents:ar.data.filter((a:any)=>a.status==='online').length,total_tasks:tr.data.length,completed_tasks:tr.data.filter((t:any)=>t.status==='completed').length}}catch{}
}

function useTemplate(tpl:any){tf.value={title:tpl.title,desc:tpl.desc,mode:tpl.mode,agentIds:[]};showCreate.value=true}

// ── SSE Streaming Execution ─────────────────────────────────────
async function doCreateStream(){
  if(!tf.value.title.trim()){msg.warning('请输入任务标题');return}
  creating.value=true
  liveRunning.value=true
  liveSteps.value=[]
  liveDoneCount.value=0
  liveTotalCount.value=0
  liveTask.value={status:'running'}

  const token = authStore.token
  try{
    const resp = await fetch('/api/agent/tasks/stream', {
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
      body: JSON.stringify({title:tf.value.title,description:tf.value.desc,mode:tf.value.mode,agent_ids:tf.value.agentIds}),
    })

    if(!resp.ok){msg.error('创建失败');liveRunning.value=false;creating.value=false;return}

    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while(true){
      const {done,value} = await reader.read()
      if(done) break
      buffer += decoder.decode(value,{stream:true})
      const lines = buffer.split('\n')
      buffer = lines.pop()||''

      for(const line of lines){
        if(!line.startsWith('data: ')) continue
        try{
          const event = JSON.parse(line.slice(6))
          handleSSEEvent(event)
        }catch{}
      }
    }
  }catch(e:any){msg.error('连接中断: '+e.message)}
  finally{
    creating.value=false
    setTimeout(()=>{loadData();liveRunning.value=false},500)
  }
}

function handleSSEEvent(e:any){
  switch(e.type){
    case 'task_created':
      liveTask.value = {id:e.task_id,title:e.title,status:'running'}
      liveTotalCount.value = e.agent_count
      liveModeLabel.value = modeLabel(e.mode)
      liveSteps.value = []
      break
    case 'agent_start':
      liveSteps.value.push({name:e.agent_name,status:'running',statusText:'执行中...',icon:capIcon(e.agent_name),preview:''})
      break
    case 'agent_done':
      const done = liveSteps.value.find(s=>s.name===e.agent_name && s.status==='running')
      if(done){done.status='completed';done.statusText='✅ 完成';done.duration_ms=e.duration_ms;done.preview=e.output_preview}
      else liveSteps.value.push({name:e.agent_name,status:'completed',statusText:'✅ 完成',duration_ms:e.duration_ms,preview:e.output_preview,icon:capIcon(e.agent_name)})
      liveDoneCount.value++
      break
    case 'agent_error':
      const err = liveSteps.value.find(s=>s.name===e.agent_name && s.status==='running')
      if(err){err.status='failed';err.statusText='❌ 失败'}
      else liveSteps.value.push({name:e.agent_name,status:'failed',statusText:'❌ 失败',icon:capIcon(e.agent_name)})
      liveDoneCount.value++
      break
    case 'parallel_start':
    case 'vote_start':
      liveTotalCount.value = e.agent_count
      break
    case 'debate_round':
      liveSteps.value.push({name:`${e.agent_name || ''}`,status:'running',statusText:e.round+' | '+e.role,icon:'💬',preview:''})
      break
    case 'debate_speech':
      const ds = liveSteps.value.find(s=>s.status==='running' && s.name && e.agent_name && s.name.includes(e.agent_name))
      if(ds){ds.status='completed';ds.statusText='💬 发言完毕';ds.duration_ms=e.duration_ms;ds.preview=e.output_preview}
      liveDoneCount.value++
      break
    case 'debate_verdict':
      liveSteps.value.push({name:'⚖️ 裁判: '+e.agent_name,status:'completed',statusText:'📋 裁定',duration_ms:0,preview:e.output_preview,icon:'⚖️'})
      break
    case 'tallying':
      liveSteps.value.push({name:'📊 计票',status:'running',statusText:'统计中...',icon:'📊',preview:''})
      break
    case 'task_completed':
      liveTask.value.status='completed'
      if(e.result_preview) liveSteps.value.push({name:'📋 汇总结果',status:'completed',statusText:'✅',preview:e.result_preview,icon:'📋'})
      msg.success('任务执行完成！')
      showCreate.value=false
      break
  }
}

// ── Silent create (no streaming) ───────────────────────────────
async function doCreate(){
  creatingSilent.value=true;tf.value.agentIds=[]
  try{
    await apiClient.post('/agent/tasks',{title:tf.value.title,description:tf.value.desc,mode:tf.value.mode})
    showCreate.value=false;msg.success('任务已创建，正在执行...');loadData()
  }catch{msg.error('创建失败')}
  finally{creatingSilent.value=false}
}

async function selectTask(t:any){selTask.value=t;showDetail.value=true;fetchExecutions()}

async function deleteTask(t:any){
  deletingId.value=t.id
  try{await apiClient.delete('/agent/tasks/'+t.id);msg.success('任务已删除');loadData();if(selTask.value?.id===t.id){showDetail.value=false;selTask.value=null}}
  catch{msg.error('删除失败')}
  finally{deletingId.value=null}
}

async function fetchExecutions(){
  if(!selTask.value) return
  loadingExec.value=true
  try{
    const r=await apiClient.get('/agent/tasks/'+selTask.value.id+'/executions')
    // Attach agent names from agents list
    executions.value=r.data.map((ex:any)=>{
      const ag = agents.value.find((a:any)=>a.id===ex.agent_id)
      return {...ex,agent_name:ag?.name||ex.agent_name||'Agent'}
    })
  }catch{executions.value=[]}
  finally{loadingExec.value=false}
}

onMounted(loadData)
</script>

<style scoped>
.ac-page{padding:32px;max-width:1300px;margin:0 auto}
.ac-hero{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.ac-hero h1{font-size:26px;font-weight:800;color:#4c1d95;margin:0 0 4px}
.ac-hero p{color:#64748b;font-size:14px;margin:0}
.stats-row{display:flex;gap:16px}
.st-card{flex:1;background:#fff;padding:20px;border-radius:16px;border:1px solid #e2e8f0;text-align:center}
.st-v{font-size:32px;font-weight:800;color:#7c3aed}.st-v.online{color:#22c55e}.st-v.success{color:#7c3aed}
.st-l{font-size:12px;color:#94a3b8;margin-top:4px}

/* Templates */
.template-row{display:flex;align-items:center;gap:8px;margin-top:20px;padding:14px 18px;background:#f8fafc;border-radius:12px;flex-wrap:wrap}
.template-label{font-size:13px;font-weight:600;color:#64748b;white-space:nowrap}

/* Agents */
.agent-list{display:flex;flex-direction:column;gap:8px}
.agent-card{padding:14px 16px;background:#fff;border-radius:14px;border:1px solid #e2e8f0;transition:all .15s}
.agent-card:hover{border-color:#c4b5fd;transform:translateY(-1px)}
.ag-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.ag-icon{font-size:22px}.ag-name{font-size:14px;font-weight:700;color:#1e293b}.ag-role{font-size:12px;color:#94a3b8;margin-top:2px}
.ag-prompt-preview{font-size:11px;color:#a78bfa;margin-top:6px;padding-top:6px;border-top:1px solid #f1f5f9;line-height:1.4}

/* Filter bar */
.filter-bar{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.filter-count{font-size:12px;color:#94a3b8;white-space:nowrap}

/* Tasks */
.task-list{display:flex;flex-direction:column;gap:8px}
.task-card{position:relative;padding:14px 16px;background:#faf9ff;border-radius:14px;border:1px solid #e8e5f5;cursor:pointer;transition:all .15s}
.task-card:hover{border-color:#c4b5fd;background:#f3f0ff;transform:translateY(-1px)}
.task-card.selected{border-color:#7c3aed;background:#f3f0ff;box-shadow:0 2px 12px rgba(124,58,237,.08)}
.tk-delete{position:absolute;top:8px;right:8px;opacity:0;transition:opacity .15s}
.task-card:hover .tk-delete{opacity:1}
.tk-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;padding-right:24px}
.tk-title{font-size:14px;font-weight:700;color:#3b2d5c}.tk-meta{font-size:12px;color:#8b7daa}
.tk-tags{margin-top:6px;display:flex;gap:4px;flex-wrap:wrap}
.tk-result{font-size:12px;color:#6b5b8a;margin-top:6px;line-height:1.5}

/* Live Execution Panel */
.live-panel{padding:16px;background:linear-gradient(135deg,#faf5ff,#f5f3ff);border:2px solid #c4b5fd;border-radius:16px;margin-bottom:16px;animation:liveGlow 3s ease-in-out infinite}
.live-header{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.live-pulse{width:10px;height:10px;background:#7c3aed;border-radius:50%;animation:pulse 1.2s ease-in-out infinite}
.live-title{font-size:14px;font-weight:700;color:#4c1d95}
.live-progress{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.live-bar{flex:1;height:6px;background:#e9d5ff;border-radius:3px;overflow:hidden}
.live-bar-fill{height:100%;background:linear-gradient(90deg,#7c3aed,#a78bfa);border-radius:3px;transition:width .5s ease}
.live-count{font-size:12px;color:#7c3aed;font-weight:700;white-space:nowrap}
.live-timeline{display:flex;flex-direction:column;gap:6px;max-height:300px;overflow-y:auto}
.live-step{padding:8px 12px;background:rgba(255,255,255,.7);border-radius:10px;border-left:3px solid #e2e8f0}
.live-step.running{border-left-color:#7c3aed;background:rgba(124,58,237,.05)}
.live-step.completed{border-left-color:#22c55e}
.live-step.failed{border-left-color:#ef4444}
.ls-header{display:flex;align-items:center;gap:6px}
.ls-agent{font-size:13px;font-weight:600;color:#334155}
.ls-dur{font-size:11px;color:#94a3b8;margin-left:auto}
.ls-preview{font-size:11px;color:#64748b;margin-top:4px;line-height:1.4;white-space:pre-wrap;max-height:60px;overflow:hidden}

@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.3)}}
@keyframes liveGlow{0%,100%{box-shadow:0 0 20px rgba(124,58,237,.08)}50%{box-shadow:0 0 30px rgba(124,58,237,.18)}}

/* Detail panel */
.detail-panel{padding:8px 0}
.dp-info{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.dp-mode{font-size:13px;color:#64748b}
.dp-desc{font-size:14px;color:#475569;padding:12px 16px;background:#f8fafc;border-radius:10px;margin-bottom:12px}
.dp-systems{margin-bottom:14px;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.dp-sys-label{font-size:12px;color:#64748b;font-weight:600}
.dp-timeline h4,.dp-result h4{font-size:14px;color:#1e293b;margin:0 0 10px}
.tl-item{display:flex;gap:12px;padding:10px 0;border-left:2px solid #e2e8f0;margin-left:8px;padding-left:20px}
.tl-item.completed{border-left-color:#22c55e}.tl-item.failed{border-left-color:#ef4444}
.tl-dot{width:10px;height:10px;border-radius:50%;background:#e2e8f0;margin-left:-27px;margin-top:6px;flex-shrink:0}
.tl-dot.completed{background:#22c55e}.tl-dot.failed{background:#ef4444}
.tl-content{flex:1}
.tl-step{font-size:13px;font-weight:600;color:#334155}
.tl-status{display:flex;align-items:center;gap:8px;margin:4px 0}
.tl-duration{font-size:11px;color:#94a3b8}
.tl-output{font-size:12px;color:#64748b;padding:8px 12px;background:#f8fafc;border-radius:8px;margin-top:6px;line-height:1.5;white-space:pre-wrap;max-height:150px;overflow-y:auto}
.dp-result-text{font-size:13px;color:#334155;padding:14px 16px;background:#f8fafc;border-radius:10px;white-space:pre-wrap;line-height:1.6;max-height:300px;overflow-y:auto}
.dp-noexec{text-align:center;color:#94a3b8;padding:20px;font-size:13px}
.empty{text-align:center;padding:40px;color:#94a3b8}

[data-theme="dark"] .ac-hero h1{color:#ede9fe}
[data-theme="dark"] .st-card{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .template-row{background:#1e1e28}
[data-theme="dark"] .agent-card,.dp-desc,.tl-output,.dp-result-text,.live-step{background:#1e1e28;border-color:#2d2d3d}
[data-theme="dark"] .task-card{background:#1e1c28;border-color:#2d2b3a}
[data-theme="dark"] .task-card:hover{background:#242030;border-color:#7c3aed}
[data-theme="dark"] .task-card.selected{background:#242030;border-color:#7c3aed;box-shadow:0 2px 16px rgba(124,58,237,.12)}
[data-theme="dark"] .tk-title{color:#d4c8f0}
[data-theme="dark"] .tk-meta{color:#7b6f9a}
[data-theme="dark"] .tk-result{color:#8b7faa}
[data-theme="dark"] .tl-step{color:#e2e8f0}
[data-theme="dark"] .tl-item{border-left-color:#2d2d3d}
[data-theme="dark"] .ls-agent{color:#e2e8f0}
[data-theme="dark"] .live-panel{background:linear-gradient(135deg,#1a1525,#1e1830);border-color:#4c1d95}
[data-theme="dark"] .ag-prompt-preview{border-top-color:#2d2d3d;color:#8b5cf6}
[data-theme="dark"] .filter-bar .filter-count{color:#7b6f9a}
</style>
