import { useState, useMemo } from 'react'

const MAX_CELL = 80

function inferType(values) {
  const sample = values.filter(v => v != null && v !== '').slice(0, 20)
  if (sample.length === 0) return 'string'
  const allNum = sample.every(v => typeof v === 'number' || (!isNaN(Number(v)) && v !== ''))
  if (allNum) return 'number'
  const dateRe = /^\d{4}-\d{2}-\d{2}/
  const allDate = sample.every(v => typeof v === 'string' && dateRe.test(v))
  if (allDate) return 'date'
  return 'string'
}

function formatCell(value, type) {
  if (value == null) return <span className="text-ink-2/40 italic">null</span>
  if (type === 'date') {
    const d = new Date(value)
    return isNaN(d) ? String(value) : d.toLocaleDateString()
  }
  const str = String(value)
  if (str.length > MAX_CELL) {
    return (
      <span title={str} className="cursor-help">
        {str.slice(0, MAX_CELL)}&hellip;
      </span>
    )
  }
  return str
}

function downloadCsv(columns, rows) {
  const escape = v => {
    const s = v == null ? '' : String(v)
    return s.includes(',') || s.includes('"') || s.includes('\n')
      ? `"${s.replace(/"/g, '""')}"`
      : s
  }
  const lines = [
    columns.map(escape).join(','),
    ...rows.map(row => row.map(escape).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'speakql_results.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export default function ResultsTable({ columns, rows }) {
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const [filter, setFilter] = useState('')

  if (!columns || !rows) return null

  const colTypes = useMemo(
    () => columns.map((_, ci) => inferType(rows.map(r => r[ci]))),
    [columns, rows]
  )

  function handleSort(ci) {
    if (sortCol === ci) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortCol(ci)
      setSortDir('asc')
    }
  }

  const filteredRows = useMemo(() => {
    if (!filter.trim()) return rows
    const q = filter.toLowerCase()
    return rows.filter(row =>
      row.some(cell => cell != null && String(cell).toLowerCase().includes(q))
    )
  }, [rows, filter])

  const sortedRows = useMemo(() => {
    if (sortCol == null) return filteredRows
    return [...filteredRows].sort((a, b) => {
      const av = a[sortCol]
      const bv = b[sortCol]
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = colTypes[sortCol] === 'number'
        ? Number(av) - Number(bv)
        : String(av).localeCompare(String(bv))
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [filteredRows, sortCol, sortDir, colTypes])

  return (
    <div className="w-full animate-fade-in space-y-3">
      <div className="flex items-center justify-between gap-3">
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter results…"
          className="bg-surface-2 border border-surface-3 rounded-lg px-3 py-1.5 text-sm text-ink placeholder-ink-2 outline-none focus:border-accent w-56 transition-colors"
        />
        <button
          onClick={() => downloadCsv(columns, sortedRows)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-2 border border-surface-3 text-xs text-ink-2 hover:text-ink hover:border-accent transition-all duration-150 active:scale-95"
        >
          ⬇ Download CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-surface-3">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-surface-3">
              {columns.map((col, ci) => (
                <th
                  key={ci}
                  onClick={() => handleSort(ci)}
                  className={`px-4 py-3 text-left text-xs font-semibold text-ink-2 uppercase tracking-wider cursor-pointer select-none hover:text-ink hover:bg-surface-2 transition-colors whitespace-nowrap ${
                    colTypes[ci] === 'number' ? 'text-right' : ''
                  }`}
                >
                  <span className="flex items-center gap-1">
                    {colTypes[ci] === 'number' ? (
                      <span className="ml-auto flex items-center gap-1">
                        {col}
                        {sortCol === ci && (
                          <span className="text-accent">{sortDir === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </span>
                    ) : (
                      <>
                        {col}
                        {sortCol === ci && (
                          <span className="text-accent">{sortDir === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-8 text-ink-2">
                  No rows match the filter.
                </td>
              </tr>
            ) : (
              sortedRows.map((row, ri) => (
                <tr
                  key={ri}
                  className={`border-b border-surface-3/50 transition-colors hover:bg-accent/5 ${
                    ri % 2 === 0 ? 'bg-surface' : 'bg-surface-2/30'
                  }`}
                >
                  {row.map((cell, ci) => (
                    <td
                      key={ci}
                      className={`px-4 py-2.5 text-ink font-mono text-xs leading-relaxed max-w-xs ${
                        colTypes[ci] === 'number' ? 'text-right tabular-nums' : ''
                      }`}
                    >
                      {formatCell(cell, colTypes[ci])}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {filteredRows.length < rows.length && (
        <p className="text-xs text-ink-2 text-right">
          Showing {filteredRows.length} of {rows.length} rows
        </p>
      )}
    </div>
  )
}
