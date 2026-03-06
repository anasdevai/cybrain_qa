import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import UniqueID from '@tiptap/extension-unique-id'
import Link from '@tiptap/extension-link'

import { Table } from '@tiptap/extension-table'
import { TableRow } from '@tiptap/extension-table-row'
import { TableCell } from '@tiptap/extension-table-cell'
import { TableHeader } from '@tiptap/extension-table-header'

import { MenuBar } from './components/MenuBar'
import StatusBar from './components/StatusBar'
import LinkModal from './components/LinkModal'
import PreviewModal from './components/PreviewModal'


import SideBySideViewer from './diff/SideBySideViewer'

import { debounce } from 'lodash'
// html2pdf imported in PreviewModal

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'

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
  const [profile, setProfile] = useState('Contract')
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false)

  /* NEW STATE */
  const [diffOldVersion, setDiffOldVersion] = useState(null)
  const [diffNewVersion, setDiffNewVersion] = useState(null)
  const [isDiffMode, setIsDiffMode] = useState(false)


  /* ---------------- EDITOR CONFIG ---------------- */

  const extensions = useMemo(() => [
    StarterKit,
    Link.configure({ openOnClick: true }),
    UniqueID.configure({
      types: ['heading', 'paragraph', 'bulletList', 'orderedList', 'table'],
      attributeName: 'block-id'
    }),
    Table.configure({ resizable: true }),
    TableRow,
    TableHeader,
    TableCell
  ], [])

  const editor = useEditor({
    extensions,
    editorProps: {
      attributes: { class: 'tiptap' }
    }
  })

  // Expose editor to window for global browser console debugging
  useEffect(() => {
    if (editor) {
      window.editor = editor
    }
  }, [editor])


  /* ---------------- SAVE SYSTEM ---------------- */

  const debouncedSave = useCallback(
    debounce((json, vId) => {
      setIsSaving(true)
      setVersions(prev => {
        const updated = prev.map(v =>
          v.id === vId
            ? { ...v, json, timestamp: formatTimestamp(new Date()), isFormatted: true }
            : v
        )
        saveToStorage(updated)
        setLastSaved(new Date())
        setTimeout(() => setIsSaving(false), 800)
        return updated
      })
    }, 2000),
    []
  )

  useEffect(() => {
    if (!editor) return

    const handleUpdate = () => {
      // Pass the CURRENT version ID into the debounced save
      debouncedSave(editor.getJSON(), currentVersionId)
    }

    editor.on('update', handleUpdate)
    return () => {
      editor.off('update', handleUpdate)
      debouncedSave.cancel()
    }
  }, [editor, currentVersionId, debouncedSave])

  const manualSave = useCallback(() => {
    if (!editor) return
    debouncedSave.cancel()

    setIsSaving(true)
    const json = editor.getJSON()

    setVersions(prev => {
      const updated = prev.map(v =>
        v.id === currentVersionId
          ? { ...v, json, timestamp: formatTimestamp(new Date()), isFormatted: true }
          : v
      )
      saveToStorage(updated)
      setLastSaved(new Date())
      setTimeout(() => setIsSaving(false), 800)
      return updated
    })
  }, [editor, currentVersionId, debouncedSave])

  /* ---------------- VERSION CONTROL ---------------- */

  const createNewVersion = useCallback(() => {
    if (!editor) return
    const versionNumber = versions.length + 1
    const newId = `v${versionNumber}`
    const json = editor.getJSON()

    const newVersion = {
      id: newId,
      json: json,
      timestamp: formatTimestamp(new Date()),
      isFormatted: true
    }

    const updated = [...versions, newVersion]
    setVersions(updated)
    setCurrentVersionId(newId)
    saveToStorage(updated)
  }, [editor, versions.length])

  const loadVersion = useCallback((versionId) => {
    const version = versions.find(v => v.id === versionId)
    if (version && editor) {
      editor.commands.setContent(version.json, false)
      setCurrentVersionId(versionId)
    }
  }, [editor, versions])

  /* ---------------- KEYBOARD SHORTCUTS ---------------- */

  useEffect(() => {
    if (!editor) return
    const handleKeyDown = (e) => {
      const mod = e.ctrlKey || e.metaKey
      if (!mod) return;

      const key = e.key.toLowerCase();

      if (!e.shiftKey && key === 's') {
        e.preventDefault()
        manualSave()
      }
      if (e.shiftKey && key === 'v') {
        e.preventDefault()
        createNewVersion()
      }
      if (!e.shiftKey && key === 'p') {
        e.preventDefault()
        setIsPreviewModalOpen(true)
      }
      if (!e.shiftKey && key === 'z') {
        e.preventDefault()
        editor.chain().focus().undo().run()
      }
      if (e.shiftKey && key === 'z') {
        e.preventDefault()
        editor.chain().focus().redo().run()
      }
      if (!e.shiftKey && key === 'k') {
        e.preventDefault()
        setLinkModalInitialUrl(editor.getAttributes('link').href || '')
        setIsLinkModalOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [editor, manualSave, createNewVersion])

  /* ---------------- STATS ---------------- */

  const text = editor?.getText() || ''
  const wordCount = text.split(/\s+/).filter(Boolean).length || 0
  const charCount = text.length || 0

  useEffect(() => {
    if (!editor) return
    const updateBlockCount = () => {
      let count = 0
      editor.state.doc.descendants(node => {
        if (node.attrs?.['block-id']) count++
      })
      setBlockCount(count)
    }
    updateBlockCount()
    editor.on('update', updateBlockCount)
    return () => editor.off('update', updateBlockCount)
  }, [editor])

  /* ---------------- LOAD SAVED VERSIONS ---------------- */

  useEffect(() => {
    if (!editor || isInitialized.current) return

    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    if (saved.length > 0) {
      setVersions(saved)
      const lastVersion = saved[saved.length - 1]
      setCurrentVersionId(lastVersion.id)
      editor.commands.setContent(lastVersion.json, false)
    } else {
      const initialContent = {
        type: "doc",
        content: [
          { type: "heading", attrs: { level: 1 }, content: [{ type: "text", text: "AI Law Document Example" }] },
          { type: "paragraph", content: [{ type: "text", text: "Testing versioning, block IDs and table structure." }] }
        ]
      }
      const initialVersion = {
        id: 'v1',
        json: initialContent,
        timestamp: formatTimestamp(new Date()),
        isFormatted: true
      }
      setVersions([initialVersion])
      setCurrentVersionId('v1')
      editor.commands.setContent(initialContent, false)
      saveToStorage([initialVersion])
    }
    isInitialized.current = true
  }, [editor])

  if (!editor) return <div className="loading">Loading AI-LAW Editor...</div>

  const handleLinkSave = (url) => {
    if (url) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    } else {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
    }
    setIsLinkModalOpen(false)
  }


  /* ---------------- DIFF VIEWER ---------------- */

  const compareTwoVersions = (v1, v2) => {
    if (!versions || versions.length < 2) return

    const version1 = versions.find(v => v.id === v1)
    const version2 = versions.find(v => v.id === v2)

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
        profile={profile}
        onProfileChange={setProfile}
        onOpenPreview={() => setIsPreviewModalOpen(true)}
      />
      <div ref={editorRef} className="pdf-export-wrapper">
        <EditorContent editor={editor} />
      </div>
      <StatusBar
        wordCount={wordCount}
        charCount={charCount}
        blockCount={blockCount}
        lastSaved={lastSaved}
        isSaving={isSaving}
        profile={profile}
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