<template>
  <div class="login-page">
    <!-- Background particles -->
    <div class="bg-particles">
      <span v-for="i in 12" :key="i" class="particle" :style="{
        left: `${(i * 37 + 11) % 100}%`,
        top: `${(i * 53 + 7) % 100}%`,
        animationDelay: `${(i * 0.7) % 6}s`,
        width: `${4 + (i % 5) * 3}px`,
        height: `${4 + (i % 5) * 3}px`,
      }" />
    </div>

    <!-- Left: Product intro -->
    <div class="login-left">
      <div class="left-inner">
        <div class="logo-area">
          <span class="logo-icon">🗂️</span>
          <h1>图库资产管家</h1>
          <p>企业级数字资产管理 · 智能标签 · 多模态检索</p>
        </div>
        <div class="feature-list">
          <div class="feat"><span>🏷️</span> AI自动打标 — 上传素材自动生成精准标签</div>
          <div class="feat"><span>🔍</span> 多模态检索 — 文本搜图/以图搜图/标签筛选</div>
          <div class="feat"><span>📁</span> 版本管理 — 素材版本追踪，随时回溯历史</div>
          <div class="feat"><span>👥</span> 团队协作 — 多角色权限，企业级安全管控</div>
        </div>
      </div>
      <div class="left-footer">面试项目 · Vue3 + FastAPI + LangChain + DeepSeek</div>
    </div>

    <!-- Right: Login form (Glassmorphism) -->
    <div class="login-right">
      <div class="form-card glass-card anim-scale-in">
        <h2>欢迎回来 👋</h2>
        <p class="form-sub">登录你的账号开始管理素材</p>

        <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
          <n-form-item label="用户名" path="username">
            <n-input
              v-model:value="form.username"
              placeholder="请输入用户名"
              size="large"
              :input-props="{ autocomplete: 'username' }"
            >
              <template #prefix><span class="input-icon">👤</span></template>
            </n-input>
          </n-form-item>
          <n-form-item label="密码" path="password">
            <n-input
              v-model:value="form.password"
              :type="showPwd ? 'text' : 'password'"
              placeholder="请输入密码"
              size="large"
              @keyup.enter="handleLogin"
              :input-props="{ autocomplete: 'current-password' }"
            >
              <template #prefix><span class="input-icon">🔒</span></template>
              <template #suffix>
                <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
                  {{ showPwd ? '🙈' : '👁️' }}
                </button>
              </template>
            </n-input>
          </n-form-item>

          <!-- Error alert -->
          <div v-if="errorMsg" class="error-alert">
            <span class="error-icon">{{ errorIcon }}</span>
            <span class="error-text">{{ errorMsg }}</span>
          </div>

          <n-button
            type="primary"
            block
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            {{ loading ? '登录中…' : '登 录' }}
          </n-button>
        </n-form>

        <div class="form-links">
          <n-button text type="primary" @click="$router.push('/forgot-password')">忘记密码？</n-button>
          <span>还没有账号？<n-button text type="primary" @click="$router.push('/register')">立即注册</n-button></span>
        </div>

        <div class="demo-hint">
          <n-divider>演示账号</n-divider>
          <div class="demo-tags">
            <n-tag type="info" size="small" round>admin</n-tag>
            <n-tag type="info" size="small" round style="margin-left:6px;">ChangeMe!2024</n-tag>
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
    // 延迟跳转，确保 pinia persist 插件将 token 写入 localStorage
    await new Promise(r => setTimeout(r, 300))
    router.push((route.query.redirect as string) || '/assets')
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    if (detail) errorMsg.value = detail
    else if (e?.response?.status === 403) errorMsg.value = '账户已被禁用'
    else errorMsg.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex; height: 100vh;
  background: linear-gradient(135deg, #0F0B1E 0%, #1A1230 40%, #2D1B69 100%);
  position: relative; overflow: hidden;
}

/* ═══ Particles ═══ */
.bg-particles {
  position: absolute; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.particle {
  position: absolute;
  background: #818CF8; border-radius: 50%; opacity: 0.08;
  animation: particle-drift 8s ease-in-out infinite;
}

/* ═══ Left Panel ═══ */
.login-left {
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  align-items: center; padding: 60px; position: relative; z-index: 1;
  color: #e0e0f0;
}
.login-left::before {
  content: ''; position: absolute; top: -120px; right: -120px;
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(99,102,241,.12), transparent 70%);
  border-radius: 50%; animation: pulse-glow 6s ease-in-out infinite;
}
.login-left::after {
  content: ''; position: absolute; bottom: -100px; left: -100px;
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(168,85,247,.08), transparent 70%);
  border-radius: 50%; animation: pulse-glow 8s ease-in-out infinite reverse;
}
.left-inner { max-width: 480px; position: relative; z-index: 1; }
.logo-area { text-align: center; margin-bottom: 44px; }
.logo-icon { font-size: 72px; display: block; margin-bottom: 16px; animation: float 4s ease-in-out infinite; }
.logo-area h1 { font-size: 30px; font-weight: 800; color: #fff; margin: 0 0 8px; letter-spacing: -0.3px; }
.logo-area p { color: #a5b4fc; font-size: 15px; margin: 0; }

.feat {
  padding: 14px 18px; margin-bottom: 8px; border-radius: 12px;
  background: rgba(255,255,255,.03); font-size: 14px; color: #c4c8e0;
  display: flex; align-items: center; gap: 12px;
  transition: all .3s var(--ease-smooth);
  border: 1px solid transparent;
}
.feat:hover {
  background: rgba(99,102,241,.10); color: #e0e4ff;
  transform: translateX(6px); border-color: rgba(99,102,241,.15);
}
.feat span { font-size: 22px; flex-shrink: 0; }
.left-footer { position: absolute; bottom: 24px; color: #4a4a6a; font-size: 12px; z-index: 1; }

/* ═══ Right Panel — Glassmorphism ═══ */
.login-right {
  width: 500px; display: flex; align-items: center; justify-content: center;
  padding: 40px; position: relative; z-index: 1;
}
.form-card {
  width: 100%; max-width: 400px; padding: 40px 36px;
  animation: scaleIn 0.6s var(--ease-spring) both;
}
.form-card h2 { font-size: 26px; font-weight: 800; margin: 0 0 6px; color: var(--text-primary); letter-spacing: -0.3px; }
.form-sub { color: var(--text-secondary); margin: 0 0 28px; font-size: 14px; }

.input-icon { font-size: 16px; opacity: 0.4; }

.pwd-toggle {
  background: none; border: none; cursor: pointer; font-size: 18px;
  padding: 4px 8px; border-radius: 6px; transition: background .15s;
}
.pwd-toggle:hover { background: rgba(0,0,0,.05); }
[data-theme="dark"] .pwd-toggle:hover { background: rgba(255,255,255,.06); }

/* ── Login Button ── */
.login-btn {
  height: 50px !important; font-size: 16px !important; font-weight: 700 !important;
  border-radius: 14px !important;
  background: var(--primary-gradient) !important; border: none !important;
  margin-top: 4px; position: relative; overflow: hidden; transition: all .25s var(--ease-smooth) !important;
}
.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(99,102,241,.35) !important;
}
.login-btn::after {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 0%, rgba(255,255,255,.2) 45%, rgba(255,255,255,.3) 50%, rgba(255,255,255,.2) 55%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 3s ease-in-out infinite;
  pointer-events: none;
}

/* ── Links ── */
.form-links {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 16px; font-size: 13px; color: var(--text-muted);
}

/* ── Error ── */
.error-alert {
  display: flex; align-items: center; gap: 10px; margin-bottom: 12px;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(239,68,68,.06); color: #EF4444;
  border: 1px solid rgba(239,68,68,.12); font-size: 14px;
  animation: slideUp 0.3s var(--ease-smooth) both;
}
.error-icon { font-size: 18px; flex-shrink: 0; }
.error-text { flex: 1; }

/* ── Demo Hint ── */
.demo-hint { text-align: center; margin-top: 20px; }
.demo-tags { display: flex; justify-content: center; align-items: center; }

/* ═══ Dark Mode ═══ */
[data-theme="dark"] .login-page { background: linear-gradient(135deg, #080510 0%, #0F0B1E 40%, #1A1530 100%); }
[data-theme="dark"] .logo-area p { color: #818CF8; }
[data-theme="dark"] .left-footer { color: #3a3a5a; }
[data-theme="dark"] .feat { background: rgba(255,255,255,.02); }
[data-theme="dark"] .feat:hover { background: rgba(99,102,241,.08); }

/* ═══ Animations ═══ */
@keyframes scaleIn { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: scale(1); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
@keyframes pulse-glow { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.08); opacity: .6; } }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
@keyframes particle-drift { 0%,100% { transform: translateY(0) rotate(0deg); } 33% { transform: translateY(-30px) rotate(120deg); } 66% { transform: translateY(15px) rotate(240deg); } }
</style>
