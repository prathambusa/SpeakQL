export default function Nav({ activePage, setActivePage }) {
  return (
    <header className="border-b border-surface-3 px-6 py-4">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🗣️</span>
          <div>
            <h1 className="text-lg font-semibold tracking-tight leading-none">SpeakQL</h1>
            <p className="text-xs text-ink-2 mt-0.5">Ask your database anything</p>
          </div>
        </div>
        <nav className="flex items-center gap-1 bg-surface-2 rounded-xl p-1">
          {[
            { id: 'query', label: 'Query' },
            { id: 'databases', label: 'Databases' },
          ].map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setActivePage(id)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                activePage === id
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-ink-2 hover:text-ink'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  )
}
