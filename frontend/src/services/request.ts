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
    const raw = sessionStorage.getItem(TOKEN_STORAGE_KEY)
    if (raw) return JSON.parse(raw).accessToken ?? null
  } catch {
    // ignore
  }
  return null
}

function getRefreshTokenValue(): string | null {
  try {
    const raw = sessionStorage.getItem(TOKEN_STORAGE_KEY)
    if (raw) return JSON.parse(raw).refreshToken ?? null
  } catch {
    // ignore
  }
  return null
}

// ---- Axios 实例 ----

const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {},
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
  sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify({
    accessToken,
    refreshToken,
    expiresIn: 7200,
  }))
}

function clearTokensFromStorage() {
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

function chatAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const token = getAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

function parseSseDataLine(
  line: string,
  onToken: (token: string) => void,
  onThreadId?: (threadId: string) => void,
): void {
  if (!line.startsWith('data: ')) return
  try {
    const json = JSON.parse(line.slice(6)) as { token?: string; thread_id?: string }
    if (json.token) {
      onToken(json.token)
    }
    if (json.thread_id && onThreadId) {
      onThreadId(json.thread_id)
    }
  } catch {
    // skip malformed SSE line
  }
}

/**
 * SSE 流式请求
 */
export async function sendStreamRequest(
  message: string,
  options: {
    threadId?: string | null
    onToken: (token: string) => void
    onThreadId?: (threadId: string) => void
    onDone: () => void
    onError: (err: Error) => void
  },
): Promise<void> {
  const { threadId, onToken, onThreadId, onDone, onError } = options

  const body: { message: string; thread_id?: string } = { message }
  if (threadId) {
    body.thread_id = threadId
  }

  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const response = await fetch(`${baseURL}/chat/stream`, {
    method: 'POST',
    headers: chatAuthHeaders(),
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError(new Error('ReadableStream not supported'))
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        parseSseDataLine(line, onToken, onThreadId)
      }
    }

    if (buffer.trim()) {
      for (const line of buffer.split('\n')) {
        parseSseDataLine(line, onToken, onThreadId)
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)))
    return
  }

  onDone()
}

/**
 * 普通对话（非流式）— 降级方案
 * POST /api/chat → { response, thread_id }
 */
export async function sendChatRequest(
  message: string,
  threadId?: string | null,
): Promise<{ response: string; threadId: string }> {
  const body: { message: string; thread_id?: string } = { message }
  if (threadId) {
    body.thread_id = threadId
  }

  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const response = await fetch(`${baseURL}/chat`, {
    method: 'POST',
    headers: chatAuthHeaders(),
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  const data = (await response.json()) as { response: string; thread_id: string }
  return {
    response: data.response,
    threadId: data.thread_id,
  }
}
