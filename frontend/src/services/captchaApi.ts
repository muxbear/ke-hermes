import request from './request'
import type { ApiResponse, SendSmsRequest } from '@/types/api'
import type {
  SlidePuzzleData,
  SlideVerifyRequest,
  SlideVerifyResponse,
  ImageCaptchaData,
} from '@/types/captcha'

export const captchaApi = {
  /** 获取滑动拼图数据 */
  getSlidePuzzle: () => request.get<ApiResponse<SlidePuzzleData>>('/captcha/slide'),

  /** 校验滑动拼图 */
  verifySlide: (data: SlideVerifyRequest) =>
    request.post<ApiResponse<SlideVerifyResponse>>('/captcha/slide/verify', data),

  /** 发送短信验证码 */
  sendSms: (data: SendSmsRequest) => request.post<ApiResponse<null>>('/sms/send', data),

  /** 获取图形验证码（降级方案） */
  getImageCaptcha: () => request.get<ApiResponse<ImageCaptchaData>>('/captcha/image'),

  /** 校验图形验证码 */
  verifyImageCaptcha: (data: { key: string; code: string }) =>
    request.post<ApiResponse<{ success: boolean }>>('/captcha/image/verify', data),
}
