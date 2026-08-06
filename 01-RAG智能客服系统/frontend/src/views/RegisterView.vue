<template>
  <div class="reg-page">
    <div class="bg-particles">
      <span v-for="i in 10" :key="i" class="particle" :style="{
        left: `${(i * 41 + 7) % 100}%`, top: `${(i * 59 + 11) % 100}%`,
        animationDelay: `${(i * 0.8) % 5}s`, animationDuration: `${4 + (i % 3) * 2.5}s`,
        width: `${5 + (i % 4) * 3}px`, height: `${5 + (i % 4) * 3}px`,
      }" />
    </div>
    <div class="reg-left">
      <div class="left-inner">
        <span class="logo-icon anim-float">✨</span>
        <h1 class="anim-fade-in-up">加入 RAG 知识库</h1>
        <p class="anim-fade-in-up anim-delay-1">注册即享 AI 智能商品问答</p>
        <div class="feat-list">
          <div class="feat anim-fade-in-up anim-delay-1"><span>🚀</span> 秒级响应</div>
          <div class="feat anim-fade-in-up anim-delay-2"><span>📚</span> 海量知识</div>
          <div class="feat anim-fade-in-up anim-delay-3"><span>🎯</span> 精准溯源</div>
          <div class="feat anim-fade-in-up anim-delay-4"><span>🔒</span> 数据安全</div>
        </div>
      </div>
    </div>
    <div class="reg-right">
      <div class="form-card anim-scale-in">
        <div class="form-header"><h2>创建账号 ✨</h2><p>填写信息完成注册</p></div>
        <div v-if="errorMsg" class="error-alert"><span class="error-icon">⚠️</span><span class="error-text">{{ errorMsg }}</span><button class="error-close" @click="errorMsg = ''">✕</button></div>
        <n-form ref="fr" :model="f" :rules="r" label-placement="top">
          <n-form-item label="用户名" path="u">
            <n-input v-model:value="f.u" placeholder="3-50个字符" size="large"><template #prefix><span class="ip-icon">👤</span></template></n-input>
          </n-form-item>
          <n-form-item label="邮箱（可选）" path="e">
            <n-input v-model:value="f.e" placeholder="your@email.com" size="large"><template #prefix><span class="ip-icon">📧</span></template></n-input>
          </n-form-item>
          <n-form-item label="密码" path="p">
            <n-input v-model:value="f.p" :type="showPwd ? 'text' : 'password'" placeholder="至少6位，建议包含字母+数字+符号" size="large">
              <template #prefix><span class="ip-icon">🔒</span></template>
              <template #suffix><button type="button" class="pwd-toggle" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁️' }}</button></template>
            </n-input>
            <div v-if="f.p" class="pw-strength"><div class="pw-bar"><div class="pw-fill" :style="pwStrength.style" /></div><span class="pw-label" :style="{ color: pwStrength.color }">{{ pwStrength.label }}</span><span class="pw-tip" v-if="pwStrength.level < 3">{{ pwStrength.tip }}</span></div>
          </n-form-item>
          <n-form-item label="确认密码" path="cp">
            <n-input v-model:value="f.cp" type="password" placeholder="再次输入密码" size="large">
              <template #prefix><span class="ip-icon">🔒</span></template>
              <template #suffix><span v-if="f.cp && f.p" class="pw-match">{{ f.cp === f.p ? '✅' : '❌' }}</span></template>
            </n-input>
          </n-form-item>
          <n-form-item path="agree"><n-checkbox v-model:checked="f.agree">我已阅读并同意<n-button text type="primary" size="tiny">服务条款</n-button>和<n-button text type="primary" size="tiny">隐私政策</n-button></n-checkbox></n-form-item>
          <n-button type="primary" block size="large" :loading="ld" @click="reg" class="reg-btn"><span v-if="!ld">注 册</span><span v-else>注册中…</span></n-button>
        </n-form>
        <div class="extra"><span>已有账号？</span><n-button text type="primary" @click="$router.push('/login')">去登录</n-button></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'; import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'; import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const router=useRouter();const auth=useAuthStore();const msg=useMessage()
const fr=ref<FormInst|null>(null);const ld=ref(false);const showPwd=ref(false);const errorMsg=ref('')
const f=reactive({u:'',e:'',p:'',cp:'',agree:false})
const r:FormRules={
  u:[{required:true,message:'请输入用户名'},{min:3,max:50,message:'3-50个字符'}],
  e:[{type:'email',message:'请输入正确的邮箱格式'}],
  p:[{required:true,message:'请输入密码'},{min:6,message:'密码至少6位'}],
  cp:[{required:true,message:'请确认密码'},{validator:(_:any,v:string)=>v===f.p,message:'两次密码不一致',trigger:'blur'}],
  agree:[{validator:(_:any,v:boolean)=>v===true,message:'请同意服务条款',trigger:'change'}],
}
const pwStrength = computed(()=>{
  const p=f.p; if(!p) return {level:0,label:'',color:'',style:{width:'0%'},tip:''}
  let score=0; if(p.length>=6)score++; if(p.length>=8)score++; if(p.length>=12)score++; if(/[a-z]/.test(p)&&/[A-Z]/.test(p))score++; if(/[0-9]/.test(p))score++; if(/[^A-Za-z0-9]/.test(p))score++
  if(score<=2)return {level:1,label:'弱',color:'#EF4444',style:{width:'25%',background:'#EF4444'},tip:'建议使用8位以上字母+数字+符号的组合'}
  if(score<=4)return {level:2,label:'中等',color:'#F59E0B',style:{width:'55%',background:'#F59E0B'},tip:'再添加大小写字母和符号会更安全'}
  return {level:3,label:'强',color:'#10B981',style:{width:'100%',background:'#10B981'},tip:''}
})
async function reg(){
  const v=await fr.value?.validate().catch(()=>false);if(!v)return
  errorMsg.value='';ld.value=true
  try{const ok=await auth.register({username:f.u,password:f.p,email:f.e||undefined});ld.value=false;if(ok){msg.success('注册成功！请登录');router.push('/login')}else errorMsg.value='注册失败，用户名可能已存在'}
  catch(e:any){ld.value=false;const detail=e?.response?.data?.detail||'';errorMsg.value=detail||'注册失败，请稍后重试';const card=document.querySelector('.form-card');if(card){card.classList.add('shake');setTimeout(()=>card.classList.remove('shake'),500)}}
}
</script>

<style scoped>
.reg-page{display:flex;height:100vh;position:relative;overflow:hidden;}
.bg-particles{position:absolute;inset:0;pointer-events:none;z-index:0;overflow:hidden;}
.particle{position:absolute;background:var(--primary);border-radius:50%;opacity:0.06;animation:particle-float 6s ease-in-out infinite;}
.reg-left{flex:1;background:linear-gradient(135deg,#0F172A 0%,#1E3A5F 100%);display:flex;align-items:center;justify-content:center;padding:60px;position:relative;overflow:hidden;}
.reg-left::before{content:'';position:absolute;top:-100px;right:-100px;width:300px;height:300px;background:radial-gradient(circle,rgba(37,99,235,.12),transparent 70%);border-radius:50%;animation:pulse-glow 4.5s ease-in-out infinite;}
.reg-left::after{content:'';position:absolute;bottom:-80px;left:-80px;width:260px;height:260px;background:radial-gradient(circle,rgba(37,99,235,.08),transparent 70%);border-radius:50%;animation:pulse-glow 5.5s ease-in-out infinite reverse;}
.left-inner{text-align:center;color:#e0e0f0;position:relative;z-index:1;}
.logo-icon{font-size:72px;display:block;margin-bottom:16px;}
.left-inner h1{font-size:30px;font-weight:800;color:#fff;margin:0 0 8px;}
.left-inner>p{color:#8899bb;margin:0 0 36px;font-size:15px;}
.feat-list{display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:340px;margin:0 auto;}
.feat{padding:12px 16px;border-radius:12px;background:rgba(255,255,255,.06);font-size:14px;color:#bcc8e0;display:flex;align-items:center;gap:8px;backdrop-filter:blur(8px);transition:all 0.3s var(--ease-smooth);border:1px solid rgba(255,255,255,.03);cursor:default;}
.feat:hover{transform:translateY(-3px);background:rgba(37,99,235,.12);border-color:rgba(37,99,235,.2);color:#e0e8f8;}
.feat span{font-size:20px;}
.reg-right{width:520px;display:flex;align-items:center;justify-content:center;padding:40px;background:radial-gradient(ellipse at 20% 50%,rgba(37,99,235,.03) 0%,transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(37,99,235,.02) 0%,transparent 50%),#fff;position:relative;z-index:1;}
.form-card{width:100%;max-width:420px;background:var(--glass-bg);border:1px solid var(--glass-border);backdrop-filter:blur(var(--glass-blur));-webkit-backdrop-filter:blur(var(--glass-blur));border-radius:var(--radius-xl);padding:36px 32px;box-shadow:var(--glass-shadow);}
.form-card.shake{animation:shake 0.5s var(--ease-smooth);}
@keyframes shake{0%,100%{transform:translateX(0)}10%,50%,90%{transform:translateX(-4px)}30%,70%{transform:translateX(4px)}}
.form-header{text-align:center;margin-bottom:24px;}
.form-header h2{font-size:28px;font-weight:800;margin:0 0 6px;color:var(--text-primary);}
.form-header p{color:var(--text-secondary);margin:0;font-size:14px;}
.error-alert{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:var(--radius-sm);margin-bottom:20px;font-size:14px;background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;animation:fadeInUp 0.3s var(--ease-smooth) both;}
.error-close{background:none;border:none;cursor:pointer;font-size:14px;padding:2px 6px;border-radius:4px;color:inherit;opacity:0.6;margin-left:auto;}
.error-close:hover{opacity:1;}
.ip-icon{font-size:16px;opacity:0.5;}
.pwd-toggle{background:none;border:none;cursor:pointer;font-size:18px;padding:4px 8px;border-radius:6px;transition:all 0.15s;line-height:1;}
.pwd-toggle:hover{background:rgba(0,0,0,.06);}
.pw-strength{display:flex;align-items:center;gap:8px;margin-top:8px;flex-wrap:wrap;}
.pw-bar{flex:1;min-width:80px;height:4px;background:var(--border-light);border-radius:2px;overflow:hidden;}
.pw-fill{height:100%;border-radius:2px;transition:width 0.4s var(--ease-smooth),background 0.4s var(--ease-smooth);}
.pw-label{font-size:12px;font-weight:700;white-space:nowrap;}
.pw-tip{width:100%;font-size:11px;color:var(--text-muted);margin-top:2px;}
.reg-btn{height:50px!important;font-size:16px!important;font-weight:700!important;border-radius:14px!important;background:linear-gradient(135deg,#3B82F6,#2563EB,#1D4ED8)!important;border:none!important;position:relative;overflow:hidden;letter-spacing:2px;}
.reg-btn::after{content:'';position:absolute;inset:0;background:linear-gradient(110deg,transparent 0%,rgba(255,255,255,.25) 45%,rgba(255,255,255,.35) 50%,rgba(255,255,255,.25) 55%,transparent 100%);background-size:200% 100%;animation:shimmer 3s ease-in-out infinite;pointer-events:none;}
.reg-btn:hover{transform:translateY(-1px);box-shadow:0 8px 24px rgba(37,99,235,.35)!important;}
.reg-btn:active{transform:translateY(0);}
.extra{text-align:center;margin-top:24px;font-size:14px;color:var(--text-secondary);}
[data-theme="dark"] .reg-right{background:radial-gradient(ellipse at 20% 50%,rgba(37,99,235,.04) 0%,transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(37,99,235,.03) 0%,transparent 50%),#0F172A;}
[data-theme="dark"] .reg-left{background:linear-gradient(135deg,#0A0A14 0%,#0F1A2E 35%,#1E3A5F 100%);}
[data-theme="dark"] .left-inner>p{color:#64748B;}
[data-theme="dark"] .feat{color:#94A3B8;background:rgba(255,255,255,.06);}
[data-theme="dark"] .feat:hover{background:rgba(37,99,235,.15);color:#BCC8E0;}
[data-theme="dark"] .form-header h2{color:#E8E8F0;}
[data-theme="dark"] .error-alert{background:rgba(220,38,38,.12);border-color:rgba(220,38,38,.2);}
[data-theme="dark"] .pwd-toggle:hover{background:rgba(255,255,255,.08);}
@media(max-width:768px){.reg-page{flex-direction:column;}.reg-left{flex:none;padding:36px 24px;}.reg-right{width:100%;padding:20px;}.form-card{padding:28px 20px;}.logo-icon{font-size:48px;}.left-inner h1{font-size:22px;}}
</style>
