<template>
  <div class="fp-outer">
    <div class="fp-container">
      <div class="fp-card">
        <!-- Steps -->
        <div class="fp-steps">
          <div class="fp-step" :class="{ done: step > 1, active: step === 1 }"><span>1</span></div>
          <div class="fp-line" :class="{ done: step > 1 }" />
          <div class="fp-step" :class="{ done: step > 2, active: step === 2 }"><span>2</span></div>
          <div class="fp-line" :class="{ done: step > 2 }" />
          <div class="fp-step" :class="{ active: step === 3 }"><span>✓</span></div>
        </div>
        <div class="fp-labels">
          <span :class="{ on: step >= 1 }">验证身份</span>
          <span :class="{ on: step >= 2 }">设置密码</span>
          <span :class="{ on: step >= 3 }">完成</span>
        </div>

        <!-- Step 1 -->
        <div v-if="step === 1" class="fp-body">
          <div class="fp-icon-wrap"><span>🔑</span></div>
          <h2>忘记密码？</h2>
          <p>输入你的用户名，验证身份后即可重置密码</p>
          <n-input v-model:value="username" placeholder="用户名" size="large" class="fp-input" @keyup.enter="handleForgot" />
          <n-button type="primary" block size="large" :loading="loading" :disabled="!username.trim()" @click="handleForgot" class="fp-btn">
            {{ loading ? '验证中…' : '下一步' }}
          </n-button>
          <div class="fp-back" @click="$router.push('/login')">← 返回登录</div>
        </div>

        <!-- Step 2 -->
        <div v-if="step === 2" class="fp-body">
          <div class="fp-icon-wrap"><span>🔐</span></div>
          <h2>设置新密码</h2>
          <p><span class="demo-badge">演示模式</span>直接设置新密码</p>
          <n-input v-model:value="np" :type="sp ? 'text' : 'password'" placeholder="新密码（至少6位）" size="large" class="fp-input" />
          <n-input v-model:value="cp" type="password" placeholder="确认密码" size="large" class="fp-input" />
          <div v-if="np" class="pw-line"><div class="pw-line-fill" :style="pwStr.style" /><span :style="{color:pwStr.color,fontSize:'11px',fontWeight:700}">{{ pwStr.label }}</span></div>
          <n-button type="primary" block size="large" :loading="loading" :disabled="!canReset" @click="handleReset" class="fp-btn">
            {{ loading ? '重置中…' : '重置密码' }}
          </n-button>
          <div class="fp-back" @click="step=1">← 上一步</div>
        </div>

        <!-- Step 3 -->
        <div v-if="step === 3" class="fp-body">
          <div class="fp-icon-wrap large"><span>✅</span></div>
          <h2>密码重置成功</h2>
          <p>请使用新密码登录</p>
          <n-button type="primary" block size="large" @click="$router.push('/login')" class="fp-btn">前往登录</n-button>
        </div>

        <div v-if="err" class="fp-err">{{ err }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { useMessage } from 'naive-ui'

const router = useRouter(); const msg = useMessage()
const step = ref(1); const username = ref(''); const np = ref(''); const cp = ref('')
const loading = ref(false); const err = ref(''); const sp = ref(false)

const pwStr = computed(() => {
  const p = np.value; if (!p) return { label:'', color:'', style:{width:'0%'} }
  let s = 0; if (p.length>=6) s++; if (p.length>=8) s++; if (/[a-z]/.test(p)&&/[A-Z]/.test(p)) s++; if (/[0-9]/.test(p)) s++; if (/[^A-Za-z0-9]/.test(p)) s++
  if (s<=2) return { label:'弱', color:'#ef4444', style:{width:'25%',background:'#ef4444'} }
  if (s<=3) return { label:'中', color:'#f59e0b', style:{width:'55%',background:'#f59e0b'} }
  return { label:'强', color:'#22c55e', style:{width:'100%',background:'#22c55e'} }
})
const canReset = computed(() => np.value.length >= 6 && np.value === cp.value)

async function handleForgot() {
  err.value = ''; loading.value = true
  try { await authApi.forgotPassword(username.value.trim()); msg.info('演示模式：跳过验证'); step.value = 2 }
  catch (e: any) { err.value = e?.response?.data?.detail || '请求失败' }
  finally { loading.value = false }
}
async function handleReset() {
  err.value = ''; loading.value = true
  try { await authApi.resetPassword(username.value.trim(), np.value); msg.success('重置成功'); step.value = 3 }
  catch (e: any) { err.value = e?.response?.data?.detail || '重置失败' }
  finally { loading.value = false }
}
</script>

<style scoped>
.fp-outer {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; background: #f8fafc;
}
.fp-container { width: 100%; max-width: 440px; padding: 24px; }
.fp-card {
  background: #fff; border-radius: 20px; padding: 40px 36px;
  box-shadow: 0 1px 3px rgba(0,0,0,.03), 0 12px 40px rgba(0,0,0,.06);
  border: 1px solid #f1f5f9;
}
/* Steps */
.fp-steps { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 6px; }
.fp-step {
  width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700; color: #94a3b8;
  background: #f1f5f9; border: 2px solid #e2e8f0; flex-shrink: 0; transition: all .25s;
}
.fp-step.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.fp-step.done { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.fp-line { width: 48px; height: 2px; background: #e2e8f0; transition: background .25s; }
.fp-line.done { background: #3b82f6; }
.fp-labels { display: flex; justify-content: space-between; padding: 0 6px; margin-bottom: 32px; font-size: 11px; color: #94a3b8; }
.fp-labels span.on { color: #3b82f6; font-weight: 600; }

/* Body */
.fp-body { text-align: center; }
.fp-icon-wrap { width: 64px; height: 64px; line-height: 64px; border-radius: 20px; background: #eff6ff; display: inline-block; font-size: 28px; margin-bottom: 16px; }
.fp-icon-wrap.large { width: 80px; height: 80px; line-height: 80px; font-size: 36px; background: #ecfdf5; }
.fp-body h2 { font-size: 22px; font-weight: 700; color: #0f172a; margin: 0 0 6px; }
.fp-body p { font-size: 14px; color: #94a3b8; margin: 0 0 24px; }
.demo-badge { background: #eff6ff; color: #3b82f6; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; margin-right: 4px; }

.fp-input { margin-bottom: 14px; }
:deep(.fp-input .n-input) {
  --n-border: 1px solid #e2e8f0 !important;
  --n-border-focus: 1px solid #3b82f6 !important;
  --n-color: #fff !important; --n-text-color: #334155 !important;
  --n-placeholder-color: #94a3b8 !important; border-radius: 12px !important;
}
.pw-line { display: flex; align-items: center; gap: 8px; margin-top: -6px; margin-bottom: 14px; }
.pw-line-fill { flex: 1; height: 4px; border-radius: 2px; transition: width .4s; }

.fp-btn {
  height: 50px !important; font-size: 16px !important; font-weight: 700 !important;
  border-radius: 14px !important; background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  border: none !important; box-shadow: 0 4px 16px rgba(59,130,246,.2); margin-top: 8px;
}
.fp-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(99,102,241,.3) !important; }
.fp-back { margin-top: 16px; font-size: 13px; color: #3b82f6; cursor: pointer; }
.fp-back:hover { text-decoration: underline; }
.fp-err { margin-top: 16px; padding: 10px 14px; border-radius: 10px; background: #fef2f2; color: #dc2626; font-size: 13px; border: 1px solid #fecaca; }
</style>
