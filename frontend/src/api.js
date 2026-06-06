const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}

export function postQuery(question, dbAlias = 'default') {
  return request('/query', {
    method: 'POST',
    body: JSON.stringify({ question, db_alias: dbAlias }),
  })
}

export function getSchema(dbAlias = 'default') {
  return request(`/schema?db_alias=${encodeURIComponent(dbAlias)}`)
}

export function refreshSchema(dbAlias = 'default') {
  return request(`/refresh-schema?db_alias=${encodeURIComponent(dbAlias)}`, {
    method: 'POST',
  })
}

export function getHealth() {
  return request('/health')
}

export function getDatabases() {
  return request('/databases')
}

export function connectDatabase(alias, url) {
  return request('/databases/connect', {
    method: 'POST',
    body: JSON.stringify({ alias, url }),
  })
}

export function getKpis(alias) {
  return request(`/databases/${encodeURIComponent(alias)}/kpis`)
}

export function deleteDatabase(alias) {
  return request(`/databases/${encodeURIComponent(alias)}`, { method: 'DELETE' })
}

export function getSuggestions(alias) {
  return request(`/databases/${encodeURIComponent(alias)}/suggestions`)
}

export function uploadDatabase(alias, file) {
  const form = new FormData()
  form.append('alias', alias)
  form.append('file', file)
  return fetch(`${BASE}/databases/upload`, { method: 'POST', body: form }).then(async res => {
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`${res.status} ${res.statusText}: ${text}`)
    }
    return res.json()
  })
}
