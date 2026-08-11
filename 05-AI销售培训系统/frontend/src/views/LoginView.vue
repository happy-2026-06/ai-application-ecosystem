<template>
  <div class="login-page">
    <!-- Gradients background -->
    <div class="bg-layer">
      <div class="bg-orb orb-1" />
      <div class="bg-orb orb-2" />
      <div class="bg-orb orb-3" />
    </div>

    <!-- Pattern dots -->
    <div class="bg-dots">
      <span v-for="i in 40" :key="i" class="dot" :style="{
        left: `${(i * 19 + 7) % 100}%`,
        top: `${(i * 31 + 13) % 100}%`,
        opacity: 0.03 + ((i % 3) * 0.02),
      }" />
    </div>

    <div class="login-container">
      <!-- Left: Brand -->
      <div class="login-brand">
        <div class="brand-badge">AI 话术教练</div>
        <h1>练就金牌<br/>销售话术</h1>
        <p>选择客户类型 · AI角色扮演 · 实时多维度评分 · 教练个性化指导</p>

        <div class="brand-features">
          <div class="bf-item">
            <div class="bf-icon-wrap blue"><span>🎭</span></div>
            <div><strong>4种客户类型</strong><p>挑剔型/价格型/犹豫型/专业型</p></div>
          </div>
          <div class="bf-item">
            <div class="bf-icon-wrap green"><span>📊</span></div>
            <div><strong>5维实时评分</strong><p>流畅度·说服力·产品知识·异议处理·情绪控制</p></div>
          </div>
          <div class="bf-item">
            <div class="bf-icon-wrap amber"><span>💡</span></div>
            <div><strong>教练即时反馈</strong><p>每轮对话给出针对性改进建议</p></div>
          </div>
          <div class="bf-item">
            <div class="bf-icon-wrap purple"><span>📈</span></div>
            <div><strong>进步实时可见</strong><p>训练记录追踪·量化成长曲线</p></div>
          </div>
        </div>

        <div class="brand-footer">Vue3 + FastAPI + LangChain + DeepSeek</div>
      </div>

      <!-- Right: Login Form -->
      <div class="login-form-panel">
        <div class="form-card">
          <div class="form-header">
            <span class="form-icon-wrap">🎯</span>
            <h2>欢迎回来</h2>
            <p>登录你的训练账号</p>
          </div>

          <n-form ref="formRef" :model="form" :rules="rules">
            <n-form-item path="username">
              <n-input
                v-model:value="form.username"
                placeholder="用户名"
                size="large"
                :input-props="{ autocomplete: 'username' }"
                class="login-input"
              >
                <template #prefix>
                  <span class="input-prefix">👤</span>
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="password">
              <n-input
                v-model:value="form.password"
                :type="showPwd ? 'text' : 'password'"
                placeholder="密码"
                size="large"
                @keyup.enter="handleLogin"
                :input-props="{ autocomplete: 'current-password' }"
                class="login-input"
              >
                <template #prefix>
                  <span class="input-prefix">🔒</span>
                </template>
                <template #suffix>
                  <span class="pwd-eye" @click="showPwd = !showPwd">
                    {{ showPwd ? '🙈' : '👁️' }}
                  </span>
                </template>
              </n-input>
            </n-form-item>

            <div v-if="errorMsg" class="error-tip">
              <span>{{ errorIcon }}</span>
              <span>{{ errorMsg }}</span>
            </div>

            <n-button
              type="primary"
              block
              size="large"
              :loading="loading"
              @click="handleLogin"
              class="submit-btn"
            >
              {{ loading ? '验证中…' : '登 录' }}
            </n-button>
          </n-form>

          <div class="form-actions">
            <n-button text @click="$router.push('/forgot-password')">忘记密码</n-button>
            <span class="sep">·</span>
            <n-button text @click="$router.push('/register')">注册账号</n-button>
          </div>

          <div class="demo-info">
            <span class="demo-label">演示账号</span>
            <div class="demo-creds">
              <code>admin</code>
              <span class="demo-dot">·</span>
              <code>ChangeMe!2024</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter(); const route = useRoute()
const authStore = useAuthStore(); const message = useMessage()
const formRef = ref<FormInst | null>(null); const loading = ref(false)
const showPwd = ref(false); const errorMsg = ref('')
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const errorIcon = computed(() => {
  if (errorMsg.value.includes('不存在')) return '🚫'
  if (errorMsg.value.includes('密码')) return '🔑'
  if (errorMsg.value.includes('禁用')) return '⛔'
  return '⚠️'
})

async function handleLogin() {
  const v = await formRef.value?.validate().catch(() => false); if (!v) return
  loading.value = true; errorMsg.value = ''
  try {
    await authStore.login({ username: form.username, password: form.password })
    message.success('登录成功')
    await new Promise(r => setTimeout(r, 300))
    router.push((route.query.redirect as string) || '/training')
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    if (detail) errorMsg.value = detail
    else if (e?.response?.status === 403) errorMsg.value = '账户已被禁用'
    else errorMsg.value = '登录失败，请检查用户名和密码'
  } finally { loading.value = false }
}
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════════════
   项目⑤ AI话术教练 — 登录页
   配色：白色底 + 蓝紫渐变点缀 + 现代企业风格
   ══════════════════════════════════════════════════════════════════ */
.login-page {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; background: #f8fafc;
  position: relative; overflow: hidden;
}

/* ── 背景 ── */
.bg-layer { position: absolute; inset: 0; pointer-events: none; }
.bg-orb { position: absolute; border-radius: 50%; filter: blur(80px); }
.orb-1 { width: 500px; height: 500px; top: -150px; right: -100px; background: rgba(59,130,246,.06); }
.orb-2 { width: 400px; height: 400px; bottom: -100px; left: -50px; background: rgba(139,92,246,.05); }
.orb-3 { width: 300px; height: 300px; top: 40%; left: 30%; background: rgba(34,197,94,.04); }
.bg-dots { position: absolute; inset: 0; pointer-events: none; }
.dot { position: absolute; width: 2px; height: 2px; background: #93c5fd; border-radius: 50%; }

/* ── 主布局 ── */
.login-container {
  display: flex; width: 1040px; min-height: 640px;
  background: #fff; border-radius: 28px; overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.04), 0 20px 80px rgba(0,0,0,.08);
  position: relative; z-index: 1;
}

/* ── 左侧品牌 ── */
.login-brand {
  flex: 1; padding: 56px 52px; display: flex; flex-direction: column;
  background: linear-gradient(160deg, #f8fafc 0%, #eff6ff 50%, #f5f3ff 100%);
}
.brand-badge {
  display: inline-block; align-self: flex-start;
  padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
  color: #3b82f6; background: rgba(59,130,246,.08); letter-spacing: 0.5px;
  margin-bottom: 24px;
}
.login-brand h1 {
  font-size: 38px; font-weight: 800; line-height: 1.2; color: #0f172a;
  margin: 0 0 16px; letter-spacing: -1px;
}
.login-brand > p {
  font-size: 15px; color: #64748b; margin: 0 0 36px; line-height: 1.5;
}

.brand-features { display: flex; flex-direction: column; gap: 16px; }
.bf-item { display: flex; align-items: flex-start; gap: 14px; }
.bf-icon-wrap {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
  flex-shrink: 0;
}
.bf-icon-wrap.blue   { background: #eff6ff; }
.bf-icon-wrap.green  { background: #ecfdf5; }
.bf-icon-wrap.amber  { background: #fffbeb; }
.bf-icon-wrap.purple { background: #f5f3ff; }
.bf-item strong { display: block; font-size: 14px; color: #1e293b; margin-bottom: 2px; }
.bf-item p { margin: 0; font-size: 12px; color: #94a3b8; }

.brand-footer {
  margin-top: auto; padding-top: 24px;
  font-size: 11px; color: #cbd5e1; letter-spacing: 0.3px;
}

/* ── 右侧表单 ── */
.login-form-panel {
  width: 440px; display: flex; align-items: center; justify-content: center;
  padding: 48px 40px;
}
.form-card { width: 100%; }
.form-header { text-align: center; margin-bottom: 32px; }
.form-icon-wrap { font-size: 40px; display: block; margin-bottom: 12px; }
.form-header h2 { font-size: 24px; font-weight: 700; color: #0f172a; margin: 0 0 4px; }
.form-header p { font-size: 14px; color: #94a3b8; margin: 0; }

/* 输入框 */
:deep(.login-input .n-input) {
  --n-border: 1px solid #e2e8f0 !important;
  --n-border-hover: 1px solid #cbd5e1 !important;
  --n-border-focus: 1px solid #3b82f6 !important;
  --n-color: #fff !important;
  --n-color-focus: #fff !important;
  --n-text-color: #1e293b !important;
  --n-placeholder-color: #94a3b8 !important;
  --n-height: 48px !important;
  border-radius: 14px !important;
}
.input-prefix { font-size: 16px; opacity: 0.45; margin-right: 4px; }
.pwd-eye { cursor: pointer; font-size: 16px; padding: 2px 6px; border-radius: 6px; opacity: 0.5; }
.pwd-eye:hover { opacity: 0.8; background: #f1f5f9; }

/* 提交按钮 */
.submit-btn {
  height: 50px !important; font-size: 16px !important; font-weight: 700 !important;
  border-radius: 14px !important; letter-spacing: 1px; margin-top: 8px;
  background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(59,130,246,0.2);
  transition: all .2s !important;
}
.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(99,102,241,0.3) !important;
}

/* 错误提示 */
.error-tip {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-radius: 10px; font-size: 13px;
  background: #fef2f2; color: #dc2626; border: 1px solid #fecaca;
  margin-bottom: 4px; animation: slideDown .25s ease both;
}

/* 操作链接 */
.form-actions {
  display: flex; align-items: center; justify-content: center; gap: 4px;
  margin-top: 20px; font-size: 13px; color: #94a3b8;
}
.sep { margin: 0 2px; }

/* 演示信息 */
.demo-info {
  margin-top: 24px; text-align: center; padding: 14px;
  background: #f8fafc; border-radius: 12px;
}
.demo-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; }
.demo-creds { margin-top: 6px; display: flex; align-items: center; justify-content: center; gap: 6px; }
.demo-creds code {
  background: #fff; border: 1px solid #e2e8f0; padding: 2px 10px;
  border-radius: 6px; font-size: 13px; color: #475569; font-family: 'SF Mono', 'Consolas', monospace;
}
.demo-dot { color: #cbd5e1; }

@keyframes slideDown { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }

/* ── 响应式 ── */
@media (max-width: 1080px) {
  .login-container { width: 90vw; flex-direction: column; }
  .login-brand { padding: 40px 32px; }
  .login-brand h1 { font-size: 28px; }
  .login-form-panel { width: 100%; padding: 0 32px 40px; }
}
</style>
