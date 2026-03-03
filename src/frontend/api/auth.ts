import request from './client'

export interface AuthResponse {
  user_id: string
  token: string
}

export function signInAnonymous(): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/anonymous', { method: 'POST' })
}
