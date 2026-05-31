import { useState, useRef } from 'react'

export function useChat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Load two videos above — I\'ll analyze transcripts, engagement data, and content strategy. Ask me anything.',
      sources: [],
      id: 0,
    }
  ])
  const [streaming, setStreaming] = useState(false)
  const idRef = useRef(1)

  const addMessage = (msg) => {
    const id = idRef.current++
    setMessages(prev => [...prev, { ...msg, id }])
    return id
  }

  const updateLast = (updater) => {
    setMessages(prev => {
      const next = [...prev]
      next[next.length - 1] = updater(next[next.length - 1])
      return next
    })
  }

  const sendMessage = async (question) => {
    if (streaming) return

    addMessage({ role: 'user', content: question, sources: [] })
    addMessage({ role: 'assistant', content: '', sources: [], streaming: true })
    setStreaming(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Request failed')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const lines = decoder.decode(value).split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token') {
              updateLast(m => ({ ...m, content: m.content + data.content }))
            }
            if (data.type === 'sources') {
              updateLast(m => ({ ...m, sources: data.content, streaming: false }))
            }
            if (data.type === 'done') {
              setStreaming(false)
            }
            if (data.type === 'error') {
              updateLast(m => ({ ...m, content: '⚠ ' + data.content, streaming: false }))
              setStreaming(false)
            }
          } catch (_) {}
        }
      }
    } catch (err) {
      updateLast(m => ({
        ...m,
        content: '⚠ ' + (err.message || 'Connection error'),
        streaming: false,
      }))
      setStreaming(false)
    }
  }

  const clearChat = async () => {
    await fetch('/api/reset', { method: 'POST' })
    setMessages([{
      role: 'assistant',
      content: 'Memory cleared. Ask a fresh question.',
      sources: [],
      id: idRef.current++,
    }])
  }

  return { messages, streaming, sendMessage, clearChat }
}
