<template>
  <div class="login-page">
    <!-- Left: Cinematic dark panel -->
    <div class="left-panel">
      <!-- Film grain overlay -->
      <div class="film-grain" />

      <!-- Spotlight effect -->
      <div class="spotlight" />

      <div class="left-content">
        <div class="left-eyebrow">SHORT VIDEO · SCRIPT STUDIO</div>
        <div class="left-title">
          <span class="title-line">AI短视频</span>
          <span class="title-line gold">脚本工坊</span>
        </div>
        <p class="left-desc">专业的短视频分镜脚本生成引擎</p>

        <div class="shot-list">
          <div class="shot-item" v-for="(s, i) in shots" :key="i"
            :style="{ animationDelay: (i * 0.15) + 's' }">
            <span class="shot-num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="shot-label">{{ s }}</span>
          </div>
        </div>
      </div>

      <div class="left-bottom">
        <span class="lb-dot" />
        面试项目 · Vue3 + FastAPI + LangChain + DeepSeek
      </div>
    </div>

    <!-- Right: Login area -->
    <div class="right-panel">
      <div class="form-wrapper anim-scale-in">
        <!-- Header -->
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>登录你的账号开始创作</p>
        </div>

        <!-- Error -->
        <div v-if="errorMsg" class="error-strip" :class="errorClass">
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
              round
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
              round
            >
              <template #suffix>
                <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
                  {{ showPwd ? '🙈' : '👁️' }}
                </button>
              </template>
            </n-input>
          </n-form-item>

          <div class="forgot-row">
            <n-button text type="primary" @click="$router.push('/forgot-password')">
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

        <div class="register-row">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="$router.push('/register')">立即注册</n-button>
        </div>

        <div class="demo-row">
          <span>演示账号</span>
          <n-tag type="warning" size="small" round>admin</n-tag>
          <n-tag type="warning" size="small" round>ChangeMe!2024</n-tag>
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
const formRef = ref<FormInst | null>(null); const passwordInputRef = ref<any>(null)
const loading = ref(false); const showPwd = ref(false); const errorMsg = ref('')
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const shots = ['镜号/时长精准规划', '画面/口播同步生成', 'B-roll素材智能推荐', '五平台差异化适配']

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
    if (ok) { message.success('欢迎回来，导演！🎬'); router.push((route.query.redirect as string) || '/studio') }
    else errorMsg.value = '用户名或密码错误'
  } catch (e: any) {
    loading.value = false
    const detail = e?.response?.data?.detail || ''
    errorMsg.value = detail || '登录失败'
    const wrapper = document.querySelector('.form-wrapper')
    if (wrapper) { wrapper.classList.add('shake'); setTimeout(() => wrapper.classList.remove('shake'), 500) }
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════
   Project ③ — 影院式暗色分屏风格
   ═══════════════════════════════════════════════════════════════════════════ */

.login-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── Left Panel — Cinematic Dark ────────────────────────────────────────── */
.left-panel {
  flex: 1;
  background: #0A0A0F;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px 60px;
  position: relative;
  overflow: hidden;
}

/* Film grain */
.film-grain {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  opacity: 0.6;
}

/* Spotlight */
.spotlight {
  position: absolute;
  top: -200px;
  left: -100px;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(200,169,81,.06), transparent 70%);
  pointer-events: none;
  animation: spotlightPulse 6s ease-in-out infinite;
}

@keyframes spotlightPulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

.left-content {
  position: relative;
  z-index: 1;
  max-width: 480px;
}

.left-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 4px;
  color: rgba(200,169,81,.6);
  margin-bottom: 20px;
}

.left-title {
  margin-bottom: 16px;
}

.title-line {
  display: block;
  font-size: 42px;
  font-weight: 800;
  color: #E8E8F0;
  line-height: 1.15;
  letter-spacing: -1px;
}

.title-line.gold {
  background: linear-gradient(90deg, #E8C860, #C8A951, #A08030);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 48px;
}

.left-desc {
  color: #6A6A78;
  font-size: 15px;
  margin: 0 0 44px;
}

/* Shot list */
.shot-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shot-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(255,255,255,.02);
  border-left: 2px solid rgba(200,169,81,.3);
  animation: shotSlideIn 0.5s ease both;
  transition: all 0.3s ease;
}

.shot-item:hover {
  background: rgba(200,169,81,.06);
  border-left-color: #C8A951;
  transform: translateX(4px);
}

@keyframes shotSlideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.shot-num {
  font-size: 13px;
  font-weight: 700;
  color: rgba(200,169,81,.6);
  font-family: "Cascadia Code", "Fira Code", monospace;
  min-width: 22px;
}

.shot-label {
  font-size: 14px;
  color: #8888A0;
}

.left-bottom {
  position: absolute;
  bottom: 28px;
  left: 60px;
  font-size: 11px;
  color: #3A3A48;
  display: flex;
  align-items: center;
  gap: 8px;
}

.lb-dot {
  width: 5px;
  height: 5px;
  background: #C8A951;
  border-radius: 50%;
}

/* ── Right Panel ────────────────────────────────────────────────────────── */
.right-panel {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #12121A;
  border-left: 1px solid #1E1E2A;
}

.form-wrapper {
  width: 100%;
  max-width: 380px;
}

.form-wrapper.shake {
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%,100% { transform: translateX(0); }
  15%,55%,85% { transform: translateX(-3px); }
  35%,70% { transform: translateX(3px); }
}

/* ── Form Header ────────────────────────────────────────────────────────── */
.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #E8E8F0;
  margin: 0 0 4px;
}

.form-header p {
  color: #6A6A78;
  font-size: 14px;
  margin: 0;
}

/* ── Error ──────────────────────────────────────────────────────────────── */
.error-strip {
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

.error-strip button {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
}
.error-strip button:hover { opacity: 1; }

.err-red { background: rgba(220,38,38,.12); color: #FCA5A5; border: 1px solid rgba(220,38,38,.2); }
.err-orange { background: rgba(234,88,12,.12); color: #FDBA74; border: 1px solid rgba(234,88,12,.2); }
.err-generic { background: rgba(220,38,38,.12); color: #FCA5A5; border: 1px solid rgba(220,38,38,.2); }

/* ── Password toggle ────────────────────────────────────────────────────── */
.pwd-toggle {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px 6px;
  border-radius: 4px;
  line-height: 1;
}
.pwd-toggle:hover { background: #1E1E2A; }

/* ── Forgot ─────────────────────────────────────────────────────────────── */
.forgot-row {
  text-align: right;
  margin-top: -8px;
  margin-bottom: 8px;
}

/* ── Login Button — Metallic Gold ───────────────────────────────────────── */
.login-btn {
  height: 48px !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  border-radius: 24px !important;
  background: linear-gradient(135deg, #E8C860, #C8A951, #A08030) !important;
  border: none !important;
  color: #1A1A24 !important;
  letter-spacing: 2px !important;
  transition: all 0.3s ease !important;
  position: relative;
  overflow: hidden;
}

.login-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    110deg,
    transparent 0%,
    rgba(255,255,255,.3) 45%,
    rgba(255,255,255,.5) 50%,
    rgba(255,255,255,.3) 55%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(200,169,81,.3) !important;
}

.login-btn:active { transform: translateY(0); }

/* ── Register ───────────────────────────────────────────────────────────── */
.register-row {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #6A6A78;
}

.demo-row {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #1E1E2A;
  font-size: 12px;
  color: #4A4A5A;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .login-page { flex-direction: column; }
  .left-panel { flex: none; padding: 40px 28px; }
  .title-line { font-size: 28px; }
  .title-line.gold { font-size: 32px; }
  .right-panel { width: 100%; flex: 1; border-left: none; border-top: 1px solid #1E1E2A; }
  .left-bottom { left: 28px; bottom: 16px; font-size: 10px; }
}
</style>
