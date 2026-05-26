/** 认证 Token */
export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number // Access Token 有效期（秒），默认 7200
}

/** 用户基本信息 */
export interface UserInfo {
  id: string
  nickname: string
  avatar: string
  phone: string
  email: string
  workspaceId: string
}

/** 账号密码登录请求 */
export interface AccountLoginRequest {
  account: string
  password: string
  captchaTicket?: string
  captchaRandstr?: string
}

/** 手机号登录请求 */
export interface PhoneLoginRequest {
  phone: string
  smsCode: string
}

/** 注册请求 */
export interface RegisterRequest {
  phone: string
  smsCode: string
  nickname: string
  password: string
  agreedProtocolVersion: string
}

/** 发送邮箱验证码请求 */
export interface SendEmailCodeRequest {
  email: string
  captchaTicket?: string
  captchaRandstr?: string
}

/** 邮箱注册请求 */
export interface EmailRegisterRequest {
  email: string
  emailCode: string
  nickname: string
  password: string
  agreedProtocolVersion: string
}

/** 登录/注册响应 */
export interface AuthResponse {
  tokens: AuthTokens
  user: UserInfo
  needProtocolAgreement?: string
}

/** 登录失败计数 */
export interface LoginFailInfo {
  failCount: number
  lockedUntil: number | null
}
