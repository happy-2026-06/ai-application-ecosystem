<template>
  <div class="lab-page">
    <header class="lab-header">
      <h2>🧠 AI 模型微调训练平台</h2>
      <n-button type="primary">⚙️ 创建微调任务</n-button>
    </header>

    <div class="lab-body">
      <main class="task-list">
        <div v-for="task in tasks" :key="task.id" class="task-card" :class="{ selected: selectedId === task.id }" @click="selectTask(task)">
          <div class="tc-header">
            <div>
              <strong>{{ task.name }}</strong>
              <n-tag :type="task.status === 'completed' ? 'success' : task.status === 'training' ? 'warning' : 'info'" size="tiny" :bordered="false">{{ task.status === 'completed' ? '✅ 完成' : task.status === 'training' ? '🔄 训练中' : '⏳ 排队中' }}</n-tag>
            </div>
            <span class="tc-method">{{ task.method.toUpperCase() }}</span>
          </div>
          <div class="tc-meta">
            基础模型: {{ task.base_model }} · 数据集: {{ task.dataset_name }}
          </div>
          <div v-if="task.status === 'training'" class="tc-progress">
            <div class="tcp-info">Epoch {{ task.current_epoch }}/{{ task.total_epochs }} · Loss: {{ task.current_loss }}</div>
            <n-progress type="line" :percentage="task.progress" color="#667eea" :height="6" :border-radius="3" />
          </div>
          <div v-if="task.status === 'completed'" class="tc-stats">
            <span>BLEU: {{ task.bleu }}</span>
            <span>训练时长: {{ task.duration }}</span>
          </div>
          <div class="tc-actions">
            <n-button v-if="task.status === 'training'" text size="tiny" type="warning">⏸ 暂停</n-button>
            <n-button v-if="task.status === 'completed'" text size="tiny" type="success">🚀 部署API</n-button>
            <n-button text size="tiny" type="info">📊 A/B对比</n-button>
          </div>
        </div>
      </main>

      <aside class="detail-panel" v-if="selectedTask">
        <h3>📊 {{ selectedTask.name }}</h3>

        <div class="detail-section">
          <h4>📈 训练曲线</h4>
          <div class="loss-chart-placeholder">
            <div class="chart-bars">
              <div v-for="(loss, i) in selectedTask.loss_history || []" :key="i" class="chart-bar" :style="{ height: (100 - loss*100) + '%' }" />
            </div>
            <div class="chart-label">Epoch →</div>
          </div>
        </div>

        <div class="detail-section">
          <h4>⚙️ 超参数</h4>
          <div class="hp-grid">
            <div class="hp-item"><span>学习率</span><strong>{{ selectedTask.hp?.lr }}</strong></div>
            <div class="hp-item"><span>Epochs</span><strong>{{ selectedTask.hp?.epochs }}</strong></div>
            <div class="hp-item"><span>Batch Size</span><strong>{{ selectedTask.hp?.batch_size }}</strong></div>
            <div class="hp-item"><span>LoRA Rank</span><strong>{{ selectedTask.hp?.lora_r }}</strong></div>
          </div>
        </div>

        <div class="detail-section" v-if="selectedTask.status === 'completed'">
          <h4>📋 评估指标</h4>
          <div class="eval-bars">
            <div class="eb-row"><span>BLEU</span><span class="eb-value green">{{ selectedTask.bleu }}</span></div>
            <div class="eb-row"><span>ROUGE-L</span><span class="eb-value blue">{{ selectedTask.rouge }}</span></div>
            <div class="eb-row"><span>人工评分</span><span class="eb-value purple">{{ selectedTask.human_score }}</span></div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const selectedId = ref('')

const tasks = ref([
  {
    id: '1', name: '客服对话模型 v2', base_model: 'Llama-3-8B', method: 'qlora', dataset_name: '客服对话 v3',
    status: 'completed', current_epoch: 5, total_epochs: 5, current_loss: '0.12', progress: 100,
    duration: '2h 34m', bleu: 0.87, rouge: 0.82, human_score: 4.5,
    hp: { lr: '2e-4', epochs: 5, batch_size: 8, lora_r: 64 },
    loss_history: [0.82, 0.61, 0.45, 0.28, 0.18, 0.15, 0.13, 0.12],
  },
  {
    id: '2', name: '商品推荐模型 v1', base_model: 'Qwen2.5-7B', method: 'qlora', dataset_name: '商品评论 v2',
    status: 'training', current_epoch: 3, total_epochs: 5, current_loss: '0.34', progress: 45,
    duration: '进行中…', bleu: '-', rouge: '-', human_score: '-',
    hp: { lr: '2e-4', epochs: 5, batch_size: 4, lora_r: 32 },
    loss_history: [0.91, 0.72, 0.54, 0.34],
  },
])

function selectTask(t: any) { selectedId.value = t.id; selectedTask.value = t }
const selectedTask = ref<any>(tasks.value[0])
selectTask(tasks.value[0])
</script>

<style scoped>
.lab-page { display: flex; flex-direction: column; height: 100%; background: #fff; }
.lab-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.lab-header h2 { margin: 0; font-size: 18px; }

.lab-body { flex: 1; display: flex; min-height: 0; }
.task-list { flex: 1; padding: 16px 24px; overflow-y: auto; border-right: 1px solid #f0f0f0; }
.task-card { padding: 16px; margin-bottom: 12px; background: #fafbfd; border-radius: 12px; border: 2px solid transparent; cursor: pointer; transition: all .15s; }
.task-card:hover { border-color: #e0e3ee; }
.task-card.selected { border-color: #667eea; background: #f0f2fb; }
.tc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.tc-method { font-size: 11px; padding: 2px 6px; background: #eef0f8; border-radius: 4px; color: #667eea; font-weight: 600; }
.tc-meta { font-size: 12px; color: #999; margin-bottom: 8px; }
.tc-progress { margin: 8px 0; }
.tcp-info { font-size: 12px; color: #666; margin-bottom: 4px; }
.tc-stats { display: flex; gap: 16px; font-size: 13px; color: #555; margin: 4px 0; }
.tc-actions { display: flex; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0f0f0; }

.detail-panel { width: 360px; min-width: 360px; padding: 16px; overflow-y: auto; background: #fafbfd; }
.detail-panel h3 { margin: 0 0 16px; font-size: 16px; }
.detail-section { margin-bottom: 20px; }
.detail-section h4 { margin: 0 0 8px; font-size: 13px; color: #888; }

.loss-chart-placeholder { height: 120px; background: linear-gradient(to bottom, #667eea05, #667eea15); border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; padding: 8px; }
.chart-bars { display: flex; align-items: flex-end; gap: 4px; height: 80px; width: 100%; }
.chart-bar { flex: 1; background: linear-gradient(to top, #667eea, #7c3aed); border-radius: 2px 2px 0 0; min-height: 4px; }
.chart-label { font-size: 10px; color: #999; margin-top: 4px; }

.hp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.hp-item { padding: 8px 12px; background: #fff; border-radius: 8px; }
.hp-item span { display: block; font-size: 11px; color: #999; }
.hp-item strong { font-size: 14px; color: #333; }

.eval-bars { display: flex; flex-direction: column; gap: 8px; }
.eb-row { display: flex; justify-content: space-between; font-size: 13px; padding: 8px 12px; background: #fff; border-radius: 8px; }
.eb-value { font-weight: 700; }
.eb-value.green { color: #10b981; }
.eb-value.blue { color: #667eea; }
.eb-value.purple { color: #8b5cf6; }

[data-theme="dark"] .lab-page { background: #101014; }
[data-theme="dark"] .lab-header { border-bottom-color: #222; }
[data-theme="dark"] .task-card { background: #1a1a24; }
[data-theme="dark"] .task-card:hover { border-color: #333; }
[data-theme="dark"] .task-card.selected { border-color: #667eea; background: #1e1e30; }
[data-theme="dark"] .tc-actions { border-top-color: #2a2a38; }
[data-theme="dark"] .task-list { border-right-color: #222; }
[data-theme="dark"] .detail-panel { background: #14141a; }
[data-theme="dark"] .hp-item { background: #1a1a24; }
[data-theme="dark"] .hp-item strong { color: #ddd; }
[data-theme="dark"] .eb-row { background: #1a1a24; }
[data-theme="dark"] .tc-method { background: #222; }
</style>
