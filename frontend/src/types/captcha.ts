/** 滑动拼图数据 */
export interface SlidePuzzleData {
  bgImage: string
  slideImage: string
  y: number
}

/** 滑动拼图校验请求 */
export interface SlideVerifyRequest {
  distance: number
  track: number[]
  ticket?: string
}

/** 滑动拼图校验响应 */
export interface SlideVerifyResponse {
  success: boolean
  ticket?: string
  randstr?: string
}

/** 图形验证码数据（降级方案） */
export interface ImageCaptchaData {
  image: string
  key: string
}
