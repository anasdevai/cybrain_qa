"""Prompt builders for SOP editor actions."""

from backend.schemas.sop_actions import ActionRequest, JustifyRequest

# Improve / Rewrite: no Qdrant/RAG — model uses only instructions + document fields + section text.
IMPROVE_REWRITE_NO_RAG_CONTEXT = (
    "(No RAG.) Use only SOP/section metadata and the quoted section text — no external library."
)

_SPEED = (
    "SPEED: One pass. Return only minified JSON (no markdown, no text outside JSON). "
    "Be concise: no filler, no extra examples."
)

_LANG = "Match input language. Keep codes and abbreviations unchanged."


def build_improve_prompt(request: ActionRequest, context: str) -> str:
    return f"""GMP/QA editor — IMPROVE (light edit, same meaning).

{_SPEED}
{_LANG}

SOP: "{request.sop_title}" | Section: "{request.section_title}" | Type: {request.section_type}
Note: {context}

Rules: fix grammar; clearer active/imperative where quick; remove hedging; no new headings/steps; keep length near original.

Text:
\"\"\"{request.section_text}\"\"\"

Return ONLY: {{"improved_text": "<text>"}}"""


def build_rewrite_prompt(request: ActionRequest, context: str) -> str:
    return f"""GMP/QA editor — REWRITE (full rephrase, same substance).

{_SPEED}
{_LANG}

SOP: "{request.sop_title}" | Section: "{request.section_title}" | Type: {request.section_type}
Note: {context}

Rules: imperative, clear order, role-anchored; no new headings; do not bloat (tight rewrite, not a longer essay).

Text:
\"\"\"{request.section_text}\"\"\"

Return ONLY: {{"rewritten_text": "<text>"}}"""


def build_gap_check_prompt(request: ActionRequest, context: str) -> str:
    return f"""You are a QA/GMP compliance auditor.

SOP: "{request.sop_title}"
Section: "{request.section_title}" (type: {request.section_type})

Context from similar compliant SOPs:
{context}

Analyze the following SOP text for QA/GMP compliance gaps.
Look for missing steps, undefined frequencies, unclear responsibilities,
missing controls, undefined terms, and missing documentation requirements.

Text to analyze:
\"\"\"{request.section_text}\"\"\"

Return ONLY a valid JSON object. If no gaps are found, return an empty gaps array:
{{
  "gaps": [
    {{
      "issue": "short descriptive label",
      "explanation": "why this is a problem in GMP/QA context",
      "recommendation": "exact text to add or change"
    }}
  ],
  "section_assessed": "{request.section_title}"
}}"""


def build_convert_prompt(request: ActionRequest) -> str:
    return f"""You are a QA document specialist.

Convert the following raw text into a properly structured SOP document.

MANDATORY:
- You must produce all five sections below.
- If a section lacks enough information, write "[To be defined - add content here]".
- Do not omit any key.
- Return procedure as a JSON array of strings, one string per step.

SOP title context: "{request.sop_title}"

Raw text to convert:
\"\"\"{request.section_text}\"\"\"

Return ONLY a valid JSON object with exactly these keys:
{{
  "purpose": "one sentence: what this SOP governs and why it exists",
  "scope": "who and what this SOP applies to",
  "responsibilities": "named roles with specific obligations",
  "procedure": [
    "Step 1: first action",
    "Step 2: second action"
  ],
  "documentation": "what records are created, where stored, retention period"
}}"""


def build_convert_retry_prompt(request: ActionRequest) -> str:
    return build_convert_prompt(request) + (
        "\n\nCRITICAL: Return only the JSON object. All five keys must be present and non-empty. "
        "Use placeholder text if source material is incomplete."
    )


def build_justify_prompt(request: JustifyRequest) -> str:
    return f"""You are a QA compliance writer generating a GMP audit trail entry.

SOP: "{request.sop_title}"
Section: "{request.section_title}" ({request.section_type})
Change descriptor: {request.change_type}

Original text:
\"\"\"{request.old_text}\"\"\"

New text:
\"\"\"{request.new_text}\"\"\"

Requirements:
- 2 to 3 sentences only
- Explicitly name the SOP "{request.sop_title}"
- Explicitly name the section "{request.section_title}"
- Explain why the change improves compliance, clarity, or accuracy
- Be specific, not boilerplate

Return ONLY a valid JSON object:
{{
  "justification": "2-3 sentences naming the SOP, section, and reason",
  "change_category": "one of exactly: clarity_improvement | compliance_alignment | error_correction | process_update | regulatory_requirement",
  "regulatory_reference": "relevant GMP clause or ISO standard, or null"
}}"""
