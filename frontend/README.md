# AI Law Document Editor

AI Law Document Editor is a structured rich text editor built with React and Tiptap that supports document versioning, comparison between versions, block identification, and export capabilities. The goal of this project is to help legal teams manage evolving documents, track changes between versions, and maintain structured content.

The editor is designed to work smoothly across desktop and mobile devices while preserving document structure such as headings, paragraphs, and tables.

---

## Features

### Rich Text Editing
The editor is powered by Tiptap and provides a modern writing experience including headings, paragraphs, lists, links, and formatting options. It also supports tables with resizable columns.

### Block ID System
Each content block receives a unique identifier. This allows the system to track document structure and identify changes between different versions.

### Version Control
Users can create multiple versions of the document. Every version stores the document structure in JSON format along with timestamps.

### Version Comparison
Two versions of a document can be compared side by side. The comparison engine highlights differences clearly:

Green indicates added content  
Red indicates removed content  
Yellow indicates modified content

This helps users quickly understand what changed between versions.

### Side by Side Diff Viewer
The project includes a responsive comparison viewer that works on both desktop and mobile devices. Desktop shows panels side by side, while mobile stacks them vertically for readability.

### Auto Save System
The editor automatically saves changes using a debounced save mechanism to avoid excessive storage operations.

### Manual Save
Users can manually trigger a save using keyboard shortcuts or toolbar controls.

### Preview Mode
Documents can be previewed in a print style layout before exporting.

### PDF Export
The editor supports exporting documents as PDFs.

### Mobile Responsive Layout
The UI adapts to smaller screens and supports scrolling for large documents and tables.

---

## Technologies Used

React  
Tiptap Editor  
ProseMirror (underlying editor engine)  
JavaScript  
CSS Flexbox layout  
LocalStorage for version persistence  
Lodash debounce

---

## How Versioning Works

Each version of the document is stored as structured JSON. When a new version is created, the editor stores the current document state along with metadata like timestamp and version ID.

The diff engine compares blocks and content between two JSON structures and generates highlighted differences.

---

## Responsive Design

The project supports multiple screen sizes including mobile devices. The comparison viewer adjusts automatically:

Desktop shows both versions side by side.

Mobile stacks the versions vertically with scroll support.
