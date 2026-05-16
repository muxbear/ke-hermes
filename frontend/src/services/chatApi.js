import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export async function sendChatRequest(message) {
  const { data } = await apiClient.post('/chat', { message })
  return data
}

export async function sendStreamRequest(message, { onToken, onDone, onError }) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  const reader = response.body.getReader()
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
        if (line.startsWith('data: ')) {
          try {
            const json = JSON.parse(line.slice(6))
            if (json.token) {
              onToken(json.token)
            }
          } catch {
            // skip unparseable lines
          }
        }
      }
    }

    if (buffer.startsWith('data: ')) {
      try {
        const json = JSON.parse(buffer.slice(6))
        if (json.token) {
          onToken(json.token)
        }
      } catch {
        // skip
      }
    }
  } catch (err) {
    onError(err)
    return
  }

  onDone()
}