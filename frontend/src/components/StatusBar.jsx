export default function StatusBar({ rowCount, executionTimeMs, columns }) {
  if (rowCount == null) return null

  return (
    <div className="flex flex-wrap items-center gap-4 text-sm text-ink-2 animate-fade-in">
      <span className="flex items-center gap-1.5">
        <span className="text-accent">■</span>
        <strong className="text-ink">{rowCount.toLocaleString()}</strong> row{rowCount !== 1 ? 's' : ''}
      </span>
      {columns && (
        <span className="flex items-center gap-1.5">
          <span className="text-accent">■</span>
          <strong className="text-ink">{columns.length}</strong> column{columns.length !== 1 ? 's' : ''}
        </span>
      )}
      {executionTimeMs != null && (
        <span className="flex items-center gap-1.5">
          <span className="text-accent">■</span>
          <strong className="text-ink">{executionTimeMs.toFixed(1)}</strong> ms
        </span>
      )}
    </div>
  )
}
