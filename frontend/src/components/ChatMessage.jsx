const BADGE_COLORS = {
  A: { bg: '#ff4d4d18', border: '#ff4d4d44', text: '#ff4d4d' },
  B: { bg: '#a855f718', border: '#a855f744', text: '#a855f7' },
}

function SourceBadge({ src }) {
  const colors = BADGE_COLORS[src.video_id] || BADGE_COLORS.A
  return (
    <span style={{
      fontSize: 10, padding: '2px 8px', borderRadius: 20,
      background: colors.bg, border: `1px solid ${colors.border}`,
      color: colors.text, fontFamily: 'var(--font-mono)',
      display: 'inline-flex', alignItems: 'center', gap: 4,
    }}>
      Video {src.video_id} · chunk {src.chunk_index}
    </span>
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className="fade-in" style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
    }}>
      <div style={{ maxWidth: '88%' }}>
        {/* Role */}
        <div style={{
          fontSize: 10, marginBottom: 4, fontFamily: 'var(--font-mono)',
          color: isUser ? 'var(--text3)' : 'var(--accent-c)',
          textAlign: isUser ? 'right' : 'left',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          {isUser ? 'you' : 'ai analyst'}
        </div>

        {/* Bubble */}
        <div style={{
          background: isUser ? 'var(--accent-c)' : 'var(--surface)',
          border: isUser ? 'none' : '1px solid var(--border)',
          borderRadius: isUser ? '12px 12px 4px 12px' : '4px 12px 12px 12px',
          padding: '10px 14px',
          fontSize: 13,
          lineHeight: 1.65,
          color: isUser ? '#fff' : 'var(--text)',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {message.content}
          {message.streaming && (
            <span style={{
              display: 'inline-block', width: 6, height: 14,
              background: 'var(--accent-c)', borderRadius: 2,
              marginLeft: 3, verticalAlign: 'middle',
              animation: 'pulse-dot 0.8s infinite',
            }} />
          )}
        </div>

        {/* Citations */}
        {message.sources?.length > 0 && (
          <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {message.sources.map((src, i) => <SourceBadge key={i} src={src} />)}
          </div>
        )}
      </div>
    </div>
  )
}
