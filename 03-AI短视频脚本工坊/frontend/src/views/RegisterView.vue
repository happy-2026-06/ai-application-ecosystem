<template>
  <div class="reg-page">
    <div class="reg-left">
      <div class="left-inner">
        <span class="logo-icon">🎬</span>
        <h1>加入脚本工坊</h1>
        <p>注册即可使用 AI 分镜脚本生成</p>
        <div class="feat-list">
          <div class="feat"><span>📋</span> 分镜脚本</div>
          <div class="feat"><span>🎤</span> 口播话术</div>
          <div class="feat"><span>🎥</span> 拍摄建议</div>
          <div class="feat"><span>📊</span> 平台适配</div>
        </div>
      </div>
    </div>
    <div class="reg-right">
      <div class="form-card">
        <h2>创建账号 ✨</h2>
        <p class="sub">填写信息完成注册</p>
        <n-form ref="fr" :model="f" :rules="r" label-placement="top">
          <n-form-item label="用户名" path="u">
            <n-input v-model:value="f.u" placeholder="3-50个字符" size="large" />
          </n-form-item>
          <n-form-item label="邮箱（可选）" path="e">
            <n-input v-model:value="f.e" placeholder="your@email.com" size="large" />
          </n-form-item>
          <n-form-item label="密码" path="p">
            <n-input v-model:value="f.p" type="password" placeholder="至少6位" size="large" />
          </n-form-item>
          <n-form-item label="确认密码" path="cp">
            <n-input v-model:value="f.cp" type="password" placeholder="再次输入" size="large" />
          </n-form-item>
          <n-button type="primary" block size="large" :loading="ld" @click="reg" :style="{height:'48px',fontSize:'16px',fontWeight:600}">
            注 册
          </n-button>
        </n-form>
        <div class="extra">
          <span>已有账号？</span>
          <n-button text type="primary" @click="$router.push('/login')">去登录</n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()
const fr = ref<FormInst | null>(null)
const ld = ref(false)

const f = reactive({ u: '', e: '', p: '', cp: '' })

function validatePass(rule: any, value: string) {
  return value === f.p
}

const r: FormRules = {
  u: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
  ],
  e: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  p: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  cp: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, message: '两次密码不一致', trigger: 'blur' },
  ],
}

async function reg() {
  const v = await fr.value?.validate().catch(() => false)
  if (!v) return
  ld.value = true
  const ok = await authStore.register({ username: f.u, email: f.e || undefined, password: f.p })
  ld.value = false
  if (ok) {
    message.success('注册成功！请登录')
    router.push('/login')
  } else {
    message.error('注册失败，用户名可能已存在')
  }
}
</script>

<style scoped>
.reg-page { display: flex; height: 100vh; }
.reg-left {
  flex: 1; background: linear-gradient(135deg, #1A1A24 0%, #2A2A38 40%, #3A3020 100%);
  color: #e0e0f0; display: flex; flex-direction: column;
  justify-content: center; align-items: center; padding: 60px;
  position: relative; overflow: hidden;
}
.reg-left::before {
  content: ''; position: absolute; top: -80px; right: -80px; width: 260px; height: 260px;
  background: rgba(200,169,81,.05); border-radius: 50%;
}
.left-inner { max-width: 420px; text-align: center; position: relative; z-index: 1; }
.logo-icon { font-size: 64px; display: block; margin-bottom: 12px; }
.left-inner h1 { font-size: 28px; font-weight: 700; color: #fff; margin: 0 0 6px; }
.left-inner p { color: #a09880; font-size: 15px; margin: 0 0 32px; }
.feat-list { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
.feat {
  padding: 10px 18px; border-radius: 10px;
  background: rgba(255,255,255,.05); font-size: 14px;
  color: #d0c8b8; display: flex; align-items: center; gap: 8px;
  transition: all .2s;
}
.feat:hover { background: rgba(200,169,81,.12); transform: translateY(-2px); }
.feat span { font-size: 18px; }

.reg-right {
  width: 480px; display: flex; align-items: center; justify-content: center;
  padding: 40px; background: #fff;
}
.form-card {
  width: 100%; max-width: 380px; padding: 32px;
  border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.form-card h2 { font-size: 26px; font-weight: 700; margin: 0 0 4px; color: #2C2C3A; }
.sub { color: #888; margin: 0 0 28px; font-size: 14px; }
.extra { text-align: center; margin-top: 20px; font-size: 14px; color: #999; }

/* Dark mode */
[data-theme="dark"] .reg-right { background: #18181D; }
[data-theme="dark"] .form-card h2 { color: #eee; }
[data-theme="dark"] .sub { color: #aaa; }
[data-theme="dark"] .extra { color: #aaa; }
[data-theme="dark"] .feat { color: #b0a890; background: rgba(255,255,255,.06); }
[data-theme="dark"] .feat:hover { background: rgba(200,169,81,.15); }
[data-theme="dark"] .left-inner p { color: #8888a0; }
</style>
