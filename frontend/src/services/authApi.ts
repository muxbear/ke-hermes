import request from './request'
import type { ApiResponse } from '@/types/api'
import type {
  AccountLoginRequest,
  PhoneLoginRequest,
  RegisterRequest,
  EmailRegisterRequest,
  AuthResponse,
  SendEmailCodeRequest,
} from '@/types/auth'

export const authApi = {
  /** 账号密码登录 */
  accountLogin: (data: AccountLoginRequest) =>
    request.post<ApiResponse<AuthResponse>>('/auth/login/account', data),

  /** 手机号登录 */
  phoneLogin: (data: PhoneLoginRequest) =>
    request.post<ApiResponse<AuthResponse>>('/auth/login/phone', data),

  /** 手机号注册 */
  register: (data: RegisterRequest) =>
    request.post<ApiResponse<AuthResponse>>('/auth/register/phone', data),

  /** 邮箱注册 */
  emailRegister: (data: EmailRegisterRequest) =>
    request.post<ApiResponse<AuthResponse>>('/auth/register/email', data),

  /** 发送邮箱验证码 */
  sendEmailCode: (data: SendEmailCodeRequest) =>
    request.post<ApiResponse<{ devCode?: string }>>('/email/send', data),

  /** 退出登录 */
  logout: () => request.post<ApiResponse<null>>('/auth/logout'),

  /** 刷新 Token */
  refreshToken: (rt: string) =>
    request.post<ApiResponse<AuthResponse>>('/auth/refresh', { refreshToken: rt }),

  /** 获取登录失败次数 */
  getFailCount: (account: string) =>
    request.get<ApiResponse<{ failCount: number }>>('/auth/fail-count', {
      params: { account },
    }),

  /** 获取 RSA 公钥 */
  getPublicKey: () =>
    request.get<ApiResponse<{ publicKey: string }>>('/auth/public-key'),
}
