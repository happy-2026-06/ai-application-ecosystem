<template>
  <div class="admin-page">
    <div class="admin-top">
      <div>
        <h2>知识库管理</h2>
        <p class="sub">上传产品文档，AI 将基于这些文档回答问题</p>
      </div>
      <n-space>
        <n-button @click="$router.push('/admin/users')">👥 用户管理</n-button>
        <n-button @click="$router.push('/admin/dashboard')">📊 仪表盘</n-button>
      </n-space>
    </div>

    <n-grid cols="4" x-gap="12" style="margin-bottom:20px;">
      <n-gi v-for="s in stats" :key="s.label">
        <n-card size="small"><n-statistic :label="s.label" :value="s.value" /></n-card>
      </n-gi>
    </n-grid>

    <n-card title="上传文档" style="margin-bottom:20px;">
      <n-upload multiple :max="10" accept=".pdf,.txt,.md,.csv,.docx" @change="handleUpload">
        <n-button type="primary">📁 选择文件上传</n-button>
      </n-upload>
      <p style="color:#999;font-size:12px;margin-top:8px;">支持 PDF、TXT、Markdown、CSV、DOCX，单文件最大 50MB</p>
    </n-card>

    <n-card title="文档列表">
      <n-data-table :columns="columns" :data="docs" :loading="loading" :pagination="{pageSize:10}" :row-key="(r:any)=>r.id" />
    </n-card>

    <!-- 预览弹窗 -->
    <n-modal v-model:show="showPreview" title="文档预览" preset="card" style="width:900px;max-height:80vh;" :bordered="false" size="huge">
      <div style="max-height:60vh;overflow-y:auto;white-space:pre-wrap;font-family:monospace;font-size:14px;line-height:1.7;padding:16px;background:#f8f9fa;border-radius:8px;">
        {{ previewContent || '此文件格式暂不支持在线预览，请下载后查看' }}
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { kbApi, type Document } from '../api/kb'
import { useMessage, NTag, NButton, NSpace, NInput, NModal } from 'naive-ui'

const message = useMessage()
const docs = ref<Document[]>([]); const loading = ref(false)
const showPreview = ref(false); const previewContent = ref('')
const editingId = ref<string | null>(null); const editingName = ref('')

const stats = computed(() => {
  const c = docs.value.filter(d=>d.status==='completed').length
  const tc = docs.value.reduce((s,d)=>s+d.chunk_count,0)
  const p = docs.value.filter(d=>d.status==='processing').length
  return [{label:'总文档',value:docs.value.length},{label:'已完成',value:c},{label:'总片段',value:tc},{label:'处理中',value:p}]
})

const columns = [
  {
    title:'文件名',key:'original_name',ellipsis:{tooltip:true},
    render(r:Document){
      if (editingId.value === r.id) {
        return h(NInput, {
          size: 'small', value: editingName.value,
          onInput: (v:string) => { editingName.value = v },
          onKeyup: (e:KeyboardEvent) => {
            if (e.key === 'Enter') saveRename(r.id)
            if (e.key === 'Escape') { editingId.value = null }
          },
          onBlur: () => saveRename(r.id),
          style: 'width:200px;',
        })
      }
      return r.original_name
    },
  },
  {title:'类型',key:'file_type',width:70},
  {title:'状态',key:'status',width:90,render(r:Document){const m:any={pending:{type:'default',text:'等待中'},processing:{type:'info',text:'处理中'},completed:{type:'success',text:'已完成'},failed:{type:'error',text:'失败'}};const s=m[r.status]||{type:'default',text:r.status};return h(NTag,{type:s.type},{default:()=>s.text})}},
  {title:'片段',key:'chunk_count',width:60},
  {title:'操作',key:'actions',width:220,render(r:Document){return h(NSpace,{},()=>[
    r.status==='failed'?h(NButton,{size:'small',onClick:()=>reprocess(r.id)},{default:()=>'重试'}):null,
    h(NButton,{size:'small',onClick:()=>startRename(r)},{default:()=>'重命名'}),
    h(NButton,{size:'small',onClick:()=>previewDoc(r)},{default:()=>'预览'}),
    h(NButton,{size:'small',type:'error',onClick:()=>del(r.id)},{default:()=>'删除'})
  ])}},
]

async function load(){ loading.value=true; try{const r=await kbApi.listDocuments();docs.value=r.data.items}catch{message.error('加载失败')}finally{loading.value=false} }
async function handleUpload(d:any){ try{const f=d.file?.file||d.file;await kbApi.uploadDocument(f);message.success(`${f.name} 上传成功`);await load()}catch{message.error('上传失败')} }
async function del(id:string){ try{await kbApi.deleteDocument(id);message.success('已删除');await load()}catch{message.error('删除失败')} }
async function reprocess(id:string){ try{await kbApi.reprocessDocument(id);message.success('已重新处理');await load()}catch{message.error('操作失败')} }

function startRename(doc: Document) {
  editingId.value = doc.id
  editingName.value = doc.original_name
}

async function saveRename(id: string) {
  if (!editingId.value) return
  const newName = editingName.value.trim()
  if (newName && newName !== docs.value.find(d=>d.id===id)?.original_name) {
    try {
      await kbApi.renameDocument(id, newName)
      message.success('已重命名')
      await load()
    } catch { message.error('重命名失败') }
  }
  editingId.value = null
}

async function previewDoc(doc: Document) {
  showPreview.value = true
  previewContent.value = '加载中...'

  try {
    const { useAuthStore } = await import('../stores/auth')
    const authStore = useAuthStore()
    const resp = await fetch(`/api/kb/documents/${doc.id}/content`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      if (data.content) {
        previewContent.value = data.content
      } else {
        previewContent.value = data.message || '此文件格式暂不支持在线预览，请下载后查看'
      }
    } else {
      previewContent.value = `文件类型: ${doc.file_type.toUpperCase()}\n文件名: ${doc.original_name}\n状态: ${doc.status}\n\n此文件无法预览，可能是文件格式不支持或文件已损坏。请下载后查看。`
    }
  } catch {
    previewContent.value = '加载预览失败，请检查网络连接'
  }
}

onMounted(load)
</script>

<style scoped>
.admin-page { padding: 28px 32px; max-width: 1200px; overflow-y: auto; height: 100%; }
.admin-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.admin-top h2 { margin: 0; font-size: 22px; }
.sub { color: #999; margin: 4px 0 0; font-size: 13px; }
[data-theme="dark"] .admin-top h2 { color: #eee; }
</style>
