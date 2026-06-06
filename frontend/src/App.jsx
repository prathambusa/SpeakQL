import { useState, useEffect, useCallback } from 'react'
import Nav from './components/Nav'
import QueryPage from './pages/QueryPage'
import DatabasesPage from './pages/DatabasesPage'
import { getDatabases } from './api'

export default function App() {
  const [page, setPage] = useState('query')
  const [dbAlias, setDbAlias] = useState('prod')
  const [databases, setDatabases] = useState([])
  const [loadingDbs, setLoadingDbs] = useState(true)

  const fetchDatabases = useCallback(async () => {
    setLoadingDbs(true)
    try {
      const data = await getDatabases()
      setDatabases(data.databases)
    } catch {
      // backend may still be starting
    } finally {
      setLoadingDbs(false)
    }
  }, [])

  useEffect(() => {
    fetchDatabases()
  }, [fetchDatabases])

  function handleQueryDb(alias) {
    setDbAlias(alias)
    setPage('query')
  }

  return (
    <div className="min-h-screen bg-surface text-ink font-sans">
      <Nav activePage={page} setActivePage={setPage} />

      {page === 'query' ? (
        <QueryPage
          dbAlias={dbAlias}
          setDbAlias={setDbAlias}
          databases={databases}
        />
      ) : (
        <DatabasesPage
          databases={databases}
          loading={loadingDbs}
          onRefresh={fetchDatabases}
          onQuery={handleQueryDb}
        />
      )}

      <footer className="border-t border-surface-3 px-6 py-4 mt-16">
        <p className="text-center text-xs text-ink-2/40">
          SpeakQL — read-only SQL generation powered by Claude
        </p>
      </footer>
    </div>
  )
}
