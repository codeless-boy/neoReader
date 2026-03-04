import api from './index'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  provider: string
  model: string
  api_key: string
  prompt: string
  temperature?: number
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
