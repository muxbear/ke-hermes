import request from './request'
import type { ApiResponse } from '@/types/api'
import type { AuthResponse } from '@/types/auth'

export const oauthApi = {
  /** 获取第三方登录授权跳转 URL */
  getAuthUrl: (provider: string) =>
    request.get<ApiResponse<{ authUrl: string }>>('/oauth/auth-url', {
      params: { provider },
    }),

  /** 处理 OAuth 回调 */
  handleCallback: (provider: string, code: string, state: string) =>
    request.post<ApiResponse<AuthResponse>>('/oauth/callback', { provider, code, state }),
}
