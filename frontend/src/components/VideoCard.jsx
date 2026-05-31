import { formatNum, formatDuration, formatDate, engagementColor } from '../utils/format'

const PLATFORM_CONFIG = {
  youtube:   { label: 'YouTube',   color: '#ff4d4d', tag: 'Video A' },
  instagram: { label: 'Instagram', color: '#a855f7', tag: 'Video B' },
}

function Stat({ label, value }) {
  return (
    <div style={{
      background: 'var(--surface2)',
      border: '1px solid var(--border)',
      borderRadius: 6,
      padding: '8px 10px',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 2, fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>{value}</div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div style={{ flex: 1, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
      {[80, 120, 60, 90].map((w, i) => (
        <div key={i} className="skeleton" style={{ height: i === 1 ? 48 : 14, width: `${w}%` }} />
      ))}
    </div>
  )
}

function EmptyCard({ label, color }) {
  return (
    <div style={{
      flex: 1, background: 'var(--surface)', border: `1px dashed ${color}33`,
      borderRadius: 12, padding: 16, display: 'flex', alignItems: 'center',
      justifyContent: 'center', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ fontSize: 28 }}>{label === 'Video A' ? '▶' : '📸'}</div>
      <div style={{ fontSize: 12, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>{label} — paste URL above</div>
    </div>
  )
}

export default function VideoCard({ video, loading, videoKey }) {
  const cfg = video ? PLATFORM_CONFIG[video.source] || PLATFORM_CONFIG.youtube : null
  const isA = videoKey === 'A'
  const color = isA ? 'var(--accent-a)' : 'var(--accent-b)'
  const label = `Video ${videoKey}`

  if (loading) return <SkeletonCard />
  if (!video) return <EmptyCard label={label} color={color} />

  const engColor = engagementColor(video.engagement_rate)
  const engagementLabel =
    video.engagement_rate === null || video.engagement_rate === undefined || video.engagement_rate === ''
      ? 'Unavailable'
      : `${video.engagement_rate}%`

  return (
    <div className="fade-in" style={{
      flex: 1, background: 'var(--surface)', border: `1px solid ${color}44`,
      borderRadius: 12, padding: 16, display: 'flex', flexDirection: 'column',
      gap: 10, overflowY: 'auto',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{
          background: color + '22', color, border: `1px solid ${color}55`,
          borderRadius: 20, padding: '2px 10px', fontSize: 11,
          fontFamily: 'var(--font-mono)', fontWeight: 700,
        }}>{label}</span>
        <span style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>
          {cfg?.label}
        </span>
      </div>

      {/* Title */}
      <div style={{
        fontSize: 13, fontWeight: 600, color: 'var(--text)', lineHeight: 1.4,
        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
      }}>{video.title}</div>

      {/* Engagement rate — hero stat */}
      <div style={{
        background: engColor + '18', border: `1px solid ${engColor}44`,
        borderRadius: 8, padding: '10px 14px', textAlign: 'center',
      }}>
        <div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 2, fontFamily: 'var(--font-mono)', textTransform: 'uppercase' }}>Engagement Rate</div>
        <div style={{ fontSize: 28, fontWeight: 800, color: engColor, fontFamily: 'var(--font-mono)' }}>
          {engagementLabel}
        </div>
        {video.engagement_note && (
          <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 4, lineHeight: 1.3 }}>
            {video.engagement_note}
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <Stat label="Views" value={formatNum(video.views)} />
        <Stat label="Likes" value={formatNum(video.likes)} />
        <Stat label="Comments" value={formatNum(video.comments)} />
        <Stat label="Duration" value={formatDuration(video.duration)} />
      </div>

      {video.metadata_note && (
        <div style={{
          fontSize: 10, color: 'var(--text3)', lineHeight: 1.35,
          background: 'var(--surface2)', border: '1px solid var(--border)',
          borderRadius: 6, padding: '7px 9px',
        }}>
          {video.metadata_note}
        </div>
      )}

      {/* Creator */}
      <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px' }}>
        <div style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginBottom: 2 }}>CREATOR</div>
        <div style={{ fontSize: 13, fontWeight: 700 }}>@{video.creator}</div>
        <div style={{ fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--font-mono)' }}>{formatNum(video.follower_count)} followers</div>
      </div>

      {/* Hashtags */}
      {video.hashtags?.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {video.hashtags.slice(0, 6).map((tag, i) => (
            <span key={i} style={{
              fontSize: 10, background: 'var(--surface2)', color: 'var(--accent-c)',
              border: '1px solid var(--border)', borderRadius: 20, padding: '2px 8px',
              fontFamily: 'var(--font-mono)',
            }}>#{tag}</span>
          ))}
        </div>
      )}

      {/* Upload date */}
      <div style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginTop: 'auto' }}>
        Uploaded {formatDate(video.upload_date)}
      </div>
    </div>
  )
}
