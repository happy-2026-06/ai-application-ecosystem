<template>
  <div class="reg-page">
    <!-- Left: Brand panel -->
    <div class="reg-left">
      <div class="left-inner">
        <div class="brand-badge">AI 模型工厂</div>
        <span class="logo-icon">🧠</span>
        <h1>加入模型工厂</h1>
        <p>注册账号，开始定制你的专属 AI 模型</p>
        <div class="feat-list">
          <div class="feat"><span>🧠</span> QLoRA 微调</div>
          <div class="feat"><span>📊</span> 训练可视化</div>
          <div class="feat"><span>🔬</span> A/B 对比</div>
          <div class="feat"><span>🚀</span> 一键部署</div>
        </div>
      </div>
    </div>
    <!-- Right: Form -->
    <div class="reg-right">
      <div class="form-card">
        <h2>创建账号 ✨</h2>
        <p class="sub">填写信息完成注册</p>
        <n-form ref="fr" :model="f" :rules="r" label-placement="top">
          <n-form-item label="用户名" path="u"><n-input v-model:value="f.u" placeholder="3-50个字符" size="large" /></n-form-item>
          <n-form-item label="邮箱（可选）" path="e"><n-input v-model:value="f.e" placeholder="your@email.com" size="large" /></n-form-item>
          <n-form-item label="密码" path="p"><n-input v-model:value="f.p" type="password" placeholder="至少6位" size="large" /></n-form-item>
          <n-form-item label="确认密码" path="cp"><n-input v-model:value="f.cp" type="password" placeholder="再次输入" size="large" /></n-form-item>
          <n-button type="primary" block size="large" :loading="ld" @click="reg" style="height:48px;font-size:16px;font-weight:600;border-radius:14px;background:linear-gradient(135deg,#f59e0b,#d97706);border:none;">注 册</n-button>
        </n-form>
        <div class="extra"><span>已有账号？</span><n-button text type="primary" @click="$router.push('/login')" style="color:#f59e0b">去登录</n-button></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'; import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'; import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
const router=useRouter(); const auth=useAuthStore(); const msg=useMessage()
const fr=ref<FormInst|null>(null); const ld=ref(false)
const f=reactive({u:'',e:'',p:'',cp:''})
const r:FormRules={u:[{required:true,message:'请输入用户名'},{min:3,max:50,message:'3-50字符'}],p:[{required:true,min:6,message:'至少6位'}],cp:[{required:true,message:'请确认密码'},{validator:(_:any,v:string)=>v===f.p,message:'两次不一致',trigger:'blur'}]}
async function reg(){const v=await fr.value?.validate().catch(()=>false);if(!v)return;ld.value=true;const ok=await auth.register({username:f.u,password:f.p,email:f.e||undefined});ld.value=false;if(ok){msg.success('注册成功');router.push('/login')}else msg.error('注册失败，用户名可能已存在')}
</script>

<style scoped>
.reg-page{display:flex;height:100vh;}
.reg-left{flex:1;background:linear-gradient(160deg,#fafaf9 0%,#fffbeb 50%,#fef3c7 100%);display:flex;align-items:center;justify-content:center;padding:60px;}
.left-inner{text-align:center;color:#1e293b;max-width:420px;}
.brand-badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;color:#d97706;background:rgba(245,158,11,.1);letter-spacing:0.5px;margin-bottom:20px;}
.logo-icon{font-size:64px;display:block;margin-bottom:12px;}
.left-inner h1{font-size:28px;font-weight:700;color:#0f172a;margin:0 0 4px;}
.left-inner p{color:#64748b;margin:0 0 30px;font-size:15px;}
.feat-list{display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:320px;margin:0 auto;}
.feat{padding:10px 14px;border-radius:8px;background:rgba(245,158,11,.06);font-size:14px;color:#78350f;display:flex;align-items:center;gap:6px;}
.reg-right{width:480px;display:flex;align-items:center;justify-content:center;padding:40px;background:#fff;}
.form-card{width:100%;max-width:380px;}
.form-card h2{font-size:26px;font-weight:700;margin:0 0 4px;color:#1a1a2e;}
.sub{color:#888;margin:0 0 24px;}
.extra{text-align:center;margin-top:20px;font-size:14px;color:#999;}
[data-theme="dark"] .reg-right{background:#16161d;}
[data-theme="dark"] .form-card h2{color:#eee;}
[data-theme="dark"] .reg-left{background:linear-gradient(160deg,#1c1917 0%,#292524 100%)}
[data-theme="dark"] .left-inner h1{color:#f5f5f4}
[data-theme="dark"] .left-inner p{color:#a8a29e}
[data-theme="dark"] .feat{background:rgba(245,158,11,.1);color:#fcd34d}
</style>
