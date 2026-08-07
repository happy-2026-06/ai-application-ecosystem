<template>
  <div class="reg-page">
    <!-- Background particles -->
    <div class="bg-particles">
      <span v-for="i in 8" :key="i" class="particle" :style="{
        left: `${(i * 43 + 13) % 100}%`,
        top: `${(i * 57 + 5) % 100}%`,
        animationDelay: `${(i * 1.1) % 5}s`,
        width: `${4 + (i % 4) * 2}px`,
        height: `${4 + (i % 4) * 2}px`,
      }" />
    </div>

    <!-- Left: Brand Intro -->
    <div class="reg-left">
      <div class="left-inner">
        <span class="logo-icon">🗂️</span>
        <h1>加入数字资产管理平台</h1>
        <p>注册即享 AI 智能素材管理 · 自动打标 · 多模态检索</p>
        <div class="feat-list">
          <div class="feat"><span>🏷️</span> AI 自动标签</div>
          <div class="feat"><span>🔍</span> 多模态检索</div>
          <div class="feat"><span>📋</span> 版本管理</div>
          <div class="feat"><span>👥</span> 团队协作</div>
        </div>
      </div>
    </div>

    <!-- Right: Register form -->
    <div class="reg-right">
      <div class="form-card anim-scale-in">
        <h2>创建账号 ✨</h2>
        <p class="sub">填写信息完成注册</p>

        <n-form ref="fr" :model="f" :rules="r" label-placement="top">
          <n-form-item label="用户名" path="u">
            <n-input v-model:value="f.u" placeholder="3-50个字符" size="large">
              <template #prefix><span class="input-icon">👤</span></template>
            </n-input>
          </n-form-item>
          <n-form-item label="邮箱（可选）" path="e">
            <n-input v-model:value="f.e" placeholder="your@email.com" size="large">
              <template #prefix><span class="input-icon">📧</span></template>
            </n-input>
          </n-form-item>
          <n-form-item label="密码" path="p">
            <n-input v-model:value="f.p" type="password" placeholder="至少6位" size="large">
              <template #prefix><span class="input-icon">🔒</span></template>
            </n-input>
          </n-form-item>

          <!-- Password strength -->
          <div v-if="f.p" class="pw-strength">
            <div class="pw-bar"><div class="pw-fill" :style="pwStrength.style" /></div>
            <span class="pw-label" :style="{ color: pwStrength.color }">{{ pwStrength.label }}</span>
          </div>

          <n-form-item label="确认密码" path="cp">
            <n-input v-model:value="f.cp" type="password" placeholder="再次输入" size="large">
              <template #prefix><span class="input-icon">🔒</span></template>
              <template #suffix>
                <span v-if="f.cp" class="pw-match" :class="{ match: f.p === f.cp, mismatch: f.p !== f.cp }">
                  {{ f.p === f.cp ? '✅' : '❌' }}
                </span>
              </template>
            </n-input>
          </n-form-item>

          <n-button
            type="primary"
            block size="large"
            :loading="ld" @click="reg"
            class="reg-btn"
          >
            {{ ld ? '注册中…' : '注 册' }}
          </n-button>
        </n-form>

        <div class="extra">
          <span>已有账号？</span><n-button text type="primary" @click="$router.push('/login')">去登录</n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter(); const auth = useAuthStore(); const msg = useMessage()
const fr = ref<FormInst | null>(null); const ld = ref(false)
const f = reactive({ u: '', e: '', p: '', cp: '' })
const r: FormRules = {
  u: [{ required: true, message: '请输入用户名' }, { min: 3, max: 50, message: '3-50字符' }],
  p: [{ required: true, min: 6, message: '至少6位' }],
  cp: [{ required: true, message: '请确认密码' }, { validator: (_: any, v: string) => v === f.p, message: '两次不一致', trigger: 'blur' }],
}

const pwStrength = computed(() => {
  const p = f.p
  if (!p) return { label: '', color: '', style: { width: '0%' } }
  let score = 0
  if (p.length >= 6) score++
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  if (score <= 2) return { label: '弱', color: '#EF4444', style: { width: '25%', background: '#EF4444' } }
  if (score <= 4) return { label: '中等', color: '#F59E0B', style: { width: '55%', background: '#F59E0B' } }
  return { label: '强', color: '#10B981', style: { width: '100%', background: '#10B981' } }
})

async function reg() {
  const v = await fr.value?.validate().catch(() => false); if (!v) return
  ld.value = true
  const ok = await auth.register({ username: f.u, password: f.p, email: f.e || undefined })
  ld.value = false
  if (ok) { msg.success('注册成功'); router.push('/login') }
  else msg.error('注册失败，用户名可能已存在')
}
</script>

<style scoped>
.reg-page {
  display: flex; height: 100vh;
  background: linear-gradient(135deg, #0F0B1E 0%, #1A1230 40%, #2D1B69 100%);
  position: relative; overflow: hidden;
}

/* Particles */
.bg-particles {
  position: absolute; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.particle {
  position: absolute; background: #818CF8; border-radius: 50%;
  opacity: 0.06; animation: particle-drift 8s ease-in-out infinite;
}

/* Left */
.reg-left {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 60px; position: relative; z-index: 1;
}
.left-inner { text-align: center; color: #e0e0f0; }
.logo-icon { font-size: 72px; display: block; margin-bottom: 16px; animation: float 4s ease-in-out infinite; }
.left-inner h1 { font-size: 28px; font-weight: 800; color: #fff; margin: 0 0 8px; }
.left-inner p { color: #a5b4fc; margin: 0 0 32px; font-size: 15px; }
.feat-list { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; max-width: 340px; margin: 0 auto; }
.feat {
  padding: 14px 16px; border-radius: 12px;
  background: rgba(255,255,255,.03); font-size: 14px; color: #c4c8e0;
  display: flex; align-items: center; gap: 8px;
  border: 1px solid transparent;
  transition: all .25s var(--ease-smooth);
}
.feat:hover {
  background: rgba(99,102,241,.10); color: #e0e4ff;
  border-color: rgba(99,102,241,.15); transform: translateY(-2px);
}
.feat span { font-size: 20px; }

/* Right */
.reg-right {
  width: 500px; display: flex; align-items: center; justify-content: center;
  padding: 40px; position: relative; z-index: 1;
}
.form-card {
  width: 100%; max-width: 400px; padding: 40px 36px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(99,102,241,.06);
}
.form-card h2 { font-size: 26px; font-weight: 800; margin: 0 0 6px; color: var(--text-primary); }
.sub { color: var(--text-secondary); margin: 0 0 28px; }
.input-icon { font-size: 16px; opacity: 0.4; }

/* Password strength */
.pw-strength {
  display: flex; align-items: center; gap: 8px;
  margin-top: -8px; margin-bottom: 16px;
}
.pw-bar { flex: 1; height: 4px; background: var(--border-light); border-radius: 2px; overflow: hidden; }
.pw-fill { height: 100%; border-radius: 2px; transition: width 0.4s var(--ease-smooth), background 0.4s var(--ease-smooth); }
.pw-label { font-size: 12px; font-weight: 700; }
.pw-match { font-size: 16px; }

/* Button */
.reg-btn {
  height: 50px !important; font-size: 16px !important; font-weight: 700 !important;
  border-radius: 14px !important;
  background: var(--primary-gradient) !important; border: none !important;
  transition: all .25s var(--ease-smooth) !important; position: relative; overflow: hidden;
}
.reg-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(99,102,241,.35) !important;
}

.extra { text-align: center; margin-top: 20px; font-size: 14px; color: var(--text-muted); }

.anim-scale-in { animation: scaleIn 0.5s var(--ease-spring) both; }

/* Dark Mode */
[data-theme="dark"] .reg-page { background: linear-gradient(135deg, #080510 0%, #0F0B1E 40%, #1A1530 100%); }
[data-theme="dark"] .left-inner p { color: #818CF8; }
[data-theme="dark"] .feat { background: rgba(255,255,255,.02); }
[data-theme="dark"] .feat:hover { background: rgba(99,102,241,.08); }

/* Keyframes */
@keyframes scaleIn { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: scale(1); } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
@keyframes particle-drift { 0%,100% { transform: translateY(0) rotate(0deg); } 33% { transform: translateY(-30px) rotate(120deg); } 66% { transform: translateY(15px) rotate(240deg); } }
</style>
