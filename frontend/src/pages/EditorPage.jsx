import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { debounce } from 'lodash'
import { useEditor, EditorContent } from '@tiptap/react'
import { Extension } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import { Table } from '@tiptap/extension-table'
import { TableRow } from '@tiptap/extension-table-row'
import { TableCell } from '@tiptap/extension-table-cell'
import { TableHeader } from '@tiptap/extension-table-header'
import {
  Bold,
  ChevronDown,
  Eye,
  FileText,
  Import,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Maximize2,
  Plus,
  Save,
  Table2,
  Underline as UnderlineIcon,
  Undo2,
  Redo2,
  Strikethrough,
  X,
} from 'lucide-react'

import RelatedContextSidebar from '../components/Editor/SOP/RelatedContextSidebar'
import LinkModal from '../components/Common/LinkModal'
import LinkingModal from '../components/Common/LinkingModal'
import PreviewModal from '../components/Common/PreviewModal'
import AIAssistantBubbleMenu from '../components/Editor/AIAssistantBubbleMenu'
import SideBySideViewer from '../components/Editor/Diff/SideBySideViewer'
import StatusBar from '../components/Editor/StatusBar'
import { useLanguage } from '../context/LanguageContext'
import {
  createDocument,
  createVersion,
  extractText,
  getDocument,
  getVersion,
  getVersions,
  updateDocument,
  updateVersionStatus,
} from '../api/editorApi'
import { DEFAULT_SOP_VERSION_METADATA, SOP_LABELS, SOP_ORDER, SOP_STATES } from '../utils/sopConstants'
import { formatOCRText } from '../utils/formatOCRText'
import { mapOCRBlocksToHTML } from '../utils/mapOCRBlocksToHTML'
import '../assets/styles/global.css'

const EMPTY_DOC = {
  type: 'doc',
  content: [],
}

const STORAGE_KEY = 'current_document_id'

const EditorShortcuts = Extension.create({
  name: 'editorShortcuts',
  addKeyboardShortcuts() {
    return {
      'Mod-b': () => this.editor.chain().focus().toggleBold().run(),
      'Mod-i': () => this.editor.chain().focus().toggleItalic().run(),
      'Mod-u': () => this.editor.chain().focus().toggleUnderline().run(),
      'Mod-Shift-1': () => this.editor.chain().focus().toggleHeading({ level: 1 }).run(),
      'Mod-Shift-2': () => this.editor.chain().focus().toggleHeading({ level: 2 }).run(),
      'Mod-Shift-3': () => this.editor.chain().focus().toggleHeading({ level: 3 }).run(),
      'Mod-Alt-1': () => this.editor.chain().focus().toggleHeading({ level: 1 }).run(),
      'Mod-Alt-2': () => this.editor.chain().focus().toggleHeading({ level: 2 }).run(),
      'Mod-Alt-3': () => this.editor.chain().focus().toggleHeading({ level: 3 }).run(),
      'Mod-Alt-t': () => this.editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
    }
  },
})

const normalizeMeta = (rawMeta) => {
  if (!rawMeta || typeof rawMeta !== 'object') {
    return { ...DEFAULT_SOP_VERSION_METADATA }
  }

  if (rawMeta.sopMetadata !== undefined) {
    return {
      ...DEFAULT_SOP_VERSION_METADATA,
      ...rawMeta,
      sopMetadata: {
        ...DEFAULT_SOP_VERSION_METADATA.sopMetadata,
        ...(rawMeta.sopMetadata || {}),
      },
      auditTrail: Array.isArray(rawMeta.auditTrail) ? rawMeta.auditTrail : [],
    }
  }

  return {
    ...DEFAULT_SOP_VERSION_METADATA,
    sopStatus: rawMeta.sopStatus || DEFAULT_SOP_VERSION_METADATA.sopStatus,
    sopMetadata: {
      ...DEFAULT_SOP_VERSION_METADATA.sopMetadata,
      ...rawMeta,
    },
    auditTrail: Array.isArray(rawMeta.auditTrail) ? rawMeta.auditTrail : [],
  }
}

const formatTimestamp = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

const buildVersionLabel = (version) => {
  if (!version) return 'SOP-NEW'
  const number = version.versionNumber || 1
  const stamp = version.timestamp || ''
  return stamp ? `v${number} (${stamp})` : `v${number}`
}

const createAuditEntry = (action, fromStatus, toStatus, note, version) => ({
  id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  action,
  fromStatus,
  toStatus,
  note,
  actor: 'Author',
  version,
  createdAt: new Date().toISOString(),
})

const hasMeaningfulDraft = (docJson, sopMetadata = {}) => {
  const text = JSON.stringify(docJson || EMPTY_DOC)
  const hasDocContent = Boolean(text && text !== JSON.stringify(EMPTY_DOC))
  const hasMetadataContent = Object.entries(sopMetadata).some(([key, value]) => {
    if (key === 'title') return value && value !== 'SOP-NEW'
    if (key === 'references') return Array.isArray(value) && value.length > 0
    return Boolean(value)
  })

  return hasDocContent || hasMetadataContent
}

const mapVersion = (version) => ({
  id: version.id,
  versionNumber: version.version_number || 1,
  json: version.doc_json || EMPTY_DOC,
  metadata: normalizeMeta(version.metadata_json),
  status: version.status || 'draft',
  timestamp: formatTimestamp(version.created_at),
})

const EditorPage = ({ isEmbedded = false, initialDocId = null }) => {
  const { language, setLanguage, t } = useLanguage()
  const { id: urlDocId } = useParams()
  const [documentId, setDocumentId] = useState(initialDocId || urlDocId || null)
  const [versions, setVersions] = useState([])
  const [currentVersionId, setCurrentVersionId] = useState(null)
  const [latestVersionId, setLatestVersionId] = useState(null)
  const [metadata, setMetadata] = useState({
    ...DEFAULT_SOP_VERSION_METADATA.sopMetadata,
    title: 'SOP-NEW',
  })
  const [sopStatus, setSopStatus] = useState(DEFAULT_SOP_VERSION_METADATA.sopStatus)
  const [auditTrail, setAuditTrail] = useState([])
  const [versionNote, setVersionNote] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false)
  const [isLinkingModalOpen, setIsLinkingModalOpen] = useState(false)
  const [linkModalInitialUrl, setLinkModalInitialUrl] = useState('')
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [isLoadingDocument, setIsLoadingDocument] = useState(false)
  const [compareBaseVersionId, setCompareBaseVersionId] = useState('')
  const [compareTargetVersionId, setCompareTargetVersionId] = useState('')
  const [diffVersions, setDiffVersions] = useState({ oldVersion: null, newVersion: null })
  const [relatedContextRefreshToken, setRelatedContextRefreshToken] = useState(0)
  const hydrationRef = useRef(false)
  const saveInFlightRef = useRef(false)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Link.configure({
        openOnClick: true,
        autolink: true,
        linkOnPaste: true,
      }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      EditorShortcuts,
    ],
    content: EMPTY_DOC,
    editorProps: {
      attributes: {
        class: 'tiptap tiptap-sop',
      },
    },
  })

  const currentVersion = versions.find((item) => item.id === currentVersionId) || null
  const isHistoricalView = Boolean(latestVersionId && currentVersionId && latestVersionId !== currentVersionId)
  const currentVersionLabel = buildVersionLabel(currentVersion)

  const applyVersionState = useCallback((versionRecord, fallbackTitle = '') => {
    if (!editor || !versionRecord) return

    hydrationRef.current = true
    const normalized = {
      ...DEFAULT_SOP_VERSION_METADATA.sopMetadata,
      ...(versionRecord.metadata?.sopMetadata || {}),
    }

    if (!normalized.title && fallbackTitle) {
      normalized.title = fallbackTitle
    }

    setMetadata(normalized)
    setSopStatus(versionRecord.metadata?.sopStatus || DEFAULT_SOP_VERSION_METADATA.sopStatus)
    setAuditTrail(versionRecord.metadata?.auditTrail || [])
    setVersionNote(versionRecord.metadata?.versionNote || '')
    editor.commands.setContent(versionRecord.json || EMPTY_DOC, false)

    window.setTimeout(() => {
      hydrationRef.current = false
    }, 0)
  }, [editor])

  const hydrateFromDocument = useCallback(async (docId) => {
    if (!docId || !editor) return

    setIsLoadingDocument(true)

    try {
      const [doc, dbVersions] = await Promise.all([
        getDocument(docId),
        getVersions(docId),
      ])

      const nextVersions = dbVersions.map(mapVersion)
      const currentDocVersion = {
        id: doc.current_version_id,
        version_number: doc.version_number,
        doc_json: doc.doc_json || EMPTY_DOC,
        metadata_json: doc.metadata_json || {},
        status: doc.status || DEFAULT_SOP_VERSION_METADATA.sopStatus,
        created_at: doc.updated_at || doc.created_at,
      }

      const normalizedCurrent = mapVersion(currentDocVersion)
      const mergedVersions = nextVersions.some((item) => item.id === normalizedCurrent.id)
        ? nextVersions.map((item) => (item.id === normalizedCurrent.id ? normalizedCurrent : item))
        : [...nextVersions, normalizedCurrent]

      setVersions(mergedVersions)
      setCurrentVersionId(normalizedCurrent.id)
      setLatestVersionId(normalizedCurrent.id)
      setCompareBaseVersionId(normalizedCurrent.id)
      setCompareTargetVersionId(normalizedCurrent.id)
      applyVersionState(normalizedCurrent, doc.title || '')
      
      // CRITICAL: Always use the UUID from the backend for subsequent API calls (like Related Context)
      if (doc.id) {
        setDocumentId(doc.id)
      }
    } finally {
      setIsLoadingDocument(false)
    }
  }, [editor, applyVersionState])

  useEffect(() => {
    if (!editor) return

    const storedId = localStorage.getItem(STORAGE_KEY)
    const targetId = initialDocId || urlDocId || storedId

    if (!targetId) {
      editor.commands.setContent(EMPTY_DOC, false)
      setDocumentId(null)
      return
    }

    hydrateFromDocument(targetId)
      .then(() => {
        // Hydration sets the correct UUID via setDocumentId(doc.id)
        localStorage.setItem(STORAGE_KEY, targetId)
      })
      .catch((error) => {
        console.error('Failed to load editor document:', error)
      })
  }, [editor, initialDocId, urlDocId, hydrateFromDocument])

  const persistDocument = useCallback(async ({ showSavingIndicator = true } = {}) => {
    if (!editor || isHistoricalView || hydrationRef.current) return
    if (saveInFlightRef.current) return

    const currentJson = editor.getJSON()
    if (!documentId && !hasMeaningfulDraft(currentJson, metadata)) return

    saveInFlightRef.current = true
    if (showSavingIndicator) {
      setIsSaving(true)
    }

    const payload = {
      title: metadata.title || 'SOP-NEW',
      doc_type: 'sop',
      doc_json: currentJson,
      metadata_json: {
        sopStatus,
        sopMetadata: metadata,
        auditTrail,
        versionNote,
      },
    }

    try {
      let response
      let createdNewDocument = false

      if (!documentId) {
        response = await createDocument(payload)
        createdNewDocument = true
        setDocumentId(response.id)
        setCurrentVersionId(response.current_version_id)
        localStorage.setItem(STORAGE_KEY, response.id)
      } else {
        response = await updateDocument(documentId, payload)
      }

      setLastSaved(new Date())

      // Only hydrate after initial create. Re-hydrating on every autosave causes
      // visible editor reflow/flicker and cursor jumps.
      if (createdNewDocument && response?.id) {
        await hydrateFromDocument(response.id)
      }
    } catch (error) {
      console.error('Save failed:', error)
    } finally {
      saveInFlightRef.current = false
      if (showSavingIndicator) {
        setIsSaving(false)
      }
    }
  }, [editor, metadata, sopStatus, auditTrail, versionNote, documentId, hydrateFromDocument, isHistoricalView])

  const debouncedSave = useMemo(
    () => debounce(() => {
      persistDocument({ showSavingIndicator: false })
    }, 1600),
    [persistDocument]
  )

  useEffect(() => {
    if (!editor) return

    const handleUpdate = () => {
      if (hydrationRef.current || isHistoricalView) return
      debouncedSave()
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
      debouncedSave.cancel()
    }
  }, [editor, debouncedSave, isHistoricalView])

  useEffect(() => {
    if (hydrationRef.current || isHistoricalView) return
    debouncedSave()
  }, [metadata, sopStatus, auditTrail, versionNote, debouncedSave, isHistoricalView])

  useEffect(() => {
    if (!editor) return
    editor.setEditable(!isHistoricalView)
  }, [editor, isHistoricalView])

  useEffect(() => {
    const onKeyDown = (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 's') return
      event.preventDefault()
      if (isHistoricalView) return
      debouncedSave.cancel()
      persistDocument({ showSavingIndicator: true })
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [debouncedSave, persistDocument, isHistoricalView])

  const handleMetadataChange = (key, value) => {
    setMetadata((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const addReference = () => {
    const value = window.prompt('Enter SOP reference')
    if (!value?.trim()) return

    setMetadata((prev) => ({
      ...prev,
      references: [...(Array.isArray(prev.references) ? prev.references : []), value.trim()],
    }))
  }

  const removeReference = (index) => {
    setMetadata((prev) => ({
      ...prev,
      references: (Array.isArray(prev.references) ? prev.references : []).filter((_, itemIndex) => itemIndex !== index),
    }))
  }

  const submitForReview = () => {
    const versionNumber = currentVersion?.versionNumber || 1
    const nextAuditTrail = [
      ...auditTrail,
      createAuditEntry('submit_review', sopStatus, SOP_STATES.UNDER_REVIEW, versionNote || 'Submitted for review', versionNumber),
    ]
    setAuditTrail(nextAuditTrail)
    setSopStatus(SOP_STATES.UNDER_REVIEW)

    if (documentId && currentVersionId) {
      updateVersionStatus(documentId, currentVersionId, {
        status: SOP_STATES.UNDER_REVIEW,
        metadata_json: {
          sopStatus: SOP_STATES.UNDER_REVIEW,
          sopMetadata: metadata,
          auditTrail: nextAuditTrail,
          versionNote,
        },
      }).catch((error) => {
        console.error('Failed to update version status:', error)
      })
    }
  }

  const createNewVersionHandler = async () => {
    if (!editor) return

    if (!documentId) {
      await persistDocument()
    }

    const activeDocumentId = documentId || localStorage.getItem(STORAGE_KEY)
    if (!activeDocumentId) return

    try {
      const result = await createVersion(activeDocumentId, {
        doc_json: editor.getJSON(),
        metadata_json: {
          sopStatus: SOP_STATES.DRAFT,
          sopMetadata: metadata,
          auditTrail: [],
          versionNote,
        },
        status: SOP_STATES.DRAFT,
      })

      await hydrateFromDocument(activeDocumentId)
      if (result?.id) {
        const loaded = await getVersion(activeDocumentId, result.id)
        setCurrentVersionId(loaded.id)
        const loadedMeta = normalizeMeta(loaded.metadata_json)
        setLatestVersionId(loaded.id)
        applyVersionState({
          id: loaded.id,
          json: loaded.doc_json || EMPTY_DOC,
          metadata: loadedMeta,
          versionNumber: loaded.version_number || currentVersion?.versionNumber || 1,
          timestamp: formatTimestamp(loaded.created_at),
        }, metadata.title || '')
      }
    } catch (error) {
      console.error('Failed to create new version:', error)
    }
  }

  const loadVersionHandler = useCallback(async (versionId) => {
    if (!documentId || !versionId) return

    try {
      const loaded = await getVersion(documentId, versionId)
      const loadedMeta = normalizeMeta(loaded.metadata_json)
      setCurrentVersionId(loaded.id)
      applyVersionState({
        id: loaded.id,
        json: loaded.doc_json || EMPTY_DOC,
        metadata: loadedMeta,
        versionNumber: loaded.version_number || 1,
        timestamp: formatTimestamp(loaded.created_at),
      }, metadata.title || '')
    } catch (error) {
      console.error('Failed to load version:', error)
    }
  }, [documentId, applyVersionState, metadata.title])

  const openLinkModal = () => {
    if (!editor) return
    setLinkModalInitialUrl(editor.getAttributes('link')?.href || '')
    setIsLinkModalOpen(true)
  }

  const handleLinkSave = (url) => {
    if (!editor) return

    if (url) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    } else {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
    }

    setIsLinkModalOpen(false)
  }

  const triggerImport = async (event) => {
    const file = event.target.files?.[0]
    if (!file || !editor) return

    setIsImporting(true)
    try {
      const data = await extractText(file)
      const html = Array.isArray(data?.blocks) && data.blocks.length
        ? mapOCRBlocksToHTML(data.blocks, 'sop')
        : formatOCRText(data?.text || '')
      editor.commands.setContent(html || EMPTY_DOC, false)
    } catch (error) {
      console.error('Import failed:', error)
    } finally {
      setIsImporting(false)
      event.target.value = ''
    }
  }

  const insertPlaceholder = () => {
    if (!editor || isHistoricalView) return
    const key = window.prompt('Enter placeholder name', 'DocumentOwner')
    if (!key?.trim()) return
    editor.chain().focus().insertContent(`{{${key.trim()}}}`).run()
  }

  const openCompareViewer = useCallback(async () => {
    if (!documentId || !compareBaseVersionId || !compareTargetVersionId) return

    try {
      const [baseVersion, targetVersion] = await Promise.all([
        getVersion(documentId, compareBaseVersionId),
        getVersion(documentId, compareTargetVersionId),
      ])

      const mapLoadedVersion = (version) => ({
        id: version.id,
        versionNumber: version.version_number || 1,
        json: version.doc_json || EMPTY_DOC,
      })

      setDiffVersions({
        oldVersion: mapLoadedVersion(baseVersion),
        newVersion: mapLoadedVersion(targetVersion),
      })
    } catch (error) {
      console.error('Failed to compare versions:', error)
    }
  }, [documentId, compareBaseVersionId, compareTargetVersionId])

  if (!editor) {
    return <div className="editor-loading">Loading editor...</div>
  }

  const references = Array.isArray(metadata.references) ? metadata.references : []
  const statusLabel = SOP_LABELS[sopStatus] || sopStatus
  const versionSelectValue = currentVersionId || (versions[0]?.id ?? '')
  const compareBaseValue = compareBaseVersionId || currentVersionId || (versions[0]?.id ?? '')
  const compareTargetValue = compareTargetVersionId || currentVersionId || (versions[0]?.id ?? '')
  const aiSopContext = useMemo(() => ({
    ...metadata,
    title: metadata?.title?.trim() || 'Untitled SOP',
    documentId: metadata?.documentId || documentId || 'SOP-NEW',
  }), [metadata, documentId])
  const plainText = editor?.getText() || ''
  const wordCount = plainText.split(/\s+/).filter(Boolean).length
  const charCount = plainText.length
  let blockCount = 0
  editor.state.doc.descendants((node) => {
    if (node.type?.name && ['paragraph', 'heading', 'bulletList', 'orderedList', 'table'].includes(node.type.name)) {
      blockCount += 1
    }
  })

  return (
    <div className={`editor-page-container${isEmbedded ? ' editor-embedded' : ''}`}>
      <div className="sop-workspace-shell">
        <header className="sop-topbar">
          <div className="sop-topbar-left">
            <button type="button" className="topbar-crumb-btn">
              <FileText size={16} />
              <span>SOPs</span>
            </button>
            <div className="topbar-document-pill">
              <FileText size={15} />
              <span>{metadata.title || 'SOP-NEW'}</span>
              <button type="button" className="pill-close-btn">
                <X size={14} />
              </button>
            </div>
          </div>

          <div className="sop-topbar-right">
            <button type="button" className="topbar-action-btn">
              <Maximize2 size={15} />
              <span>Focus</span>
            </button>
            <button type="button" className="topbar-action-btn" onClick={createNewVersionHandler}>
              <Plus size={15} />
              <span>New Version</span>
            </button>
            <button type="button" className="topbar-action-btn" onClick={() => setIsPreviewOpen(true)}>
              <Eye size={15} />
              <span>Preview</span>
            </button>
            <button type="button" className="topbar-action-btn" onClick={() => window.open(window.location.href, '_blank', 'noopener,noreferrer')}>
              <LinkIcon size={15} />
              <span>Open Tab</span>
            </button>
            <button
              type="button"
              className="topbar-save-btn"
              onClick={persistDocument}
              disabled={isHistoricalView}
              title="Save (Ctrl/Cmd+S)"
            >
              <Save size={15} />
              <span>{isHistoricalView ? 'Read Only' : isSaving ? 'Saving...' : 'Save'}</span>
            </button>
          </div>
        </header>

        <div className="sop-toolbar-row">
          <div className="editor-toolbar-grid">
            <div className="toolbar-lane toolbar-lane-primary">
              <button
                type="button"
                className="toolbar-chip toolbar-chip-green"
                onClick={persistDocument}
                disabled={isHistoricalView}
                title="Save (Ctrl/Cmd+S)"
              >
                Save
              </button>
              <button type="button" className="toolbar-chip toolbar-chip-green" onClick={createNewVersionHandler}>
                New Version
              </button>

              <div className="toolbar-select-wrap toolbar-chip-select version-toolbar-select">
                <select
                  className="toolbar-select"
                  value={versionSelectValue}
                  onChange={(event) => loadVersionHandler(event.target.value)}
                  disabled={versions.length === 0}
                >
                  {versions.length === 0 ? (
                    <option value="">v1 (draft)</option>
                  ) : null}
                  {versions.map((item) => (
                    <option key={item.id} value={item.id}>
                      {buildVersionLabel(item)}
                    </option>
                  ))}
                </select>
                <ChevronDown size={16} />
              </div>

              <button type="button" className="toolbar-chip toolbar-chip-purple" onClick={() => setIsPreviewOpen(true)}>
                {t.previewExport}
              </button>

              <button type="button" className={`toolbar-chip${editor.isActive('bold') ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleBold().run()} disabled={isHistoricalView} title="Bold (Ctrl/Cmd+B)">
                {t.bold}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('italic') ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleItalic().run()} disabled={isHistoricalView} title="Italic (Ctrl/Cmd+I)">
                {t.italic}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('underline') ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleUnderline().run()} disabled={isHistoricalView} title="Underline (Ctrl/Cmd+U)">
                {t.underline}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('strike') ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleStrike().run()} disabled={isHistoricalView}>
                {t.strike}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('heading', { level: 1 }) ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} disabled={isHistoricalView} title="Heading 1 (Ctrl/Cmd+Shift+1)">
                {t.heading1}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('heading', { level: 2 }) ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} disabled={isHistoricalView} title="Heading 2 (Ctrl/Cmd+Shift+2)">
                {t.heading2}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('heading', { level: 3 }) ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} disabled={isHistoricalView} title="Heading 3 (Ctrl/Cmd+Shift+3)">
                {t.heading3}
              </button>
              <div className="toolbar-select-wrap toolbar-chip-select language-toolbar-select">
                <select
                  className="toolbar-select"
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                >
                  <option value="en">{t.english}</option>
                  <option value="de">{t.german}</option>
                </select>
                <ChevronDown size={16} />
              </div>
            </div>

            <div className="toolbar-lane toolbar-lane-secondary">
              <button type="button" className={`toolbar-chip${editor.isActive('bulletList') ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleBulletList().run()} disabled={isHistoricalView}>
                {t.bulletList}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('orderedList') ? ' active' : ''}`} onClick={() => editor.chain().focus().toggleOrderedList().run()} disabled={isHistoricalView}>
                {t.numberedList}
              </button>
              <button type="button" className="toolbar-chip" onClick={() => editor.chain().focus().undo().run()} disabled={isHistoricalView} title="Undo (Ctrl/Cmd+Z)">
                {t.undo}
              </button>
              <button type="button" className="toolbar-chip" onClick={() => editor.chain().focus().redo().run()} disabled={isHistoricalView} title="Redo (Ctrl/Cmd+Shift+Z)">
                {t.redo}
              </button>
              <button type="button" className={`toolbar-chip${editor.isActive('link') ? ' active' : ''}`} onClick={openLinkModal} disabled={isHistoricalView}>
                {t.insertUrl}
              </button>
              <button type="button" className="toolbar-chip" onClick={insertPlaceholder} disabled={isHistoricalView}>
                {t.insertPlaceholder}
              </button>

              <div className="compare-toolbar-group">
                <div className="toolbar-select-wrap toolbar-chip-select compare-select">
                  <select
                    className="toolbar-select"
                    value={compareBaseValue}
                    onChange={(event) => setCompareBaseVersionId(event.target.value)}
                    disabled={versions.length === 0}
                  >
                    {versions.length === 0 ? (
                      <option value="">Base: v1</option>
                    ) : null}
                    {versions.map((item) => (
                      <option key={`base-${item.id}`} value={item.id}>
                        Base: v{item.versionNumber || 1}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={16} />
                </div>
                <span className="compare-separator">vs</span>
                <div className="toolbar-select-wrap toolbar-chip-select compare-select">
                  <select
                    className="toolbar-select"
                    value={compareTargetValue}
                    onChange={(event) => setCompareTargetVersionId(event.target.value)}
                    disabled={versions.length === 0}
                  >
                    {versions.length === 0 ? (
                      <option value="">Target: v1</option>
                    ) : null}
                    {versions.map((item) => (
                      <option key={`target-${item.id}`} value={item.id}>
                        Target: v{item.versionNumber || 1}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={16} />
                </div>
                <button type="button" className="toolbar-chip" onClick={openCompareViewer} disabled={!documentId || !compareBaseVersionId || !compareTargetVersionId}>
                  {t.compare}
                </button>
              </div>

              <button type="button" className="toolbar-chip" onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()} disabled={isHistoricalView} title="Insert table (Ctrl/Cmd+Alt+T)">
                {t.insertTable}
              </button>

              <label className={`toolbar-chip toolbar-chip-file${isHistoricalView ? ' disabled' : ''}`}>
                {t.importPdfDocx}
                <input type="file" accept=".pdf,.txt,.md,.doc,.docx" hidden onChange={triggerImport} disabled={isHistoricalView} />
              </label>
            </div>
          </div>
        </div>

        <div className="sop-body-layout">
          <main className="sop-editor-stage">
            <div className="editor-stage-header">
              <div className="editor-stage-statuses">
                {isHistoricalView ? (
                  <span className="editor-stage-hint">Historical version loaded. Switch back to latest version to edit.</span>
                ) : null}
                {isLoadingDocument ? (
                  <span className="editor-stage-hint">Loading...</span>
                ) : null}
              </div>
            </div>

            <div className="sop-editor-paper">
              <EditorContent editor={editor} />
              <AIAssistantBubbleMenu
                editor={editor}
                sopMetadata={aiSopContext}
                isEditable={!isHistoricalView}
              />
            </div>
          </main>

          <aside className="sop-sidebar">
            <div className="sidebar-card sidebar-card-emphasis">
              <div className="sidebar-section-kicker">Document details</div>
              <h3 className="sidebar-title">SOP-Metadata</h3>
              <div className="sidebar-field-stack">
                <input className="sidebar-input" value={metadata.documentId || ''} onChange={(event) => handleMetadataChange('documentId', event.target.value)} placeholder="SOP-001" disabled={isHistoricalView} />
                <input className="sidebar-input" value={metadata.title || ''} onChange={(event) => handleMetadataChange('title', event.target.value)} placeholder="Document title" disabled={isHistoricalView} />
                <input className="sidebar-input" value={metadata.department || ''} onChange={(event) => handleMetadataChange('department', event.target.value)} placeholder="Department" disabled={isHistoricalView} />
                <input className="sidebar-input" value={metadata.author || ''} onChange={(event) => handleMetadataChange('author', event.target.value)} placeholder="Author" disabled={isHistoricalView} />
                <input className="sidebar-input" value={metadata.reviewer || ''} onChange={(event) => handleMetadataChange('reviewer', event.target.value)} placeholder="Reviewer" disabled={isHistoricalView} />
                <input className="sidebar-input" type="date" value={metadata.effectiveDate || ''} onChange={(event) => handleMetadataChange('effectiveDate', event.target.value)} disabled={isHistoricalView} />
                <input className="sidebar-input" type="date" value={metadata.reviewDate || ''} onChange={(event) => handleMetadataChange('reviewDate', event.target.value)} disabled={isHistoricalView} />
                <input className="sidebar-input" value={metadata.riskLevel || ''} onChange={(event) => handleMetadataChange('riskLevel', event.target.value)} placeholder="Risk level" disabled={isHistoricalView} />
              </div>
            </div>

            <div className="sidebar-card">
              <div className="sidebar-section-kicker">Reference management</div>
              <h3 className="sidebar-title">SOP-Referenzen</h3>
              <div className="reference-entry-row">
                <button type="button" className="sidebar-mini-btn success" onClick={addReference} disabled={isHistoricalView}>Hinzufugen</button>
              </div>
              <div className="sidebar-list">
                {references.length === 0 ? (
                  <p className="sidebar-empty-text">No references added.</p>
                ) : (
                  references.map((item, index) => (
                    <div key={`${item}-${index}`} className="reference-row">
                      <span>{item}</span>
                      <button type="button" className="sidebar-mini-btn danger" onClick={() => removeReference(index)} disabled={isHistoricalView}>Entfernen</button>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="sidebar-card">
              <div className="sidebar-section-kicker">Workflow action</div>
              <h3 className="sidebar-title">SOP-Aktionen</h3>
              <div className="status-note">Aktueller Status: {statusLabel}</div>
              <textarea
                className="sidebar-textarea"
                value={versionNote}
                onChange={(event) => setVersionNote(event.target.value)}
                placeholder="Anderungszusammenfassung hinzufugen/Genehmigungsvermerk/Grund fur Verwaltung..."
                disabled={isHistoricalView}
              />
              <button type="button" className="sidebar-primary-btn" onClick={submitForReview} disabled={isHistoricalView}>
                Zur Uberprufung einreichen
              </button>
            </div>

            <div className="sidebar-card">
              <div className="sidebar-section-kicker">Lifecycle</div>
              <h3 className="sidebar-title">SOP-Lebenszyklus</h3>
              <div className="lifecycle-stack">
                {SOP_ORDER.map((stateId) => (
                  <div key={stateId} className={`lifecycle-pill${sopStatus === stateId ? ' active' : ''}`}>
                    <span>{SOP_LABELS[stateId] || stateId}</span>
                    {sopStatus === stateId ? <span>(Aktuell)</span> : null}
                  </div>
                ))}
              </div>
            </div>

            <div className="sidebar-card">
              <div className="sidebar-section-kicker">Change log</div>
              <h3 className="sidebar-title">SOP-Audit-Trail</h3>
              {auditTrail.length === 0 ? (
                <p className="sidebar-empty-text">Bisher keine Prufeintrage.</p>
              ) : (
                <div className="audit-stack">
                  {auditTrail.slice().reverse().map((entry) => (
                    <div key={entry.id} className="audit-item">
                      <div className="audit-item-top">
                        <strong>v{entry.version || currentVersion?.versionNumber || 1}</strong>
                        <span>{SOP_LABELS[entry.toStatus] || entry.toStatus}</span>
                      </div>
                      <p>{entry.note || 'Workflow update'}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <RelatedContextSidebar
              sopId={documentId}
              onLinkClick={() => setIsLinkingModalOpen(true)}
              refreshToken={relatedContextRefreshToken}
            />
          </aside>
        </div>

        <StatusBar
          wordCount={wordCount}
          charCount={charCount}
          blockCount={blockCount}
          lastSaved={lastSaved}
          isSaving={isSaving}
          profile="sop"
          onProfileChange={() => {}}
          workflowStatus={sopStatus}
        />
      </div>

      <LinkModal
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
        onSave={handleLinkSave}
        initialUrl={linkModalInitialUrl}
      />

      <LinkingModal
        isOpen={isLinkingModalOpen}
        onClose={() => setIsLinkingModalOpen(false)}
        sourceId={documentId}
        sourceType="sop"
        onLinkCreated={() => {
          setRelatedContextRefreshToken((prev) => prev + 1)
        }}
      />

      <PreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        editor={editor}
        versionId={currentVersion?.versionNumber || 1}
      />

      {diffVersions.oldVersion && diffVersions.newVersion ? (
        <SideBySideViewer
          oldVersion={diffVersions.oldVersion}
          newVersion={diffVersions.newVersion}
          onClose={() => setDiffVersions({ oldVersion: null, newVersion: null })}
        />
      ) : null}
    </div>
  )
}

export default EditorPage
