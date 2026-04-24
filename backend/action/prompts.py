"""Prompt builders for SOP editor actions.
Language priority: German (de). All other languages are fully supported.
The AI always detects the language of the input text and responds in the same language.
"""

from schemas.sop_actions import ActionRequest, JustifyRequest

# Improve / Rewrite: no Qdrant/RAG — LLM uses only system-style instructions + document fields + section text.
IMPROVE_REWRITE_NO_RAG_CONTEXT = (
    "(Kein RAG.) Nutze nur Metadaten + unten stehenden Text. / "
    "(No RAG.) Use only metadata + quoted text below."
)

_LANGUAGE_RULE = """LANGUAGE: Match the input language (German if input is German). Do not mix languages. Keep identifiers, codes, and abbreviations unchanged."""

_SPEED_FIRST = """SPEED: Single pass. Return only the JSON object (no markdown, no text before/after). Be concise: no filler, no optional examples, no duplicate lists. Lean text = faster review."""


def _doc_block(request: ActionRequest, context: str) -> str:
    return f"""DOCUMENT
  title: {request.sop_title}
  section: {request.section_title}
  type: {request.section_type}
CONTEXT: {context}"""


def build_improve_prompt(request: ActionRequest, context: str) -> str:
    return f"""You are a GMP/QA technical editor. Task: IMPROVE (light edit only).

{_SPEED_FIRST}

{_LANGUAGE_RULE}

{_doc_block(request, context)}

EDIT RULES (minimal change, same meaning):
- Fix grammar, spelling, punctuation.
- Prefer clear active/imperative phrasing where it helps; remove hedging and vague terms when you can do it briefly.
- Do not add section headings, new structure, or new process steps. Do not change intent.
- Keep length close to the original (no expansion for “polish”).

TEXT:
\"\"\"{request.section_text}\"\"\"

If the section is long, the string value must still be valid JSON: use \\n for line breaks and \\" for any double quote inside the text.

Return ONLY this JSON (one key):
{{"improved_text": "<improved text>"}}"""


def build_rewrite_prompt(request: ActionRequest, context: str) -> str:
    return f"""You are a GMP/QA technical editor. Task: REWRITE (full rephrase, same substance).

{_SPEED_FIRST}

{_LANGUAGE_RULE}

{_doc_block(request, context)}

REWRITE RULES (clear SOP style, do not bloat):
- Imperative, active, role-anchored phrasing; logical order; parallel lists.
- Name responsibilities with concrete roles where the source implies them; replace vague terms with specific conditions only when the source gives enough to do it without inventing data.
- No new section headings (Purpose/Scope/etc.). Do not change the topic or add new process requirements.
- Do not pad: aim for a tight professional rewrite, not a longer essay (similar length to source is ideal unless the source is broken).

TEXT:
\"\"\"{request.section_text}\"\"\"

If the section is long, the string value must still be valid JSON: use \\n for line breaks and \\" for any double quote inside the text.

Return ONLY this JSON (one key):
{{"rewritten_text": "<rewritten text>"}}"""


def build_gap_check_prompt(request: ActionRequest, context: str) -> str:
    return f"""Du bist ein leitender GMP/QA Compliance-Auditor mit Expertise in:
  • ISO 9001:2015 und ISO 13485:2016
  • EU GMP Annex 11 (Computergestützte Systeme)
  • FDA 21 CFR Parts 11, 211 und 820
  • ICH Q10 Pharmazeutisches Qualitätssystem
  • GAMP 5 (Good Automated Manufacturing Practice)
You are equally fluent in German, English, and all other European languages.

{_LANGUAGE_RULE}

═══════════════════════════════════════════════════════════════
DOKUMENTKONTEXT / DOCUMENT CONTEXT
═══════════════════════════════════════════════════════════════
SOP-Titel / SOP Title    : "{request.sop_title}"
Abschnittstitel / Section: "{request.section_title}"
Abschnittstyp / Type     : {request.section_type}

═══════════════════════════════════════════════════════════════
REFERENZMATERIAL / BENCHMARKS FROM COMPLIANT SOPs
═══════════════════════════════════════════════════════════════
{context}

═══════════════════════════════════════════════════════════════
AUFGABE: COMPLIANCE-LÜCKENANALYSE / TASK: COMPLIANCE GAP ANALYSIS
═══════════════════════════════════════════════════════════════
Führe eine gründliche Compliance-Lückenanalyse des folgenden Textes durch.
Perform a thorough compliance gap analysis on the text below.

PRÜFLISTE / AUDIT CHECKLIST:
  1. FEHLENDE SCHRITTE — Sind alle kritischen Prozessschritte vorhanden?
     MISSING STEPS — Are all critical process steps present?
  2. UNDEFINIERTE VERANTWORTLICHKEITEN — Sind Rollen spezifisch benannt?
     UNDEFINED RESPONSIBILITIES — Are roles named specifically?
  3. UNKLARE HÄUFIGKEITEN — Sind Überprüfungsintervalle und Fristen explizit angegeben?
     UNDEFINED FREQUENCIES — Are review/monitoring intervals explicitly stated?
  4. FEHLENDE KONTROLLEN — Sind Datenschutz- und Zugangskontrollmaßnahmen erwähnt?
     MISSING CONTROLS — Are data integrity and access controls mentioned?
  5. UNKLARE SPRACHE — Gibt es vage Begriffe wie "angemessen", "bei Bedarf", "regelmäßig"?
     AMBIGUOUS LANGUAGE — Are vague terms present ("appropriate", "regularly", "as needed")?
  6. DOKUMENTATIONSLÜCKEN — Sind Formularname, Aufbewahrungsort und -dauer angegeben?
     DOCUMENTATION GAPS — Are record names, storage locations, and retention periods specified?
  7. REGULATORISCHE AUSRICHTUNG — Fehlen regulatorische Referenzen wo erforderlich?
     REGULATORY ALIGNMENT — Are required regulatory references missing?
  8. UNDEFINIERTE BEGRIFFE — Werden Abkürzungen oder technische Begriffe ohne Definition verwendet?
     UNDEFINED TERMS — Are abbreviations or technical terms used without definition?

ZU ANALYSIERENDER TEXT / TEXT TO ANALYZE:
\"\"\"{request.section_text}\"\"\"

═══════════════════════════════════════════════════════════════
AUSGABEFORMAT / OUTPUT FORMAT
═══════════════════════════════════════════════════════════════
Schreibe eine klare, gut strukturierte, menschenlesbare Analyse.
KEINE JSON-Struktur — nur lesbaren Fließtext mit nummerierten Punkten.
Write a clear, well-structured, human-readable analysis.
NO JSON structure — only readable text with numbered points.

Format deine Antwort so / Format your response like this:

**Compliance-Lückenanalyse: {request.section_title}**

[Für jede gefundene Lücke / For each gap found:]
**N. [Lückentitel / Gap Title]**
Problem: [Kurze Erklärung warum dies eine GMP/regulatorische Anforderung verletzt]
Empfehlung: [Konkreter, einfügbereiter SOP-Text zur Behebung der Lücke]

[Falls keine Lücken gefunden / If no gaps found:]
✅ Keine Compliance-Lücken identifiziert. Der Text entspricht den GMP/QA-Anforderungen.

Gib NUR eine gültige JSON-Antwort zurück / Return ONLY a valid JSON:
{{
  "analysis": "Deine vollständige, formatierte Analyse hier / Your complete formatted analysis here"
}}"""


def build_convert_prompt(request: ActionRequest) -> str:
    return f"""Du bist ein erfahrener GMP/QA Dokumentationsspezialist.
You are a senior GMP/QA technical writer and regulatory documentation specialist.

{_LANGUAGE_RULE}

Konvertiere den folgenden Rohtext in ein vollständig strukturiertes SOP-Dokument.
Convert the following raw text into a properly structured SOP document.

═══════════════════════════════════════════════════════════════
DOKUMENTKONTEXT / DOCUMENT CONTEXT
═══════════════════════════════════════════════════════════════
SOP-Titel / SOP Title: "{request.sop_title}"

ROHTEXT / RAW TEXT:
\"\"\"{request.section_text}\"\"\"

═══════════════════════════════════════════════════════════════
PFLICHTANFORDERUNGEN / MANDATORY REQUIREMENTS
═══════════════════════════════════════════════════════════════
  • Alle fünf Abschnitte sind PFLICHT. Kein Abschnitt darf fehlen.
    All five sections are MANDATORY. No section may be omitted.
  • Falls ein Abschnitt nicht genug Informationen hat, schreibe:
    "[Zu definieren — [spezifisches Detail] vor SOP-Freigabe festlegen]"
  • Schreibe "procedure" als JSON-Array von Strings, einen Schritt pro String.
  • Verwende GMP-konforme Sprache: imperative Verben, benannte Rollen, keine Mehrdeutigkeit.
  • Minimum 5 Schritte im Verfahrensabschnitt / Minimum 5 steps in the procedure section.

Gib NUR ein gültiges JSON-Objekt mit genau diesen Schlüsseln zurück:
Return ONLY a valid JSON object with exactly these keys:
{{
  "purpose": "Ein Satz: Was diese SOP regelt und warum sie existiert / One sentence: what this SOP governs and why",
  "scope": "Vollständige Geltungsbereichsdefinition mit Rollen, Systemen und ggf. Ausnahmen / Full scope definition",
  "responsibilities": "Benannte Rollen mit spezifischen, imperativen Verpflichtungen / Named roles with specific obligations",
  "procedure": [
    "Schritt 1: [Benannte Rolle] soll [Aktion] mit [Methode/Werkzeug] / Step 1: ...",
    "Schritt 2: [Benannte Rolle] soll [Aktion] und dokumentieren in [Formularname] / Step 2: ...",
    "Schritt 3: ...",
    "Schritt 4: ...",
    "Schritt 5: ..."
  ],
  "documentation": "Alle Formulare, Protokolle und Aufzeichnungen: Name, Aufbewahrungsort, Aufbewahrungsfrist / All records: name, location, retention period"
}}"""


def build_convert_retry_prompt(request: ActionRequest) -> str:
    return build_convert_prompt(request) + (
        "\n\n═══════════════════════════════════════════════════════════════\n"
        "KRITISCHE WIEDERHOLUNGSANWEISUNG / CRITICAL RETRY INSTRUCTION\n"
        "═══════════════════════════════════════════════════════════════\n"
        "Deine vorherige Antwort war kein gültiges JSON oder enthielt fehlende Schlüssel.\n"
        "Your previous response was not valid JSON or was missing required keys.\n"
        "Du MUSST NUR ein gültiges JSON-Objekt mit genau diesen fünf Schlüsseln zurückgeben:\n"
        "  'purpose', 'scope', 'responsibilities', 'procedure' (als Array), 'documentation'\n"
        "Alle fünf Schlüssel müssen vorhanden und nicht leer sein.\n"
        "Verwende professionellen Platzhaltertext wenn Quellinformationen unvollständig sind.\n"
        "KEIN Markdown, KEINE Erklärung, KEIN Text außerhalb des JSON-Objekts."
    )


def build_justify_prompt(request: JustifyRequest) -> str:
    return f"""Du bist ein leitender GMP/QA Compliance-Schreiber, der GMP-Audit-Trail-Einträge erstellt,
die regulatorischen Inspektionsanforderungen entsprechen.
You are a senior GMP/QA compliance writer generating GMP audit trail entries.

{_LANGUAGE_RULE}

═══════════════════════════════════════════════════════════════
ÄNDERUNGSKONTEXT / CHANGE CONTEXT
═══════════════════════════════════════════════════════════════
SOP-Titel / SOP Title    : "{request.sop_title}"
Abschnittstitel / Section: "{request.section_title}"
Abschnittstyp / Type     : {request.section_type}
Änderungstyp / Change    : {request.change_type}

ORIGINALTEXT / ORIGINAL TEXT:
\"\"\"{request.old_text}\"\"\"

NEUER TEXT / NEW TEXT:
\"\"\"{request.new_text}\"\"\"

═══════════════════════════════════════════════════════════════
AUFGABE / TASK
═══════════════════════════════════════════════════════════════
Erstelle eine formelle, rechtlich vertretbare Begründung für diese Änderung.
Write a formal, legally defensible justification for this change.

ANFORDERUNGEN / REQUIREMENTS:
  • Nennt explizit die SOP: "{request.sop_title}"
  • Nennt explizit den Abschnitt: "{request.section_title}"
  • Beschreibt WAS sich geändert hat (Art der Änderung)
  • Erklärt WARUM die Änderung vorgenommen wurde
  • Beschreibt WIE die Änderung Compliance, Risikominimierung oder Qualität verbessert
  • Genau 2 bis 3 Sätze — nicht mehr, nicht weniger
  • Formelle, professionelle Sprache (kein "ich/wir")
  • Vergangenheitsform (die Änderung wurde vorgenommen)

Gib NUR ein gültiges JSON-Objekt zurück / Return ONLY a valid JSON object:
{{
  "justification": "2-3 formelle Sätze mit expliziter Nennung der SOP und des Abschnitts sowie der spezifischen Begründung.",
  "change_category": "eines von genau: clarity_improvement | compliance_alignment | error_correction | process_update | regulatory_requirement",
  "regulatory_reference": "Spezifische regulatorische Klausel (z.B. 'ISO 13485:2016 Abschnitt 4.2.4') oder null"
}}"""
