import apiClient from './client'

export interface TrainingSession {
  id: string
  user_id: string
  customer_type: string
  product_context: string | null
  overall_score: number | null
  total_rounds: number
  status: string
  created_at: string
  updated_at: string
}

export interface TrainingRound {
  id: string
  training_session_id: string
  round_number: number
  user_response: string
  customer_response: string
  coach_hint: string | null
  scores: Record<string, number> | null
  created_at: string
}

export interface CustomerType {
  key: string
  name: string
  icon: string
  difficulty: number
  persona: string
}

export interface ScoreTrendEntry {
  round: number
  overall: number
  [dimension: string]: number
}

export interface TrainingReport {
  session: TrainingSession
  rounds: TrainingRound[]
  score_trend: ScoreTrendEntry[]
  strengths: string[]
  improvements: string[]
  recommendation: string
}

export const trainingApi = {
  // Sessions
  listSessions(page = 1, pageSize = 20) {
    return apiClient.get<TrainingSession[]>('/training/sessions', {
      params: { page, page_size: pageSize },
    })
  },

  createSession(customerType: string, productContext?: string) {
    return apiClient.post<TrainingSession>('/training/sessions', {
      customer_type: customerType,
      product_context: productContext,
    })
  },

  getSession(sessionId: string) {
    return apiClient.get<TrainingSession>(`/training/sessions/${sessionId}`)
  },

  deleteSession(sessionId: string) {
    return apiClient.delete(`/training/sessions/${sessionId}`)
  },

  // Rounds
  getRounds(sessionId: string) {
    return apiClient.get<TrainingRound[]>(`/training/sessions/${sessionId}/rounds`)
  },

  // SSE streaming respond
  respond(sessionId: string, response: string, token: string): Promise<Response> {
    return fetch(`/api/training/sessions/${sessionId}/respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ response }),
    })
  },

  // End & Report
  endSession(sessionId: string) {
    return apiClient.post(`/training/sessions/${sessionId}/end`)
  },

  getReport(sessionId: string) {
    return apiClient.get<TrainingReport>(`/training/sessions/${sessionId}/report`)
  },

  // Customer types
  getCustomerTypes() {
    return apiClient.get<CustomerType[]>('/training/customer-types')
  },
}
