/**
 * Data center API client
 */
import apiClient from './client'

export interface DataSet {
  id: string; user_id: string; name: string; description?: string
  source: string; item_count: number; status: string; tags?: string[]
  created_at: string; updated_at: string
}

export interface DataVersion {
  id: string; dataset_id: string; version_number: number
  item_count: number; change_log?: string; quality_score?: number
  metadata?: any; created_at: string
}

export interface Annotation {
  id: string; dataset_id: string; data_item: string
  label?: string; category?: string; sentiment?: string
  confidence?: number; is_verified: boolean; annotated_by: string
  created_at: string
}

export interface QualityReport {
  dataset_id: string; dataset_name: string; total_items: number
  annotated_items: number; verified_items: number
  label_distribution: Record<string,number>
  category_distribution: Record<string,number>
  avg_confidence: number; quality_score: number; completeness: number
}

export interface DashboardStats {
  total_datasets: number; total_items: number
  total_annotations: number; ai_annotated: number
  human_verified: number; avg_quality_score: number
  recent_datasets: DataSet[]
}

export const dataApi = {
  dashboard() { return apiClient.get<DashboardStats>('/data/dashboard') },

  listDatasets(page=1,size=20) { return apiClient.get<DataSet[]>('/data/datasets',{params:{page,page_size:size}}) },
  createDataset(data:{name:string;description?:string;source?:string}) { return apiClient.post<DataSet>('/data/datasets',data) },
  getDataset(id:string) { return apiClient.get<DataSet>('/data/datasets/'+id) },
  deleteDataset(id:string) { return apiClient.delete('/data/datasets/'+id) },

  ingestData(id:string, texts:string[]) { return apiClient.post('/data/datasets/'+id+'/ingest',{texts}) },
  cleanData(id:string, opts?:any) { return apiClient.post('/data/datasets/'+id+'/clean',opts||{}) },

  getAnnotations(id:string, page=1,size=50) { return apiClient.get<Annotation[]>('/data/datasets/'+id+'/annotations',{params:{page,page_size:size}}) },
  annotateData(id:string, items:{text:string;index:number}[]) { return apiClient.post('/data/datasets/'+id+'/annotate',{items}) },
  verifyAnnotation(id:string, data:{label?:string;category?:string;sentiment?:string}) { return apiClient.patch('/data/annotations/'+id,data) },

  getVersions(id:string) { return apiClient.get<DataVersion[]>('/data/datasets/'+id+'/versions') },
  createVersion(id:string, changeLog?:string) { return apiClient.post('/data/datasets/'+id+'/versions',{change_log:changeLog}) },

  getQualityReport(id:string) { return apiClient.get<QualityReport>('/data/datasets/'+id+'/quality') },

  // Cross-project external ingest
  ingestExternal(sourceProject:string, dataType:string, texts:string[], datasetName?:string) {
    return apiClient.post('/data/external/ingest', {
      source_project: sourceProject,
      data_type: dataType,
      texts,
      dataset_name: datasetName || `来自${sourceProject}的数据`,
      description: `从 ${sourceProject} 自动汇入的${dataType}数据`,
    })
  },
  exportForFinetune(id:string) { return apiClient.get('/data/datasets/'+id+'/export-for-finetune') },
}
