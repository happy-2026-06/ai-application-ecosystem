<template>
  <div class="login-page">
    <!-- Left: Product intro -->
    <div class="login-left">
      <div class="left-inner">
        <div class="logo-area">
          <span class="logo-icon">🗂️</span>
          <h1>AI素材管理平台</h1>
          <p>企业级数字资产管理 · 智能标签 · 多模态检索</p>
        </div>
        <div class="feature-list">
          <div class="feat active"><span>🏷️</span> AI自动打标 — 上传素材自动生成标签和描述</div>
          <div class="feat"><span>🔍</span> 多模态检索 — 文本搜图/以图搜图/标签筛选</div>
          <div class="feat"><span>📁</span> 版本管理 — 素材版本追踪，随时回溯</div>
          <div class="feat"><span>👥</span> 权限控制 — 多角色权限，团队协作</div>
        </div>
      </div>
      <div class="left-footer">面试项目 · Vue3 + FastAPI + LangChain + DeepSeek</div>
    </div>

    <!-- Right: Login form -->
    <div class="login-right">
      <div class="form-card anim-scale-in">
        <h2>欢迎回来 👋</h2>
        <p class="form-sub">登录你的账号开始管理素材</p>
        <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
          <n-form-item label="用户名" path="username">
            <n-input v-model:value="form.username" placeholder="请输入用户名" size="large" :input-props="{autocomplete:'username'}" />
          </n-form-item>
          <n-form-item label="密码" path="password">
            <n-input v-model:value="form.password" :type="showPwd ? 'text' : 'password'" placeholder="请输入密码" size="large" @keyup.enter="handleLogin" :input-props="{autocomplete:'current-password'}">
              <template #suffix>
                <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
                  {{ showPwd ? '🙈' : '👁️' }}
                </button>
              </template>
            </n-input>
          </n-form-item>
          <n-button type="primary" block size="large" :loading="loading" @click="handleLogin" style="height:48px;font-size:16px;font-weight:600;">
            登 录
          </n-button>
        </n-form>
        <div class="form-extra">
          <n-button text type="primary" @click="$router.push('/forgot-password')">忘记密码？</n-button>
        </div>
        <div class="form-extra">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="$router.push('/register')">立即注册</n-button>
        </div>
        <div v-if="errorMsg" class="error-alert">
          <span>{{ errorIcon }}</span>
          <span>{{ errorMsg }}</span>
        </div>
        <div class="demo-hint">
          <n-divider>演示账号</n-divider>
          <n-tag type="info" size="small">admin</n-tag>
          <n-tag type="info" size="small" style="margin-left:6px;">123456</n-tag>
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
const formRef = ref<FormInst|null>(null); const loading = ref(false)
const showPwd = ref(false); const errorMsg = ref('')
const form = reactive({username:'',password:''})
const rules: FormRules = {
  username:[{required:true,message:'请输入用户名',trigger:'blur'}],
  password:[{required:true,message:'请输入密码',trigger:'blur'}],
}

const errorIcon = computed(() => {
  if (errorMsg.value.includes('不存在')) return '🚫'
  if (errorMsg.value.includes('密码')) return '🔑'
  if (errorMsg.value.includes('禁用')) return '⛔'
  return '⚠️'
})

async function handleLogin(){
  const v=await formRef.value?.validate().catch(()=>false); if(!v) return
  loading.value=true; errorMsg.value=''
  try {
    await authStore.login({username:form.username,password:form.password})
    message.success('登录成功')
    router.push((route.query.redirect as string)||'/assets')
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    const code = e?.response?.headers?.['x-error-code'] || ''
    if (detail) errorMsg.value = detail
    else if (e?.response?.status === 403) errorMsg.value = '账户已被禁用'
    else errorMsg.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { display:flex; height:100vh; }
.login-left {
  flex:1; background:linear-gradient(135deg,#0F0B1E 0%,#1A1230 40%,#2D1B69 100%);
  color:#e0e0f0; display:flex; flex-direction:column; justify-content:center;
  align-items:center; padding:60px; position:relative; overflow:hidden;
}
.login-left::before {
  content:''; position:absolute; top:-100px; right:-100px; width:300px; height:300px;
  background:rgba(99,102,241,.1); border-radius:50%;
}
.login-left::after {
  content:''; position:absolute; bottom:-80px; left:-80px; width:250px; height:250px;
  background:rgba(168,85,247,.08); border-radius:50%;
}
.left-inner { max-width:460px; position:relative; z-index:1; }
.logo-area { text-align:center; margin-bottom:40px; }
.logo-icon { font-size:64px; display:block; margin-bottom:12px; }
.logo-area h1 { font-size:28px; font-weight:700; color:#fff; margin:0 0 6px; }
.logo-area p { color:#a5b4fc; font-size:15px; margin:0; }
.feat { padding:12px 16px; margin-bottom:8px; border-radius:10px; background:rgba(255,255,255,.04); font-size:14px; color:#bcc8e0; display:flex; align-items:center; gap:10px; transition: all .25s; }
.feat:hover, .feat.active { background:rgba(99,102,241,.12); color:#c7d2fe; transform: translateX(4px); }
.feat span { font-size:20px; }
.left-footer { position:absolute; bottom:20px; color:#556; font-size:12px; }

.login-right { width:480px; display:flex; align-items:center; justify-content:center; padding:40px; background:#fff; }
.form-card { width:100%; max-width:380px; }
.form-card h2 { font-size:26px; font-weight:700; margin:0 0 4px; color:#1A1230; }
.form-sub { color:#888; margin:0 0 28px; font-size:14px; }
.form-extra { text-align:center; margin-top:12px; font-size:14px; color:#999; }
.demo-hint { text-align:center; margin-top:16px; }

.pwd-toggle {
  background: none; border: none; cursor: pointer; font-size: 18px;
  padding: 4px 8px; border-radius: 6px;
}
.pwd-toggle:hover { background: rgba(0,0,0,.06); }

.error-alert {
  display: flex; align-items: center; gap: 8px; margin-top: 16px;
  padding: 10px 14px; border-radius: 8px;
  background: rgba(220,38,38,.06); color: #DC2626;
  border: 1px solid rgba(220,38,38,.12);
  font-size: 14px; animation: fadeInUp 0.3s ease both;
}

.anim-scale-in { animation: scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both; }
@keyframes scaleIn { from { opacity: 0; transform: scale(.95); } to { opacity: 1; transform: scale(1); } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

[data-theme="dark"] .login-right { background:#12101A; }
[data-theme="dark"] .form-card h2 { color:#e8e8f0; }
[data-theme="dark"] .form-sub { color:#6B6580; }
[data-theme="dark"] .pwd-toggle:hover { background: rgba(255,255,255,.08); }
[data-theme="dark"] .login-left { background:linear-gradient(135deg,#080510 0%,#0F0B1E 40%,#1A1530 100%); }
[data-theme="dark"] .logo-area p { color:#818CF8; }
[data-theme="dark"] .left-footer { color:#4a4a5a; }
</style>
