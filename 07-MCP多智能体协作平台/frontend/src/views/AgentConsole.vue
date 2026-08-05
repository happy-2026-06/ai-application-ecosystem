<template>
  <div class="agent-page">
    <!-- 顶部: Agent注册中心 -->
    <header class="agent-header">
      <h2>🤝 MCP 多智能体协作平台</h2>
      <n-button type="primary" @click="showRegister = true">🤖 注册Agent</n-button>
    </header>

    <!-- Agent 卡片区 -->
    <section class="agent-cards">
      <div v-for="agent in agents" :key="agent.id" class="agent-card" :class="{ offline: agent.status === 'offline' }">
        <div class="ac-top">
          <span class="ac-icon">{{ agent.icon }}</span>
          <span class="ac-status" :class="agent.status">{{ statusLabel(agent.status) }}</span>
        </div>
        <div class="ac-name">{{ agent.name }}</div>
        <div class="ac-type">{{ agent.agent_type }}</div>
        <div class="ac-version">{{ agent.version }}</div>
        <div class="ac-capabilities">
          <n-tag v-for="c in agent.capabilities" :key="c" size="tiny" :bordered="false">{{ c }}</n-tag>
        </div>
        <div class="ac-health">最后心跳: {{ agent.health_check_at ? formatTime(agent.health_check_at) : '未知' }}</div>
      </div>
    </section>

    <div class="agent-body">
      <!-- 任务编排 -->
      <main class="pipeline-panel">
        <div class="pp-header">
          <h3>📋 任务编排</h3>
          <n-button size="small" @click="showNewTask = true">+ 创建任务</n-button>
        </div>

        <div v-if="pipelines.length === 0" class="pp-empty">
          <div class="empty-icon">🔗</div>
          <p>还没有任务编排</p>
          <p class="sub">点击"创建任务"开始编排Agent协作流程</p>
        </div>

        <div v-for="pipe in pipelines" :key="pipe.id" class="pipeline-card" @click="selectPipeline(pipe)">
          <div class="pc-header">
            <strong>{{ pipe.name }}</strong>
            <n-tag :type="pipe.pipeline_type === 'sequential' ? 'info' : pipe.pipeline_type === 'parallel' ? 'success' : 'warning'" size="tiny" :bordered="false">
              {{ pipe.pipeline_type === 'sequential' ? '串行' : pipe.pipeline_type === 'parallel' ? '并行' : '投票' }}
            </n-tag>
          </div>
          <div class="pc-chain">
            <span v-for="(step, i) in pipe.agent_chain" :key="i">
              <span v-if="i > 0" class="pc-arrow">{{ pipe.pipeline_type === 'parallel' ? '⇌' : '→' }}</span>
              <span class="pc-step">{{ step.agent_name }}</span>
            </span>
          </div>
          <div class="pc-desc">{{ pipe.description }}</div>
        </div>
      </main>

      <!-- 执行日志 -->
      <aside class="log-panel">
        <h3>📝 执行日志</h3>
        <div v-if="executions.length === 0" class="log-empty">选择任务查看执行记录</div>
        <div v-for="exec in executions" :key="exec.id" class="log-item" :class="exec.status">
          <div class="li-header">
            <span class="li-status">{{ exec.status === 'completed' ? '✅' : exec.status === 'running' ? '🔄' : '❌' }}</span>
            <span class="li-name">{{ exec.pipeline_name }}</span>
          </div>
          <div class="li-meta">耗时 {{ exec.duration_ms }}ms · Token {{ exec.total_tokens }}</div>
          <div class="li-steps">
            <div v-for="(step, si) in (exec.logs || [])" :key="si" class="li-step">
              {{ step.agent_name }}: {{ step.duration_ms }}ms
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const showRegister = ref(false)
const showNewTask = ref(false)

const agents = ref([
  { id: '1', name: '数据分析Agent', icon: '📊', agent_type: 'data-analysis', version: 'v1.2.0', status: 'running', capabilities: ['市场分析', '趋势预测', '竞品对比'], health_check_at: new Date().toISOString() },
  { id: '2', name: '内容创作Agent', icon: '✍️', agent_type: 'content-creation', version: 'v2.0.1', status: 'running', capabilities: ['文案撰写', '脚本创作', '标题生成'], health_check_at: new Date().toISOString() },
  { id: '3', name: '发布管理Agent', icon: '🚀', agent_type: 'publish', version: 'v1.0.0', status: 'idle', capabilities: ['多平台发布', '排期管理'], health_check_at: new Date(Date.now() - 3600000).toISOString() },
  { id: '4', name: '质量审查Agent', icon: '🔍', agent_type: 'review', version: 'v1.5.0', status: 'running', capabilities: ['内容审核', '事实核查', '质量评分'], health_check_at: new Date().toISOString() },
  { id: '5', name: '创意生成Agent', icon: '💡', agent_type: 'creative', version: 'v0.9.0', status: 'offline', capabilities: ['创意构思', '头脑风暴'], health_check_at: new Date(Date.now() - 86400000).toISOString() },
])

const pipelines = ref([
  { id: '1', name: '竞品分析 + 营销方案', pipeline_type: 'sequential', description: '分析竞品市场→创作营销内容→审核→发布', agent_chain: [{ agent_name: '数据分析Agent' }, { agent_name: '内容创作Agent' }, { agent_name: '质量审查Agent' }, { agent_name: '发布管理Agent' }] },
  { id: '2', name: '多角度内容创作', pipeline_type: 'parallel', description: '三个Agent同时创作不同风格→择优选用', agent_chain: [{ agent_name: '内容创作Agent' }, { agent_name: '创意生成Agent' }, { agent_name: '数据分析Agent' }] },
])

const executions = ref([
  { id: '1', pipeline_name: '竞品分析 + 营销方案', status: 'completed', duration_ms: 4200, total_tokens: 12340, logs: [{ agent_name: '数据分析Agent', duration_ms: 2300 }, { agent_name: '内容创作Agent', duration_ms: 1200 }, { agent_name: '质量审查Agent', duration_ms: 400 }, { agent_name: '发布管理Agent', duration_ms: 300 }] },
])

function statusLabel(s: string): string {
  const m: Record<string, string> = { running: '🟢 运行中', idle: '🟡 空闲', offline: '🔴 离线' }
  return m[s] || s
}
function formatTime(t: string): string {
  return new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
function selectPipeline(p: any) {
  executions.value = executions.value.filter(e => e.pipeline_name === p.name || e.pipeline_name.includes(p.name.slice(0, 3)))
}
</script>

<style scoped>
.agent-page { display: flex; flex-direction: column; height: 100%; background: #fff; }

.agent-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.agent-header h2 { margin: 0; font-size: 18px; }

.agent-cards { display: flex; gap: 12px; padding: 16px 24px; overflow-x: auto; flex-shrink: 0; border-bottom: 1px solid #f0f0f0; }
.agent-card { min-width: 170px; padding: 14px; background: #fafbfd; border-radius: 12px; border: 2px solid transparent; transition: all .15s; }
.agent-card:hover { border-color: #e0e3ee; }
.agent-card.offline { opacity: .5; }
.ac-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ac-icon { font-size: 28px; }
.ac-status { font-size: 11px; }
.ac-status.running { color: #10b981; }
.ac-status.idle { color: #f59e0b; }
.ac-status.offline { color: #ef4444; }
.ac-name { font-size: 14px; font-weight: 600; color: #333; }
.ac-type { font-size: 11px; color: #999; margin: 2px 0; }
.ac-version { font-size: 10px; color: #667eea; margin-bottom: 6px; }
.ac-capabilities { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 6px; }
.ac-health { font-size: 10px; color: #ccc; }

.agent-body { flex: 1; display: flex; min-height: 0; }
.pipeline-panel { flex: 1; padding: 16px 24px; overflow-y: auto; border-right: 1px solid #f0f0f0; }
.pp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.pp-header h3 { margin: 0; font-size: 16px; }
.pp-empty { text-align: center; padding: 60px 20px; color: #999; }
.empty-icon { font-size: 40px; margin-bottom: 8px; }
.sub { font-size: 12px; color: #ccc; }

.pipeline-card { padding: 14px 16px; margin-bottom: 8px; background: #fafbfd; border-radius: 10px; border: 2px solid transparent; cursor: pointer; transition: all .15s; }
.pipeline-card:hover { border-color: #e0e3ee; }
.pc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.pc-chain { font-size: 13px; color: #555; margin-bottom: 4px; }
.pc-arrow { margin: 0 4px; color: #667eea; }
.pc-step { background: #eef0f8; padding: 2px 8px; border-radius: 4px; }
.pc-desc { font-size: 12px; color: #999; }

.log-panel { width: 300px; min-width: 300px; padding: 16px; overflow-y: auto; background: #fafbfd; }
.log-panel h3 { margin: 0 0 12px; font-size: 16px; }
.log-empty { text-align: center; padding: 40px 10px; color: #ccc; font-size: 13px; }
.log-item { padding: 10px; margin-bottom: 6px; background: #fff; border-radius: 8px; border-left: 3px solid #10b981; }
.log-item.running { border-left-color: #f59e0b; }
.log-item.failed { border-left-color: #ef4444; }
.li-header { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
.li-meta { font-size: 11px; color: #999; margin: 2px 0 6px; }
.li-steps { font-size: 11px; color: #666; }
.li-step { padding: 2px 0; }

[data-theme="dark"] .agent-page { background: #101014; }
[data-theme="dark"] .agent-header, [data-theme="dark"] .agent-cards { border-bottom-color: #222; }
[data-theme="dark"] .agent-card { background: #1a1a24; }
[data-theme="dark"] .ac-name { color: #ddd; }
[data-theme="dark"] .pipeline-card { background: #1a1a24; }
[data-theme="dark"] .pipeline-card:hover { border-color: #333; }
[data-theme="dark"] .pc-step { background: #222; }
[data-theme="dark"] .pipeline-panel { border-right-color: #222; }
[data-theme="dark"] .log-panel { background: #14141a; }
[data-theme="dark"] .log-item { background: #1a1a24; }
</style>
