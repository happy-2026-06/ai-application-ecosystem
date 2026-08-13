<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-brand">
        <div class="brand-badge">MCP 多智能体平台</div>
        <h1>多Agent<br/>协作调度</h1>
        <p>Agent注册 · 任务编排 · 流水线/并行/投票/辩论 · 执行监控</p>
        <div class="brand-features">
          <div class="bf-item"><div class="bf-icon-wrap purple"><span>🤖</span></div><div><strong>Agent注册中心</strong><p>注册/发现/健康检查/状态管理</p></div></div>
          <div class="bf-item"><div class="bf-icon-wrap blue"><span>🔗</span></div><div><strong>多模式编排</strong><p>流水线·并行·投票·辩论</p></div></div>
          <div class="bf-item"><div class="bf-icon-wrap green"><span>📡</span></div><div><strong>MCP协议通信</strong><p>标准化JSON Schema Agent间通信</p></div></div>
          <div class="bf-item"><div class="bf-icon-wrap amber"><span>📊</span></div><div><strong>执行监控</strong><p>实时任务状态·日志·结果聚合</p></div></div>
        </div>
      </div>
      <div class="login-form-panel">
        <div class="form-card">
          <div class="form-header"><span class="form-icon-wrap">🤖</span><h2>欢迎回来</h2><p>登录Agent协作平台</p></div>
          <n-form ref="fr" :model="f" :rules="r">
            <n-form-item path="u"><n-input v-model:value="f.u" placeholder="用户名" size="large" class="ii"><template #prefix><span class="ip">👤</span></template></n-input></n-form-item>
            <n-form-item path="p"><n-input v-model:value="f.p" :type="sp ? 'text' : 'password'" placeholder="密码" size="large" @keyup.enter="login" class="ii"><template #prefix><span class="ip">🔒</span></template><template #suffix><span class="pe" @click="sp=!sp">{{sp?'🙈':'👁️'}}</span></template></n-input></n-form-item>
            <div v-if="err" class="err"><span>{{ei}}</span><span>{{err}}</span></div>
            <n-button type="primary" block size="large" :loading="ld" @click="login" class="sb">{{ld?'验证中…':'登 录'}}</n-button>
          </n-form>
          <div class="fa"><n-button text @click="$router.push('/forgot-password')">忘记密码</n-button><span class="sep">·</span><n-button text @click="$router.push('/register')">注册账号</n-button></div>
          <div class="di"><span class="dl">演示账号</span><div class="dc"><code>admin</code><span class="dd">·</span><code>ChangeMe!2024</code></div></div>
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
const router = useRouter(); const route = useRoute(); const auth = useAuthStore(); const msg = useMessage()
const fr = ref<FormInst|null>(null); const ld = ref(false); const sp = ref(false); const err = ref('')
const f = reactive({ u: '', p: '' })
const r: FormRules = { u: [{ required: true }], p: [{ required: true }] }
const ei = computed(() => err.value.includes('不存在')?'🚫':err.value.includes('密码')?'🔑':'⚠️')
async function login() {const v = await fr.value?.validate().catch(() => false); if (!v) return; ld.value = true; err.value = ''; const ok = await auth.login({ username: f.u, password: f.p }); if (!ok) { err.value = '用户名或密码错误' } else { msg.success('登录成功'); await new Promise(r=>setTimeout(r,300)); router.push((route.query.redirect as string)||'/agent') } ld.value = false}
</script>

<style scoped>
.login-page{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#faf9fe}
.login-container{display:flex;width:1040px;min-height:640px;background:#fff;border-radius:28px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04),0 20px 80px rgba(0,0,0,.08)}
.login-brand{flex:1;padding:56px 52px;display:flex;flex-direction:column;background:linear-gradient(160deg,#f5f3ff 0%,#ede9fe 50%,#faf9fe 100%)}
.brand-badge{display:inline-block;align-self:flex-start;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;color:#6d28d9;background:rgba(124,58,237,.08);margin-bottom:24px}
.login-brand h1{font-size:38px;font-weight:800;line-height:1.2;color:#4c1d95;margin:0 0 16px;letter-spacing:-1px}
.login-brand>p{font-size:15px;color:#64748b;margin:0 0 36px}
.brand-features{display:flex;flex-direction:column;gap:16px}
.bf-item{display:flex;align-items:flex-start;gap:14px}
.bf-icon-wrap{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.bf-icon-wrap.purple{background:#f5f3ff}.bf-icon-wrap.blue{background:#f0f9ff}.bf-icon-wrap.green{background:#ecfdf5}.bf-icon-wrap.amber{background:#fffbeb}
.bf-item strong{display:block;font-size:14px;color:#1e293b;margin-bottom:2px}
.bf-item p{margin:0;font-size:12px;color:#94a3b8}
.login-form-panel{width:440px;display:flex;align-items:center;justify-content:center;padding:48px 40px}
.form-card{width:100%}.form-header{text-align:center;margin-bottom:32px}.form-icon-wrap{font-size:40px;display:block;margin-bottom:12px}
.form-header h2{font-size:24px;font-weight:700;color:#4c1d95;margin:0 0 4px}.form-header p{font-size:14px;color:#94a3b8;margin:0}
:deep(.ii .n-input){--n-border:1px solid #e2e8f0!important;--n-border-focus:1px solid #7c3aed!important;--n-color:#fff!important;--n-text-color:#1e293b!important;--n-placeholder-color:#94a3b8!important;--n-height:48px!important;border-radius:14px!important}
.ip{font-size:16px;opacity:.45}.pe{cursor:pointer;font-size:16px;padding:2px 6px;border-radius:6px;opacity:.5}.pe:hover{opacity:.8;background:#f1f5f9}
.sb{height:50px!important;font-size:16px!important;font-weight:700!important;border-radius:14px!important;margin-top:8px;background:linear-gradient(135deg,#7c3aed,#6d28d9)!important;border:none!important;box-shadow:0 4px 16px rgba(124,58,237,.2)}
.sb:hover{transform:translateY(-1px);box-shadow:0 8px 24px rgba(124,58,237,.35)!important}
.err{display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;font-size:13px;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;margin-bottom:4px}
.fa{display:flex;align-items:center;justify-content:center;gap:4px;margin-top:20px;font-size:13px;color:#94a3b8}.sep{margin:0 2px}
.di{margin-top:24px;text-align:center;padding:14px;background:#f8fafc;border-radius:12px}.dl{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.8px}
.dc{margin-top:6px;display:flex;align-items:center;justify-content:center;gap:6px}.dc code{background:#fff;border:1px solid #e2e8f0;padding:2px 10px;border-radius:6px;font-size:13px;color:#475569;font-family:monospace}.dd{color:#cbd5e1}
</style>
