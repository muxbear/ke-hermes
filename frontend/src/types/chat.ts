export type TraceEventType =
  | 'agent_start'
  | 'agent_end'
  | 'tool_start'
  | 'tool_end'
  | 'subagent_start'
  | 'subagent_end'

export interface TraceEntry {
  id: number
  type: TraceEventType
  name: string
  agent?: string
  input?: string
  output?: string
  status?: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  reasoning?: string
  streaming: boolean
  traces?: TraceEntry[]
}
