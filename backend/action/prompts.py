"""Prompt builders for SOP editor actions.
Language priority: German (de). All other languages are fully supported.
The AI always detects the language of the input text and responds in the same language.
"""

from backend.schemas.sop_actions import ActionRequest, JustifyRequest

_LANGUAGE_RULE = """
LANGUAGE RULE (MANDATORY):
  • Detect the language of the input text automatically.
  • Primary priority: German (Deutsch). If the text is in German, respond in German.
  • For all other languages (English, French, Italian, Spanish, etc.), respond in that same language.
  • Never mix languages in your output.
  • Preserve all technical terms, SOP identifiers, and regulatory abbreviations exactly as they appear.
"""


def build_improve_prompt(request: ActionRequest, context: str) -> str:
    return f"""Du bist ein erfahrener GMP/QA Technischer Redakteur (Senior GMP/QA Technical Writer) mit umfassender
Expertise in ISO 9001, ISO 13485, EU GMP Annex 11, ICH Q10 und FDA 21 CFR Part 11.
You are equally fluent in German, English, and all other European languages.

{_LANGUAGE_RULE}

═══════════════════════════════════════════════════════════════
DOKUMENTKONTEXT / DOCUMENT CONTEXT
═══════════════════════════════════════════════════════════════
SOP-Titel / SOP Title    : "{request.sop_title}"
Abschnittstitel / Section: "{request.section_title}"
Abschnittstyp / Type     : {request.section_type}

═══════════════════════════════════════════════════════════════
REFERENZMATERIAL / REFERENCE MATERIAL
═══════════════════════════════════════════════════════════════
{context}

═══════════════════════════════════════════════════════════════
AUFGABE: TEXT VERBESSERN / TASK: IMPROVE THE TEXT
═══════════════════════════════════════════════════════════════
Verbessere ausschließlich den unten angegebenen Text.
Improve ONLY the text provided below.

QUALITÄTSKRITERIEN / QUALITY CRITERIA:
  • Korrigiere alle Grammatik-, Interpunktions- und Rechtschreibfehler
    (Fix all grammar, punctuation, and spelling errors)
  • Ersetze Passivkonstruktionen durch Aktivsätze, wo dies die Klarheit verbessert
    (Replace passive voice with active voice where it improves clarity)
  • Entferne unklare oder mehrdeutige Formulierungen
    (Remove vague or ambiguous language)
  • Ersetze unspezifische Begriffe ("bei Bedarf", "regelmäßig", "as needed", "regularly")
    durch konkrete Angaben mit Häufigkeit oder definierten Bedingungen
  • Stelle sicher, dass Verantwortlichkeiten namentlich benannten Rollen zugeordnet sind
    (Ensure responsibilities are attributed to named roles)
  • Verwende durchgehend imperative, klare Formulierungen
    (Use consistent, imperative, unambiguous language)

STRIKTE REGELN / STRICT RULES:
  ✗ KEINE neuen Abschnittsüberschriften hinzufügen (Zweck, Geltungsbereich, etc.)
  ✗ KEINE Umstrukturierung in ein vollständiges SOP-Format
  ✗ KEINE Änderung des inhaltlichen Sinns oder Kernaussage
  ✗ NUR die kleinsten sinnvollen Verbesserungen, die die Qualitätskriterien erfüllen
  ✓ Die Struktur und den Stil des Originaltexts beibehalten

ZU VERBESSERNDER TEXT / TEXT TO IMPROVE:
\"\"\"{request.section_text}\"\"\"

═══════════════════════════════════════════════════════════════
AUSGABEFORMAT / OUTPUT FORMAT
═══════════════════════════════════════════════════════════════
Gib NUR ein gültiges JSON-Objekt zurück (kein Markdown, keine Erklärungen außerhalb):
Return ONLY a valid JSON object (no markdown, no text outside the JSON):
{{
  "improved_text": "Der vollständig verbesserte Text hier. / The fully improved text here."
}}"""


def build_rewrite_prompt(request: ActionRequest, context: str) -> str:
    return f"""Du bist ein führender GMP/QA Technischer Redakteur und Regulatory-Dokumentationsspezialist
mit tiefgreifender Expertise in ISO 9001:2015, ISO 13485:2016, EU GMP Annex 11, GAMP 5 und FDA 21 CFR.
You are equally fluent in German, English, and all other European languages.

{_LANGUAGE_RULE}

═══════════════════════════════════════════════════════════════
DOKUMENTKONTEXT / DOCUMENT CONTEXT
═══════════════════════════════════════════════════════════════
SOP-Titel / SOP Title    : "{request.sop_title}"
Abschnittstitel / Section: "{request.section_title}"
Abschnittstyp / Type     : {request.section_type}

═══════════════════════════════════════════════════════════════
REFERENZMATERIAL / REFERENCE MATERIAL
═══════════════════════════════════════════════════════════════
{context}

═══════════════════════════════════════════════════════════════
AUFGABE: TEXT VOLLSTÄNDIG UMSCHREIBEN / TASK: COMPLETE REWRITE
═══════════════════════════════════════════════════════════════
Schreibe den unten angegebenen Text vollständig um.
Perform a COMPLETE rewrite of the text below.

Das Ziel ist ein produktionsreifer, professioneller SOP-Text, der einer regulatorischen Inspektion standhalten kann.
The goal is a production-ready, professional SOP text that could pass a regulatory inspection.

UMSCHREIBKRITERIEN / REWRITE CRITERIA:
  • Verwende ausschließlich Aktivsätze und imperative Verbformen
    (Use active voice and imperative verbs throughout)
  • Jeder Satz muss eine benannte Rolle als Subjekt haben (z.B. "Der QA-Manager", "The System Owner")
    (Every sentence must name a specific role — never "someone" or "the team")
  • Ersetze alle vagen Qualifikatoren durch konkrete Werte, Häufigkeiten oder definierte Bedingungen
    (Replace all vague qualifiers with specific values, frequencies, or defined conditions)
  • Stelle eine logische, chronologische Prozessreihenfolge sicher
    (Ensure logical, chronological process order)
  • Verwende parallele Struktur in Aufzählungen und Listen
    (Use parallel structure in lists and enumerated items)
  • Markiere kritische Schritte mit entsprechender Sprache (z.B. "Kritisch:", "ACHTUNG:", "Critical:", "CAUTION:")
    (Flag critical steps with appropriate language)
  • Füge Querbezüge zu Formularen, Registern oder unterstützenden Dokumenten ein, wo angemessen
    (Reference supporting forms, registers, or documents where applicable)

STRIKTE REGELN / STRICT RULES:
  ✗ KEINE Abschnittsüberschriften wie Zweck/Geltungsbereich/Verantwortlichkeiten
  ✗ KEINE Änderung des grundlegenden Themas oder Inhalts
  ✓ Vollständige Neuformulierung von Sätzen und Absätzen erlaubt
  ✓ Neuanordnung von Informationen für besseren Fluss erlaubt
  ✓ Der umgeschriebene Text soll spürbar länger und detaillierter sein als das Original

ZU ÜBERARBEITENDER TEXT / TEXT TO REWRITE:
\"\"\"{request.section_text}\"\"\"

═══════════════════════════════════════════════════════════════
AUSGABEFORMAT / OUTPUT FORMAT
═══════════════════════════════════════════════════════════════
Gib NUR ein gültiges JSON-Objekt zurück (kein Markdown, keine Erklärungen außerhalb):
Return ONLY a valid JSON object (no markdown, no text outside the JSON):
{{
  "rewritten_text": "Der vollständig neu formulierte, produktionsreife Text hier. / The complete production-ready rewritten text here."
}}"""


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
