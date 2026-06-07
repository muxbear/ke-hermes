export type TraceEventType = 'agent_start' | 'agent_end' | 'tool_start' | 'tool_end'

export interface TraceEntry {
  id: number
  type: TraceEventType
  name: string
  agent?: string
  input?: string
  output?: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  streaming: boolean
  traces?: TraceEntry[]
}
