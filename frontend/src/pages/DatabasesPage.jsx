import { useState, useRef } from 'react'
import { uploadDatabase, deleteDatabase } from '../api'

function DialectBadge({ dialect }) {
  const styles = {
    postgresql: 'bg-blue-500/15 text-blue-400',
    sqlite: 'bg-emerald-500/15 text-emerald-400',
  }
  const labels = { postgresql: 'PostgreSQL', sqlite: 'SQLite' }
  const cls = styles[dialect] ?? 'bg-surface-3 text-ink-2'
  const label = labels[dialect] ?? dialect

  return (
    <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${cls}`}>
      {label}
    </span>
  )
}

function SourceBadge({ source }) {
  const map = {
    env: { label: 'Built-in', cls: 'bg-surface-3 text-ink-2' },
    dynamic: { label: 'Connected', cls: 'bg-violet-500/15 text-violet-400' },
    upload: { label: 'Uploaded', cls: 'bg-amber-500/15 text-amber-400' },
  }
  const { label, cls } = map[source] ?? map.env

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>
      {label}
    </span>
  )
}

function DbCard({ db, onQuery, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    setDeleting(true)
    try {
      await onDelete(db.alias)
    } finally {
      setDeleting(false)
      setConfirming(false)
    }
  }

  const isDeletable = db.source !== 'env'

  return (
    <div className="bg-surface-2 border border-surface-3 rounded-2xl p-5 space-y-4 flex flex-col">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-ink truncate">{db.alias}</span>
            <DialectBadge dialect={db.dialect} />
            <SourceBadge source={db.source} />
          </div>
          <p className="text-xs text-ink-2 mt-1.5">
            {db.table_count} table{db.table_count !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => onQuery(db.alias)}
          className="shrink-0 px-3 py-1.5 text-xs font-medium rounded-lg bg-accent/10 text-accent hover:bg-accent hover:text-white transition-all duration-150 active:scale-95"
        >
          Query →
        </button>
      </div>

      {db.tables.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(e => !e)}
            className="text-left text-xs text-ink-2/50 hover:text-ink-2 transition-colors"
          >
            {expanded ? '▾ Hide tables' : '▸ Show tables'}
          </button>
          {expanded && (
            <div className="flex flex-wrap gap-1.5">
              {db.tables.map(t => (
                <span
                  key={t}
                  className="px-2 py-0.5 bg-surface-3 rounded text-xs font-mono text-ink-2"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </>
      )}

      {isDeletable && (
        <div className="flex items-center justify-end pt-1 border-t border-surface-3/50">
          {confirming ? (
            <div className="flex items-center gap-3">
              <span className="text-xs text-ink-2">Remove this database?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-xs font-medium text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
              >
                {deleting ? 'Deleting…' : 'Yes, delete'}
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="text-xs text-ink-2 hover:text-ink transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="text-xs text-ink-2/40 hover:text-red-400 transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      )}
    </div>
  )
}

const ACCEPTED = '.db,.sqlite,.csv,.tsv,.xlsx,.xls,.json,.parquet,.sql'
const FORMAT_HINT = '.db · .sqlite · .sql · .csv · .tsv · .xlsx · .xls · .json · .parquet'

function Spinner({ className = 'h-4 w-4' }) {
  return (
    <svg className={`animate-spin ${className}`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  )
}

function UploadFileForm({ onAdded }) {
  const [alias, setAlias] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!alias.trim() || !file) return
    setLoading(true)
    setStatus(null)
    try {
      const data = await uploadDatabase(alias.trim(), file)
      setStatus({ ok: true, message: data.message })
      setAlias('')
      setFile(null)
      onAdded()
    } catch (err) {
      setStatus({ ok: false, message: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative">
      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 bg-surface-2/80 backdrop-blur-sm rounded-xl z-10 flex flex-col items-center justify-center gap-3">
          <Spinner className="h-7 w-7 text-accent" />
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-ink">Processing your file…</p>
            <p className="text-xs text-ink-2">Uploading · Indexing tables · Generating smart suggestions</p>
            <p className="text-xs text-ink-2/50">This may take 15–30 seconds</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className={`space-y-4 ${loading ? 'pointer-events-none select-none opacity-40' : ''}`}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-ink-2 mb-1.5">Alias</label>
            <input
              value={alias}
              onChange={e => setAlias(e.target.value)}
              placeholder="e.g. sales_data"
              disabled={loading}
              className="w-full bg-surface-3 border border-surface-3 rounded-xl px-3 py-2 text-sm text-ink outline-none focus:border-accent transition-colors disabled:opacity-50"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs text-ink-2 mb-1.5">File</label>
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => !loading && inputRef.current?.click()}
              className={`cursor-pointer border-2 border-dashed rounded-xl px-4 py-3 text-center text-sm transition-colors ${
                dragging
                  ? 'border-accent bg-accent/5 text-accent'
                  : 'border-surface-3 text-ink-2 hover:border-accent/50 hover:text-ink'
              }`}
            >
              {file ? (
                <span className="text-ink font-medium">{file.name}</span>
              ) : (
                <span>Drop a file here, or <span className="text-accent">browse</span></span>
              )}
            </div>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED}
              className="hidden"
              onChange={e => setFile(e.target.files[0] ?? null)}
            />
          </div>
        </div>

        <p className="text-xs text-ink-2/50">{FORMAT_HINT}</p>

        {status && (
          <p className={`text-xs ${status.ok ? 'text-emerald-400' : 'text-red-400'}`}>
            {status.ok ? '✓' : '✗'} {status.message}
          </p>
        )}

        <button
          type="submit"
          disabled={!alias.trim() || !file || loading}
          className="px-5 py-2 rounded-xl bg-accent text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent-hover transition-colors active:scale-95"
        >
          Upload & Connect
        </button>
      </form>
    </div>
  )
}

export default function DatabasesPage({ databases, loading, onRefresh, onQuery }) {
  async function handleDelete(alias) {
    await deleteDatabase(alias)
    onRefresh()
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 space-y-12">
      {/* Connected databases */}
      <section className="space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Connected Databases</h2>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="text-xs text-ink-2 hover:text-ink px-3 py-1.5 rounded-lg hover:bg-surface-2 transition-colors disabled:opacity-40"
          >
            {loading ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>

        {loading && databases.length === 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 bg-surface-2 border border-surface-3 rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : databases.length === 0 ? (
          <p className="text-ink-2 text-sm">No databases connected yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {databases.map(db => (
              <DbCard key={db.alias} db={db} onQuery={onQuery} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </section>

      {/* Add a database */}
      <section className="space-y-5">
        <h2 className="text-xl font-semibold">Add a Database</h2>
        <div className="bg-surface-2 border border-surface-3 rounded-2xl p-6">
          <UploadFileForm onAdded={onRefresh} />
        </div>
      </section>
    </main>
  )
}
