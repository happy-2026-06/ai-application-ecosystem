<template>
  <div class="reg-page">
    <!-- Animated gradient background -->
    <div class="reg-bg" />

    <!-- Center register panel -->
    <div class="reg-panel anim-scale-in">
      <!-- Brand area -->
      <div class="reg-brand">
        <div class="reg-icon-wrap">
          <span class="reg-icon">🎯</span>
        </div>
        <h1 class="reg-title">创建训练账号</h1>
        <p class="reg-desc">开始你的 AI 销售角色扮演训练之旅</p>
      </div>

      <n-form ref="fr" :model="f" :rules="r" label-placement="top">
        <n-form-item path="u">
          <n-input v-model:value="f.u" placeholder="用户名（3-50个字符）" size="large" class="reg-input">
            <template #prefix><span class="reg-input-icon">👤</span></template>
          </n-input>
        </n-form-item>
        <n-form-item path="e">
          <n-input v-model:value="f.e" placeholder="邮箱（可选）" size="large" class="reg-input">
            <template #prefix><span class="reg-input-icon">📧</span></template>
          </n-input>
        </n-form-item>
        <n-form-item path="p">
          <n-input v-model:value="f.p" type="password" placeholder="密码（至少6位）" size="large" class="reg-input">
            <template #prefix><span class="reg-input-icon">🔒</span></template>
          </n-input>
        </n-form-item>

        <!-- Password strength -->
        <div v-if="f.p" class="pw-strength">
          <div class="pw-bar"><div class="pw-fill" :style="pwStrength.style" /></div>
          <span class="pw-label" :style="{ color: pwStrength.color }">{{ pwStrength.label }}</span>
        </div>

        <n-form-item path="cp">
          <n-input v-model:value="f.cp" type="password" placeholder="确认密码" size="large" class="reg-input">
            <template #prefix><span class="reg-input-icon">🔒</span></template>
            <template #suffix>
              <span v-if="f.cp" class="pw-match" :class="{ match: f.p === f.cp, mismatch: f.p !== f.cp }">
                {{ f.p === f.cp ? '✅' : '❌' }}
              </span>
            </template>
          </n-input>
        </n-form-item>

        <n-button type="primary" block size="large" :loading="ld" @click="reg" class="reg-btn">
          {{ ld ? '注册中…' : '注 册' }}
        </n-button>
      </n-form>

      <div class="reg-extra">
        已有账号？<n-button text type="primary" size="small" @click="$router.push('/login')">去登录</n-button>
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
  e: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }],
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
  return { label: '强', color: '#22c55e', style: { width: '100%', background: '#22c55e' } }
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
/* ══════════════════════════════════════════════════════════════════
   注册页 — 与登录页同款深海军蓝 + 金色点缀
   ══════════════════════════════════════════════════════════════════ */

.reg-page {
  display: flex; align-items: center; justify-content: center;
  height: 100vh; background: #0a0e1a; position: relative; overflow: hidden;
}
.reg-bg {
  position: absolute; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 60% 70% at 30% 40%, rgba(34, 197, 94, 0.07) 0%, transparent 60%),
    radial-gradient(ellipse 70% 60% at 70% 60%, rgba(59, 130, 246, 0.09) 0%, transparent 60%),
    #0a0e1a;
  animation: bgShift 12s ease-in-out infinite;
}
@keyframes bgShift {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

/* ── Panel ───────────────────────────────────────────────────────── */
.reg-panel {
  position: relative; z-index: 1;
  width: 440px; padding: 44px 44px;
  background: rgba(15, 18, 30, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 24px;
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  box-shadow:
    0 4px 32px rgba(0, 0, 0, .4), 0 1px 4px rgba(0, 0, 0, .2),
    inset 0 1px 0 rgba(255, 255, 255, .03);
  animation: scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* ── Brand ────────────────────────────────────────────────────────── */
.reg-brand { text-align: center; margin-bottom: 32px; }
.reg-icon-wrap {
  display: inline-block;
  width: 64px; height: 64px; line-height: 64px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(34, 197, 94, 0.12));
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 14px;
}
.reg-icon { font-size: 30px; }
.reg-title { font-size: 24px; font-weight: 800; color: #f1f5f9; margin: 0 0 4px; }
.reg-desc { font-size: 13px; color: #64748b; margin: 0; }

/* ── Inputs ───────────────────────────────────────────────────────── */
:deep(.reg-input .n-input) {
  --n-border: 1px solid rgba(255, 255, 255, 0.06) !important;
  --n-border-hover: 1px solid rgba(255, 255, 255, 0.10) !important;
  --n-border-focus: 1px solid rgba(59, 130, 246, 0.3) !important;
  --n-color: rgba(255, 255, 255, 0.03) !important;
  --n-color-focus: rgba(255, 255, 255, 0.04) !important;
  --n-text-color: #e2e8f0 !important;
  --n-placeholder-color: #475569 !important;
  border-radius: 12px !important;
}
.reg-input-icon { font-size: 15px; opacity: 0.35; }

/* ── Password Strength ────────────────────────────────────────────── */
.pw-strength { display: flex; align-items: center; gap: 8px; margin-top: -8px; margin-bottom: 16px; }
.pw-bar { flex: 1; height: 4px; background: rgba(255,255,255,.06); border-radius: 2px; overflow: hidden; }
.pw-fill { height: 100%; border-radius: 2px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), background 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.pw-label { font-size: 11px; font-weight: 700; }
.pw-match { font-size: 14px; }

/* ── Button ────────────────────────────────────────────────────────── */
.reg-btn {
  height: 50px !important; font-size: 16px !important; font-weight: 700 !important;
  border-radius: 14px !important; letter-spacing: 1px;
  background: linear-gradient(135deg, #3b82f6, #2563eb, #1d4ed8) !important;
  border: none !important;
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.25);
  transition: all .25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.reg-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(59, 130, 246, 0.4) !important; }

.reg-extra { text-align: center; margin-top: 20px; font-size: 13px; color: #64748b; }

@keyframes scaleIn { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: scale(1); } }
</style>
