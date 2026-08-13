import apiClient from './client'
import { useAuthStore } from '../stores/auth'

export interface AssetItem {
  id: string
  filename: string
  original_name: string
  file_type: string
  file_size: number
  tags: string[]
  ai_tags: string[]
  ai_description: string | null
  thumbnail_url: string | null
  width: number | null
  height: number | null
  duration_seconds: number | null
  status: string
  version: number
  created_at: string
  updated_at: string | null
}

export interface AssetListParams {
  page?: number
  page_size?: number
  tag?: string
  search?: string
  file_type?: string
  sort?: string
}

export interface AssetListResponse {
  items: AssetItem[]
  total: number
  page: number
  page_size: number
}

export interface AssetUpdateRequest {
  original_name?: string
  tags?: string[]
  ai_description?: string
  status?: string
}

export interface AssetStats {
  total: number
  tagged: number
  total_size_bytes: number
  by_type: Record<string, number>
  by_status: Record<string, number>
}

export interface PopularTags {
  tags: string[]
}

export interface ImageSearchResponse {
  description: string
  keywords: string[]
  fallback: boolean
  note: string | null
  items: AssetItem[]
  total: number
}

export interface StockPhoto {
  id: string
  description?: string
  width: number
  height: number
  url: string
  thumbnail: string
  download_url: string
  author: string
}

export interface StockVideo {
  id: string
  url: string
  thumbnail: string
  download_url: string
  width: number
  height: number
  duration: number
  author: string
}

export interface UnsplashSearchResponse {
  photos: StockPhoto[]
  source: string
  total: number
  page: number
}

export interface PexelsSearchResponse {
  photos?: StockPhoto[]
  videos?: StockVideo[]
  source: string
  total: number
  page: number
}

export const assetApi = {
  /** List assets with optional filters */
  list(params?: AssetListParams) {
    return apiClient.get<AssetListResponse>('/assets/list', { params })
  },

  /** Get a single asset by ID */
  get(assetId: string) {
    return apiClient.get<AssetItem>(`/assets/${assetId}`)
  },

  /** Upload one or more files */
  upload(file: File, tags?: string, customFilename?: string, onProgress?: (pct: number) => void) {
    const form = new FormData()
    form.append('file', file)
    if (tags) form.append('tags', tags)
    if (customFilename) form.append('filename', customFilename)
    return apiClient.post<AssetItem>('/assets/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      },
    })
  },

  /** Update asset metadata */
  update(assetId: string, data: AssetUpdateRequest) {
    return apiClient.patch<AssetItem>(`/assets/${assetId}`, data)
  },

  /** Soft-delete an asset */
  remove(assetId: string) {
    return apiClient.delete(`/assets/${assetId}`)
  },

  /** Get the file download URL for an asset */
  getFileUrl(assetId: string) {
    return `/api/assets/${assetId}/file`
  },

  /** Get a URL with auth token as query param. Use for <img> and <a> elements. */
  getAuthUrl(assetId: string) {
    const authStore = useAuthStore()
    const token = authStore.token
    const base = `/api/assets/${assetId}/file`
    return token ? `${base}?token=${encodeURIComponent(token)}` : base
  },

  /** Get quick asset statistics */
  getStats() {
    return apiClient.get<AssetStats>('/assets/stats')
  },

  /** Get popular tags */
  getPopularTags() {
    return apiClient.get<PopularTags>('/assets/tags/popular')
  },

  /** 以图搜图: upload an image, AI generates a description and searches similar assets */
  searchByImage(file: File) {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<ImageSearchResponse>('/assets/search-by-image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Get free stock photos (no API key required) */
  getFreeStockPhotos(page = 1, perPage = 12) {
    return apiClient.get<{
      photos: Array<{
        id: string
        author: string
        width: number
        height: number
        url: string
        thumbnail: string
        preview: string
        download_url: string
      }>
      source: string
      source_url: string
      license: string
      page: number
    }>('/assets/free-stock-photos', { params: { page, per_page: perPage } })
  },

  /** Search free photos on Unsplash (requires UNSPLASH_API_KEY on the backend) */
  searchUnsplash(q: string, page = 1, perPage = 12) {
    return apiClient.get<UnsplashSearchResponse>('/assets/unsplash/search', {
      params: { q, page, per_page: perPage },
    })
  },

  /** Search free photos/videos on Pexels (requires PEXELS_API_KEY on the backend) */
  searchPexels(q: string, type: 'photos' | 'videos' = 'photos', page = 1, perPage = 12) {
    return apiClient.get<PexelsSearchResponse>('/assets/pexels/search', {
      params: { q, type, page, per_page: perPage },
    })
  },

  /** Import asset from a public URL */
  importFromUrl(url: string, tags?: string) {
    return apiClient.post<AssetItem>('/assets/import-from-url', { url, tags })
  },
}
