import { useRef, useEffect, useState } from 'react'
import ChatMessage from './ChatMessage'
import { useChat } from '../hooks/useChat'

const SUGGESTED = [
  "Why did Video A get more engagement than Video B?",
  "What's the engagement rate of each video?",
  "Compare the hooks in the first 5 seconds",
  "Who is the creator of Video B and their follower count?",
  "Suggest improvements for Video B based on Video A",
]

export default function ChatPanel({ ready }) {
  const { messages, streaming, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const q = input.trim()
    if (!q || !ready || streaming) return
    sendMessage(q)
    setInput('')
    textareaRef.current?.focus()
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg)', borderLeft: '1px solid var(--border)',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexShrink: 0,
      }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>AI Video Analyst</div>
          <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: ready ? 'var(--green)' : 'var(--text3)', marginTop: 2 }}>
            {ready ? '● READY — Groq llama-3.3-70b' : '○ WAITING FOR VIDEOS'}
          </div>
        </div>
        {ready && (
          <button onClick={clearChat} style={{
            fontSize: 10, color: 'var(--text3)', background: 'none',
            fontFamily: 'var(--font-mono)', padding: '4px 8px',
            border: '1px solid var(--border)', borderRadius: 4,
          }}
            onMouseEnter={e => e.target.style.color = 'var(--text)'}
            onMouseLeave={e => e.target.style.color = 'var(--text3)'}
          >
            clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', minHeight: 0 }}>
        {messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}
        <div ref={bottomRef} />
      </div>

      {/* Suggested questions */}
      {ready && !streaming && (
        <div style={{
          padding: '8px 16px', borderTop: '1px solid var(--border)',
          display: 'flex', gap: 6, overflowX: 'auto', flexShrink: 0,
        }}>
          {SUGGESTED.map((q, i) => (
            <button key={i} onClick={() => sendMessage(q)} style={{
              fontSize: 10, whiteSpace: 'nowrap',
              background: 'var(--surface)', border: '1px solid var(--border)',
              color: 'var(--text2)', borderRadius: 20, padding: '4px 12px',
              fontFamily: 'var(--font-mono)', flexShrink: 0,
              transition: 'all 0.15s',
            }}
              onMouseEnter={e => { e.target.style.background = 'var(--surface2)'; e.target.style.color = 'var(--text)' }}
              onMouseLeave={e => { e.target.style.background = 'var(--surface)'; e.target.style.color = 'var(--text2)' }}
            >
              {q.slice(0, 32)}...
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={!ready || streaming}
            rows={2}
            placeholder={ready ? 'Ask anything about these videos...' : 'Load videos to start chatting...'}
            style={{
              flex: 1, background: 'var(--surface)', border: '1px solid var(--border2)',
              borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--text)',
              resize: 'none', outline: 'none', fontFamily: 'var(--font-display)',
              opacity: ready ? 1 : 0.4, lineHeight: 1.5,
              transition: 'border-color 0.15s',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--accent-c)'}
            onBlur={e => e.target.style.borderColor = 'var(--border2)'}
          />
          <button onClick={handleSend}
            disabled={!ready || streaming || !input.trim()}
            style={{
              background: ready && input.trim() ? 'var(--accent-c)' : 'var(--surface2)',
              color: ready && input.trim() ? '#fff' : 'var(--text3)',
              border: 'none', borderRadius: 8, padding: '0 18px',
              fontSize: 13, fontWeight: 700, transition: 'all 0.15s',
              opacity: streaming ? 0.5 : 1,
            }}>
            {streaming ? '...' : '→'}
          </button>
        </div>
      </div>
    </div>
  )
}
