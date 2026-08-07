<template>
  <div class="fp-page">
    <!-- Background particles -->
    <div class="bg-particles">
      <span v-for="i in 10" :key="i" class="particle" :style="{
        left: `${(i * 41 + 7) % 100}%`,
        top: `${(i * 59 + 11) % 100}%`,
        animationDelay: `${(i * 0.8) % 5}s`,
        width: `${5 + (i % 4) * 3}px`,
        height: `${5 + (i % 4) * 3}px`,
      }" />
    </div>

    <div class="fp-container">
      <div class="fp-card anim-scale-in">
        <!-- Step indicator -->
        <div class="fp-steps">
          <div class="step-dot" :class="{ active: step >= 1, done: step > 1 }">1</div>
          <div class="step-line" :class="{ done: step > 1 }" />
          <div class="step-dot" :class="{ active: step >= 2, done: step > 2 }">2</div>
          <div class="step-line" :class="{ done: step > 2 }" />
          <div class="step-dot" :class="{ active: step >= 3 }">✓</div>
        </div>

        <!-- Step labels -->
        <div class="step-labels">
          <span :class="{ active: step >= 1 }">验证身份</span>
          <span :class="{ active: step >= 2 }">重置密码</span>
          <span :class="{ active: step >= 3 }">完成</span>
        </div>

        <!-- ═══ Step 1: Enter username ═══ -->
        <template v-if="step === 1">
          <div class="step-content">
            <div class="step-icon">🔑</div>
            <h2>忘记密码？</h2>
            <p class="step-desc">输入你的用户名，我们将帮助你重置密码</p>

            <n-input
              v-model:value="username"
              placeholder="请输入用户名"
              size="large"
              class="step-input"
              @keyup.enter="handleForgot"
            >
              <template #prefix><span class="input-prefix-icon">👤</span></template>
            </n-input>

            <n-button
              type="primary"
              block
              size="large"
              :loading="loading"
              :disabled="!username.trim()"
              @click="handleForgot"
              class="fp-btn"
            >
              {{ loading ? '验证中…' : '下一步' }}
            </n-button>

            <n-button text type="primary" @click="$router.push('/login')" class="back-link">
              ← 返回登录
            </n-button>
          </div>
        </template>

        <!-- ═══ Step 2: Set new password ═══ -->
        <template v-if="step === 2">
          <div class="step-content">
            <div class="step-icon anim-float">✉️</div>
            <h2>验证成功</h2>
            <p class="step-desc">
              <span class="demo-badge">演示模式</span>
              直接设置新密码即可
            </p>

            <!-- New password -->
            <n-input
              v-model:value="newPassword"
              :type="showPwd ? 'text' : 'password'"
              placeholder="请输入新密码（至少6位）"
              size="large"
              class="step-input"
            >
              <template #prefix><span class="input-prefix-icon">🔒</span></template>
              <template #suffix>
                <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
                  {{ showPwd ? '🙈' : '👁️' }}
                </button>
              </template>
            </n-input>

            <!-- Confirm password -->
            <n-input
              v-model:value="confirmPassword"
              type="password"
              placeholder="再次输入新密码"
              size="large"
              class="step-input"
            >
              <template #prefix><span class="input-prefix-icon">🔒</span></template>
              <template #suffix>
                <span v-if="confirmPassword" class="pw-match" :class="{ match: newPassword === confirmPassword, mismatch: newPassword !== confirmPassword }">
                  {{ newPassword === confirmPassword ? '✅' : '❌' }}
                </span>
              </template>
            </n-input>

            <!-- Password strength -->
            <div v-if="newPassword" class="pw-strength">
              <div class="pw-bar">
                <div class="pw-fill" :style="pwStrength.style" />
              </div>
              <span class="pw-label" :style="{ color: pwStrength.color }">{{ pwStrength.label }}</span>
            </div>

            <n-button
              type="primary"
              block
              size="large"
              :loading="loading"
              :disabled="!canReset"
              @click="handleReset"
              class="fp-btn"
            >
              {{ loading ? '重置中…' : '重置密码' }}
            </n-button>
          </div>
        </template>

        <!-- ═══ Step 3: Success ═══ -->
        <template v-if="step === 3">
          <div class="step-content">
            <div class="step-icon anim-scale-in">✅</div>
            <h2>密码重置成功！</h2>
            <p class="step-desc">请使用新密码登录你的账号</p>

            <n-button
              type="primary"
              block
              size="large"
              @click="$router.push('/login')"
              class="fp-btn"
            >
              前往登录
            </n-button>
          </div>
        </template>

        <!-- Error alert -->
        <div v-if="errorMsg" class="error-alert">
          <span class="error-icon">⚠️</span>
          <span class="error-text">{{ errorMsg }}</span>
          <button class="error-close" @click="errorMsg = ''">✕</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { useMessage } from 'naive-ui'

const router = useRouter()
const message = useMessage()

const step = ref(1)
const username = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')
const showPwd = ref(false)

const canReset = computed(() => {
  return newPassword.value.length >= 6 && newPassword.value === confirmPassword.value
})

const pwStrength = computed(() => {
  const p = newPassword.value
  if (!p) return { level: 0, label: '', color: '', style: { width: '0%' } }

  let score = 0
  if (p.length >= 6) score++
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++

  if (score <= 2) return { level: 1, label: '弱', color: '#EF4444', style: { width: '25%', background: '#EF4444' } }
  if (score <= 4) return { level: 2, label: '中等', color: '#F59E0B', style: { width: '55%', background: '#F59E0B' } }
  return { level: 3, label: '强', color: '#10B981', style: { width: '100%', background: '#10B981' } }
})

async function handleForgot() {
  if (!username.value.trim()) return
  errorMsg.value = ''
  loading.value = true

  try {
    const res = await authApi.forgotPassword(username.value.trim())
    loading.value = false

    if (res.data.demo) {
      message.info('演示模式：跳过邮箱验证，直接设置新密码')
    } else {
      message.success(res.data.message)
    }
    step.value = 2
  } catch (e: any) {
    loading.value = false
    errorMsg.value = e?.response?.data?.detail || '请求失败，请稍后重试'
  }
}

async function handleReset() {
  if (!canReset.value) return
  errorMsg.value = ''
  loading.value = true

  try {
    await authApi.resetPassword(username.value.trim(), newPassword.value)
    loading.value = false
    step.value = 3
    message.success('密码重置成功！')
  } catch (e: any) {
    loading.value = false
    errorMsg.value = e?.response?.data?.detail || '重置失败，请稍后重试'
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════
   Forgot Password Page — Indigo DAM Theme
   ═══════════════════════════════════════════════════════════════════════════ */

.fp-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #0F0B1E 0%, #1A1230 40%, #2D1B69 100%);
  position: relative;
  overflow: hidden;
}

.fp-page::before {
  content: '';
  position: absolute;
  top: -150px;
  right: -150px;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(99,102,241,.12), transparent 70%);
  border-radius: 50%;
  animation: pulse-glow 5s ease-in-out infinite;
}

.fp-page::after {
  content: '';
  position: absolute;
  bottom: -120px;
  left: -120px;
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(168,85,247,.08), transparent 70%);
  border-radius: 50%;
  animation: pulse-glow 6s ease-in-out infinite reverse;
}

/* ── Particles ──────────────────────────────────────────────────────────── */
.bg-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: #818CF8;
  border-radius: 50%;
  opacity: 0.06;
  animation: particle-float 6s ease-in-out infinite;
}

/* ── Container ──────────────────────────────────────────────────────────── */
.fp-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  padding: 24px;
}

.fp-card {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(99,102,241,0.10);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px 36px;
  box-shadow:
    0 4px 24px rgba(0,0,0,.08),
    0 1px 4px rgba(0,0,0,.04);
}

/* ── Step Indicator ─────────────────────────────────────────────────────── */
.fp-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 8px;
}

.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  background: #F1F3F9;
  color: #A09AB5;
  border: 2px solid #E4E2ED;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.step-dot.active {
  background: #6366F1;
  color: #fff;
  border-color: #6366F1;
}

.step-dot.done {
  background: #6366F1;
  color: #fff;
  border-color: #6366F1;
}

.step-line {
  width: 48px;
  height: 2px;
  background: #E4E2ED;
  transition: background 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-line.done {
  background: #6366F1;
}

.step-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 10px;
  margin-bottom: 32px;
  font-size: 11px;
  color: #A09AB5;
}

.step-labels span.active {
  color: #6366F1;
  font-weight: 600;
}

/* ── Step Content ───────────────────────────────────────────────────────── */
.step-content {
  text-align: center;
  animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1) both;
}

.step-icon {
  font-size: 56px;
  margin-bottom: 12px;
}

.step-content h2 {
  font-size: 24px;
  font-weight: 800;
  margin: 0 0 8px;
  color: #1A1230;
}

.step-desc {
  color: #6B6580;
  font-size: 14px;
  margin: 0 0 24px;
}

.demo-badge {
  display: inline-block;
  background: #EEF2FF;
  color: #6366F1;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 6px;
}

/* ── Input ──────────────────────────────────────────────────────────────── */
.step-input {
  margin-bottom: 16px;
}

.input-prefix-icon {
  font-size: 16px;
  opacity: 0.5;
}

.pwd-toggle {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px 8px;
  border-radius: 6px;
}

.pwd-toggle:hover {
  background: rgba(0,0,0,.06);
}

.pw-match {
  font-size: 16px;
}

/* ── Password Strength ──────────────────────────────────────────────────── */
.pw-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: -8px;
  margin-bottom: 16px;
}

.pw-bar {
  flex: 1;
  height: 4px;
  background: #F3F1F9;
  border-radius: 2px;
  overflow: hidden;
}

.pw-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), background 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.pw-label {
  font-size: 12px;
  font-weight: 700;
}

/* ── Button ─────────────────────────────────────────────────────────────── */
.fp-btn {
  height: 50px !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  border-radius: 14px !important;
  background: linear-gradient(135deg, #818CF8, #6366F1) !important;
  border: none !important;
  margin-top: 8px;
  position: relative;
  overflow: hidden;
}

.fp-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    110deg,
    transparent 0%,
    rgba(255,255,255,.25) 45%,
    rgba(255,255,255,.35) 50%,
    rgba(255,255,255,.25) 55%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 3s ease-in-out infinite;
  pointer-events: none;
}

.fp-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(99,102,241,.35) !important;
}

.back-link {
  margin-top: 16px;
  font-size: 14px;
}

/* ── Error Alert ────────────────────────────────────────────────────────── */
.error-alert {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 14px;
  background: rgba(220,38,38,.08);
  color: #DC2626;
  border: 1px solid rgba(220,38,38,.15);
  animation: fadeInUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) both;
}

.error-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 4px;
  color: inherit;
  opacity: 0.6;
  margin-left: auto;
}

.error-close:hover { opacity: 1; }

/* ═══════════════════════════════════════════════════════════════════════════
   Dark Mode
   ═══════════════════════════════════════════════════════════════════════════ */
[data-theme="dark"] .fp-page {
  background: linear-gradient(135deg, #0A0614 0%, #12101A 40%, #1A1530 100%);
}

[data-theme="dark"] .fp-card {
  background: rgba(18,16,26,0.85);
  border-color: rgba(99,102,241,.08);
}

[data-theme="dark"] .step-content h2 {
  color: #E8E8F0;
}

[data-theme="dark"] .step-desc {
  color: #A09AB5;
}

[data-theme="dark"] .step-dot {
  background: #1A1530;
  color: #A09AB5;
  border-color: #2D1B69;
}

[data-theme="dark"] .pwd-toggle:hover {
  background: rgba(255,255,255,.08);
}

[data-theme="dark"] .pw-bar {
  background: #1A1530;
}

[data-theme="dark"] .fp-card {
  box-shadow: 0 4px 24px rgba(99,102,241,.06);
}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 520px) {
  .fp-container { padding: 16px; }
  .fp-card { padding: 28px 20px; }
  .step-line { width: 32px; }
}

/* ── Keyframes ──────────────────────────────────────────────────────────── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-glow {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: .7; }
}
@keyframes particle-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
