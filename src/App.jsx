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
import { MenuBar } from './components/MenuBar'
import StatusBar from './components/StatusBar'
import LinkModal from './components/LinkModal'
import PreviewModal from './components/PreviewModal'
import SideBySideViewer from './diff/SideBySideViewer'

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

import { PlaceholderHighlight } from './extensions/PlaceholderHighlight'
import { PlaceholderSuggestion } from './extensions/PlaceholderSuggestion'

import { mapOCRBlocksToHTML } from './utils/mapOCRBlocksToHTML'
import { formatOCRText } from './utils/formatOCRText'

import './App.css'

const STORAGE_KEY = 'tiptap_editor_v5_stable'

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

  const [versions, setVersions] = useState([])
  const [currentVersionId, setCurrentVersionId] = useState('v1')
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)
  const [blockCount, setBlockCount] = useState(0)
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false)
  const [linkModalInitialUrl, setLinkModalInitialUrl] = useState('')
  const [profile, setProfile] = useState('contract')
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false)

  const [diffOldVersion, setDiffOldVersion] = useState(null)
  const [diffNewVersion, setDiffNewVersion] = useState(null)
  const [isDiffMode, setIsDiffMode] = useState(false)

  const [showVariablesPanel, setShowVariablesPanel] = useState(true)

  const [isOcrLoading, setIsOcrLoading] = useState(false)
  const [ocrError, setOcrError] = useState('')

  const [isClientReviewMode, setIsClientReviewMode] = useState(false)
  const [reviewLink, setReviewLink] = useState('')
  const [reviewToken, setReviewToken] = useState(null)

  const {
    variables,
    setVariables,
    updateVariable,
    variableEntries,
    resetVariables,
    syncPlaceholders,
  } = useContractVariables()

  const normalizedProfile = profile?.toLowerCase() || 'contract'
  const isContractProfile = normalizedProfile === 'contract'
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

  const handleProfileChange = useCallback((value) => {
    setProfile(value?.toLowerCase() || 'contract')
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
      debounce((json, vId, setVersionsRef, setLastSavedRef, setIsSavingRef) => {
        setIsSavingRef(true)
        setVersionsRef((prev) => {
          const updated = prev.map((v) =>
            v.id === vId
              ? {
                ...v,
                json,
                timestamp: formatTimestamp(new Date()),
                isFormatted: true,
                metadata: {
                  ...(v.metadata || {}),
                  variables,
                },
              }
              : v
          )
          saveToStorage(updated)
          setLastSavedRef(new Date())
          setTimeout(() => setIsSavingRef(false), 800)
          return updated
        })
      }, 2000),
    [variables]
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

        if (!isEditorEditable) return true

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

      const result = transitionSOP({
        currentStatus: statusNow,
        nextStatus,
        note,
        actor,
        currentTrail,
      })

      if (!result.ok) {
        console.error(result.error)
        return
      }

      updateCurrentVersionMetadata({
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
      })
    },
    [currentVersion, updateCurrentVersionMetadata]
  )

  const submitSOPForReview = useCallback(
    (note = '') => {
      updateSOPState(
        SOP_STATES.UNDER_REVIEW,
        note || 'Submitted for review'
      )
    },
    [updateSOPState]
  )

  const approveSOP = useCallback(
    (note = '') => {
      updateSOPState(SOP_STATES.EFFECTIVE, note || 'Approved')
    },
    [updateSOPState]
  )

  const sendSOPBackToDraft = useCallback(
    (note = '') => {
      updateSOPState(SOP_STATES.DRAFT, note || 'Sent back to draft')
    },
    [updateSOPState]
  )

  const markSOPObsolete = useCallback(
    (note = '') => {
      updateSOPState(SOP_STATES.OBSOLETE, note || 'Marked obsolete')
    },
    [updateSOPState]
  )

  useEffect(() => {
    if (isContractProfile) {
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

  const manualSave = useCallback(() => {
    if (!editor || !isEditorEditable) return

    debouncedSave.cancel()
    setIsSaving(true)

    const json = editor.getJSON()

    setVersions((prev) => {
      const updated = prev.map((v) =>
        v.id === currentVersionId
          ? {
            ...v,
            json,
            timestamp: formatTimestamp(new Date()),
            isFormatted: true,
            metadata: {
              ...(v.metadata || {}),
              variables,
            },
          }
          : v
      )

      saveToStorage(updated)
      setLastSaved(new Date())
      setTimeout(() => setIsSaving(false), 800)
      return updated
    })
  }, [editor, currentVersionId, debouncedSave, variables, isEditorEditable])

  const createNewVersion = useCallback(() => {
    if (!editor || !isEditorEditable) return

    setVersions((prev) => {
      const versionNumber = prev.length + 1
      const newId = `v${versionNumber}`
      const json = editor.getJSON()

      const newVersion = {
        id: newId,
        json,
        timestamp: formatTimestamp(new Date()),
        isFormatted: true,
        metadata: {
          variables,
          reviewStatus: WORKFLOW_STATES.DRAFT,
          sentForReviewAt: null,
          reviewComments: [],
          reviewToken: null,
          sopStatus: currentVersion?.metadata?.sopStatus || SOP_STATES.DRAFT,
          sopMetadata:
            currentVersion?.metadata?.sopMetadata ||
            DEFAULT_SOP_VERSION_METADATA.sopMetadata,
          auditTrail: currentVersion?.metadata?.auditTrail || [],
          versionNote: currentVersion?.metadata?.versionNote || '',
          approvedBy: currentVersion?.metadata?.approvedBy || '',
          obsoleteReason: currentVersion?.metadata?.obsoleteReason || '',
        },
      }

      const updated = [...prev, newVersion]
      saveToStorage(updated)
      setCurrentVersionId(newId)
      setReviewLink('')
      setReviewToken(null)
      return updated
    })
  }, [editor, variables, currentVersion, isEditorEditable])

  useEffect(() => {
    if (!editor) return

    const handleUpdate = () => {
      if (!isEditorEditable) return

      debouncedSave(
        editor.getJSON(),
        currentVersionId,
        setVersions,
        setLastSaved,
        setIsSaving
      )
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
      debouncedSave.cancel()
    }
  }, [editor, currentVersionId, debouncedSave, isEditorEditable])

  const loadVersion = useCallback(
    (versionId) => {
      const version = versions.find((v) => v.id === versionId)

      if (version && editor) {
        editor.commands.setContent(version.json, false)
        setCurrentVersionId(versionId)
        setVariables(version.metadata?.variables || {})
        setReviewToken(version.metadata?.reviewToken || null)

        if (version.metadata?.reviewToken) {
          setReviewLink(
            buildReviewLink({
              token: version.metadata.reviewToken,
              versionId,
            })
          )
        } else {
          setReviewLink('')
        }
      }
    },
    [editor, versions, setVariables]
  )

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
    if (!editor || isInitialized.current) return

    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')

    if (saved.length > 0) {
      const normalizedSaved = saved.map((version) => ({
        ...version,
        metadata: {
          ...(version.metadata || {}),
          variables: version.metadata?.variables || {},
          reviewStatus: version.metadata?.reviewStatus || WORKFLOW_STATES.DRAFT,
          sentForReviewAt: version.metadata?.sentForReviewAt || null,
          reviewComments: version.metadata?.reviewComments || [],
          reviewToken: version.metadata?.reviewToken || null,
          sopStatus: version.metadata?.sopStatus || SOP_STATES.DRAFT,
          sopMetadata:
            version.metadata?.sopMetadata ||
            DEFAULT_SOP_VERSION_METADATA.sopMetadata,
          auditTrail: version.metadata?.auditTrail || [],
          versionNote: version.metadata?.versionNote || '',
          approvedBy: version.metadata?.approvedBy || '',
          obsoleteReason: version.metadata?.obsoleteReason || '',
        },
      }))

      setVersions(normalizedSaved)

      const lastVersion = normalizedSaved[normalizedSaved.length - 1]
      setCurrentVersionId(lastVersion.id)
      editor.commands.setContent(lastVersion.json, false)
      setVariables(lastVersion.metadata?.variables || {})
      setReviewToken(lastVersion.metadata?.reviewToken || null)

      if (lastVersion.metadata?.reviewToken) {
        setReviewLink(
          buildReviewLink({
            token: lastVersion.metadata.reviewToken,
            versionId: lastVersion.id,
          })
        )
      }
    } else {
      const initialContent = {
        type: 'doc',
        content: [
          {
            type: 'heading',
            attrs: { level: 1 },
            content: [{ type: 'text', text: 'AI Law Document Example' }],
          },
          {
            type: 'paragraph',
            content: [
              {
                type: 'text',
                text: 'Testing versioning, block IDs and table structure.',
              },
            ],
          },
        ],
      }

      const initialVersion = {
        id: 'v1',
        json: initialContent,
        timestamp: formatTimestamp(new Date()),
        isFormatted: true,
        metadata: {
          variables: {},
          reviewStatus: WORKFLOW_STATES.DRAFT,
          sentForReviewAt: null,
          reviewComments: [],
          reviewToken: null,
          ...DEFAULT_SOP_VERSION_METADATA,
        },
      }

      setVersions([initialVersion])
      setCurrentVersionId('v1')
      editor.commands.setContent(initialContent, false)
      setVariables(initialVersion.metadata?.variables || {})
      saveToStorage([initialVersion])
    }

    isInitialized.current = true
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

        const response = await fetch('http://localhost:8000/extract-text', {
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
        if (
          (mod && key === 's') ||
          (mod && key === 'p') ||
          (mod && e.shiftKey && key === 'v')
        ) {
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
        createNewVersion()
      }

      if (mod && !e.shiftKey && !e.altKey && key === 'p') {
        e.preventDefault()
        printDocument(editor.getHTML(), variables)
      }
    }

    window.addEventListener('keydown', handleGlobalKeyDown)
    return () => window.removeEventListener('keydown', handleGlobalKeyDown)
  }, [editor, variables, manualSave, createNewVersion, isEditorEditable])

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
      {!isClientReviewMode && (
        <MenuBar
          editor={editor}
          onSave={manualSave}
          onNewVersion={createNewVersion}
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

        {isContractProfile && showVariablesPanel && (
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
            />

            <SOPReferencesPanel
              references={currentSOPMetadata?.references || []}
              onChange={updateSOPReferences}
              isReadOnly={!isEditorEditable}
            />

            <SOPActions
              sopStatus={currentSOPStatus}
              onSubmitForReview={submitSOPForReview}
              onApprove={approveSOP}
              onSendBackToDraft={sendSOPBackToDraft}
              onMarkObsolete={markSOPObsolete}
              isClientReviewMode={isClientReviewMode}
            />

            <SOPTimeline sopStatus={currentSOPStatus} />

            <SOPAuditTrail auditTrail={currentSOPAuditTrail} />
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