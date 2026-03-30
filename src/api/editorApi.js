const API_BASE = 'http://127.0.0.1:8000'

export async function createDocument(payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create document')
  return res.json()
}

export async function getDocument(docId) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}`)
  if (!res.ok) throw new Error('Failed to load document')
  return res.json()
}

export async function updateDocument(docId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to update document')
  return res.json()
}

export async function getVersions(docId) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions`)
  if (!res.ok) throw new Error('Failed to load versions')
  return res.json()
}

export async function createVersion(docId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create version')
  return res.json()
}

export async function getVersion(docId, versionId) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions/${versionId}`)
  if (!res.ok) throw new Error('Failed to load version')
  return res.json()
}

export async function updateVersionStatus(docId, versionId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions/${versionId}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to update version status')
  return res.json()
}
