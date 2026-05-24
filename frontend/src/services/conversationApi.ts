import instance from "./request"

export interface ConversationItem {
    thread_id: string
    title: string
    updated_at: string
}

export interface MessageItem {
    role: 'system' | 'user' | 'assistant' | 'tool'
    content: string
}

export interface ConversationDetail {
    thread_id: string
    title: string
    messages: MessageItem[]
}

export async function fetchConversations(): Promise<ConversationItem[]> {
    const res = await instance.get('/conversations')
    return res.data.data as ConversationItem[]
}

export async function fetchConversationMessages(thread_id: string): Promise<ConversationDetail> {
    const res = await instance.get(`/conversations/${thread_id}`)
    return res.data.data as ConversationDetail
}

export async function rename_conversation(thread_id: string, title: string): Promise<{ thread_id: string, title: string}> {
    const res = await instance.patch(`/conversations/${thread_id}`, { title })
    return res.data.data
}

export async function deleteConversation(threadId: string): Promise<void> {
    await instance.delete(`/conversations/${threadId}`)
}