import { getAccessToken } from './request'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export interface AttachmentUploadResult {
  id: string
  filename: string
  file_path: string
  file_size: number
  file_type: string
  status: string
}

export function uploadAttachment(
  file: File,
  onProgress: (percent: number) => void,
): Promise<AttachmentUploadResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText)
          if (response.code === 0 && response.data) {
            resolve(response.data as AttachmentUploadResult)
          } else {
            reject(new Error(response.message || '上传失败'))
          }
        } catch {
          reject(new Error('解析响应失败'))
        }
      } else {
        reject(new Error(`上传失败: HTTP ${xhr.status}`))
      }
    })

    xhr.addEventListener('error', () => reject(new Error('网络错误')))
    xhr.addEventListener('abort', () => reject(new Error('上传已取消')))

    xhr.open('POST', `${API_BASE}/chat/upload`)
    const token = getAccessToken()
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    }
    xhr.send(formData)
  })
}

export async function deleteAttachment(id: string): Promise<void> {
  const token = getAccessToken()
  const headers: Record<string, string> = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(`${API_BASE}/chat/upload/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers,
  })
  if (!res.ok) {
    throw new Error(`删除失败: HTTP ${res.status}`)
  }
}
