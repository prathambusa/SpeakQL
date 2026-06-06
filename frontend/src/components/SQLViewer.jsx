import { useState } from 'react'

export default function SQLViewer({ sql }) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  if (!sql) return null

  function handleCopy() {
    navigator.clipboard.writeText(sql).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="w-full animate-fade-in">
      <button
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-2 text-sm text-ink-2 hover:text-ink transition-colors group"
      >
        <span
          className={`transition-transform duration-200 text-accent ${
            expanded ? 'rotate-90' : ''
          }`}
        >
          ▶
        </span>
        <span className="font-medium">Generated SQL</span>
        <span className="text-xs text-ink-2/50">(click to {expanded ? 'collapse' : 'expand'})</span>
      </button>

      {expanded && (
        <div className="mt-2 relative rounded-xl border border-surface-3 overflow-hidden animate-fade-in">
          <div className="flex items-center justify-between px-4 py-2 bg-surface-2 border-b border-surface-3">
            <span className="text-xs font-mono text-ink-2 uppercase tracking-wider">SQL</span>
            <button
              onClick={handleCopy}
              className={`text-xs px-3 py-1 rounded-lg transition-all duration-150 ${
                copied
                  ? 'bg-success/20 text-success'
                  : 'bg-surface-3 text-ink-2 hover:bg-surface-3/80 hover:text-ink active:scale-95'
              }`}
            >
              {copied ? '✓ Copied' : '⎘ Copy'}
            </button>
          </div>
          <pre className="overflow-x-auto p-4 text-sm font-mono text-ink leading-relaxed bg-surface">
            <code>{sql}</code>
          </pre>
        </div>
      )}
    </div>
  )
}
