<template>
  <div class="set-page">
    <h2>个人中心</h2>

    <!-- Avatar -->
    <div class="set-section">
      <h3>选择头像</h3>
      <p class="desc">点击即可切换</p>
      <div class="avatar-grid">
        <div v-for="e in avatars" :key="e" class="av-item" :class="{sel:authStore.avatar===e}" @click="authStore.setAvatar(e)">{{ e }}</div>
      </div>
    </div>

    <n-divider />

    <!-- Name -->
    <div class="set-section">
      <h3>显示名称</h3>
      <p class="desc">会显示在侧边栏和聊天中</p>
      <n-space vertical>
        <n-input v-model:value="displayName" placeholder="输入昵称" size="large" maxlength="20" style="max-width:360px;" />
        <n-button type="primary" @click="saveName" :loading="sn">保存名称</n-button>
      </n-space>
    </div>

    <n-divider />

    <!-- Password -->
    <div class="set-section">
      <h3>修改密码</h3>
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
.set-page { padding:28px 40px; max-width:680px; overflow-y:auto; height:100%; }
.set-page h2 { margin:0 0 24px; font-size:22px; }
.set-section { margin:20px 0; }
.set-section h3 { margin:0 0 4px; font-size:16px; }
.desc { color:#999; margin:0 0 14px; font-size:13px; }
.avatar-grid { display:flex; flex-wrap:wrap; gap:8px; }
.av-item { width:48px; height:48px; display:flex; align-items:center; justify-content:center; font-size:26px; border-radius:10px; cursor:pointer; transition:all .15s; border:2px solid transparent; background:#f5f6fa; }
.av-item:hover { transform:scale(1.1); background:#eef0f8; }
.av-item.sel { border-color:#f59e0b; background:#fffbeb; transform:scale(1.12); }
[data-theme="dark"] .set-page h2,[data-theme="dark"] .set-section h3 { color: #eee; }
[data-theme="dark"] .av-item { background: #1e1e28; }
[data-theme="dark"] .av-item.sel { background: rgba(245,158,11,.2); border-color:#f59e0b; }
</style>
