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
  const controller = new AbortController()
  const timeoutMs = 20000
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  const normalizedAction = String(payload?.action || '').trim().toLowerCase().replace(/-/g, '_')
  const sopActionRoute = {
    improve: '/sop/improve',
    rewrite: '/sop/rewrite',
    gap_check: '/sop/gaps',
  }[normalizedAction]

  const routePayload = {
    document_id: payload?.document_id || null,
    section_id: payload?.section_id || null,
    sop_title: payload?.sop_title || null,
    section_title: payload?.section_name || payload?.section_title || 'Selected text',
    section_type: payload?.section_type || 'Paragraph',
    section_text: payload?.text || '',
  }

  if (sopActionRoute) {
    let sopRes
    try {
      sopRes = await fetch(`${API_BASE}${sopActionRoute}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(routePayload),
        signal: controller.signal,
      })
    } catch (err) {
      if (err?.name === 'AbortError') {
        throw new Error('AI action timed out after 20 seconds. Please try again.')
      }
      throw err
    } finally {
      clearTimeout(timer)
    }

    if (sopRes.ok) {
      const sopData = await sopRes.json()
      return normalizeSOPActionResponse(normalizedAction, payload, sopData)
    }

    if (![404, 405].includes(sopRes.status)) {
      await throwApiError(sopRes, 'AI action failed')
    }
  }

  let fallbackRes
  try {
    fallbackRes = await fetch(`${API_BASE}/api/ai/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: normalizedAction,
        text: payload?.text || '',
        sop_title: payload?.sop_title || null,
        section_name: payload?.section_name || payload?.section_title || null,
        section_type: payload?.section_type || null,
      }),
      signal: controller.signal,
    })
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw new Error('AI action timed out after 20 seconds. Please try again.')
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
  if (!fallbackRes.ok) await throwApiError(fallbackRes, 'AI action failed')
  return fallbackRes.json()
}

function normalizeSOPActionResponse(action, payload, response) {
  const result = response?.result || {}

  if (action === 'improve') {
    const improvedText = result.improved_text || payload?.text || ''
    const changesMade = Array.isArray(result.changes_made) ? result.changes_made : []
    return {
      action: 'improve',
      original_text: payload?.text || '',
      suggested_text: renderRichText(improvedText),
      explanation: result.compliance_note || changesMade.join(' '),
      structured_data: {
        improved_text: improvedText,
        changes_made: changesMade,
        compliance_note: result.compliance_note || '',
        improved_version: improvedText,
        reason_for_improvement: result.compliance_note || changesMade.join(' '),
      },
      suggestion_id: response?.suggestion_id,
      status: response?.status,
    }
  }

  if (action === 'rewrite') {
    const rewrittenText = result.rewritten_text || payload?.text || ''
    return {
      action: 'rewrite',
      original_text: payload?.text || '',
      suggested_text: renderRichText(rewrittenText),
      explanation: result.rationale || result.structural_changes || '',
      structured_data: {
        rewritten_text: rewrittenText,
        structural_changes: result.structural_changes || '',
        rationale: result.rationale || '',
        purpose: '',
        scope: '',
        responsibilities: '',
        procedure: splitLinesAsSteps(rewrittenText),
        documentation: '',
      },
      suggestion_id: response?.suggestion_id,
      status: response?.status,
    }
  }

  const gaps = Array.isArray(result.gaps) ? result.gaps : []
  const firstGap = gaps[0] || {}
  return {
    action: 'gap_check',
    original_text: payload?.text || '',
    suggested_text: renderGapCheckHtml(gaps),
    explanation: `Checked ${result.section_assessed || payload?.section_name || 'selected text'} for QA and compliance gaps.`,
    structured_data: {
      issue: firstGap.issue || 'No specific issue returned.',
      explanation: firstGap.explanation || 'No explanation returned.',
      recommendation: firstGap.recommendation || 'No recommendation returned.',
      gaps,
      section_assessed: result.section_assessed || payload?.section_name || 'Selected text',
    },
    suggestion_id: response?.suggestion_id,
    status: response?.status,
  }
}

function renderGapCheckHtml(gaps) {
  if (!Array.isArray(gaps) || gaps.length === 0) {
    return '<p>No structured gaps were returned.</p>'
  }

  return gaps
    .map((gap) => (
      `<div><h3>Issue</h3><p>${escapeHtml(gap.issue || '')}</p><h3>Explanation</h3><p>${escapeHtml(gap.explanation || '')}</p><h3>Recommendation</h3><p>${escapeHtml(gap.recommendation || '')}</p></div>`
    ))
    .join('')
}

function splitLinesAsSteps(text) {
  return String(text || '')
    .split(/\r?\n+/)
    .map((line) => line.replace(/^\s*\d+[.)-]?\s*/, '').trim())
    .filter(Boolean)
}

function renderRichText(text) {
  const lines = String(text || '')
    .split(/\r?\n+/)
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length === 0) {
    return '<p>No suggestion returned.</p>'
  }

  return lines
    .map((line) => `<p>${escapeHtml(line)}</p>`)
    .join('')
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
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
