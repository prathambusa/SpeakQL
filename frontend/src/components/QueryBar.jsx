import { useState, useRef, useEffect } from 'react'

const STEPS = [
  { icon: '🔍', label: 'Finding relevant tables' },
  { icon: '✍️', label: 'Generating SQL' },
  { icon: '▶️', label: 'Running query' },
  { icon: '✅', label: 'Done' },
]

const DB_LABELS = {
  prod: 'Northwind (invoices & orders)',
  chinook: 'Chinook (music store)',
  financial: 'Financial (stocks & earnings)',
  superstore: 'Superstore (sales & locations)',
}

function dbLabel(db) {
  return DB_LABELS[db.alias] ?? `${db.alias} (${db.dialect})`
}

function StepProgress({ currentStep }) {
  return (
    <div className="flex items-center gap-1 mt-4 flex-wrap justify-center">
      {STEPS.map((step, i) => {
        const done = i < currentStep
        const active = i === currentStep
        return (
          <div key={i} className="flex items-center">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
                done
                  ? 'bg-accent/20 text-accent'
                  : active
                  ? 'bg-accent text-white shadow-lg shadow-accent/30'
                  : 'bg-surface-3 text-ink-2'
              }`}
            >
              <span>{step.icon}</span>
              <span>{step.label}</span>
              {active && (
                <span className="inline-flex">
                  <span className="animate-bounce delay-0">.</span>
                  <span className="animate-bounce delay-100">.</span>
                  <span className="animate-bounce delay-200">.</span>
                </span>
              )}
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`w-4 h-px mx-1 transition-colors duration-300 ${
                  done ? 'bg-accent' : 'bg-surface-3'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function QueryBar({ onSubmit, loading, currentStep, dbAlias, setDbAlias, databases = [] }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!loading && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [loading])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() && !loading) {
        onSubmit(value.trim(), dbAlias)
      }
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (value.trim() && !loading) {
      onSubmit(value.trim(), dbAlias)
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div
          className={`relative rounded-2xl border transition-all duration-200 ${
            loading
              ? 'border-accent/50 shadow-lg shadow-accent/10'
              : 'border-surface-3 hover:border-surface-3 focus-within:border-accent focus-within:shadow-lg focus-within:shadow-accent/10'
          } bg-surface-2`}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Ask anything about your data…"
            rows={2}
            maxLength={500}
            className="w-full bg-transparent text-ink placeholder-ink-2 resize-none px-5 py-4 pr-28 text-base outline-none font-sans leading-relaxed rounded-2xl"
          />

          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            <span className="text-xs text-ink-2/50">{value.length}/500</span>
            <button
              type="submit"
              disabled={!value.trim() || loading}
              className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-all duration-150 active:scale-95"
            >
              {loading ? (
                <span className="flex items-center gap-1.5">
                  <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Running
                </span>
              ) : (
                'Ask →'
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between mt-2 px-1">
          <p className="text-xs text-ink-2">
            Press <kbd className="px-1 py-0.5 bg-surface-3 rounded text-ink-2 font-mono text-xs">Enter</kbd> to run
            &nbsp;·&nbsp;
            <kbd className="px-1 py-0.5 bg-surface-3 rounded text-ink-2 font-mono text-xs">Shift+Enter</kbd> for new line
          </p>
          <label className="flex items-center gap-2 text-xs text-ink-2">
            <span>Database:</span>
            <select
              value={dbAlias}
              onChange={e => setDbAlias(e.target.value)}
              className="bg-surface-3 border border-surface-3 rounded-lg px-2 py-1 text-ink text-xs outline-none focus:border-accent cursor-pointer"
            >
              {databases.length > 0 ? (
                databases.map(db => (
                  <option key={db.alias} value={db.alias}>
                    {dbLabel(db)}
                  </option>
                ))
              ) : (
                <option value={dbAlias}>{dbAlias}</option>
              )}
            </select>
          </label>
        </div>
      </form>

      {loading && <StepProgress currentStep={currentStep} />}
    </div>
  )
}
