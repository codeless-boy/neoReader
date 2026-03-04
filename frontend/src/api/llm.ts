import api from './index'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  provider: string
  model: string
  config_key: string
  prompt: string
  temperature?: number
  stream?: boolean
  session_id?: string
}

export interface ChatResponse {
  content: string
  provider: string
  model: string
  usage?: any
}

export const sendChatMessage = async (data: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('/llm/chat', data)
  return response.data
}

export const getChatHistory = async (sessionId: string): Promise<ChatMessage[]> => {
  const response = await api.get<ChatMessage[]>(`/llm/chat/history/${sessionId}`)
  return response.data
}

export const getChatSessions = async (): Promise<{ id: string, title: string }[]> => {
  const response = await api.get<{ id: string, title: string }[]>('/llm/chat/sessions')
  return response.data
}

export const deleteChatSession = async (sessionId: string): Promise<void> => {
  await api.delete(`/llm/chat/sessions/${sessionId}`)
}

export const sendChatStream = async (
  data: ChatRequest, 
  onChunk: (chunk: string) => void,
  onError?: (error: string) => void
): Promise<void> => {
  const response = await fetch('/api/llm/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ...data, stream: true }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('Response body is unavailable')

  const decoder = new TextDecoder()
  let buffer = ''
  
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n\n')
      // Keep the last incomplete chunk in buffer
      const lastLine = lines.pop()
      buffer = lastLine === undefined ? '' : lastLine

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6)
          if (jsonStr === '[DONE]') return

          try {
            const parsed = JSON.parse(jsonStr)
            if (parsed.error) {
              if (onError) onError(parsed.error)
              return
            }
            if (parsed.content) {
              onChunk(parsed.content)
            }
          } catch (e) {
            console.error('Failed to parse SSE JSON:', e, line)
          }
        }
      }
    }
  } catch (e: any) {
    if (onError) onError(e.message || 'Stream reading failed')
    throw e
  } finally {
    reader.releaseLock()
  }
}
