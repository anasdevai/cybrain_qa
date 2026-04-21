import React, { useRef } from 'react'
import { useEditorState } from '@tiptap/react'
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  Download,
  Eye,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Redo,
  Table as TableIcon,
  Underline as UnderlineIcon,
  Undo,
} from 'lucide-react'

import { menuBarStateSelector } from './menuBarState'
import './MenuBar.css'

export const MenuBar = ({
  editor,
  onOpenLinkModal,
  onOpenPreview,
  onOCRUpload,
  isOcrLoading,
  isReadOnly = false,
}) => {
  const fileInputRef = useRef(null)

  const editorState = useEditorState({
    editor,
    selector: menuBarStateSelector,
  })

  if (!editor) return null

  const handleFileChange = async (event) => {
    if (isReadOnly) {
      event.target.value = ''
      return
    }

    const file = event.target.files?.[0]
    if (!file) return
    await onOCRUpload?.(file)
    event.target.value = ''
  }

  const runIfEditable = (callback) => {
    if (isReadOnly) return
    callback?.()
  }

  return (
    <div className="editor-menubar">
      <div className="editor-menubar-section">
        {/* Paragraph Dropdown */}
        <div className="editor-select-wrap">
          <select 
            className="editor-select-main"
            onChange={(e) => {
              const val = parseInt(e.target.value)
              if (val === 0) editor.chain().focus().setParagraph().run()
              else editor.chain().focus().toggleHeading({ level: val }).run()
            }}
          >
            <option value="0">Paragraph</option>
            <option value="1">Heading 1</option>
            <option value="2">Heading 2</option>
            <option value="3">Heading 3</option>
          </select>
        </div>

        <div className="editor-divider" />

        {/* Formatting Chipsets */}
        <div className="editor-toolbar-chipset">
          <button type="button" className="editor-icon-btn" onClick={() => runIfEditable(() => editor.chain().focus().undo().run())} disabled={isReadOnly || !editorState.canUndo}>
            <Undo size={18} />
          </button>
          <button type="button" className="editor-icon-btn" onClick={() => runIfEditable(() => editor.chain().focus().redo().run())} disabled={isReadOnly || !editorState.canRedo}>
            <Redo size={18} />
          </button>
        </div>

        <div className="editor-divider" />

        <div className="editor-toolbar-chipset">
          <button type="button" className={`editor-icon-btn ${editorState.isBold ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().toggleBold().run())} disabled={isReadOnly || !editorState.canBold}>
            <Bold size={18} />
          </button>
          <button type="button" className={`editor-icon-btn ${editorState.isItalic ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().toggleItalic().run())} disabled={isReadOnly || !editorState.canItalic}>
            <Italic size={18} />
          </button>
          <button type="button" className={`editor-icon-btn ${editorState.isUnderline ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().toggleUnderline().run())} disabled={isReadOnly}>
            <UnderlineIcon size={18} />
          </button>
        </div>

        <div className="editor-divider" />

        <div className="editor-toolbar-chipset">
          <button type="button" className={`editor-icon-btn ${editor.isActive({ textAlign: 'left' }) ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().setTextAlign('left').run())}>
            <AlignLeft size={18} />
          </button>
          <button type="button" className={`editor-icon-btn ${editor.isActive({ textAlign: 'center' }) ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().setTextAlign('center').run())}>
            <AlignCenter size={18} />
          </button>
          <button type="button" className={`editor-icon-btn ${editor.isActive({ textAlign: 'right' }) ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().setTextAlign('right').run())}>
            <AlignRight size={18} />
          </button>
        </div>

        <div className="editor-divider" />

        <div className="editor-toolbar-chipset">
          <button type="button" className={`editor-icon-btn ${editorState.isBulletList ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().toggleBulletList().run())}>
            <List size={18} />
          </button>
          <button type="button" className={`editor-icon-btn ${editorState.isOrderedList ? 'active' : ''}`} onClick={() => runIfEditable(() => editor.chain().focus().toggleOrderedList().run())}>
            <ListOrdered size={18} />
          </button>
        </div>

        <div className="editor-divider" />

        <div className="editor-toolbar-chipset">
          <button type="button" className={`editor-icon-btn ${editor.isActive('link') ? 'active' : ''}`} onClick={() => runIfEditable(onOpenLinkModal)} disabled={isReadOnly}>
            <LinkIcon size={18} />
          </button>
          <button type="button" className="editor-icon-btn" onClick={() => runIfEditable(() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run())} disabled={isReadOnly}>
            <TableIcon size={18} />
          </button>
        </div>
      </div>

      {/* Right Side: Import & Preview */}
      <div className="menubar-right-actions">
        <button type="button" className="menubar-outline-btn" onClick={() => fileInputRef.current?.click()} disabled={isReadOnly || isOcrLoading}>
          <Download size={16} />
          <span>{isOcrLoading ? '…' : 'Import'}</span>
        </button>
        <button type="button" className="menubar-outline-btn" onClick={onOpenPreview}>
          <Eye size={16} />
          <span>Preview</span>
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
    </div>
  )
}

export default MenuBar
