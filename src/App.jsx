/**
 * App.jsx
 *
 * Main application component for the AI-LAW Editor.
 * This component handles the Tiptap editor initialization, state management for versions,
 * contract variables, workflow status, OCR upload, and renders the layout including the MenuBar,
 * StatusBar, and various dialog modals.
 */

import SOPMetadataPanel from './components/SOP/SOPMetadataPanel'
import SOPReferencesPanel from './components/SOP/SOPReferencesPanel'
import SOPActions from './components/SOP/SOPActions'
import SOPTimeline from './components/SOP/SOPTimeline'
import SOPAuditTrail from './components/SOP/SOPAuditTrail'
import {
  DEFAULT_SOP_VERSION_METADATA,
  SOP_STATES,
} from './utils/sopConstants'
import { transitionSOP, canEditSOP } from './utils/sopStateMachine'
import { validateSOPTransition } from './utils/sopValidation'
import sopWorkflowConfig from './utils/sopWorkflowConfig'


import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import UniqueID from '@tiptap/extension-unique-id'
import Link from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import { Table } from '@tiptap/extension-table'
import { TableRow } from '@tiptap/extension-table-row'
import { TableCell } from '@tiptap/extension-table-cell'
import { TableHeader } from '@tiptap/extension-table-header'
import { extractPlaceholdersFromText } from './utils/resolveVariables'
import { printDocument } from './utils/printHelpers'
import TopNavbar from './components/TopNavbar'
import { MenuBar } from './components/MenuBar'
import StatusBar from './components/StatusBar'
import LinkModal from './components/LinkModal'
import PreviewModal from './components/PreviewModal'
import SideBySideViewer from './diff/SideBySideViewer'
import Toast from './components/Toast'

import VariablesPanel from './components/contract/VariablesPanel'
import WorkflowTimeline from './components/contract/WorkflowTimeline'
import ReviewActions from './components/contract/ReviewActions'
import ReviewLinkPanel from './components/contract/ReviewLinkPanel'

import useContractVariables from './hooks/useContractVariables'
import { WORKFLOW_LABELS, WORKFLOW_STATES } from './utils/contractConstants'
import {
  createReviewToken,
  buildReviewLink,
  getReviewParamsFromUrl,
} from './utils/reviewLinkUtils'

import { debounce } from 'lodash'
import { useState, useEffect, useCallback, useRef, useMemo } from 'react'

import {
  createDocument,
  getDocument,
  updateDocument,
  getVersions,
  createVersion,
  getVersion,
  updateVersionStatus,
  duplicateDocument,
} from './api/editorApi'

import { isEditorContentEmpty } from './utils/editorUtils'

import { PlaceholderHighlight } from './extensions/PlaceholderHighlight'
import { PlaceholderSuggestion } from './extensions/PlaceholderSuggestion'

import { mapOCRBlocksToHTML } from './utils/mapOCRBlocksToHTML'
import { formatOCRText } from './utils/formatOCRText'

import featureFlags from './config/featureFlags'
import './App.css'

const STORAGE_KEY = 'tiptap_editor_v5_stable'

/**
 * Normalize backend metadata_json into the shape the frontend expects:
 * { sopStatus, sopMetadata: {...fields}, auditTrail, versionNote, ... }
 *
 * The backend stores whatever the frontend last saved.
 * - If previously saved by the frontend, metadata already has sopMetadata + sopStatus.
 * - If seeded raw from DB (flat fields), we wrap it into sopMetadata.
 */
const normalizeMeta = (rawMeta) => {
  if (!rawMeta || typeof rawMeta !== 'object') return { ...DEFAULT_SOP_VERSION_METADATA }
  // Already has the expected frontend shape — use as-is
  if (rawMeta.sopMetadata !== undefined) return rawMeta
  // Flat/seeded metadata — treat the whole object as sopMetadata fields
  return {
    ...DEFAULT_SOP_VERSION_METADATA,
    sopMetadata: { ...DEFAULT_SOP_VERSION_METADATA.sopMetadata, ...rawMeta },
    sopStatus: rawMeta.sopStatus || DEFAULT_SOP_VERSION_METADATA.sopStatus,
    auditTrail: rawMeta.auditTrail || [],
  }
}

const formatTimestamp = (date) => {
  const d = date || new Date()
  const pad = (n) => n.toString().padStart(2, '0')
  let hours = d.getHours()
  const ampm = hours >= 12 ? 'pm' : 'am'
  hours = hours % 12
  hours = hours ? hours : 12
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} , ${hours}:${pad(d.getMinutes())} ${ampm}`
}

const saveToStorage = (updatedVersions) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedVersions))
}

const App = () => {
  const editorRef = useRef(null)
  const isInitialized = useRef(false)
  const initStarted = useRef(false)

  const [versions, setVersions] = useState([])
  const [currentVersionId, setCurrentVersionId] = useState('v1')
  const [documentId, setDocumentId] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)
  const [blockCount, setBlockCount] = useState(0)
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false)
  const [linkModalInitialUrl, setLinkModalInitialUrl] = useState('')
  const [profile, setProfile] = useState(featureFlags.defaultProfile)
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false)

  const [diffOldVersion, setDiffOldVersion] = useState(null)
  const [diffNewVersion, setDiffNewVersion] = useState(null)
  const [isDiffMode, setIsDiffMode] = useState(false)

  const [showVariablesPanel, setShowVariablesPanel] = useState(true)

  const [isOcrLoading, setIsOcrLoading] = useState(false)
  const [ocrError, setOcrError] = useState('')
  const [sopFieldErrors, setSOPFieldErrors] = useState({})
  const [isClientReviewMode, setIsClientReviewMode] = useState(false)
  const [reviewLink, setReviewLink] = useState('')
  const [reviewToken, setReviewToken] = useState(null)

  // Toast notification state — { message, type }
  const [toast, setToast] = useState(null)
  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type })
  }, [])

  const {
    variables,
    setVariables,
    updateVariable,
    variableEntries,
    resetVariables,
    syncPlaceholders,
  } = useContractVariables()

  const rawProfile = profile?.toLowerCase() || featureFlags.defaultProfile
  // If the stored/selected profile is disabled, fall back to the default profile
  const normalizedProfile =
    (rawProfile === 'contract' && !featureFlags.contractProfileEnabled) ||
    (rawProfile === 'sop' && !featureFlags.sopProfileEnabled)
      ? featureFlags.defaultProfile
      : rawProfile
  const isContractProfile = normalizedProfile === 'contract' && featureFlags.contractProfileEnabled
  const isSOPProfile = normalizedProfile === 'sop'

  const currentVersion = versions.find((v) => v.id === currentVersionId)

  const workflowStatus =
    currentVersion?.metadata?.reviewStatus || WORKFLOW_STATES.DRAFT

  const currentReviewComments =
    currentVersion?.metadata?.reviewComments || []

  const currentSentForReviewAt =
    currentVersion?.metadata?.sentForReviewAt || null

  const currentReviewToken =
    currentVersion?.metadata?.reviewToken || null

  const currentSOPStatus =
    currentVersion?.metadata?.sopStatus || SOP_STATES.DRAFT

  const currentSOPAuditTrail =
    currentVersion?.metadata?.auditTrail || []

  const currentSOPMetadata =
    currentVersion?.metadata?.sopMetadata ||
    DEFAULT_SOP_VERSION_METADATA.sopMetadata

  const isEditorEditable =
    !isClientReviewMode &&
    (isContractProfile || canEditSOP(currentSOPStatus))

  const canCreateNewVersion = !isClientReviewMode

  const handleProfileChange = useCallback((value) => {
    const next = value?.toLowerCase() || featureFlags.defaultProfile
    // Prevent switching to a disabled profile
    if (next === 'contract' && !featureFlags.contractProfileEnabled) return
    if (next === 'sop' && !featureFlags.sopProfileEnabled) return
    setProfile(next)
  }, [])

  const updateCurrentVersionMetadata = useCallback(
    (updates) => {
      setVersions((prev) => {
        const updated = prev.map((v) =>
          v.id === currentVersionId
            ? {
              ...v,
              metadata: {
                ...(v.metadata || {}),
                ...updates,
              },
            }
            : v
        )

        saveToStorage(updated)
        return updated
      })
    },
    [currentVersionId]
  )

  const updateSOPMetadata = useCallback(
    (nextMetadata) => {
      updateCurrentVersionMetadata({
        sopMetadata: nextMetadata,
      })

      setSOPFieldErrors((prev) => {
        if (!prev || Object.keys(prev).length === 0) return prev

        const nextErrors = { ...prev }

        if (nextMetadata?.documentId?.trim()) delete nextErrors.documentId
        if (nextMetadata?.author?.trim()) delete nextErrors.author
        if (nextMetadata?.reviewer?.trim()) delete nextErrors.reviewer

        return nextErrors
      })
    },
    [updateCurrentVersionMetadata]
  )

  const updateSOPReferences = useCallback(
    (nextReferences) => {
      updateCurrentVersionMetadata({
        sopMetadata: {
          ...(currentVersion?.metadata?.sopMetadata ||
            DEFAULT_SOP_VERSION_METADATA.sopMetadata),
          references: nextReferences,
        },
      })
    },
    [currentVersion, updateCurrentVersionMetadata]
  )

  const sendForReview = useCallback(() => {
    updateCurrentVersionMetadata({
      reviewStatus: WORKFLOW_STATES.UNDER_REVIEW,
      sentForReviewAt: new Date().toISOString(),
    })
  }, [updateCurrentVersionMetadata])

  const markApproved = useCallback(() => {
    updateCurrentVersionMetadata({
      reviewStatus: WORKFLOW_STATES.ACCEPTED,
    })
  }, [updateCurrentVersionMetadata])

  const markChangesRequested = useCallback(() => {
    updateCurrentVersionMetadata({
      reviewStatus: WORKFLOW_STATES.CHANGES_REQUESTED,
    })
  }, [updateCurrentVersionMetadata])

  const markRejected = useCallback(() => {
    updateCurrentVersionMetadata({
      reviewStatus: WORKFLOW_STATES.REJECTED,
    })
  }, [updateCurrentVersionMetadata])

  const addReviewComment = useCallback(
    (text) => {
      if (!text?.trim()) return

      const existingComments = currentVersion?.metadata?.reviewComments || []

      updateCurrentVersionMetadata({
        reviewComments: [
          ...existingComments,
          {
            text: text.trim(),
            createdAt: new Date().toISOString(),
          },
        ],
      })
    },
    [currentVersion, updateCurrentVersionMetadata]
  )

  const generateReviewLink = useCallback(() => {
    if (!currentVersionId) return

    const token = currentReviewToken || createReviewToken()

    updateCurrentVersionMetadata({
      reviewToken: token,
    })

    const link = buildReviewLink({
      token,
      versionId: currentVersionId,
    })

    setReviewToken(token)
    setReviewLink(link)
  }, [currentVersionId, currentReviewToken, updateCurrentVersionMetadata])

  const debouncedSave = useMemo(
    () =>
      debounce(async (json, metadata) => {
        if (!documentId) return
        setIsSaving(true)

        try {
          await updateDocument(documentId, {
            doc_json: json,
            metadata_json: metadata,
          })
          setLastSaved(new Date())
        } catch (error) {
          console.error('Autosave failed:', error)
        } finally {
          setTimeout(() => setIsSaving(false), 800)
        }
      }, 2000),
    [documentId]
  )

  const extensions = useMemo(
    () => [
      StarterKit,
      Underline,
      Link.configure({
        openOnClick: true,
        autolink: true,
        linkOnPaste: true,
      }),
      UniqueID.configure({
        types: ['heading', 'paragraph', 'bulletList', 'orderedList', 'table'],
        attributeName: 'block-id',
      }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      PlaceholderHighlight,
      PlaceholderSuggestion,
    ],
    []
  )

  const editor = useEditor({
    extensions,
    editorProps: {
      attributes: { class: 'tiptap' },
      handleKeyDown: (_view, event) => {
        const e = event
        const mod = e.ctrlKey || e.metaKey
        const key = e.key.toLowerCase()

        if (!isEditorEditable) return false

        if (mod && e.altKey && key === 'p') {
          e.preventDefault()
          setIsPreviewModalOpen(true)
          return true
        }

        if (mod && !e.shiftKey && !e.altKey && key === 'u') {
          e.preventDefault()
          editor?.chain().focus().toggleUnderline().run()
          return true
        }

        if (mod && !e.shiftKey && !e.altKey && key === 'k') {
          e.preventDefault()
          setLinkModalInitialUrl(editor?.getAttributes('link')?.href || '')
          setIsLinkModalOpen(true)
          return true
        }

        if (!mod && e.altKey && key === '1') {
          e.preventDefault()
          editor?.chain().focus().toggleHeading({ level: 1 }).run()
          return true
        }

        if (!mod && e.altKey && key === '2') {
          e.preventDefault()
          editor?.chain().focus().toggleHeading({ level: 2 }).run()
          return true
        }

        if (!mod && e.altKey && key === '3') {
          e.preventDefault()
          editor?.chain().focus().toggleHeading({ level: 3 }).run()
          return true
        }

        if (mod && e.shiftKey && !e.altKey && key === '7') {
          e.preventDefault()
          editor?.chain().focus().toggleOrderedList().run()
          return true
        }

        if (mod && e.shiftKey && !e.altKey && key === 'l') {
          e.preventDefault()
          editor?.chain().focus().toggleBulletList().run()
          return true
        }

        if (!mod && e.altKey && key === 't') {
          e.preventDefault()
          editor?.chain()
            .focus()
            .insertTable({ rows: 4, cols: 4, withHeaderRow: true })
            .run()
          return true
        }

        if (mod && e.shiftKey && key === 'x') {
          e.preventDefault()
          editor?.chain().focus().toggleStrike().run()
          return true
        }

        return false
      },
    },
  })

  const openVersionInClientReviewMode = useCallback(
    (tokenFromUrl, versionIdFromUrl) => {
      if (!tokenFromUrl || !versionIdFromUrl || !editor || versions.length === 0) return

      const matchedVersion = versions.find(
        (v) =>
          v.id === versionIdFromUrl &&
          v.metadata?.reviewToken === tokenFromUrl
      )

      if (!matchedVersion) {
        setIsClientReviewMode(false)
        return
      }

      setCurrentVersionId(matchedVersion.id)
      editor.commands.setContent(matchedVersion.json, false)
      setVariables(matchedVersion.metadata?.variables || {})
      setIsClientReviewMode(true)
      setReviewToken(tokenFromUrl)
      setSOPFieldErrors({})
      setReviewLink(
        buildReviewLink({
          token: tokenFromUrl,
          versionId: matchedVersion.id,
        })
      )
    },
    [editor, versions, setVariables]
  )

  const updateSOPState = useCallback(
    (nextStatus, note = '', actor = 'Author') => {
      const currentTrail = currentVersion?.metadata?.auditTrail || []
      const statusNow =
        currentVersion?.metadata?.sopStatus || SOP_STATES.DRAFT
      const vLabel = currentVersion?.versionNumber ? `v${currentVersion.versionNumber}` : (currentVersionId || 'v1')

      const result = transitionSOP({
        currentStatus: statusNow,
        nextStatus,
        note,
        actor,
        version: vLabel,
        currentTrail,
      })

      if (!result.ok) {
        console.error(result.error)
        return null
      }

      const nextMeta = {
        sopStatus: nextStatus,
        auditTrail: result.nextTrail,
        versionNote: note || currentVersion?.metadata?.versionNote || '',
        approvedBy:
          nextStatus === SOP_STATES.EFFECTIVE
            ? actor
            : currentVersion?.metadata?.approvedBy || '',
        obsoleteReason:
          nextStatus === SOP_STATES.OBSOLETE
            ? note || 'Marked obsolete'
            : currentVersion?.metadata?.obsoleteReason || '',
      }

      updateCurrentVersionMetadata(nextMeta)
      return nextMeta
    },
    [currentVersion, updateCurrentVersionMetadata, currentVersionId]
  )

  /**
   * Generic SOP action handler — replaces submitSOPForReview, approveSOP,
   * sendSOPBackToDraft, and markSOPObsolete with a single config-driven function.
   */
  const executeSOPAction = useCallback(
    async (actionId, { note = '', actionFields = {} } = {}) => {
      const transition = sopWorkflowConfig.transitions[actionId]
      if (!transition) return { ok: false, error: `Unknown action: ${actionId}` }

      // Validate using config-driven rules
      const result = validateSOPTransition(
        actionId,
        { metadata: currentSOPMetadata, note, actionFields },
        sopWorkflowConfig
      )

      setSOPFieldErrors(result.fieldErrors || {})
      if (!result.ok) return result

      // Persist action-specific extra fields into version metadata
      const extraMetadata = {}
      for (const field of transition.fields || []) {
        if (actionFields[field.key] !== undefined) {
          extraMetadata[field.key] = actionFields[field.key]
        }
      }
      if (Object.keys(extraMetadata).length > 0) {
        updateCurrentVersionMetadata(extraMetadata)
      }

      // Execute the state transition
      const appliedMetadata = updateSOPState(
        transition.to,
        note || `Action: ${actionId}`
      )

      // Sync status to backend
      if (documentId && currentVersionId && appliedMetadata) {
        try {
          // Explicitly merge current metadata + extra fields + new transition data
          // to ensure the backend receives the absolute source of truth.
          const finalMetadata = {
            ...(currentVersion?.metadata || {}),
            ...extraMetadata,
            ...appliedMetadata,
          }

          await updateVersionStatus(documentId, currentVersionId, {
            status: transition.to,
            metadata_json: finalMetadata,
          })
        } catch (err) {
          console.error('Failed to sync SOP status to backend:', err)
        }
      }

      setSOPFieldErrors({})
      return { ok: true }
    },
    [currentSOPMetadata, updateCurrentVersionMetadata, updateSOPState, documentId, currentVersionId, currentVersion]
  )

  useEffect(() => {
    if (isContractProfile && featureFlags.contractProfileEnabled) {
      setShowVariablesPanel(true)
    }
  }, [isContractProfile])

  useEffect(() => {
    if (editor) {
      window.editor = editor
      window.editorInstance = editor
    }

    return () => {
      if (window.editor === editor) delete window.editor
      if (window.editorInstance === editor) delete window.editorInstance
    }
  }, [editor])

  useEffect(() => {
    if (!editor) return
    editor.setEditable(isEditorEditable)
  }, [editor, isEditorEditable])

  useEffect(() => {
    if (!editor) return

    if (editor.storage?.placeholderSuggestion) {
      editor.storage.placeholderSuggestion.items = [
        'ClientName',
        'Address',
        'Date',
        'Amount',
      ]
    }
  }, [editor])

  const manualSave = useCallback(async () => {
    if (!editor || !isEditorEditable) return

    // Pre-save: capture state
    const json = editor.getJSON()
    const currentVer = versions.find((v) => v.id === currentVersionId)
    const metadata = {
      ...(currentVer?.metadata || {}),
      variables,
    }

    debouncedSave.cancel()
    setIsSaving(true)

    try {
      if (!documentId) {
        // CASE: First save for a brand new unsaved document
        const newDoc = await createDocument({
          title: variables?.sopMetadata?.title || 'Untitled SOP',
          profile: 'sop',
          doc_json: json,
          metadata_json: metadata,
        })

        // Identify created doc
        const createdId = newDoc.id
        const createdVerId = newDoc.current_version_id

        const newVerObj = {
          id: createdVerId,
          versionNumber: newDoc.version_number || '1',
          json: json,
          timestamp: formatTimestamp(new Date()),
          isFormatted: true,
          metadata: normalizeMeta(newDoc.metadata_json),
        }

        setDocumentId(createdId)
        localStorage.setItem('current_document_id', createdId)
        setVersions([newVerObj])
        setCurrentVersionId(createdVerId)
        showToast('Document created and saved')
      } else {
        // CASE: Normal update to existing document
        await updateDocument(documentId, {
          doc_json: json,
          metadata_json: metadata,
        })

        setVersions((prev) =>
          prev.map((v) =>
            v.id === currentVersionId
              ? {
                ...v,
                json,
                timestamp: formatTimestamp(new Date()),
                metadata: normalizeMeta(metadata),
              }
              : v
          )
        )
        showToast('Saved successfully')
      }
      setLastSaved(new Date())
    } catch (error) {
      console.error('Save failed:', error)
      showToast('Save failed', 'error')
    } finally {
      setTimeout(() => setIsSaving(false), 800)
    }
  }, [editor, isEditorEditable, documentId, versions, currentVersionId, variables, debouncedSave, showToast])

  const createNewVersionHandler = useCallback(async () => {
    if (!editor || !canCreateNewVersion || !documentId) return

    const editorJson = editor.getJSON()

    // ── Empty-content detection ──────────────────────────────────────────────
    // If the editor is blank/only has empty paragraphs, do NOT save blank content.
    // Prefer the previous version's content as a safe fallback instead.
    let finalJson = editorJson

    if (isEditorContentEmpty(editorJson)) {
      // Try to fall back to the current version's already-saved content
      const previousContent = currentVersion?.json || null

      if (!previousContent || isEditorContentEmpty(previousContent)) {
        // Both editor AND previous version are empty — block version creation
        alert('Cannot create a new version with empty content.\nPlease add content to the editor first.')
        return
      }

      // Silently use the previous version's content as the base for the new version
      console.warn(
        '[createNewVersionHandler] Editor is empty — using previous version content as base for new version'
      )
      finalJson = previousContent
    }
    // ────────────────────────────────────────────────────────────────────────

    const currentMeta = currentVersion?.metadata || {}
    const newMetadata = {
      ...currentMeta,
      variables,
      sopStatus: SOP_STATES.DRAFT,
    }

    try {
      const newVersion = await createVersion(documentId, {
        doc_json: finalJson,
        change_summary: 'New version created',
        metadata_json: newMetadata,
      })

      const fullVersion = await getVersion(documentId, newVersion.id)

      const versionObj = {
        id: fullVersion.id,
        versionNumber: fullVersion.version_number,
        json: fullVersion.doc_json,
        timestamp: formatTimestamp(new Date(fullVersion.created_at)),
        isFormatted: true,
        metadata: normalizeMeta(fullVersion.metadata_json),
      }

      setVersions((prev) => [...prev, versionObj])
      setCurrentVersionId(fullVersion.id)
      setReviewLink('')
      setReviewToken(null)
      setSOPFieldErrors({})
      editor.commands.setContent(fullVersion.doc_json, false)
    } catch (error) {
      console.error('Create version failed:', error)
      alert(`Version creation failed: ${error.message}`)
    }
  }, [editor, canCreateNewVersion, documentId, currentVersion, variables])

  // ──────────────────────────────────────────────────────────────────────────
  // Create New Document
  //
  // Creates a brand-new parent SOP (new sops.id) with a fresh first version.
  // Separate from "Create New Version" which stays under the same sops.id.
  // ──────────────────────────────────────────────────────────────────────────

  const createNewDocumentHandler = useCallback(() => {
    if (!editor) return

    // Simply reset frontend state to a blank canvas.
    // No backend call is made here. No DB row is created.
    setDocumentId(null)
    localStorage.removeItem('current_document_id')
    
    const initialContent = { type: 'doc', content: [] }
    const initialVersions = [
      {
        id: 'v1',
        versionNumber: '1',
        json: initialContent,
        metadata: { ...DEFAULT_SOP_VERSION_METADATA },
        status: SOP_STATES.DRAFT,
        timestamp: formatTimestamp(new Date()),
        isFormatted: true,
      },
    ]

    setVersions(initialVersions)
    setCurrentVersionId('v1')
    editor.commands.setContent(initialContent, false)
    setVariables({})
    setReviewLink('')
    setReviewToken(null)
    setSOPFieldErrors({})
    showToast('New document initialized (local only). Save to persist.')
  }, [editor, setVariables, showToast])

  // ──────────────────────────────────────────────────────────────────────────
  // Duplicate as New Document
  //
  // Copies current document content into a brand-new sops record (new sops.id).
  // Title is automatically derived — no prompt needed.
  // ──────────────────────────────────────────────────────────────────────────

  const duplicateAsNewDocumentHandler = useCallback(async () => {
    if (!editor || !documentId) return

    // Derive title automatically from current doc metadata — no prompt
    const currentTitle =
      currentVersion?.metadata?.sopMetadata?.title ||
      versions[0]?.metadata?.sopMetadata?.title ||
      'SOP Document'
    const title = `Copy of ${currentTitle}`

    try {
      // Prefer live editor content; fall back to last saved version content
      const editorJson = editor.getJSON()
      const contentToCopy = isEditorContentEmpty(editorJson)
        ? currentVersion?.json || { type: 'doc', content: [] }
        : editorJson

      const currentMeta = currentVersion?.metadata || {}

      // POST /api/editor/docs/{id}/duplicate → new sops.id + v1 sop_versions
      const newDoc = await duplicateDocument(documentId, {
        title,
        doc_json: contentToCopy,
        metadata_json: {
          ...currentMeta,
          sopStatus: SOP_STATES.DRAFT,  // always reset to draft on duplication
        },
      })

      const doc = await getDocument(newDoc.id)
      const dbVersions = await getVersions(newDoc.id)

      const mappedVersions = dbVersions.map((v) => ({
        id: v.id,
        versionNumber: v.version_number,
        json: v.doc_json || { type: 'doc', content: [] },
        metadata: normalizeMeta(v.metadata_json),
        status: v.status,
        timestamp: formatTimestamp(new Date(v.created_at)),
        isFormatted: true,
      }))

      // Switch to the new duplicated document
      setDocumentId(newDoc.id)
      localStorage.setItem('current_document_id', newDoc.id)
      setVersions(mappedVersions)
      setCurrentVersionId(doc.current_version_id)
      editor.commands.setContent(doc.doc_json || { type: 'doc', content: [] }, false)
      setVariables(doc.metadata_json?.variables || {})
      setReviewLink('')
      setReviewToken(null)
      setSOPFieldErrors({})
      showToast(`Duplicate document created successfully: ${title}`)
    } catch (error) {
      console.error('Duplicate document failed:', error)
      showToast(`Failed to duplicate document: ${error.message}`, 'error')
    }
  }, [editor, documentId, currentVersion, versions, setVariables, showToast])
  useEffect(() => {
    if (!editor) return

    const handleUpdate = () => {
      if (!isEditorEditable) return

      const currentVer = versions.find((v) => v.id === currentVersionId)
      const metadata = {
        ...(currentVer?.metadata || {}),
        variables,
      }

      debouncedSave(editor.getJSON(), metadata)
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
      debouncedSave.cancel()
    }
  }, [editor, currentVersionId, debouncedSave, isEditorEditable, versions, variables])

  const loadVersion = useCallback(
    async (versionId) => {
      if (!documentId || !editor) return

      try {
        const version = await getVersion(documentId, versionId)

        editor.commands.setContent(version.doc_json || { type: 'doc', content: [] }, false)
        setCurrentVersionId(version.id)
        setVariables(version.metadata_json?.variables || {})
        setReviewToken(version.metadata_json?.reviewToken || null)
        setSOPFieldErrors({})

        // Sync fetched version data into local versions array so SOP panel reads fresh metadata
        setVersions((prev) =>
          prev.map((v) =>
            v.id === version.id
              ? {
                ...v,
                json: version.doc_json || { type: 'doc', content: [] },
                metadata: normalizeMeta(version.metadata_json),  // normalize into {sopStatus, sopMetadata, ...} shape
                status: version.status,
              }
              : v
          )
        )
      } catch (error) {
        console.error('Load version failed:', error)
      }
    },
    [documentId, editor, setVariables]
  )

  const refreshDocumentFromBackend = useCallback(async (docId) => {
    if (!docId || !editor) return

    try {
      // GET /api/editor/docs/{id} returns a FLAT old-editor response:
      // { id, title, doc_type, doc_json, metadata_json, current_version_id, version_number, status, ... }
      // There is NO nested current_version object — we build one from the flat fields.
      const doc = await getDocument(docId)
      const dbVersions = await getVersions(docId)
      const mappedVersions = dbVersions.map((v) => ({
        id: v.id,
        versionNumber: v.version_number,
        json: v.doc_json || { type: 'doc', content: [] },
        metadata: normalizeMeta(v.metadata_json),
        status: v.status,
        timestamp: formatTimestamp(new Date(v.created_at)),
        isFormatted: true,
      }))

      // Build synthetic currentVer from flat doc response (old editor compat shape)
      const currentVer = {
        id: doc.current_version_id,
        doc_json: doc.doc_json || { type: 'doc', content: [] },
        metadata_json: doc.metadata_json || {},
        version_number: doc.version_number,
        status: doc.status,
      }

      const finalVersions = mappedVersions.map((v) =>
        v.id === currentVer.id
          ? { ...v, json: currentVer.doc_json || { type: 'doc', content: [] }, metadata: normalizeMeta(currentVer.metadata_json) }
          : v
      )

      setVersions(finalVersions)
      setCurrentVersionId(currentVer.id)
      editor.commands.setContent(currentVer.doc_json || { type: 'doc', content: [] }, false)
      setVariables(currentVer.metadata_json?.variables || {})
      setReviewToken(currentVer.metadata_json?.reviewToken || null)
      setSOPFieldErrors({})
    } catch (error) {
      console.error('Failed to refresh document:', error)
    }
  }, [editor, setVariables])

  useEffect(() => {
    window.refreshCurrentDocument = async () => {
      const docId = localStorage.getItem('current_document_id')
      if (docId) await refreshDocumentFromBackend(docId)
    }
    return () => {
      delete window.refreshCurrentDocument
    }
  }, [refreshDocumentFromBackend])


  const text = editor?.getText() || ''
  const wordCount = text.split(/\s+/).filter(Boolean).length || 0
  const charCount = text.length || 0

  useEffect(() => {
    if (!editor) return

    const updateBlockCount = () => {
      let count = 0

      editor.state.doc.descendants((node) => {
        if (node.attrs?.['block-id']) count++
      })

      setBlockCount(count)
    }

    updateBlockCount()
    editor.on('update', updateBlockCount)

    return () => editor.off('update', updateBlockCount)
  }, [editor])
  useEffect(() => {
    if (!editor || isInitialized.current || initStarted.current) return
    initStarted.current = true

    const init = async () => {
      try {
        let docId = localStorage.getItem('current_document_id')

        if (docId) {
          try {
            const doc = await getDocument(docId)
            setDocumentId(docId)

            const dbVersions = await getVersions(docId)
            const mappedVersions = dbVersions.map((v) => ({
              id: v.id,
              versionNumber: v.version_number,
              json: v.doc_json || { type: 'doc', content: [] },
              metadata: normalizeMeta(v.metadata_json),
              status: v.status,
              timestamp: formatTimestamp(new Date(v.created_at)),
              isFormatted: true,
            }))

            const currentVer = {
              id: doc.current_version_id,
              doc_json: doc.doc_json || { type: 'doc', content: [] },
              metadata_json: doc.metadata_json || {},
              version_number: doc.version_number,
              status: doc.status,
            }

            const finalVersions = mappedVersions.map((v) =>
              v.id === currentVer.id
                ? { ...v, json: currentVer.doc_json, metadata: normalizeMeta(currentVer.metadata_json) }
                : v
            )

            setVersions(finalVersions)
            setCurrentVersionId(currentVer.id)
            editor.commands.setContent(currentVer.doc_json, false)
            setVariables(currentVer.metadata_json?.variables || {})
          } catch (fetchError) {
            console.warn('Stored document not found, clearing:', fetchError)
            localStorage.removeItem('current_document_id')
            setDocumentId(null)
          }
        } else {
          // If no docId in localStorage, we start with a blank canvas
          // NO DB row is created here.
          setDocumentId(null)
          setVersions([])
          setCurrentVersionId('v1')
          editor.commands.setContent({ type: 'doc', content: [] }, false)
          setVariables({}) 
        }
      } catch (error) {
        console.error('Failed to initialize document:', error)
      } finally {
        isInitialized.current = true
      }
    }

    init()
  }, [editor, setVariables])

  useEffect(() => {
    if (!editor || versions.length === 0) return

    const {
      reviewToken: tokenFromUrl,
      versionId: versionIdFromUrl,
    } = getReviewParamsFromUrl()

    if (!tokenFromUrl || !versionIdFromUrl) {
      setIsClientReviewMode(false)
      return
    }

    openVersionInClientReviewMode(tokenFromUrl, versionIdFromUrl)
  }, [editor, versions, openVersionInClientReviewMode])


  useEffect(() => {
    if (!editor) return

    const updatePlaceholdersFromEditor = () => {
      const textContent = editor.getText()
      const placeholders = extractPlaceholdersFromText(textContent)
      syncPlaceholders(placeholders)
    }

    const timeout = setTimeout(() => {
      updatePlaceholdersFromEditor()
    }, 0)

    editor.on('update', updatePlaceholdersFromEditor)

    return () => {
      clearTimeout(timeout)
      editor.off('update', updatePlaceholdersFromEditor)
    }
  }, [editor, syncPlaceholders])

  const handleOCRUpload = useCallback(
    async (file) => {
      if (!file || !editor || !isEditorEditable) return

      setOcrError('')
      setIsOcrLoading(true)

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/extract-text`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`OCR request failed with status ${response.status}`)
        }

        const data = await response.json()

        const extractedText = data?.text?.trim()
        const blocks = Array.isArray(data?.blocks) ? data.blocks : []

        if (!extractedText && !blocks.length) {
          throw new Error('No text was extracted from the uploaded file.')
        }

        let formattedHtml = ''

        if (blocks.length) {
          formattedHtml = mapOCRBlocksToHTML(blocks, normalizedProfile)
        } else {
          formattedHtml = formatOCRText(extractedText || '')
        }

        editor.commands.setContent(formattedHtml, false)

        const latestText = editor.getText()
        const placeholders = extractPlaceholdersFromText(latestText)
        syncPlaceholders(placeholders)

        let count = 0
        editor.state.doc.descendants((node) => {
          if (node.attrs?.['block-id']) count++
        })
        setBlockCount(count)
      } catch (error) {
        console.error('OCR upload failed:', error)
        setOcrError(error.message || 'OCR upload failed.')
      } finally {
        setIsOcrLoading(false)
      }
    },
    [editor, normalizedProfile, syncPlaceholders, isEditorEditable]
  )

  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      const mod = e.ctrlKey || e.metaKey
      const key = e.key.toLowerCase()

      if (!editor) return

      if (!isEditorEditable) {
        if (mod && e.shiftKey && !e.altKey && key === 'v' && canCreateNewVersion) {
          e.preventDefault()
          createNewVersionHandler()
          return
        }

        if ((mod && key === 's') || (mod && key === 'p')) {
          e.preventDefault()
        }
        return
      }

      if (mod && !e.shiftKey && !e.altKey && key === 's') {
        e.preventDefault()
        manualSave()
      }

      if (mod && e.shiftKey && !e.altKey && key === 'v') {
        e.preventDefault()
        createNewVersionHandler()
      }

      if (mod && !e.shiftKey && !e.altKey && key === 'p') {
        e.preventDefault()
        printDocument(editor.getHTML(), variables)
      }
    }

    window.addEventListener('keydown', handleGlobalKeyDown)
    return () => window.removeEventListener('keydown', handleGlobalKeyDown)
  }, [editor, variables, manualSave, createNewVersionHandler, isEditorEditable, canCreateNewVersion])

  if (!editor) return <div className="loading">Loading AI-LAW Editor...</div>

  const handleLinkSave = (url) => {
    if (!isEditorEditable) {
      setIsLinkModalOpen(false)
      return
    }

    if (url) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    } else {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
    }
    setIsLinkModalOpen(false)
  }

  const insertPlaceholder = useCallback(
    (name) => {
      if (!editor || !isEditorEditable) return
      editor.chain().focus().insertContent(`{{${name}}}`).run()
    },
    [editor, isEditorEditable]
  )

  const compareTwoVersions = (v1, v2) => {
    if (!versions || versions.length < 1) return

    const version1 = versions.find((v) => v.id === v1)
    const version2 = versions.find((v) => v.id === v2)

    if (!version1 || !version2) return

    setDiffOldVersion(version1)
    setDiffNewVersion(version2)
    setIsDiffMode(true)
  }

  return (
    <div className="editor-wrapper">
      {/* Global toast notifications */}
      <Toast
        message={toast?.message}
        type={toast?.type}
        onClose={() => setToast(null)}
      />

      <TopNavbar />
      {!isClientReviewMode && (
        <MenuBar
          editor={editor}
          onSave={manualSave}
          onNewVersion={createNewVersionHandler}
          onCreateNewDocument={createNewDocumentHandler}
          onDuplicateAsNewDocument={duplicateAsNewDocumentHandler}
          currentVersion={currentVersionId}
          onLoadVersion={loadVersion}
          onCompare={compareTwoVersions}
          versions={versions}
          onOpenLinkModal={() => {
            if (!isEditorEditable) return
            setLinkModalInitialUrl(editor.getAttributes('link')?.href || '')
            setIsLinkModalOpen(true)
          }}
          onOpenPreview={() => setIsPreviewModalOpen(true)}
          profile={normalizedProfile}
          onToggleVariablesPanel={() => setShowVariablesPanel((prev) => !prev)}
          onSendForReview={sendForReview}
          onInsertPlaceholder={insertPlaceholder}
          onOCRUpload={handleOCRUpload}
          isOcrLoading={isOcrLoading}
          ocrError={ocrError}
          isReadOnly={!isEditorEditable}
          canCreateNewVersion={canCreateNewVersion}
        />
      )}

      <div
        className={`editor-layout ${(isContractProfile && showVariablesPanel) || isSOPProfile
          ? 'with-right-panel'
          : ''
          }`}
      >
        <div className="center-editor">
          <div ref={editorRef} className="pdf-export-wrapper">
            <EditorContent editor={editor} />
          </div>
        </div>

        {isContractProfile && featureFlags.contractProfileEnabled && showVariablesPanel && (
          <div className="right-panel">
            {!isClientReviewMode && (
              <VariablesPanel
                variableEntries={variableEntries}
                onChange={updateVariable}
                onReset={resetVariables}
              />
            )}

            <ReviewLinkPanel
              isClientReviewMode={isClientReviewMode}
              reviewLink={reviewLink}
              onGenerateReviewLink={generateReviewLink}
            />

            <ReviewActions
              workflowStatus={WORKFLOW_LABELS[workflowStatus] || workflowStatus}
              onSendForReview={sendForReview}
              onApprove={markApproved}
              onRequestChanges={markChangesRequested}
              onReject={markRejected}
              reviewComments={currentReviewComments}
              onAddComment={addReviewComment}
              sentForReviewAt={currentSentForReviewAt}
              isClientReviewMode={isClientReviewMode}
            />

            <WorkflowTimeline workflowStatus={workflowStatus} />
          </div>
        )}

        {isSOPProfile && (
          <div className="right-panel">
            <SOPMetadataPanel
              metadata={currentSOPMetadata}
              onChange={updateSOPMetadata}
              isReadOnly={!isEditorEditable}
              errors={sopFieldErrors}
            />

            <SOPReferencesPanel
              references={currentSOPMetadata?.references || []}
              onChange={updateSOPReferences}
              isReadOnly={!isEditorEditable}
            />

            <SOPActions
              sopStatus={currentSOPStatus}
              onAction={executeSOPAction}
              isClientReviewMode={isClientReviewMode}
              onCreateNewVersion={createNewVersionHandler}
              onCreateNewDocument={createNewDocumentHandler}
              onDuplicateAsNewDocument={duplicateAsNewDocumentHandler}
              canCreateNewVersion={canCreateNewVersion}
            />

            <SOPTimeline sopStatus={currentSOPStatus} />

            <SOPAuditTrail
              auditTrail={currentSOPAuditTrail}
              currentVersion={currentVersion?.versionNumber ? `v${currentVersion.versionNumber}` : currentVersionId}
            />
          </div>
        )}
      </div>

      <StatusBar
        wordCount={wordCount}
        charCount={charCount}
        blockCount={blockCount}
        lastSaved={lastSaved}
        isSaving={isSaving}
        profile={normalizedProfile}
        onProfileChange={handleProfileChange}
        workflowStatus={isContractProfile ? workflowStatus : currentSOPStatus}
      />

      <LinkModal
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
        initialUrl={linkModalInitialUrl}
        onSave={handleLinkSave}
      />

      <PreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        editor={editor}
        versionId={currentVersionId}
        profile={normalizedProfile}
        contractVariables={variables}
      />

      {isDiffMode && (
        <SideBySideViewer
          oldVersion={diffOldVersion}
          newVersion={diffNewVersion}
          onClose={() => setIsDiffMode(false)}
        />
      )}
    </div>
  )
}

export default App