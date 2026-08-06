<template>
  <div class="login-page">
    <!-- Subtle dot grid background -->
    <div class="bg-dots" />

    <!-- Center card only — no split screen -->
    <div class="login-container">
      <!-- Card -->
      <div class="login-card anim-scale-in">
        <!-- Logo area -->
        <div class="card-logo">
          <span class="logo-icon">💬</span>
          <h1>RAG 知识库问答</h1>
          <p>企业级 AI 知识库问答平台</p>
        </div>

        <!-- Error -->
        <div v-if="errorMsg" class="error-bar" :class="errorClass">
          <span>{{ errorIcon }} {{ errorMsg }}</span>
          <button @click="errorMsg = ''">✕</button>
        </div>

        <!-- Form -->
        <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
          <n-form-item label="用户名" path="username">
            <n-input
              v-model:value="form.username"
              placeholder="请输入用户名"
              size="large"
              :input-props="{ autocomplete: 'username' }"
              @keyup.enter="focusPassword"
            />
          </n-form-item>

          <n-form-item label="密码" path="password">
            <n-input
              ref="passwordInputRef"
              v-model:value="form.password"
              :type="showPwd ? 'text' : 'password'"
              placeholder="请输入密码"
              size="large"
              :input-props="{ autocomplete: 'current-password' }"
              @keyup.enter="handleLogin"
            >
              <template #suffix>
                <button type="button" class="pwd-btn" @click="showPwd = !showPwd">
                  {{ showPwd ? '🙈' : '👁️' }}
                </button>
              </template>
            </n-input>
          </n-form-item>

          <!-- Row: remember + forgot -->
          <div class="form-row">
            <n-checkbox v-model:checked="rememberMe" size="small">记住登录</n-checkbox>
            <n-button text type="primary" size="small" @click="$router.push('/forgot-password')">
              忘记密码？
            </n-button>
          </div>

          <n-button
            type="primary"
            block
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            {{ loading ? '验证中…' : '登 录' }}
          </n-button>
        </n-form>

        <!-- Bottom links -->
        <div class="card-footer">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="$router.push('/register')">创建账号</n-button>
        </div>
      </div>

      <!-- Demo hint below card -->
      <div class="demo-hint">
        <span>演示账号</span>
        <n-tag type="info" size="small">admin</n-tag>
        <n-tag type="info" size="small">123456</n-tag>
      </div>

      <!-- Footer -->
      <p class="login-footer">毕业设计项目 · LangChain + FastAPI + Vue 3</p>
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
const formRef = ref<FormInst | null>(null); const passwordInputRef = ref<any>(null)
const loading = ref(false); const showPwd = ref(false); const errorMsg = ref(''); const rememberMe = ref(false)
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const errorIcon = computed(() => {
  if (errorMsg.value.includes('不存在')) return '🚫'
  if (errorMsg.value.includes('密码')) return '🔑'
  return '⚠️'
})
const errorClass = computed(() => {
  if (errorMsg.value.includes('不存在')) return 'err-red'
  if (errorMsg.value.includes('密码')) return 'err-orange'
  return 'err-generic'
})

function focusPassword() { passwordInputRef.value?.focus() }

async function handleLogin() {
  errorMsg.value = ''
  const v = await formRef.value?.validate().catch(() => false)
  if (!v) return
  loading.value = true
  try {
    const ok = await authStore.login({ username: form.username, password: form.password })
    loading.value = false
    if (ok) { message.success('登录成功！'); router.push((route.query.redirect as string) || '/chat') }
    else errorMsg.value = '用户名或密码错误'
  } catch (e: any) {
    loading.value = false
    const detail = e?.response?.data?.detail || ''
    errorMsg.value = detail || '登录失败'
    const card = document.querySelector('.login-card')
    if (card) { card.classList.add('shake'); setTimeout(() => card.classList.remove('shake'), 500) }
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════
   Project ① — 简约企业SaaS风格
   ═══════════════════════════════════════════════════════════════════════════ */

.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F0F2F5;
  position: relative;
  overflow: hidden;
}

/* ── Dot grid background ────────────────────────────────────────────────── */
.bg-dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #D1D5DB 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.5;
}

/* ── Center container ───────────────────────────────────────────────────── */
.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 24px;
}

/* ── Card ───────────────────────────────────────────────────────────────── */
.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px 32px;
  box-shadow:
    0 1px 3px rgba(0,0,0,.04),
    0 4px 16px rgba(0,0,0,.04),
    0 12px 40px rgba(0,0,0,.06);
  border: 1px solid #E5E7EB;
}

.login-card.shake {
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%,100% { transform: translateX(0); }
  15%,55%,85% { transform: translateX(-3px); }
  35%,70% { transform: translateX(3px); }
}

/* ── Logo ───────────────────────────────────────────────────────────────── */
.card-logo {
  text-align: center;
  margin-bottom: 28px;
}

.logo-icon {
  font-size: 44px;
  display: block;
  margin-bottom: 8px;
}

.card-logo h1 {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
  letter-spacing: -0.3px;
}

.card-logo p {
  color: #9CA3AF;
  font-size: 14px;
  margin: 0;
}

/* ── Error bar ──────────────────────────────────────────────────────────── */
.error-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 18px;
  font-size: 13px;
  font-weight: 500;
  animation: fadeInDown 0.25s ease both;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.error-bar button {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
  padding: 0 2px;
}

.error-bar button:hover { opacity: 1; }

.err-red { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.err-orange { background: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA; }
.err-generic { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }

/* ── Form row ───────────────────────────────────────────────────────────── */
.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: -10px;
  margin-bottom: 16px;
}

/* ── Password button ────────────────────────────────────────────────────── */
.pwd-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px 6px;
  border-radius: 4px;
  line-height: 1;
}
.pwd-btn:hover { background: #F3F4F6; }

/* ── Login button ───────────────────────────────────────────────────────── */
.login-btn {
  height: 46px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  background: #2563EB !important;
  border: none !important;
  transition: all 0.2s ease !important;
}

.login-btn:hover {
  background: #1D4ED8 !important;
  box-shadow: 0 4px 12px rgba(37,99,235,.3) !important;
  transform: translateY(-1px);
}

.login-btn:active { transform: translateY(0); }

/* ── Footer ─────────────────────────────────────────────────────────────── */
.card-footer {
  text-align: center;
  margin-top: 22px;
  font-size: 14px;
  color: #9CA3AF;
}

.demo-hint {
  text-align: center;
  margin-top: 20px;
  font-size: 12px;
  color: #9CA3AF;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.demo-hint span:first-child {
  color: #9CA3AF;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
  font-size: 11px;
  color: #C4C8CF;
}

/* ── Dark mode ──────────────────────────────────────────────────────────── */
[data-theme="dark"] .login-page {
  background: #0F172A;
}

[data-theme="dark"] .bg-dots {
  background-image: radial-gradient(circle, #1E293B 1px, transparent 1px);
  opacity: 0.6;
}

[data-theme="dark"] .login-card {
  background: #1E293B;
  border-color: #334155;
  box-shadow: 0 12px 40px rgba(0,0,0,.4);
}

[data-theme="dark"] .card-logo h1 { color: #F1F5F9; }
[data-theme="dark"] .card-logo p { color: #64748B; }
[data-theme="dark"] .login-footer { color: #475569; }
[data-theme="dark"] .demo-hint { color: #64748B; }
[data-theme="dark"] .pwd-btn:hover { background: #334155; }
[data-theme="dark"] .card-footer { color: #64748B; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 480px) {
  .login-container { padding: 16px; }
  .login-card { padding: 28px 20px 24px; }
  .logo-icon { font-size: 36px; }
  .card-logo h1 { font-size: 20px; }
}
</style>
