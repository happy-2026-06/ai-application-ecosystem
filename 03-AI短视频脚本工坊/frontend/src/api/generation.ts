import apiClient from './client'
import { useAuthStore } from '../stores/auth'

export interface TTSVoice {
  id: string
  name: string
  gender: 'male' | 'female'
  style: string
  tags: string[]
}

export interface TTSResponse {
  file_url: string
  filename: string
  voice: string
  duration_chars: number
}

export interface VideoTask {
  index?: number
  task_id?: string
  status: string
  model?: string
  prompt?: string
  video_url?: string
  error?: string
  reason?: string
}

export interface SubtitleResponse {
  file_url: string
  filename: string
  format: string
  entry_count: number
  audio_aligned: boolean
  alignment_mode: string  // "per_shot" | "scaled" | "estimated"
  total_duration_sec: number
}

export const generationApi = {
  // ═══ TTS ═══════════════════════════════════════════════════════════
  listVoices(language = 'zh') {
    return apiClient.get<{ voices: TTSVoice[]; count: number }>('/generation/tts/voices', {
      params: { language },
    })
  },

  generateTTS(sessionId: string, voice?: string, speed?: string, messageId?: string) {
    return apiClient.post<TTSResponse>('/generation/tts', {
      session_id: sessionId,
      voice: voice || 'zh-CN-XiaoxiaoNeural',
      speed: speed || '+0%',
      message_id: messageId || undefined,
    })
  },

  getTTSDownloadUrl(filename: string): string {
    return `/api/generation/tts/download/${filename}`
  },

  // ═══ Video ═════════════════════════════════════════════════════════
  submitVideo(sessionId: string, model?: string, shotIndexes?: number[], messageId?: string) {
    return apiClient.post<{ tasks: VideoTask[]; count: number }>('/generation/video', {
      session_id: sessionId,
      model: model || 'cogvideox-2',
      shot_indexes: shotIndexes || undefined,
      message_id: messageId || undefined,
    })
  },

  getVideoStatus(taskId: string) {
    return apiClient.get<VideoTask>(`/generation/video/${taskId}`)
  },

  // ═══ Subtitles ═════════════════════════════════════════════════════
  exportSubtitles(sessionId: string, format: 'srt' | 'ass' = 'srt', wps = 3.5, messageId?: string) {
    return apiClient.post<SubtitleResponse>('/generation/subtitles', {
      session_id: sessionId,
      format,
      words_per_second: wps,
      message_id: messageId || undefined,
    })
  },

  getSubtitleDownloadUrl(filename: string): string {
    return `/api/generation/subtitles/download/${filename}`
  },
}
