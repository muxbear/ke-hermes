/** 后端统一响应包装 */
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
  requestId: string
  timestamp: number
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/** 短信验证码发送请求 */
export interface SendSmsRequest {
  phone: string
  captchaTicket: string
  captchaRandstr: string
}
