import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosError,
} from 'axios'
import type { ApiResponse } from '@/types/api'

// ---- Token 存储（与 auth store 共享 key，避免循环依赖） ----

const TOKEN_STORAGE_KEY = 'auth_tokens'

function getAccessToken(): string | null {
  try {
    const fromLocal = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (fromLocal) return JSON.parse(fromLocal).accessToken ?? null
    const fromSession = sessionStorage.getItem(TOKEN_STORAGE_KEY)
    if (fromSession) return JSON.parse(fromSession).accessToken ?? null
  } catch {
    // ignore
  }
  return null
}

function getRefreshTokenValue(): string | null {
  try {
    const fromLocal = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (fromLocal) return JSON.parse(fromLocal).refreshToken ?? null
    const fromSession = sessionStorage.getItem(TOKEN_STORAGE_KEY)
    if (fromSession) return JSON.parse(fromSession).refreshToken ?? null
  } catch {
    // ignore
  }
  return null
}

// ---- Axios 实例 ----

const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：从存储读取并注入 token
instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Token 刷新去重锁
let refreshPromise: Promise<string> | null = null

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse
    if (data.code !== 0) {
      return Promise.reject(new ApiError(data.code, data.message))
    }
    return response
  },
  async (error: AxiosError<ApiResponse>) => {
    if (error.response?.status === 401 && error.config) {
      const rt = getRefreshTokenValue()
      if (!rt) {
        clearTokensFromStorage()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        if (!refreshPromise) {
          refreshPromise = (async () => {
            try {
              const res = await axios.post<ApiResponse<{ tokens: { accessToken: string; refreshToken: string } }>>(
                `${instance.defaults.baseURL}/auth/refresh`,
                { refreshToken: rt },
              )
              const { accessToken, refreshToken } = res.data.data.tokens
              // 更新存储中的 token
              updateStoredTokens(accessToken, refreshToken)
              return accessToken
            } finally {
              refreshPromise = null
            }
          })()
        }

        const newToken = await refreshPromise
        error.config!.headers.Authorization = `Bearer ${newToken}`
        return instance.request(error.config!)
      } catch {
        clearTokensFromStorage()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

function updateStoredTokens(accessToken: string, refreshToken: string) {
  const payload = JSON.stringify({
    accessToken,
    refreshToken,
    expiresIn: 7200,
  })
  // 在 localStorage 中查找并更新，否则更新 sessionStorage
  if (localStorage.getItem(TOKEN_STORAGE_KEY)) {
    localStorage.setItem(TOKEN_STORAGE_KEY, payload)
  } else {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, payload)
  }
}

function clearTokensFromStorage() {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
}

export { getAccessToken, getRefreshTokenValue, clearTokensFromStorage }

export class ApiError extends Error {
  constructor(
    public code: string | number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export default instance

/**
 * SSE 流式请求
 */
export async function sendStreamRequest(
  message: string,
  callbacks: {
    onToken: (token: string) => void
    onDone: () => void
    onError: (err: Error) => void
  },
): Promise<void> {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const response = await fetch(`${baseURL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    console.error('[SSE] HTTP error:', response.status, errorText)
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  console.log('[SSE] Response OK, content-type:', response.headers.get('content-type'))

  const reader = response.body?.getReader()
  if (!reader) {
    console.error('[SSE] No ReadableStream')
    callbacks.onError(new Error('ReadableStream not supported'))
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        console.log('[SSE] Stream done')
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      console.log('[SSE] chunk:', chunk)
      buffer += chunk
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const json = JSON.parse(line.slice(6))
            console.log('[SSE] token:', json.token)
            if (json.token) {
              callbacks.onToken(json.token)
            }
          } catch {
            console.log('[SSE] skip line:', line)
          }
        }
      }
    }

    if (buffer.startsWith('data: ')) {
      try {
        const json = JSON.parse(buffer.slice(6))
        if (json.token) {
          callbacks.onToken(json.token)
        }
      } catch {
        // skip
      }
    }
  } catch (err) {
    console.error('[SSE] error:', err)
    callbacks.onError(err instanceof Error ? err : new Error(String(err)))
    return
  }

  console.log('[SSE] calling onDone')
  callbacks.onDone()
}

/**
 * 普通对话（非流式）— 降级方案
 * POST /api/chat → { response: string }
 */
export async function sendChatRequest(message: string): Promise<string> {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const response = await fetch(`${baseURL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  const data = await response.json()
  return data.response
}
