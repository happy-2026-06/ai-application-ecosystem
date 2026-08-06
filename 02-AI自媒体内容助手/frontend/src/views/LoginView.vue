<template>
  <div class="login-page">
    <!-- Animated gradient background -->
    <div class="bg-gradient" />

    <!-- Floating creative elements -->
    <div class="float-elements">
      <span v-for="e in floatingEmojis" :key="e.char" class="float-el" :style="{
        left: e.x, top: e.y,
        animationDelay: e.delay + 's',
        animationDuration: e.dur + 's',
        fontSize: e.size + 'px',
      }">{{ e.char }}</span>
    </div>

    <!-- Center login panel -->
    <div class="login-panel anim-scale-in">
      <!-- Brand area -->
      <div class="brand-area">
        <div class="brand-icon-wrap">
          <span class="brand-icon">✍️</span>
        </div>
        <h1>AI自媒体内容助手</h1>
        <p>爆款标题 · 视频脚本 · 图文文案 — 一键生成</p>
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="error-toast" :class="errorClass">
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
              <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
                {{ showPwd ? '🙈' : '👁️' }}
              </button>
            </template>
          </n-input>
        </n-form-item>

        <!-- Forgot link -->
        <div class="forgot-line">
          <n-button text type="primary" @click="$router.push('/forgot-password')">
            忘记密码？
          </n-button>
        </div>

        <!-- Login button -->
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

      <!-- Register -->
      <div class="register-line">
        <span>还没有账号？</span>
        <n-button text type="primary" @click="$router.push('/register')">立即注册</n-button>
      </div>

      <!-- Demo -->
      <div class="demo-line">
        <span>演示</span>
        <n-tag type="warning" size="small" round>admin</n-tag>
        <n-tag type="warning" size="small" round>123456</n-tag>
      </div>
    </div>

    <!-- Footer -->
    <p class="page-footer">AI自媒体内容助手 · LangChain + FastAPI + Vue 3</p>
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
const formRef = ref<FormInst | null>(null); const passwordInputRef = ref<HTMLInputElement | null>(null)
const loading = ref(false); const showPwd = ref(false); const errorMsg = ref('')
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const floatingEmojis = [
  { char: '🔥', x: '5%', y: '15%', delay: 0, dur: 7, size: 28 },
  { char: '🎬', x: '88%', y: '10%', delay: 1.5, dur: 8, size: 32 },
  { char: '📝', x: '12%', y: '78%', delay: 0.8, dur: 6.5, size: 24 },
  { char: '💡', x: '78%', y: '82%', delay: 2.2, dur: 7.5, size: 26 },
  { char: '⭐', x: '45%', y: '8%', delay: 3, dur: 9, size: 22 },
  { char: '🚀', x: '92%', y: '45%', delay: 1, dur: 8.5, size: 30 },
  { char: '✨', x: '8%', y: '50%', delay: 2.5, dur: 6, size: 20 },
  { char: '💬', x: '55%', y: '88%', delay: 0.3, dur: 7.8, size: 28 },
]

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
    if (ok) { message.success('欢迎回来！创作灵感就在眼前 🚀'); router.push((route.query.redirect as string) || '/home') }
    else errorMsg.value = '用户名或密码错误'
  } catch (e: any) {
    loading.value = false
    const detail = e?.response?.data?.detail || ''
    errorMsg.value = detail || '登录失败'
    const panel = document.querySelector('.login-panel')
    if (panel) { panel.classList.add('shake'); setTimeout(() => panel.classList.remove('shake'), 500) }
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════
   Project ② — 创意动态全屏风格
   ═══════════════════════════════════════════════════════════════════════════ */

.login-panel.shake {
  animation: shake 0.5s var(--ease-smooth);
}

@keyframes shake {
  0%,100% { transform: translateX(0); }
  15%,55%,85% { transform: translateX(-4px); }
  35%,70% { transform: translateX(4px); }
}

.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* ── Animated gradient background ───────────────────────────────────────── */
.bg-gradient {
  position: absolute;
  inset: -50%;
  background:
    radial-gradient(ellipse at 20% 50%, #FF6B35 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, #E11D48 0%, transparent 50%),
    radial-gradient(ellipse at 40% 80%, #FF2442 0%, transparent 50%),
    radial-gradient(ellipse at 60% 10%, #7C3AED 0%, transparent 50%);
  background-size: 200% 200%;
  animation: gradientShift 12s ease-in-out infinite;
  opacity: 0.15;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  25% { background-position: 100% 0%; }
  50% { background-position: 100% 100%; }
  75% { background-position: 0% 100%; }
}

/* ── Floating emojis ────────────────────────────────────────────────────── */
.float-elements {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.float-el {
  position: absolute;
  animation: floatAround ease-in-out infinite;
  opacity: 0.3;
  filter: blur(0.5px);
}

@keyframes floatAround {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(15px, -20px) rotate(5deg); }
  50% { transform: translate(-10px, -35px) rotate(-3deg); }
  75% { transform: translate(-18px, -10px) rotate(2deg); }
}

/* ── Login Panel ────────────────────────────────────────────────────────── */
.login-panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 44px 36px 36px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 24px;
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow:
    0 4px 24px rgba(255,107,53,.08),
    0 1px 4px rgba(0,0,0,.04);
  margin: 24px;
}

/* ── Brand ──────────────────────────────────────────────────────────────── */
.brand-area {
  text-align: center;
  margin-bottom: 28px;
}

.brand-icon-wrap {
  display: inline-block;
  padding: 16px;
  border-radius: 20px;
  background: linear-gradient(135deg, #FFF0EB, #FFE0D5);
  margin-bottom: 12px;
  box-shadow: 0 4px 16px rgba(255,107,53,.15);
}

.brand-icon {
  font-size: 40px;
  display: block;
}

.brand-area h1 {
  font-size: 24px;
  font-weight: 800;
  color: #1A0F2E;
  margin: 0 0 4px;
  letter-spacing: -0.3px;
}

.brand-area p {
  color: #B08870;
  font-size: 13px;
  margin: 0;
}

/* ── Error toast ────────────────────────────────────────────────────────── */
.error-toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 10px;
  margin-bottom: 18px;
  font-size: 13px;
  font-weight: 500;
  animation: fadeInDown 0.25s ease both;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.error-toast button {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
}
.error-toast button:hover { opacity: 1; }

.err-red { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.err-orange { background: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA; }
.err-generic { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }

/* ── Login Button — glow effect ─────────────────────────────────────── */
.login-btn {
  height: 50px !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  border-radius: 14px !important;
  letter-spacing: 1px !important;
  background: linear-gradient(135deg, #FF8C42, #FF6B35, #E55A2B) !important;
  border: none !important;
  transition: all 0.3s ease !important;
  position: relative;
  overflow: hidden;
}

.login-btn::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 16px;
  background: linear-gradient(135deg, #FF8C42, #FF6B35, #FF2442, #FF6B35);
  background-size: 400% 400%;
  z-index: -1;
  animation: glowBorder 3s ease infinite;
  opacity: 0;
  transition: opacity 0.3s;
}

.login-btn:hover::before { opacity: 1; }
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255,107,53,.4), 0 0 40px rgba(255,107,53,.15) !important;
}
.login-btn:active { transform: translateY(0); }

@keyframes glowBorder {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* ── Register ───────────────────────────────────────────────────────────── */
.register-line {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #B08870;
}

.demo-line {
  text-align: center;
  margin-top: 16px;
  font-size: 12px;
  color: #C4B5A8;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* ── Footer ─────────────────────────────────────────────────────────────── */
.page-footer {
  position: relative;
  z-index: 1;
  margin-top: 8px;
  font-size: 11px;
  color: rgba(0,0,0,.25);
}

/* ── Dark mode ──────────────────────────────────────────────────────────── */
[data-theme="dark"] .bg-gradient {
  opacity: 0.25;
}

[data-theme="dark"] .login-panel {
  background: rgba(30,25,40,0.85);
  border-color: rgba(255,255,255,.06);
  box-shadow: 0 4px 24px rgba(0,0,0,.3);
}

[data-theme="dark"] .brand-area h1 { color: #F0E8E0; }
[data-theme="dark"] .brand-area p { color: #8A7A8A; }
[data-theme="dark"] .brand-icon-wrap { background: linear-gradient(135deg, #2A1528, #3A2028); }

[data-theme="dark"] .input-group {
  background: rgba(255,255,255,.04);
  border-color: #3A2A35;
}

[data-theme="dark"] .input-group:focus-within {
  border-color: #FF6B35;
  background: rgba(255,255,255,.08);
}

[data-theme="dark"] .custom-input { color: #E8E0D8; }
[data-theme="dark"] .custom-input::placeholder { color: #6A5A68; }

[data-theme="dark"] .page-footer { color: rgba(255,255,255,.15); }
[data-theme="dark"] .register-line { color: #8A7A8A; }
[data-theme="dark"] .demo-line { color: #6A5A68; }

[data-theme="dark"] .error-toast { border-color: transparent; }
[data-theme="dark"] .err-red { background: rgba(220,38,38,.15); }
[data-theme="dark"] .err-orange { background: rgba(234,88,12,.15); }
[data-theme="dark"] .err-generic { background: rgba(220,38,38,.15); }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 480px) {
  .login-panel { padding: 32px 24px 28px; margin: 16px; }
  .brand-area h1 { font-size: 20px; }
  .brand-icon { font-size: 32px; }
}
</style>
