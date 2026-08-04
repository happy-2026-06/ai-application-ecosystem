<template>
  <div class="reg-page">
    <div class="reg-left">
      <div class="left-inner">
        <span class="logo-icon">✍️</span>
        <h1>加入创作社区</h1>
        <p>注册即享 AI 爆款内容生成</p>
        <div class="feat-list">
          <div class="feat"><span>🔥</span> 爆款标题</div><div class="feat"><span>🎬</span> 视频脚本</div>
          <div class="feat"><span>📝</span> 图文文案</div><div class="feat"><span>📊</span> 数据分析</div>
        </div>
      </div>
    </div>
    <div class="reg-right">
      <div class="form-card">
        <h2>创建账号 ✨</h2>
        <p class="sub">填写信息完成注册</p>
        <n-form ref="fr" :model="f" :rules="r" label-placement="top">
          <n-form-item label="用户名" path="u"><n-input v-model:value="f.u" placeholder="3-50个字符" size="large" /></n-form-item>
          <n-form-item label="邮箱（可选）" path="e"><n-input v-model:value="f.e" placeholder="your@email.com" size="large" /></n-form-item>
          <n-form-item label="密码" path="p"><n-input v-model:value="f.p" type="password" placeholder="至少6位" size="large" /></n-form-item>
          <n-form-item label="确认密码" path="cp"><n-input v-model:value="f.cp" type="password" placeholder="再次输入" size="large" /></n-form-item>
          <n-button type="primary" block size="large" :loading="ld" @click="reg" style="height:48px;font-size:16px;font-weight:600;">注 册</n-button>
        </n-form>
        <div class="extra"><span>已有账号？</span><n-button text type="primary" @click="$router.push('/login')">去登录</n-button></div>
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
.reg-left{flex:1;background:linear-gradient(135deg,#1A0F2E 0%,#3D1525 50%,#FF6B35 100%);display:flex;align-items:center;justify-content:center;padding:60px;position:relative;overflow:hidden;}
.reg-left::before{content:'';position:absolute;top:-80px;right:-80px;width:240px;height:240px;background:rgba(255,107,53,.12);border-radius:50%;}
.reg-left::after{content:'';position:absolute;bottom:-60px;left:-60px;width:200px;height:200px;background:rgba(225,29,72,.10);border-radius:50%;}
.left-inner{text-align:center;color:#e0e0f0;position:relative;z-index:1;}
.logo-icon{font-size:72px;display:block;margin-bottom:12px;}
.left-inner h1{font-size:32px;font-weight:800;color:#fff;margin:0 0 4px;}
.left-inner p{color:#ffc4a8;margin:0 0 30px;}
.feat-list{display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:320px;margin:0 auto;}
.feat{padding:10px 14px;border-radius:10px;background:rgba(255,255,255,.06);font-size:15px;color:#d4c8e0;display:flex;align-items:center;gap:6px;transition:all .25s;backdrop-filter:blur(4px);line-height:1.6;}
.feat:hover{background:rgba(255,107,53,.10);transform:translateX(4px);}
.reg-right{width:480px;display:flex;align-items:center;justify-content:center;padding:40px;background:#FFFBF8;}
.form-card{width:100%;max-width:380px;background:#fff;border-radius:16px;padding:32px 28px;box-shadow:0 4px 24px rgba(0,0,0,.06);}
.form-card h2{font-size:28px;font-weight:700;margin:0 0 4px;color:#1A0F2E;}
.sub{color:#888;margin:0 0 24px;}
.extra{text-align:center;margin-top:20px;font-size:14px;color:#999;}

[data-theme="dark"] .reg-right{background:#18181D;}
[data-theme="dark"] .form-card{background:#1e1e28;box-shadow:0 4px 24px rgba(0,0,0,.3);}
[data-theme="dark"] .form-card h2{color:#eee;}
[data-theme="dark"] .reg-left{background:linear-gradient(135deg,#0A0614 0%,#1A0F1E 50%,#3D1525 100%);}
[data-theme="dark"] .left-inner p{color:#8a7a8a;}
[data-theme="dark"] .feat{color:#9a8aaa;}
[data-theme="dark"] .feat:hover{background:rgba(255,107,53,.08);}

@media (max-width: 768px) {
  .reg-page{flex-direction:column;}
  .reg-left{flex:none;padding:40px 20px;}
  .reg-right{width:100%;}
}
</style>
