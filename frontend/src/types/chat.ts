// ---- SSE event types ----

export type SseEventType =
  | 'agent_start'
  | 'agent_end'
  | 'token'
  | 'reasoning'
  | 'tool_start'
  | 'tool_output'
  | 'tool_end'
  | 'error'
  | 'done'

export interface AgentStartData {
  agent_name: string
  agent_type: 'main' | 'sub'
  call_id: string
}

export interface AgentEndData {
  agent_name: string
  call_id: string
  status: string
  error?: string
}

export interface ToolStartData {
  tool_name: string
  call_id: string
  agent_name: string
  input: string
}

export interface ToolEndData {
  tool_name: string
  call_id: string
  output: string
}

// ---- Execution block types (trace mode) ----

export interface ToolCallInfo {
  callId: string
  name: string
  input: string
  output: string
  status: 'running' | 'completed' | 'failed'
}

export interface SubAgentInfo {
  callId: string
  name: string
  status: 'running' | 'completed' | 'failed'
  blocks: ExecutionBlock[]
}

export type ExecutionBlock =
  | { type: 'text'; content: string }
  | { type: 'tool_call'; toolCall: ToolCallInfo }
  | { type: 'sub_agent'; subAgent: SubAgentInfo }

// ---- Chat message ----

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  reasoning?: string
  streaming: boolean
  /** Execution blocks — only populated when traceEnabled is on */
  blocks?: ExecutionBlock[]
}

// ---- Legacy (kept for backward compat, no longer emitted by backend) ----

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
