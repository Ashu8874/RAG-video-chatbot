// frontend/src/components/SuggestedQuestions.jsx

const QUESTIONS = [
  "Why did Video A get more engagement than Video B?",
  "What's the engagement rate of each video?",
  "Compare the hooks in the first 5 seconds",
  "Who is the creator of Video B and their follower count?",
  "Suggest improvements for Video B based on what worked in A",
]

const styles = {
  container: {
    padding: '12px 16px',
    borderBottom: '1px solid var(--border)',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  label: {
    width: '100%',
    fontFamily: 'var(--font-mono)',
    fontSize: '9px',
    color: 'var(--text3)',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    marginBottom: '2px',
  },
  btn: {
    fontFamily: 'var(--font-head)',
    fontSize: '11px',
    color: 'var(--text2)',
    background: 'var(--surface2)',
    border: '1px solid var(--border)',
    borderRadius: '6px',
    padding: '5px 10px',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    outline: 'none',
  },
}

export default function SuggestedQuestions({ onSelect, disabled }) {
  if (disabled) return null

  return (
    <div style={styles.container}>
      <p style={styles.label}>Quick questions</p>
      {QUESTIONS.map((q, i) => (
        <button
          key={i}
          style={styles.btn}
          onClick={() => onSelect(q)}
          onMouseEnter={e => {
            e.target.style.color = 'var(--accent)'
            e.target.style.borderColor = 'var(--accent)'
            e.target.style.background = '#141400'
          }}
          onMouseLeave={e => {
            e.target.style.color = 'var(--text2)'
            e.target.style.borderColor = 'var(--border)'
            e.target.style.background = 'var(--surface2)'
          }}
        >
          {q.length > 42 ? q.slice(0, 42) + '…' : q}
        </button>
      ))}
    </div>
  )
}
