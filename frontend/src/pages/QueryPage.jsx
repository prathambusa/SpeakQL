import { useState, useEffect } from 'react'
import QueryBar from '../components/QueryBar'
import ResultsTable from '../components/ResultsTable'
import SQLViewer from '../components/SQLViewer'
import StatusBar from '../components/StatusBar'
import ErrorBanner from '../components/ErrorBanner'
import { postQuery, getSuggestions, getKpis } from '../api'

const EXAMPLE_QUESTIONS = {
  prod: [
    'Who are the top 10 customers by total order value?',
    'Which products have never been ordered?',
    'Show me monthly revenue for the last year',
    'Which employees handled the most orders?',
  ],
  chinook: [
    'Which artists have the most albums?',
    'What are the top 5 selling tracks of all time?',
    'Which invoices are over $10?',
    'Show me customers by country with their total spend',
  ],
  financial: [
    'Which stocks have the highest average price?',
    'Show me quarterly earnings for Apple',
    'Which companies paid the most dividends this year?',
    'What are the top analyst buy ratings?',
  ],
  superstore: [
    'Which cities have the highest total sales?',
    'What is the profit margin by product category?',
    'Show me the top 10 customers by revenue',
    'Which states have the most returns?',
  ],
}

const STEP_RETRIEVE = 0
const STEP_GENERATE = 1
const STEP_EXECUTE = 2
const STEP_DONE = 3

function Spinner({ className = 'h-3.5 w-3.5' }) {
  return (
    <svg className={`animate-spin ${className}`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  )
}

function SkeletonTable() {
  return (
    <div className="w-full space-y-2 animate-pulse">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="h-8 skeleton rounded-lg" />
      ))}
    </div>
  )
}

const GRID_COLS = ['', 'grid-cols-1', 'grid-cols-2', 'grid-cols-3', 'grid-cols-4']

function KpiCards({ kpis, loading }) {
  if (loading) {
    return (
      <div className="flex justify-center">
        <div className="inline-grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 w-44 sm:w-52 bg-surface-2 border border-surface-3 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }
  if (!kpis || kpis.length === 0) return null

  const cols = Math.min(kpis.length, 4)
  // On mobile collapse to 2 cols when there are 3-4 cards
  const gridClass = cols <= 2
    ? GRID_COLS[cols]
    : `grid-cols-2 sm:${GRID_COLS[cols]}`

  return (
    <div className="flex justify-center">
      <div className={`inline-grid ${gridClass} gap-3`}>
        {kpis.map(kpi => (
          <div
            key={kpi.label}
            className="bg-surface-2 border border-surface-3 rounded-xl px-4 py-3 w-44 sm:w-52 space-y-0.5"
          >
            <p className="text-xs text-ink-2 leading-snug">{kpi.label}</p>
            <p className="text-lg font-semibold text-ink leading-tight">{kpi.value}</p>
            {kpi.sub && (
              <p className="text-xs text-ink-2/50 truncate">{kpi.sub}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function QueryPage({ dbAlias, setDbAlias, databases }) {
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [result, setResult] = useState(null)
  const [suggestionCache, setSuggestionCache] = useState({})
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [kpiCache, setKpiCache] = useState({})
  const [loadingKpis, setLoadingKpis] = useState(false)

  // Fetch suggestions from the API when switching to a non-built-in database
  useEffect(() => {
    if (dbAlias in EXAMPLE_QUESTIONS) return
    if (dbAlias in suggestionCache) return

    let cancelled = false
    setLoadingSuggestions(true)

    getSuggestions(dbAlias)
      .then(data => {
        if (!cancelled) {
          setSuggestionCache(c => ({ ...c, [dbAlias]: data.suggestions ?? [] }))
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSuggestionCache(c => ({ ...c, [dbAlias]: [] }))
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingSuggestions(false)
      })

    return () => { cancelled = true }
  }, [dbAlias])

  // Fetch KPIs whenever the database changes
  useEffect(() => {
    if (dbAlias in kpiCache) return

    let cancelled = false
    setLoadingKpis(true)

    getKpis(dbAlias)
      .then(data => {
        if (!cancelled) setKpiCache(c => ({ ...c, [dbAlias]: data.kpis ?? [] }))
      })
      .catch(() => {
        if (!cancelled) setKpiCache(c => ({ ...c, [dbAlias]: [] }))
      })
      .finally(() => {
        if (!cancelled) setLoadingKpis(false)
      })

    return () => { cancelled = true }
  }, [dbAlias])

  async function handleSubmit(question, alias) {
    setLoading(true)
    setResult(null)
    setCurrentStep(STEP_RETRIEVE)

    const stepTimer1 = setTimeout(() => setCurrentStep(STEP_GENERATE), 800)
    const stepTimer2 = setTimeout(() => setCurrentStep(STEP_EXECUTE), 2200)

    try {
      const data = await postQuery(question, alias)
      clearTimeout(stepTimer1)
      clearTimeout(stepTimer2)
      setCurrentStep(STEP_DONE)
      setResult(data)
    } catch (err) {
      clearTimeout(stepTimer1)
      clearTimeout(stepTimer2)
      setResult({ error: err.message, question })
    } finally {
      setLoading(false)
    }
  }

  const hasError = result?.error
  const hasClarify = result?.clarify
  const hasResults = result?.columns && result?.rows && !hasError && !hasClarify
  const examples = EXAMPLE_QUESTIONS[dbAlias] ?? suggestionCache[dbAlias] ?? []
  const kpis = kpiCache[dbAlias] ?? []
  const showKpis = !result && !loading && (loadingKpis || kpis.length > 0)

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 space-y-8">
      <section className="flex flex-col items-center gap-2">
        <h2 className="text-3xl font-semibold text-center leading-snug">
          What do you want to know<br className="hidden sm:block" /> about your data?
        </h2>
        <p className="text-ink-2 text-sm text-center">
          Type a plain-English question. SpeakQL writes and runs the SQL for you.
        </p>
      </section>

      {/* KPI snapshot — shown before any query is run */}
      {showKpis && (
        <KpiCards kpis={kpis} loading={loadingKpis} />
      )}

      <QueryBar
        onSubmit={handleSubmit}
        loading={loading}
        currentStep={currentStep}
        dbAlias={dbAlias}
        setDbAlias={setDbAlias}
        databases={databases}
      />

      {loading && !result && <SkeletonTable />}

      {result && !loading && (
        <div className="space-y-5 animate-fade-in">
          <p className="text-ink-2 text-sm">
            <span className="text-ink-2/50">You asked: </span>
            <span className="text-ink font-medium">"{result.question}"</span>
          </p>

          <ErrorBanner
            message={hasError ? result.error : null}
            clarify={hasClarify}
            clarifyMessage={result.clarify_message}
          />

          {result.sql && <SQLViewer sql={result.sql} />}

          {hasResults && (
            <StatusBar
              rowCount={result.row_count}
              executionTimeMs={result.execution_time_ms}
              columns={result.columns}
            />
          )}

          {hasResults && <ResultsTable columns={result.columns} rows={result.rows} />}

          {result.reasoning_trace && (
            <details className="mt-2">
              <summary className="text-xs text-ink-2/50 cursor-pointer hover:text-ink-2 transition-colors">
                Reasoning trace
              </summary>
              <pre className="mt-2 p-4 bg-surface-2 rounded-xl text-xs font-mono text-ink-2 whitespace-pre-wrap overflow-x-auto border border-surface-3">
                {result.reasoning_trace}
              </pre>
            </details>
          )}
        </div>
      )}

      {!loading && !result && (
        <div className="text-center py-16 text-ink-2 space-y-3">
          <p className="text-4xl">⌨️</p>
          <p className="text-sm">Start by asking a question above.</p>

          {loadingSuggestions ? (
            <div className="flex items-center justify-center gap-2 mt-6 text-xs text-ink-2/60">
              <Spinner />
              <span>Generating smart suggestions for this database…</span>
            </div>
          ) : examples.length > 0 ? (
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {examples.map(q => (
                <button
                  key={q}
                  onClick={() => handleSubmit(q, dbAlias)}
                  className="px-3 py-1.5 rounded-full bg-surface-2 border border-surface-3 text-xs text-ink-2 hover:text-ink hover:border-accent transition-all duration-150 active:scale-95"
                >
                  {q}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </main>
  )
}
