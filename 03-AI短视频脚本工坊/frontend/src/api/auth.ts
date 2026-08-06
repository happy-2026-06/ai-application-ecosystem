import apiClient from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  display_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    username: string
    email?: string
    display_name?: string
    role: string
    is_active: boolean
  }
}

export const authApi = {
  login(data: LoginRequest) {
    return apiClient.post<TokenResponse>('/auth/login', data)
  },
  register(data: RegisterRequest) {
    return apiClient.post('/auth/register', data)
  },
  refreshToken(refreshToken: string) {
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken })
  },
  changePassword(oldPassword: string, newPassword: string) {
    return apiClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  },
  forgotPassword(username: string) {
    return apiClient.post<{ message: string; demo: boolean; hint?: string }>('/auth/forgot-password', { username })
  },
  resetPassword(username: string, newPassword: string) {
    return apiClient.post('/auth/reset-password', { username, new_password: newPassword })
  },
  getMe() {
    return apiClient.get('/auth/me')
  },
}
