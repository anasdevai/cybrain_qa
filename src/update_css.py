# import re
# import os

# app_css_path = r'c:\Users\zma\Desktop\Testing-Module\vite-project\src\App.css'

# with open(app_css_path, 'r', encoding='utf-8') as f:
#     content = f.read()

# # Make the body background match Juris Obsidian desk
# content = re.sub(r'background: linear-gradient\(135deg, #f5f7fa, #c3cfe2\);', r'background: var(--color-surface);', content)

# # Fonts
# content = re.sub(r"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;", r'font-family: var(--font-body);', content)

# # Editor Wrapper
# content = re.sub(r'\.editor-wrapper\s*\{[^}]+\}', r'''.editor-wrapper {
#   max-width: 1400px;
#   margin: 0 auto;
#   padding: 40px;
#   padding-bottom: calc(110px + env(safe-area-inset-bottom));
#   min-height: 100dvh;
#   background: transparent;
#   width: 100%;
#   min-width: 0;
#   border: none;
# }''', content)

# # Button Group
# content = re.sub(r'\.button-group\s*\{[^}]+\}', r'''.button-group {
#   display: flex;
#   flex-wrap: wrap;
#   align-items: center;
#   gap: 8px;
#   padding: 16px;
#   background: var(--color-surface-container-lowest);
#   border: none;
#   border-radius: var(--radius-lg);
#   box-shadow: var(--shadow-ambient);
#   width: 100%;
#   min-width: 0;
# }''', content)

# # Button Group hover
# content = re.sub(r'\.button-group button:hover[^}]+background:\s*#\w+;[^}]+}', r'''.button-group button:hover:not(:disabled) {
#   background: var(--color-surface-container-high);
#   border-color: var(--color-ghost-border);
# }''', content)

# content = re.sub(r'\.button-group button\.is-active\s*\{[^}]+\}', r'''.button-group button.is-active {
#   background: var(--color-secondary);
#   color: var(--color-on-primary);
#   border-color: var(--color-secondary);
# }''', content)

# content = re.sub(r'\.button-group button\.is-active:hover\s*\{[^}]+\}', r'''.button-group button.is-active:hover {
#   filter: brightness(1.2);
# }''', content)

# # Buttons generic
# content = re.sub(r'\.button-group button\s*\{[^}]+\}', r'''.button-group button {
#   padding: 8px 12px;
#   border: 1px solid var(--color-ghost-border);
#   background: transparent;
#   color: var(--color-on-surface);
#   border-radius: var(--radius-md);
#   cursor: pointer;
#   font-size: 14px;
#   font-family: var(--font-body);
#   font-weight: 600;
#   display: inline-flex;
#   align-items: center;
#   justify-content: center;
#   gap: 4px;
#   flex: 0 1 auto;
#   transition: all 0.2s ease;
#   min-width: 0;
#   max-width: 100%;
# }''', content)

# # Primary action buttons
# content = re.sub(r'\.save-btn,\s*\n\.version-btn\s*\{[^}]+\}', r'''.save-btn,
# .version-btn,
# .pdf-export-btn {
#   background: linear-gradient(135deg, var(--color-primary), var(--color-primary-container)) !important;
#   color: var(--color-on-primary) !important;
#   border: 1px solid rgba(255, 255, 255, 0.1) !important;
#   box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), var(--shadow-sm);
# }''', content)
# content = re.sub(r'\.pdf-export-btn\s*\{[^}]+\}', '', content)

# # Dropdowns
# content = re.sub(r'\.version-select\s*\{[^}]+\}', r'''.version-select {
#   padding: 8px 12px;
#   border: 1px solid var(--color-ghost-border);
#   border-radius: var(--radius-md);
#   background: var(--color-surface-container-lowest);
#   color: var(--color-on-surface);
#   font-family: var(--font-body);
#   font-size: 14px;
#   cursor: pointer;
#   min-width: 0;
#   max-width: 100%;
#   transition: border-color 0.2s ease;
# }
# .version-select:focus {
#   border-color: rgba(204, 168, 48, 0.5);
#   font-weight: 500;
#   outline: none;
# }''', content)

# # Layout
# content = re.sub(r'\.editor-layout\.with-right-panel\s*\{[^}]+\}', r'''.editor-layout.with-right-panel {
#   display: grid;
#   grid-template-columns: minmax(0, 1fr) 340px;
#   gap: 24px;
#   align-items: start;
#   width: 100%;
# }''', content)
# content = re.sub(r'max-width: 320px;', 'max-width: 340px;', content)

# # Tiptap editing area
# content = re.sub(r'\.tiptap \{[\s\S]*?transition: all 0.3s ease;[\s\S]*?\}', r'''.tiptap {
#   background: var(--color-surface-container-lowest);
#   color: var(--color-on-surface);
#   border: none;
#   padding: 60px 40px;
#   border-radius: var(--radius-md);
#   min-height: 800px;
#   font-size: 16px;
#   line-height: 1.6;
#   font-family: var(--font-body);
#   outline: none;
#   box-shadow: var(--shadow-ambient);
#   transition: all 0.3s ease;
#   width: 100%;
#   box-sizing: border-box;
#   caret-color: var(--color-tertiary);
# }''', content)

# content = re.sub(r'\.tiptap:focus-within\s*\{[^}]+\}', r'''.tiptap:focus-within {
#   box-shadow: var(--shadow-md);
# }''', content)

# content = re.sub(r'\.tiptap h1\s*\{[^}]+\}', r'''.tiptap h1 {
#   font-family: var(--font-heading);
#   color: var(--color-primary-container);
#   line-height: 1.2;
#   text-align: center;
#   font-size: 32px;
#   font-weight: 500;
#   margin: 0 0 40px 0;
# }''', content)
# content = re.sub(r'\.tiptap h2\s*\{[^}]+\}', r'''.tiptap h2 {
#   font-family: var(--font-heading);
#   color: var(--color-primary-container);
#   line-height: 1.2;
#   font-size: 24px;
#   font-weight: 500;
#   margin: 32px 0 16px;
# }''', content)
# content = re.sub(r'\.tiptap h3\s*\{[^}]+\}', r'''.tiptap h3 {
#   font-family: var(--font-heading);
#   color: var(--color-primary-container);
#   line-height: 1.2;
#   font-size: 18px;
#   font-weight: 500;
#   margin: 24px 0 12px;
#   text-transform: uppercase;
# }''', content)

# # Panels
# content = re.sub(r'\.contract-panel\s*\{[^}]+\}', r'''.contract-panel {
#   background: var(--color-surface-container-high);
#   border: none;
#   border-radius: var(--radius-lg);
#   padding: 24px;
#   box-sizing: border-box;
#   box-shadow: var(--shadow-sm);
#   min-width: 0;
# }''', content)
# content = re.sub(r'\.contract-panel h3\s*\{[^}]+\}', r'''.contract-panel h3 {
#   margin: 0 0 16px 0;
#   font-size: 18px;
#   font-family: var(--font-heading);
#   font-weight: 500;
#   color: var(--color-primary-container);
# }''', content)

# content = re.sub(r'\.variable-field input\s*\{[^}]+\}', r'''.variable-field input {
#   width: 100%;
#   padding: 12px 14px;
#   border: 1px solid var(--color-ghost-border);
#   background: var(--color-surface-container-lowest);
#   border-radius: var(--radius-md);
#   font-family: var(--font-body);
#   font-size: 14px;
#   color: var(--color-on-surface);
#   box-sizing: border-box;
#   transition: border-color 0.2s ease;
# }
# .variable-field input:focus {
#   border-color: rgba(204, 168, 48, 0.5);
#   outline: none;
# }''', content)

# # Status bar
# content = content.replace(r'background: #f8fafc;', r'background: var(--color-surface-container-lowest);')
# content = content.replace(r'border-top: 1px solid #dbe3ee;', r'border-top: 1px solid var(--color-ghost-border); box-shadow: 0 -4px 30px rgba(25, 28, 29, 0.05);')
# content = content.replace(r'color: #f59e0b;', r'color: var(--color-tertiary-hover);')

# # Status chip
# content = re.sub(r'\.workflow-status-chip\s*\{[^}]+\}', r'''.workflow-status-chip {
#   display: inline-flex;
#   align-items: center;
#   justify-content: center;
#   padding: 6px 14px;
#   border-radius: var(--radius-xl);
#   font-size: 13px;
#   font-weight: 700;
#   text-transform: uppercase;
#   background: var(--color-tertiary-container);
#   color: #3b2f00;
#   border: none;
#   white-space: nowrap;
# }''', content)

# with open(app_css_path, 'w', encoding='utf-8') as f:
#     f.write(content)

# print("CSS updating applied.")
