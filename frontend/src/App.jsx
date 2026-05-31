import { useState } from 'react'
import VideoCard from './components/VideoCard'
import ChatPanel from './components/ChatPanel'

const STEPS = ['Downloading transcripts...', 'Transcribing audio...', 'Embedding into ChromaDB...', 'Building RAG chain...']

export default function App() {
  const [ytUrl, setYtUrl] = useState('')
  const [igUrl, setIgUrl] = useState('')
  const [videos, setVideos] = useState({ video_a: null, video_b: null })
  const [loading, setLoading] = useState(false)
  const [ingested, setIngested] = useState(false)
  const [error, setError] = useState('')
  const [stepIdx, setStepIdx] = useState(0)

  const handleIngest = async () => {
    if (!ytUrl.trim() || !igUrl.trim()) {
      setError('Both URLs are required')
      return
    }
    setError('')
    setLoading(true)
    setStepIdx(0)

    // Cycle through loading steps visually
    const interval = setInterval(() => setStepIdx(i => Math.min(i + 1, STEPS.length - 1)), 8000)

    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: ytUrl.trim(), instagram_url: igUrl.trim() }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Ingest failed')
      }
      const data = await res.json()
      setVideos(data)
      setIngested(true)
    } catch (e) {
      setError(e.message)
    } finally {
      clearInterval(interval)
      setLoading(false)
    }
  }

  const handleReset = () => {
    setYtUrl('')
    setIgUrl('')
    setVideos({ video_a: null, video_b: null })
    setIngested(false)
    setError('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg)' }}>

      {/* Header */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 20px', borderBottom: '1px solid var(--border)', flexShrink: 0,
        background: 'var(--surface)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 18 }}>🎬</span>
          <span style={{ fontWeight: 800, fontSize: 16, letterSpacing: '-0.02em' }}>
            Video RAG Analyst
          </span>
          <span style={{
            fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--text3)',
            background: 'var(--surface2)', border: '1px solid var(--border)',
            borderRadius: 4, padding: '2px 6px', marginLeft: 4,
          }}>v1.0</span>
        </div>
        <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text3)' }}>
          LangChain · Groq · ChromaDB · BGE Embeddings
        </div>
      </header>

      {/* URL input */}
      <div style={{
        padding: '10px 20px', borderBottom: '1px solid var(--border)',
        background: 'var(--surface)', flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>

          {/* YouTube */}
          <div style={{ flex: 1, position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
              fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--accent-a)',
              pointerEvents: 'none', fontWeight: 700,
            }}>YT</span>
            <input value={ytUrl} onChange={e => setYtUrl(e.target.value)}
              placeholder="YouTube URL — Video A"
              disabled={loading || ingested}
              style={{
                width: '100%', background: 'var(--surface2)', border: '1px solid var(--border)',
                borderRadius: 8, padding: '9px 12px 9px 34px', fontSize: 12, color: 'var(--text)',
                outline: 'none', fontFamily: 'var(--font-display)', opacity: ingested ? 0.5 : 1,
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent-a)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          {/* Instagram */}
          <div style={{ flex: 1, position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
              fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--accent-b)',
              pointerEvents: 'none', fontWeight: 700,
            }}>IG</span>
            <input value={igUrl} onChange={e => setIgUrl(e.target.value)}
              placeholder="Instagram Reel URL — Video B"
              disabled={loading || ingested}
              style={{
                width: '100%', background: 'var(--surface2)', border: '1px solid var(--border)',
                borderRadius: 8, padding: '9px 12px 9px 34px', fontSize: 12, color: 'var(--text)',
                outline: 'none', fontFamily: 'var(--font-display)', opacity: ingested ? 0.5 : 1,
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent-b)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          {ingested ? (
            <button onClick={handleReset} style={{
              background: 'var(--surface2)', color: 'var(--text2)',
              border: '1px solid var(--border)', borderRadius: 8,
              padding: '9px 16px', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
            }}>↺ Reset</button>
          ) : (
            <button onClick={handleIngest} disabled={loading} style={{
              background: loading ? 'var(--surface2)' : 'var(--accent-c)',
              color: loading ? 'var(--text3)' : '#fff',
              border: 'none', borderRadius: 8,
              padding: '9px 20px', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap',
              transition: 'background 0.15s',
            }}>
              {loading ? STEPS[stepIdx] : 'Analyze Videos'}
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div style={{ fontSize: 11, color: 'var(--accent-a)', marginTop: 6, fontFamily: 'var(--font-mono)' }}>
            ⚠ {error}
          </div>
        )}

        {/* Progress bar */}
        {loading && (
          <div style={{ marginTop: 8, height: 2, background: 'var(--border)', borderRadius: 1, overflow: 'hidden' }}>
            <div style={{
              height: '100%', background: 'var(--accent-c)', borderRadius: 1,
              width: `${((stepIdx + 1) / STEPS.length) * 100}%`,
              transition: 'width 1s ease',
            }} />
          </div>
        )}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>

        {/* Video cards */}
        <div style={{ width: '55%', display: 'flex', gap: 12, padding: 16, overflow: 'hidden' }}>
          <VideoCard video={videos.video_a} loading={loading} videoKey="A" />
          <VideoCard video={videos.video_b} loading={loading} videoKey="B" />
        </div>

        {/* Chat panel */}
        <div style={{ width: '45%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ChatPanel ready={ingested} />
        </div>
      </div>
    </div>
  )
}
