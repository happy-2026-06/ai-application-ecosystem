import apiClient from './client'

export interface Document {
  id: string
  filename: string
  original_name: string
  file_type: string
  file_size: number
  chunk_count: number
  char_count: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface KBStats {
  doc_count: number
  chunk_count: number
  total_chars: number
  total_size_bytes: number
  last_updated: string | null
}

export const kbApi = {
  listDocuments(page = 1, pageSize = 20, status?: string) {
    return apiClient.get<{ items: Document[]; total: number }>('/kb/documents', {
      params: { page, page_size: pageSize, status },
    })
  },
  uploadDocument(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<Document>('/kb/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteDocument(docId: string) {
    return apiClient.delete(`/kb/documents/${docId}`)
  },
  reprocessDocument(docId: string) {
    return apiClient.post(`/kb/documents/${docId}/reprocess`)
  },
  getStats() {
    return apiClient.get<KBStats>('/kb/stats')
  },
}
