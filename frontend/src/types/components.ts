/** 登录方式标签项 */
export interface LoginTabItem {
  key: 'account' | 'phone'
  label: string
}

/** 品牌区特性项 */
export interface FeatureItem {
  icon: string
  title: string
  description: string
}

/** 第三方登录平台 */
export interface OAuthProvider {
  name: string
  icon: string
  bgColor: string
  textColor: string
  shadowColor: string
}

/** 验证码通过结果 */
export interface CaptchaResult {
  ticket: string
  randstr: string
}

/** 待处理操作（验证码通过后执行） */
export interface PendingAction {
  type: 'send-sms' | 'login'
  payload?: unknown
}
