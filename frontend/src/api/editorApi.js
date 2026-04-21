const API_BASE = import.meta.env.VITE_API_BASE || ''

// ─────────────────────────────────────────────────────
// Helper: parse error body and throw with backend message
// ─────────────────────────────────────────────────────

async function throwApiError(res, fallbackMsg) {
  let detail = fallbackMsg
  try {
    const body = await res.json()
    if (body?.detail) detail = body.detail
  } catch {
    // Ignore non-JSON error bodies and fall back to the provided message.
  }
  const err = new Error(detail)
  err.status = res.status
  throw err
}

// ─────────────────────────────────────────────────────
// Document (sops) operations
// ─────────────────────────────────────────────────────

export async function createDocument(payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'Failed to create document')
  return res.json()
}

export async function getDocuments() {
  // NOTE: GET /api/editor/docs (list) does NOT exist on the backend.
  // This function exists only for legacy editor compat — do NOT use for dashboard/SOP listing.
  // Use getSOPs() instead for any list/read flows.
  throw new Error('getDocuments() is not supported. Use getSOPs() for listing SOPs.')
}

export async function getDocument(docId) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}`)
  if (!res.ok) await throwApiError(res, 'Failed to load document')
  return res.json()
}

export async function updateDocument(docId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'Failed to update document')
  return res.json()
}

export async function duplicateDocument(docId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/duplicate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'Failed to duplicate document')
  return res.json()
}

// ─────────────────────────────────────────────────────
// Version (sop_versions) operations
// ─────────────────────────────────────────────────────

export async function getVersions(docId) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions`)
  if (!res.ok) await throwApiError(res, 'Failed to load versions')
  return res.json()
}

export async function createVersion(docId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'Failed to create version')
  return res.json()
}

export async function getVersion(docId, versionId) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions/${versionId}`)
  if (!res.ok) await throwApiError(res, 'Failed to load version')
  return res.json()
}

export async function updateVersionStatus(docId, versionId, payload) {
  const res = await fetch(`${API_BASE}/api/editor/docs/${docId}/versions/${versionId}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'Failed to update version status')
  return res.json()
}

// ─────────────────────────────────────────────────────
// Dashboard data APIs
// ─────────────────────────────────────────────────────

export async function getPublicSOPs(status = 'all') {
  const res = await fetch(`${API_BASE}/api/public/sops?status=${status}`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch SOPs')
  return res.json()
}

export async function getSOPs() {
  const res = await fetch(`${API_BASE}/api/sops`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch SOPs')
  return res.json()
}

export async function getDeviations() {
  const res = await fetch(`${API_BASE}/api/deviations`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch deviations')
  return res.json()
}

export async function getDeviationContext(deviationId) {
  const res = await fetch(`${API_BASE}/api/deviations/${deviationId}/context`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch deviation context')
  return res.json()
}

export async function getCAPAs() {
  const res = await fetch(`${API_BASE}/api/capas`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch CAPAs')
  return res.json()
}

export async function getAuditFindings() {
  const res = await fetch(`${API_BASE}/api/audits`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch audit findings')
  return res.json()
}

export async function getDecisions() {
  const res = await fetch(`${API_BASE}/api/decisions`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch decisions')
  return res.json()
}

export async function searchKnowledge(query) {
  const params = new URLSearchParams({ q: query })
  const res = await fetch(`${API_BASE}/api/search?${params}`)
  if (!res.ok) await throwApiError(res, 'Failed to perform knowledge search')
  return res.json()
}

export async function getKnowledgeStats() {
  const res = await fetch(`${API_BASE}/api/stats`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch knowledge stats')
  return res.json()
}

// TODO: Connect to real AI endpoint when available (e.g. POST /api/ai/query)
// The AI endpoint should accept { question: string } and return
// { answer: string, sources: Array<{ id: string, type: string, label: string }> }
export async function queryAI(question, options = {}) {
  const payload = { question }
  if (Array.isArray(options.chat_history) && options.chat_history.length > 0) {
    payload.chat_history = options.chat_history
  }
  if (options.category) {
    payload.category = options.category
  }

  const controller = new AbortController()
  const timeoutMs = 70000
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let res
  try {
    res = await fetch(`${API_BASE}/api/ai/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw new Error('AI query timed out. Please try again.')
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
  if (!res.ok) await throwApiError(res, 'AI query failed')
  return res.json()
}

export async function createLink(payload) {
  const res = await fetch(`${API_BASE}/api/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'Failed to create link')
  return res.json()
}

export async function deleteLink(linkType, linkId) {
  const res = await fetch(`${API_BASE}/api/links/${linkType}/${linkId}`, {
    method: 'DELETE',
  })
  if (!res.ok) await throwApiError(res, 'Failed to delete link')
  return res.json()
}

export async function getRelatedContext(sopId) {
  const res = await fetch(`${API_BASE}/api/sops/${sopId}/related`)
  if (!res.ok) await throwApiError(res, 'Failed to fetch related context')
  return res.json()
}

export async function performAIAction(payload) {
  const res = await fetch(`${API_BASE}/api/ai/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) await throwApiError(res, 'AI action failed')
  return res.json()
}

export async function semanticReindex(entityId) {
  const res = await fetch(`${API_BASE}/api/semantic/reindex`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity_id: entityId }),
  })
  if (!res.ok) await throwApiError(res, 'Failed to trigger reindexing')
  return res.json()
}

export async function extractText(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/extract-text`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) await throwApiError(res, 'OCR extraction failed')
  return res.json()
}
