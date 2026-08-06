<template>
  <div class="set-page">
    <div class="page-header">
      <h2>⚙️ 个人中心</h2>
      <p>管理你的账户信息和偏好设置</p>
    </div>

    <!-- Avatar -->
    <div class="set-card">
      <div class="card-label">🎭 选择头像</div>
      <p class="card-desc">点击即可切换</p>
      <div class="avatar-grid">
        <div v-for="e in avatars" :key="e" class="av-item" :class="{sel:authStore.avatar===e}" @click="authStore.setAvatar(e)">{{ e }}</div>
      </div>
    </div>

    <!-- Display Name -->
    <div class="set-card">
      <div class="card-label">✏️ 显示名称</div>
      <p class="card-desc">会显示在侧边栏和聊天中</p>
      <n-space vertical>
        <n-input v-model:value="displayName" placeholder="输入昵称" size="large" maxlength="20" style="max-width:360px;" />
        <n-button type="primary" @click="saveName" :loading="sn">保存名称</n-button>
      </n-space>
    </div>

    <!-- Password -->
    <div class="set-card">
      <div class="card-label">🔒 修改密码</div>
      <n-form ref="pf" :model="pfm" :rules="pfr" label-placement="top" style="max-width:360px;">
        <n-form-item label="旧密码" path="op"><n-input v-model:value="pfm.op" type="password" /></n-form-item>
        <n-form-item label="新密码" path="np"><n-input v-model:value="pfm.np" type="password" /></n-form-item>
        <n-form-item label="确认密码" path="cp"><n-input v-model:value="pfm.cp" type="password" /></n-form-item>
        <n-button type="primary" @click="chpwd" :loading="sp">修改密码</n-button>
      </n-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'

const authStore=useAuthStore(); const message=useMessage()
const displayName=ref(authStore.user?.display_name||authStore.user?.username||'')
const sn=ref(false); const sp=ref(false); const pf=ref<FormInst|null>(null)
const avatars=['🐱','🐶','🐼','🐨','🦊','🐰','🐸','🐵','🐥','🦄','🐙','🦋','🐬','🦉','🐯','🐮','🐷','🐭','🐹','🐻','🐧','🐤','🦆','🦅','🐺','🐗','🐴','🦌','🐢','🐊','😊','😎','🤩','🥳','😇','🤖','👻','💩','👽','🎃']
const pfm=reactive({op:'',np:'',cp:''})
const pfr:FormRules={op:[{required:true,message:'请输入旧密码'}],np:[{required:true,min:6,message:'至少6位'}],cp:[{required:true,message:'请确认密码'},{validator:(_r:any,v:string)=>v===pfm.np,message:'两次不一致',trigger:'blur'}]}
async function saveName(){if(!displayName.value.trim()){message.warning('名称不能为空');return}sn.value=true;const ok=await authStore.updateProfile(displayName.value.trim());sn.value=false;message[ok?'success':'error'](ok?'名称已保存':'保存失败')}
async function chpwd(){const v=await pf.value?.validate().catch(()=>false);if(!v)return;sp.value=true;const ok=await authStore.changePassword(pfm.op,pfm.np);sp.value=false;if(ok){message.success('密码已修改');pfm.op='';pfm.np='';pfm.cp=''}else message.error('旧密码不正确')}
</script>

<style scoped>
.set-page { padding: 32px 40px; max-width: 720px; overflow-y: auto; height: 100%; }

.page-header { margin-bottom: 28px; }
.page-header h2 { margin: 0 0 4px; font-size: 24px; font-weight: 800; color: var(--text-primary, #0F172A); letter-spacing: -0.3px; }
.page-header p { margin: 0; color: var(--text-secondary, #64748B); font-size: 14px; }

.set-card {
  padding: 24px; margin-bottom: 20px;
  background: var(--bg-card, #fff); border: 1px solid var(--border, #E5E7EB);
  border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.03);
  transition: background var(--transition-normal), border-color var(--transition-normal);
}
.card-label { font-size: 15px; font-weight: 700; color: var(--text-primary, #0F172A); margin-bottom: 4px; }
.card-desc { color: var(--text-muted, #94A3B8); margin: 0 0 16px; font-size: 13px; }

.avatar-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.av-item {
  width: 48px; height: 48px; display: flex; align-items: center; justify-content: center;
  font-size: 26px; border-radius: 12px; cursor: pointer; transition: all .2s var(--ease-smooth);
  border: 2px solid transparent; background: var(--bg-surface, #F1F5F9);
}
.av-item:hover { transform: scale(1.12); background: #E2E8F0; border-color: #CBD5E1; }
.av-item.sel { border-color: var(--primary, #2563EB); background: var(--primary-light, #DBEAFE); transform: scale(1.15); box-shadow: 0 2px 8px rgba(37,99,235,.15); }

[data-theme="dark"] .page-header h2 { color: #E2E8F0; }
[data-theme="dark"] .page-header p { color: #64748B; }
[data-theme="dark"] .set-card { background: #1E293B; border-color: #334155; }
[data-theme="dark"] .card-label { color: #E2E8F0; }
[data-theme="dark"] .card-desc { color: #64748B; }
[data-theme="dark"] .av-item { background: #0F172A; border-color: #1E293B; }
[data-theme="dark"] .av-item:hover { background: #1E293B; border-color: #334155; }
[data-theme="dark"] .av-item.sel { background: rgba(37,99,235,.2); border-color: #2563EB; }
</style>
