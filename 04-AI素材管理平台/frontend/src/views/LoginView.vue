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
          <div class="feat"><span>🏷️</span> AI自动打标 — 上传素材自动生成标签和描述</div>
          <div class="feat"><span>🔍</span> 多模态检索 — 文本搜图/以图搜图/标签筛选</div>
          <div class="feat"><span>📁</span> 版本管理 — 素材版本追踪，随时回溯</div>
          <div class="feat"><span>👥</span> 权限控制 — 多角色权限，团队协作</div>
        </div>
      </div>
      <div class="left-footer">面试项目 · Vue3 + FastAPI + LangChain + CLIP</div>
    </div>

    <!-- Right: Login form -->
    <div class="login-right">
      <div class="form-card">
        <h2>欢迎回来 👋</h2>
        <p class="form-sub">登录你的账号开始使用</p>
        <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
          <n-form-item label="用户名" path="username">
            <n-input v-model:value="form.username" placeholder="请输入用户名" size="large" :input-props="{autocomplete:'username'}" />
          </n-form-item>
          <n-form-item label="密码" path="password">
            <n-input v-model:value="form.password" type="password" placeholder="请输入密码" size="large" @keyup.enter="handleLogin" :input-props="{autocomplete:'current-password'}" />
          </n-form-item>
          <n-button type="primary" block size="large" :loading="loading" @click="handleLogin" style="height:48px;font-size:16px;font-weight:600;">
            登 录
          </n-button>
        </n-form>
        <div class="form-extra">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="$router.push('/register')">立即注册</n-button>
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
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter(); const route = useRoute()
const authStore = useAuthStore(); const message = useMessage()
const formRef = ref<FormInst|null>(null); const loading = ref(false)
const form = reactive({username:'',password:''})
const rules: FormRules = {
  username:[{required:true,message:'请输入用户名',trigger:'blur'}],
  password:[{required:true,message:'请输入密码',trigger:'blur'}],
}
async function handleLogin(){
  const v=await formRef.value?.validate().catch(()=>false); if(!v) return
  loading.value=true
  const ok=await authStore.login({username:form.username,password:form.password})
  loading.value=false
  if(ok){message.success('登录成功');router.push((route.query.redirect as string)||'/assets')}
  else message.error('用户名或密码错误')
}
</script>

<style scoped>
.login-page { display:flex; height:100vh; }
.login-left {
  flex:1; background:linear-gradient(135deg,#1a1a2e 0%,#16213e 40%,#0f3460 100%);
  color:#e0e0f0; display:flex; flex-direction:column; justify-content:center;
  align-items:center; padding:60px; position:relative; overflow:hidden;
}
.login-left::before {
  content:''; position:absolute; top:-100px; right:-100px; width:300px; height:300px;
  background:rgba(102,126,234,.1); border-radius:50%;
}
.login-left::after {
  content:''; position:absolute; bottom:-80px; left:-80px; width:250px; height:250px;
  background:rgba(124,58,237,.08); border-radius:50%;
}
.left-inner { max-width:460px; position:relative; z-index:1; }
.logo-area { text-align:center; margin-bottom:40px; }
.logo-icon { font-size:64px; display:block; margin-bottom:12px; }
.logo-area h1 { font-size:28px; font-weight:700; color:#fff; margin:0 0 6px; }
.logo-area p { color:#8899bb; font-size:15px; margin:0; }
.feat { padding:12px 16px; margin-bottom:8px; border-radius:10px; background:rgba(255,255,255,.04); font-size:14px; color:#bcc8e0; display:flex; align-items:center; gap:10px; }
.feat span { font-size:20px; }
.left-footer { position:absolute; bottom:20px; color:#556; font-size:12px; }

.login-right { width:480px; display:flex; align-items:center; justify-content:center; padding:40px; background:#fff; }
.form-card { width:100%; max-width:380px; }
.form-card h2 { font-size:26px; font-weight:700; margin:0 0 4px; color:#1a1a2e; }
.form-sub { color:#888; margin:0 0 28px; font-size:14px; }
.form-extra { text-align:center; margin-top:20px; font-size:14px; color:#999; }
.demo-hint { text-align:center; margin-top:16px; }

[data-theme="dark"] .login-right { background:#16161d; }
[data-theme="dark"] .form-card h2 { color:#eee; }
</style>
