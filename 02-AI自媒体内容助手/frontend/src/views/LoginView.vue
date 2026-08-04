<template>
  <div class="login-page">
    <!-- Left: Product intro -->
    <div class="login-left">
      <div class="left-inner">
        <div class="logo-area">
          <span class="logo-icon">✍️</span>
          <h1>AI自媒体内容助手</h1>
          <p>爆款标题 · 视频脚本 · 图文文案 — 一键生成</p>
        </div>
        <div class="feature-list">
          <div class="feat"><span>🔥</span> 爆款标题 — 5大平台风格适配，高点击率标题模板</div>
          <div class="feat"><span>🎬</span> 视频脚本 — 完整口播分镜脚本，可直接拍摄使用</div>
          <div class="feat"><span>📝</span> 图文文案 — 小红书/公众号风格种草笔记</div>
          <div class="feat"><span>💡</span> 发布建议 — 最佳发布时间+互动话术+封面建议</div>
        </div>
      </div>
      <div class="left-footer">AI自媒体内容助手 · LangChain + FastAPI + Vue 3</div>
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
          <n-tag type="warning" size="small" round>admin</n-tag>
          <n-tag type="error" size="small" round style="margin-left:6px;">123456</n-tag>
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
  if(ok){message.success('登录成功');router.push((route.query.redirect as string)||'/home')}
  else message.error('用户名或密码错误')
}
</script>

<style scoped>
.login-page { display:flex; height:100vh; }
.login-left {
  flex:1; background:linear-gradient(135deg,#1A0F2E 0%,#3D1525 50%,#FF6B35 100%);
  color:#e0e0f0; display:flex; flex-direction:column; justify-content:center;
  align-items:center; padding:60px; position:relative; overflow:hidden;
}
.login-left::before {
  content:''; position:absolute; top:-100px; right:-100px; width:300px; height:300px;
  background:rgba(255,107,53,.12); border-radius:50%;
}
.login-left::after {
  content:''; position:absolute; bottom:-80px; left:-80px; width:250px; height:250px;
  background:rgba(225,29,72,.10); border-radius:50%;
}
.left-inner { max-width:460px; position:relative; z-index:1; }
.logo-area { text-align:center; margin-bottom:40px; }
.logo-icon { font-size:72px; display:block; margin-bottom:12px; }
.logo-area h1 { font-size:32px; font-weight:800; color:#fff; margin:0 0 6px; }
.logo-area p { color:#ffc4a8; font-size:15px; margin:0; }
.feat { padding:12px 16px; margin-bottom:8px; border-radius:10px; background:rgba(255,255,255,.04); font-size:15px; color:#d4c8e0; display:flex; align-items:center; gap:10px; transition: all .25s; backdrop-filter: blur(4px); line-height:1.6; }
.feat:hover { background: rgba(255,107,53,.10); transform: translateX(4px); }
.feat span { font-size:20px; }
.left-footer { position:absolute; bottom:20px; color:rgba(255,255,255,.35); font-size:12px; }

.login-right { width:480px; display:flex; align-items:center; justify-content:center; padding:40px; background:#fff; }
.form-card { width:100%; max-width:380px; background: #fff; border-radius: 16px; padding: 32px 28px; box-shadow: 0 4px 24px rgba(0,0,0,.06); }
.form-card h2 { font-size:28px; font-weight:700; margin:0 0 4px; color:#1A0F2E; }
.form-sub { color:#888; margin:0 0 28px; font-size:14px; }
.form-extra { text-align:center; margin-top:20px; font-size:14px; color:#999; }
.demo-hint { text-align:center; margin-top:16px; }

[data-theme="dark"] .login-right { background:#18181D; }
[data-theme="dark"] .form-card { background: #1e1e28; box-shadow: 0 4px 24px rgba(0,0,0,.3); }
[data-theme="dark"] .form-card h2 { color:#eee; }
[data-theme="dark"] .login-left { background: linear-gradient(135deg,#0A0614 0%,#1A0F1E 50%,#3D1525 100%); }
[data-theme="dark"] .logo-area p { color:#8a7a8a; }
[data-theme="dark"] .feat { color:#9a8aaa; }
[data-theme="dark"] .feat:hover { background: rgba(255,107,53,.08); }

@media (max-width: 768px) {
  .login-page { flex-direction: column; }
  .login-left { flex: none; padding: 40px 20px; }
  .login-right { width: 100%; }
}
</style>
