/**
 * editorUtils.js
 * ==============
 * Utilities for inspecting TipTap editor state.
 * Kept separate from App.jsx so they can be unit-tested independently.
 */

/**
 * Recursively extract all plain text from a TipTap node tree.
 * Returns a flat string of every text leaf joined by spaces.
 *
 * @param {object} node - Any TipTap JSON node
 * @returns {string}
 */
export function extractTextFromNode(node) {
  if (!node || typeof node !== 'object') return ''
  if (node.type === 'text') return (node.text || '').trim()

  const children = node.content || []
  return children
    .map(extractTextFromNode)
    .filter(Boolean)
    .join(' ')
    .trim()
}

/**
 * Determine whether a TipTap JSON document is effectively empty.
 *
 * A document is considered empty when ALL of the following are true:
 *   - It has no nodes, OR
 *   - Every node is a blank paragraph (type=paragraph with no content children), OR
 *   - Every text leaf in the entire tree is whitespace-only
 *
 * A document is NOT empty if it contains:
 *   - A heading with any text
 *   - A paragraph with any non-whitespace text
 *   - A list, table, image, or any other non-empty block
 *
 * @param {object|null} tiptapJson - The result of editor.getJSON()
 * @returns {boolean} true if the document has no meaningful content
 */
export function isEditorContentEmpty(tiptapJson) {
  if (!tiptapJson || typeof tiptapJson !== 'object') return true

  const nodes = tiptapJson.content || []
  if (nodes.length === 0) return true

  // Extract all text from the entire document tree
  const allText = extractTextFromNode(tiptapJson)
  if (allText.length > 0) return false

  // Check for non-text meaningful nodes (images, horizontal rules, etc.)
  const hasMeaningfulNode = nodes.some((node) => {
    const t = node.type || ''
    // These node types are meaningful even without text
    return ['image', 'horizontalRule', 'codeBlock', 'table'].includes(t)
  })

  return !hasMeaningfulNode
}

/**
 * Count the approximate number of words in a TipTap document.
 *
 * @param {object|null} tiptapJson
 * @returns {number}
 */
export function countWordsInDocument(tiptapJson) {
  const text = extractTextFromNode(tiptapJson || {})
  if (!text) return 0
  return text.split(/\s+/).filter(Boolean).length
}
