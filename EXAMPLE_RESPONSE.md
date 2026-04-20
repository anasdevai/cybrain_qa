# SOP RAG — Example API Response

## Request

```json
POST /rag/query
{
  "query": "What access controls exist for external vendors and what deviations occurred?",
  "status_filter": null,
  "department_filter": null
}
```

---

## Response

```json
{
  "answer": "## SOPs\nAccess to the OT network is restricted to authorised IP ranges, and admin rights require Multi-Factor Authentication (MFA) [SOP-0]. External vendors must request VPN access at least 24 hours in advance via the IT security portal [SOP-1].\n\n## Deviations\nVendor 'Siemens' accessed the PLC node without the required 24-hour advance notice by manually bypassing the VPN gate, which constitutes a Major deviation [DEV-0]. Additionally, an outdated administrator account belonging to a former employee remained active due to an offboarding sync failure between HR and IT [DEV-1].\n\n## CAPAs\nTo remediate the manual bypass, Jira was integrated with the VPN gateway to automatically enforce the 24-hour rule [CAPA-0]. Core switches were reconfigured for strict VLAN isolation via 802.1X to harden network segmentation [CAPA-1].\n\n## Decisions\nAll VPNs for external vendors were suspended until CAPA-IT-101 is validated, due to recurring major deviations in vendor access controls [DEC-0].\n",

  "language": "en",

  "sections": {
    "sops": "Access to the OT network is restricted to authorised IP ranges, and admin rights require Multi-Factor Authentication (MFA) [SOP-0]. External vendors must request VPN access at least 24 hours in advance via the IT security portal [SOP-1].",
    "deviations": "Vendor 'Siemens' accessed the PLC node without the required 24-hour advance notice by manually bypassing the VPN gate, which constitutes a Major deviation [DEV-0]. Additionally, an outdated administrator account belonging to a former employee remained active due to an offboarding sync failure between HR and IT [DEV-1].",
    "capas": "To remediate the manual bypass, Jira was integrated with the VPN gateway to automatically enforce the 24-hour rule [CAPA-0]. Core switches were reconfigured for strict VLAN isolation via 802.1X to harden network segmentation [CAPA-1].",
    "decisions": "All VPNs for external vendors were suspended until CAPA-IT-101 is validated, due to recurring major deviations in vendor access controls [DEC-0]."
  },

  "citations": [
    { "tag": "[SOP-0]",  "ref": "SOP-IT-001", "title": "Zugriffsmanagement im Produktionsnetzwerk (OT)", "chunk_id": "SOP-IT-001_chunk_1", "rerank_score": 9.41, "section": "SOPs" },
    { "tag": "[SOP-1]",  "ref": "SOP-IT-001", "title": "Zugriffsmanagement im Produktionsnetzwerk (OT)", "chunk_id": "SOP-IT-001_chunk_2", "rerank_score": 8.87, "section": "SOPs" },
    { "tag": "[DEV-0]",  "ref": "DEV-IT-001", "title": "Nicht autorisierter Fernzugriff",               "chunk_id": "DEV-IT-001_chunk_0", "rerank_score": 0.0,  "section": "Deviations" },
    { "tag": "[DEV-1]",  "ref": "DEV-IT-002", "title": "Veralteter Administrator-Account",               "chunk_id": "DEV-IT-002_chunk_0", "rerank_score": 0.0,  "section": "Deviations" },
    { "tag": "[CAPA-0]", "ref": "CAPA-IT-101","title": "Automatisierte VPN-Gate-Erzwingung",             "chunk_id": "CAPA-IT-101_chunk_0","rerank_score": 0.0,  "section": "CAPAs" },
    { "tag": "[CAPA-1]", "ref": "CAPA-IT-102","title": "Härtung der VLAN-Segmentierung",                 "chunk_id": "CAPA-IT-102_chunk_0","rerank_score": 0.0,  "section": "CAPAs" },
    { "tag": "[DEC-0]",  "ref": "DEC-2026-01","title": "VPN-Abschaltung",                                "chunk_id": "DEC-2026-01_chunk_0","rerank_score": 0.0,  "section": "Decisions" }
  ],

  "citation_check": {
    "found":        ["[CAPA-0]","[CAPA-1]","[DEC-0]","[DEV-0]","[DEV-1]","[SOP-0]","[SOP-1]"],
    "valid":        ["[CAPA-0]","[CAPA-1]","[DEC-0]","[DEV-0]","[DEV-1]","[SOP-0]","[SOP-1]"],
    "hallucinated": [],
    "clean":        true
  },

  "retrieval_stats": {
    "sop_chunks_retrieved":       5,
    "deviation_chunks_retrieved": 4,
    "capa_chunks_retrieved":      2,
    "decision_chunks_retrieved":  1,
    "retrieval_latency_ms":       847.3
  },

  "cached": false
}
```

---

## Same query in German

```json
POST /rag/query
{
  "query": "Welche Zugriffskontrollen gibt es für externe Dienstleister und welche Abweichungen sind aufgetreten?"
}
```

Response `answer` field (German sections):

```
## SOPs
Der Zugriff auf das OT-Netzwerk ist auf autorisierte IP-Bereiche beschränkt; Admin-Rechte erfordern MFA [SOP-0]. Externe Anbieter müssen den VPN-Zugriff mindestens 24 Stunden im Voraus beantragen [SOP-1].

## Abweichungen
Der Dienstleister 'Siemens' hat ohne die erforderliche 24-Stunden-Ankündigung auf den SPS-Knoten zugegriffen [DEV-0]. Anmeldedaten eines ehemaligen Mitarbeiters blieben durch einen Offboarding-Synchronisationsfehler aktiv [DEV-1].

## CAPAs
Jira wurde mit dem VPN-Gateway integriert, um die 24-Stunden-Frist automatisch durchzusetzen [CAPA-0]. Core-Switches wurden für eine strikte VLAN-Isolierung via 802.1X neu konfiguriert [CAPA-1].

## Entscheidungen
Sämtliche VPNs für externe Anbieter wurden suspendiert, bis CAPA-IT-101 validiert ist [DEC-0].
```
