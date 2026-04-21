import React, { useState, useEffect, useCallback } from 'react'
import AISearchSection from '../components/Dashboard/AISearchSection'
import CaseTracker from '../components/Dashboard/CaseTracker'
import RelevantSOPs from '../components/Dashboard/RelevantSOPs'
import AISummaryCard from '../components/Dashboard/AISummaryCard'
import {
  getSOPs,
  getDeviations,
  getCAPAs,
  getAuditFindings,
  getDecisions,
  queryAI,
} from '../api/editorApi'
import './DashboardPage.css'

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [sops, setSops] = useState([])
  const [deviations, setDeviations] = useState([])
  const [capas, setCapas] = useState([])
  const [audits, setAudits] = useState([])
  const [decisions, setDecisions] = useState([])
  const [aiResponse, setAiResponse] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [sopsData, devsData, capsData, auditsData, decsData] = await Promise.all([
        getSOPs().catch(() => []),
        getDeviations().catch(() => []),
        getCAPAs().catch(() => []),
        getAuditFindings().catch(() => []),
        getDecisions().catch(() => []),
      ])

      // Sort SOPs: active first, then by updated_at desc
      const sortedSOPs = Array.isArray(sopsData)
        ? [...sopsData].sort((a, b) => {
            if (a.is_active !== b.is_active) return a.is_active ? -1 : 1
            return new Date(b.updated_at) - new Date(a.updated_at)
          })
        : []

      setSops(sortedSOPs)
      setDeviations(Array.isArray(devsData) ? devsData : [])
      setCapas(Array.isArray(capsData) ? capsData : [])
      setAudits(Array.isArray(auditsData) ? auditsData : [])
      setDecisions(Array.isArray(decsData) ? decsData : [])
    } catch (err) {
      console.error('Dashboard data load failed:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleAISearch = useCallback(async (query) => {
    if (!query?.trim()) return
    setAiLoading(true)
    setAiError(null)
    setAiResponse(null)
    try {
      const result = await queryAI(query.trim())
      setAiResponse({
        query: query.trim(),
        text: result.answer || result.text || result.response || '',
        sources: Array.isArray(result.sources) ? result.sources : [],
        timestamp: new Date(),
      })
    } catch (err) {
      setAiError(err.message || 'Die KI-Anfrage konnte nicht verarbeitet werden.')
    } finally {
      setAiLoading(false)
    }
  }, [])

  // ──────────────────────────────────────────────────────────────
  // Map all real entities into unified "cases" list for CaseTracker
  // Priority: open deviations first, then CAPAs, audits, decisions
  // Max 6 items shown (matches UI card height)
  // ──────────────────────────────────────────────────────────────
  const cases = [
    ...deviations.map(d => ({
      id: d.deviation_number || String(d.id).slice(0, 8),
      title: d.title,
      status: d.external_status || 'open',
      type: 'deviation',
      impact_level: d.impact_level || '',
      category: d.category || '',
      updated_at: d.updated_at,
    })),
    ...capas.map(c => ({
      id: c.capa_number || String(c.id).slice(0, 8),
      title: c.title,
      status: c.external_status || 'open',
      type: 'capa',
      impact_level: '',
      category: c.action_type || '',
      updated_at: c.updated_at,
    })),
    ...audits.map(a => ({
      id: a.finding_number || a.audit_number || String(a.id).slice(0, 8),
      title: a.finding_text || a.question_text || `Audit ${a.audit_number || ''}`.trim(),
      status: a.acceptance_status || 'pending',
      type: 'audit',
      impact_level: '',
      category: a.authority || '',
      updated_at: a.updated_at,
    })),
    ...decisions.map(dec => ({
      id: dec.decision_number || String(dec.id).slice(0, 8),
      title: dec.title,
      status: dec.decision_type || 'decision',
      type: 'decision',
      impact_level: '',
      category: dec.decision_type || '',
      updated_at: dec.updated_at,
    })),
  ]
    // Sort: open/pending first, then by most recently updated
    .sort((a, b) => {
      const openStatuses = ['open', 'pending', 'in_progress', 'active']
      const aOpen = openStatuses.includes((a.status || '').toLowerCase())
      const bOpen = openStatuses.includes((b.status || '').toLowerCase())
      if (aOpen !== bOpen) return aOpen ? -1 : 1
      return new Date(b.updated_at) - new Date(a.updated_at)
    })
    .slice(0, 6)

  // Map SOPs for RelevantSOPs component — use native /api/sops shape
  // { id, sop_number, title, department, current_version, is_active, updated_at }
  const mappedSOPs = sops.slice(0, 3).map(s => ({
    id: String(s.id),
    title: s.title,
    status: s.current_version?.external_status || 'draft',
    version_number: s.current_version?.version_number || '1',
    metadata_json: { sop_number: s.sop_number },
    department: s.department,
    updated_at: s.updated_at,
  }))

  const showSummary = aiResponse || aiLoading || aiError

  return (
    <div className="dashboard-page-container">
      <AISearchSection onSubmit={handleAISearch} loading={aiLoading} />

      {showSummary && (
        <AISummaryCard
          query={aiResponse?.query}
          response={aiResponse?.text}
          sources={aiResponse?.sources || []}
          timestamp={aiResponse?.timestamp}
          loading={aiLoading}
          error={aiError}
        />
      )}

      <div className="dashboard-content-grid">
        <CaseTracker cases={cases} loading={loading} />
        <RelevantSOPs sops={mappedSOPs} loading={loading} />
      </div>
    </div>
  )
}
