<template>
  <div class="login-page">
    <!-- Left: Product intro -->
    <div class="login-left">
      <div class="left-inner">
        <div class="logo-area">
          <span class="logo-icon">🎬</span>
          <h1>AI短视频脚本工坊</h1>
          <p>专业的短视频分镜脚本生成引擎</p>
        </div>
        <div class="feature-list">
          <div class="feat"><span>📋</span> 分镜脚本 — 镜号/时长/画面/口播/字幕一键生成</div>
          <div class="feat"><span>🎤</span> 口播话术 — 黄金3秒钩子 + 痛点引爆 + 行动号召</div>
          <div class="feat"><span>🎥</span> 拍摄建议 — B-roll素材/转场效果/字幕样式</div>
          <div class="feat"><span>📊</span> 平台适配 — 抖音/小红书/B站/视频号/快手五平台</div>
        </div>
      </div>
      <div class="left-footer">面试项目 · Vue3 + FastAPI + LangChain + DeepSeek</div>
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
          <n-button type="primary" block size="large" :loading="loading" @click="handleLogin" :style="{height:'48px',fontSize:'16px',fontWeight:600}">
            登 录
          </n-button>
        </n-form>
        <div class="form-extra">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="$router.push('/register')">立即注册</n-button>
        </div>
        <div class="demo-hint">
          <n-divider>演示账号</n-divider>
          <n-tag type="warning" size="small">admin</n-tag>
          <n-tag type="warning" size="small" style="margin-left:6px;">admin123</n-tag>
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
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
async function handleLogin() {
  const v = await formRef.value?.validate().catch(() => false); if (!v) return
  loading.value = true
  const ok = await authStore.login({ username: form.username, password: form.password })
  loading.value = false
  if (ok) { message.success('登录成功'); router.push((route.query.redirect as string) || '/studio') }
  else message.error('用户名或密码错误')
}
</script>

<style scoped>
.login-page { display: flex; height: 100vh; }
.login-left {
  flex: 1; background: linear-gradient(135deg, #1A1A24 0%, #2A2A38 40%, #3A3020 100%);
  color: #e0e0f0; display: flex; flex-direction: column; justify-content: center;
  align-items: center; padding: 60px; position: relative; overflow: hidden;
}
.login-left::before {
  content: ''; position: absolute; top: -100px; right: -100px; width: 300px; height: 300px;
  background: rgba(200,169,81,.06); border-radius: 50%;
}
.login-left::after {
  content: ''; position: absolute; bottom: -80px; left: -80px; width: 250px; height: 250px;
  background: rgba(200,169,81,.06); border-radius: 50%;
}
.left-inner { max-width: 460px; position: relative; z-index: 1; }
.logo-area { text-align: center; margin-bottom: 40px; }
.logo-icon { font-size: 64px; display: block; margin-bottom: 12px; }
.logo-area h1 { font-size: 28px; font-weight: 700; color: #fff; margin: 0 0 6px; }
.logo-area p { color: #a09880; font-size: 15px; margin: 0; }
.feat {
  padding: 12px 16px; margin-bottom: 8px; border-radius: 10px;
  background: rgba(255,255,255,.04); font-size: 14px; color: #c8c0b0;
  display: flex; align-items: center; gap: 10px;
  backdrop-filter: blur(8px); transition: transform .2s;
}
.feat:hover { transform: translateX(6px); background: rgba(200,169,81,.1); }
.feat span { font-size: 20px; }
.left-footer { position: absolute; bottom: 20px; color: #665; font-size: 12px; }

.login-right {
  width: 480px; display: flex; align-items: center; justify-content: center;
  padding: 40px; background: #fff;
}
.form-card {
  width: 100%; max-width: 380px; padding: 32px;
  border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.form-card h2 { font-size: 26px; font-weight: 700; margin: 0 0 4px; color: #2C2C3A; }
.form-sub { color: #888; margin: 0 0 28px; font-size: 14px; }
.form-extra { text-align: center; margin-top: 20px; font-size: 14px; color: #999; }
.demo-hint { text-align: center; margin-top: 20px; }

/* Dark mode */
[data-theme="dark"] .login-right { background: #18181D; }
[data-theme="dark"] .form-card h2 { color: #eee; }
[data-theme="dark"] .form-sub { color: #aaa; }
[data-theme="dark"] .form-extra { color: #aaa; }
[data-theme="dark"] .feat { color: #b0a890; background: rgba(255,255,255,.06); }
[data-theme="dark"] .feat:hover { background: rgba(200,169,81,.15); }
[data-theme="dark"] .left-footer { color: #64748B; }
[data-theme="dark"] .logo-area p { color: #8888a0; }
</style>
