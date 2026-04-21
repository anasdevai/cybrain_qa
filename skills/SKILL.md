---

name: sop-editor-qa-system
description: Use this skill when working on the SOP Editor, QA workflow, versioning system, UI layout, or API integration in the Cybrain QS project.
----------------------------------------------------------------------------------------------------------------------------------------------------

# 🎯 Purpose

This skill ensures safe, structured, and production-ready development of the AI-powered SOP Editor and QA system.

The system is NOT a simple editor. It is a **QA workspace** with:

* SOP document editing
* Versioning
* Linked QA context (Deviations, CAPAs, Audits, Decisions)
* API-driven architecture
* Future AI-assisted workflows

---

# 🧠 Core Principles

1. Always preserve **working functionality**
2. Never break **API integration**
3. Maintain **data integrity (PostgreSQL)**
4. UI must follow **Figma design strictly**
5. System should behave like a **real QA tool**, not a demo UI

---

# ⚙️ System Context

## Frontend

* React + Vite
* TipTap editor
* Component-based architecture

## Backend

* FastAPI
* PostgreSQL (cybrain_db)

## Key Features

* SOP Editor (rich text)
* Versioning system
* Linked data graph
* Related context API (`/api/sops/{id}/related`)

---

# 🚫 Critical Rules (DO NOT BREAK)

* Do NOT modify working API endpoints
* Do NOT change request/response structure
* Do NOT remove versioning logic
* Do NOT break editor initialization
* Do NOT replace TipTap core setup
* Do NOT introduce random UI frameworks (keep consistency)

---

# 🧩 Editor Behavior Requirements

## Default Mode (IMPORTANT)

* Editor opens in **full-width focused mode**
* No sidebar visible by default
* No AI/chat assistant visible
* No split layout

## Visible Components

* Top header
* Action bar (Save, New Version, Preview)
* Toolbar
* Editor canvas

## Hidden by Default

* Metadata panel
* References panel
* Lifecycle panel
* Linked context
* AI assistant

These must be:
→ conditionally rendered (NOT deleted)

---

# 🧱 UI Implementation Rules

* Follow Figma design strictly (no improvisation)
* Maintain spacing system (16px / 24px)
* Use consistent layout structure across app
* Avoid mixing Tailwind + custom CSS inconsistently
* Use existing styling patterns from codebase

## Layout Structure

* Header
* Action bar
* Toolbar
* Editor canvas (centered / full-width)
* Optional right sidebar (toggle-based)

---

# 🔗 Linked Context Rules

* Data source: `/api/sops/{id}/related`
* Must include:

  * Deviations
  * CAPAs
  * Audit Findings
  * Decisions

## UI Requirements

* Group data by entity type
* Each item must be:

  * Card/row styled
  * Show title + status
* NEVER display raw JSON

---

# 🧾 Versioning Rules

* Support:

  * Create new version
  * Save draft
  * Load version history
* Must not break existing version flow
* Version compare should remain functional

---

# 🔌 API Integration Rules

* Use existing functions from `editorApi.js`
* If function missing:
  → FIX export OR align usage
  → DO NOT invent new API

## Required flows:

* Load SOP
* Save SOP
* Create version
* Fetch versions
* Fetch related context

---

# 🧠 AI Feature Constraints (Current Phase)

Allowed:

* Suggest improvements
* Provide explanations

NOT allowed:

* Auto write-back into editor
* Auto overwrite content

---

# 🧪 Validation Checklist (MANDATORY)

Before completing ANY task:

* App runs without Vite errors
* No console errors
* Editor loads successfully
* Save works
* Versioning works
* Related context loads
* Layout is responsive
* UI matches Figma
* No broken imports

---

# 📱 Responsiveness Rules

* Follow existing app responsiveness patterns
* Do NOT create custom breakpoints randomly
* Ensure:

  * Editor scales properly
  * No overflow issues
  * No layout break on smaller screens

---

# 🔄 Workflow to Follow

1. Understand task scope
2. Identify affected files
3. Avoid touching unrelated logic
4. Implement changes cleanly
5. Run project
6. Fix errors (if any)
7. Validate against checklist
8. Then mark complete

---

# ⚠️ Common Mistakes to Avoid

* Breaking imports (TipTap extensions)
* Removing functionality to fix build
* Mixing old + new UI layouts
* Showing raw backend data in UI
* Leaving empty layout gaps
* Ignoring responsiveness
* Modifying API unnecessarily

---

# ✅ Expected Outcome

A **stable, production-ready SOP Editor** that:

* Works end-to-end
* Matches Figma design
* Supports QA workflows
* Maintains clean architecture
* Ready for AI enhancement phase

---
