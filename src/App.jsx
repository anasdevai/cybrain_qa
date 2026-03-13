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
import { MenuBar } from './components/MenuBar'
import StatusBar from './components/StatusBar'
import LinkModal from './components/LinkModal'
import PreviewModal from './components/PreviewModal'
import SideBySideViewer from './diff/SideBySideViewer'

import VariablesPanel from './components/contract/VariablesPanel'
import WorkflowTimeline from './components/contract/WorkflowTimeline'
import ReviewActions from './components/contract/ReviewActions'

import useContractVariables from './hooks/useContractVariables'
import useWorkflowState from './hooks/useWorkflowState'
import { WORKFLOW_LABELS } from './utils/contractConstants'

import { debounce } from 'lodash'
import { useState, useEffect, useCallback, useRef, useMemo } from 'react'

import { PlaceholderHighlight } from './extensions/PlaceholderHighlight';
import { PlaceholderSuggestion } from './extensions/PlaceholderSuggestion';
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

  const {
    variables,
    setVariables,
    updateVariable,
    variableEntries,
    resetVariables,
    syncPlaceholders,
  } = useContractVariables()

  const {
    workflowStatus,
    setUnderReview,
    setAccepted,
    setChangesRequested,
    setRejected,
  } = useWorkflowState()

  const normalizedProfile = profile?.toLowerCase() || 'contract'

  const handleProfileChange = useCallback((value) => {
    setProfile(value?.toLowerCase() || 'contract')
  }, [])

  useEffect(() => {
    if (normalizedProfile === 'contract') {
      setShowVariablesPanel(true)
    }
  }, [normalizedProfile])

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

  const manualSave = useCallback(() => {
    if (!window.editorInstance) return

    debouncedSave.cancel()
    setIsSaving(true)

    const json = window.editorInstance.getJSON()

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
  }, [currentVersionId, debouncedSave, variables])

  const createNewVersion = useCallback(() => {
    if (!window.editorInstance) return

    setVersions((prev) => {
      const versionNumber = prev.length + 1
      const newId = `v${versionNumber}`
      const json = window.editorInstance.getJSON()

      const newVersion = {
        id: newId,
        json,
        timestamp: formatTimestamp(new Date()),
        isFormatted: true,
        metadata: {
          variables,
        },
      }

      const updated = [...prev, newVersion]
      saveToStorage(updated)
      setCurrentVersionId(newId)
      return updated
    })
  }, [variables])

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

        if (mod && !e.shiftKey && !e.altKey && key === 's') {
          e.preventDefault()
          manualSave()
          return true
        }

        if (mod && e.shiftKey && !e.altKey && key === 'v') {
          e.preventDefault()
          createNewVersion()
          return true
        }

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
          setLinkModalInitialUrl(editor?.getAttributes('link').href || '')
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
          editor?.chain().focus().insertTable({ rows: 4, cols: 4, withHeaderRow: true }).run()
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

  useEffect(() => {
    if (editor) {
      window.editor = editor
      window.editorInstance = editor
    }
  }, [editor])


  useEffect(() => {
    if (!editor) return;

    editor.storage.placeholderSuggestion.items = [
      'ClientName',
      'Address',
      'Date',
      'Amount',
    ];
  }, [editor]);



  useEffect(() => {
    if (!editor) return

    const handleUpdate = () => {
      debouncedSave(editor.getJSON(), currentVersionId, setVersions, setLastSaved, setIsSaving)
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
      debouncedSave.cancel()
    }
  }, [editor, currentVersionId, debouncedSave])

  const loadVersion = useCallback(
    (versionId) => {
      const version = versions.find((v) => v.id === versionId)
      if (version && editor) {
        editor.commands.setContent(version.json, false)
        setCurrentVersionId(versionId)
        setVariables(version.metadata?.variables || {})
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
      setVersions(saved)
      const lastVersion = saved[saved.length - 1]
      setCurrentVersionId(lastVersion.id)
      editor.commands.setContent(lastVersion.json, false)
      setVariables(lastVersion.metadata?.variables || {})
    } else {
      const initialContent = {
        type: 'doc',
        content: [
          { type: 'heading', attrs: { level: 1 }, content: [{ type: 'text', text: 'AI Law Document Example' }] },
          { type: 'paragraph', content: [{ type: 'text', text: 'Testing versioning, block IDs and table structure.' }] },
        ],
      }

      const initialVersion = {
        id: 'v1',
        json: initialContent,
        timestamp: formatTimestamp(new Date()),
        isFormatted: true,
        metadata: {
          variables: {},
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
    if (!editor) return

    const updatePlaceholdersFromEditor = () => {
      const text = editor.getText()
      const placeholders = extractPlaceholdersFromText(text)
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

  if (!editor) return <div className="loading">Loading AI-LAW Editor...</div>

  const handleLinkSave = (url) => {
    if (url) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    } else {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
    }
    setIsLinkModalOpen(false)
  }

  const insertPlaceholder = useCallback((name) => {
    if (!editor) return
    editor.chain().focus().insertContent(`{{${name}}}`).run()
  }, [editor])

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
      <MenuBar
        editor={editor}
        onSave={manualSave}
        onNewVersion={createNewVersion}
        currentVersion={currentVersionId}
        onLoadVersion={loadVersion}
        onCompare={compareTwoVersions}
        versions={versions}
        onOpenLinkModal={() => {
          setLinkModalInitialUrl(editor.getAttributes('link').href || '')
          setIsLinkModalOpen(true)
        }}
        onOpenPreview={() => setIsPreviewModalOpen(true)}
        profile={normalizedProfile}
        onToggleVariablesPanel={() => setShowVariablesPanel((prev) => !prev)}
        onSendForReview={setUnderReview}
        onInsertPlaceholder={insertPlaceholder}
      />

      <div className={`editor-layout ${normalizedProfile === 'contract' && showVariablesPanel ? 'with-right-panel' : ''}`}>
        <div className="center-editor">
          <div ref={editorRef} className="pdf-export-wrapper">
            <EditorContent editor={editor} />
          </div>
        </div>

        {normalizedProfile === 'contract' && showVariablesPanel && (
          <div className="right-panel">
            <VariablesPanel
              variableEntries={variableEntries}
              onChange={updateVariable}
              onReset={resetVariables}
            />

            <ReviewActions
              workflowStatus={WORKFLOW_LABELS[workflowStatus] || workflowStatus}
              setUnderReview={setUnderReview}
              setAccepted={setAccepted}
              setChangesRequested={setChangesRequested}
              setRejected={setRejected}
            />

            <WorkflowTimeline workflowStatus={workflowStatus} />
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
        workflowStatus={workflowStatus}
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