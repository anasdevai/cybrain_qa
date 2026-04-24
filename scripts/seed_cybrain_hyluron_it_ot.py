#!/usr/bin/env python3
r"""
Liest das Cybrain IT/OT-Referenzdataset (Hyloronsäure, deutsch) in PostgreSQL (server_db) ein.

Verwendet dieselben Regeln wie der Cybrain-Backend-Stack:
- tenant_id 11111111-1111-1111-1111-111111111111
- sops + sop_versions (TipTap content_json, metadata_json)
- deviations, capas, audit_findings, decisions
- manuelle Verknüpfungen: sop_deviation, deviation_capa, capa_audit, audit_decision, decision_sop
- source_system = "cybrain_hyluron_sops_it_ot_2024" für idempotentes Löschen

Nutzung (Repo-Root = cybrain_qa):
  set PYTHONPATH=backend
  python scripts/seed_cybrain_hyluron_it_ot.py

Nach dem Insert: semantische Neuindexierung anstoßen, damit BGE-M3 + Qdrant die neuen
Chunks erhalten, z. B. POST /api/semantic/reindex (full) oder den Embedding-Worker laufen lassen.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Backend-Packages
HERE = Path(__file__).resolve().parent
CYBRAIN_QA = HERE.parent
BACKEND = CYBRAIN_QA / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DOTENV", str(CYBRAIN_QA / ".env"))
# database.py lädt .env aus backend/../  (= cybrain_qa/.env)
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AuditFinding,
    AuditDecisionLink,
    Capa,
    CapaAuditLink,
    Decision,
    DecisionSopLink,
    Deviation,
    DeviationCapaLink,
    AILinkSuggestion,
    EmbeddingJob,
    KnowledgeChunk,
    SOP,
    SOPVersion,
    SopDeviationLink,
)

from cybrain_it_ot_sop_bodies_de import (  # noqa: E402
    SOP_S001,
    SOP_S002,
    SOP_S003,
    SOP_S004,
    SOP_S005,
)

TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SRC = "cybrain_hyluron_sops_it_ot_2024"


def U(s: str) -> uuid.UUID:
    return uuid.uuid5(NS, s)


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s + "T12:00:00")


def tiptap(sop_num: str, display_title: str, body: str) -> dict:
    head = f"{sop_num} {display_title}"
    return {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": head}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": body.strip()}],
            },
        ],
    }


def ver_meta(
    version_label: str,
    sop_num: str,
    title: str,
    status: str,
    dept: str,
    risk: str,
) -> dict:
    return {
        "sopStatus": status,
        "variables": {},
        "approvedBy": "QP",
        "auditTrail": [],
        "versionNote": f"Gültige Version laut SOP-Register ({version_label}).",
        "sopMetadata": {
            "title": title,
            "author": "Dokumentation/QA",
            "reviewer": "IT/QA",
            "riskLevel": risk,
            "department": dept,
            "documentId": sop_num,
            "references": [sop_num, "SOP-IT-001", "SOP-IT-002", "GMP-Annex-11", "ISO-27001"],
            "reviewDate": "2024-10-15",
            "effectiveDate": "2024-01-01",
            "regulatoryReferences": ["EudraGMP", "FDA 21 CFR Part 11 (Referenz)"],
        },
    }


SOP_LIST = [
    {
        "num": "SOP-IT-001",
        "title": "Zugriffsmanagement auf Produktionsnetzwerk (OT)",
        "ver": "3.1",
        "vstat": "effective",
        "dept": "IT/Produktion/QA",
        "risk": "Hoch",
        "body": SOP_S001,
    },
    {
        "num": "SOP-IT-002",
        "title": "Netzwerksicherheit & Firewall (OT/IT-Trennung)",
        "ver": "2.2",
        "vstat": "effective",
        "dept": "IT/OT",
        "risk": "Hoch",
        "body": SOP_S002,
    },
    {
        "num": "SOP-IT-003",
        "title": "Notfallzugriff (Break-Glass-Verfahren)",
        "ver": "1.4",
        "vstat": "effective",
        "dept": "IT/QA/Produktion",
        "risk": "Hoch",
        "body": SOP_S003,
    },
    {
        "num": "SOP-IT-004",
        "title": "KI-Systeme in der Produktion (Predictive Maintenance, Prozessoptimierung)",
        "ver": "1.0",
        "vstat": "under_review",  # in Freigabe; Editor/Semantik wie Backend
        "dept": "IT/Data Science/QA",
        "risk": "Kritisch",
        "body": SOP_S004,
    },
    {
        "num": "SOP-IT-005",
        "title": "Patch-Management für Produktionssysteme",
        "ver": "2.0",
        "vstat": "effective",
        "dept": "IT/OT",
        "risk": "Hoch",
        "body": SOP_S005,
    },
]

# 45 Abweichungen: vollständige sops_data + Ergänzung 026-030, 037-040 (Fach Thema SOP-003/004)
# Tuple: (nr, title, event_date, sop, description, root_cause, ext_status, impact, category, site)
DEV: list[tuple] = [
    (1, "Externer Dienstleister ohne Anmeldung", "2024-05-15", "SOP-IT-001",
     "Siemens-Techniker remote auf SPS zugegriffen ohne 24h-Vorlauf; Verstoß gegen SOP-IT-001 Ablauf 4.2.",
     "Nicht voll integriertes Ticket-/Buchungssystem für Dienstleister, manuelle Rückfälle möglich.",
     "closed", "major", "IT/OT Sicherheit", "Werk-01"),
    (2, "Standardpasswort auf Abfüllmaschine", "2024-07-20", "SOP-IT-001",
     "Konto „admin/admin“ auf ABF-01 (Abfülllinie) stand noch nach 6 Monaten im Betrieb.",
     "Fehlende Härtung bei der Abnahme; fehlendes Durchsetzungs-Workflow-Feld in der Maschinen-Checkliste.",
     "closed", "major", "IT/OT Sicherheit", "Werk-01"),
    (3, "Fehlende 2FA bei VPN-Zugang", "2024-08-10", "SOP-IT-001",
     "Externer Dienstleistern account: nur Passwort, 2FA-Vorgabe technisch umgänglich.",
     "Dienstleister-Policy nicht in VPN-Gateway erzwungen; Mangel bei Token-Zwang.",
     "open", "major", "IT/OT Sicherheit", "Werk-01"),
    (4, "Zugriffslog nicht vollständig", "2024-06-12", "SOP-IT-001",
     "3 Tage ohne Log-Eintrag (05.–07.06.2024) im zentralen IAM-Audit-Trail (Graylog-Cluster).",
     "Backup-Volume belegt, Rotation nicht getriggert; kein vollwertiger Lücken-Alarm in QA-Monitoring.",
     "closed", "major", "IT/OT Sicherheit", "Werk-01"),
    (5, "Operator mit Admin-Rechten", "2024-04-03", "SOP-IT-001",
     "Fermenter-Steuerung: Operatorkonto „maier_p“ wies versehentlich AD-Gruppe admin_ot zu.",
     "Fehler in Rollen-Template, zu breite AD-Gruppen, kein wöchentliches Soll-Ist-Review (CAPA-005).",
     "closed", "major", "IT/OT Sicherheit", "Werk-01"),
    (6, "Dienstleister-Vertraulichkeitserklärung fehlt", "2024-09-15", "SOP-IT-001",
     "Firmen-NetSecure am Switch ohne unterzeichnete CDA, Arbeit an OT-Zelle gestartet.",
     "Erfassung nur per E-Mail-Verteiler, HR-Workflow unvollständig; Dienstleistermandat nicht in ERP.",
     "open", "major", "IT/OT Sicherheit", "Werk-01"),
    (7, "Zugriff außerhalb Arbeitszeit", "2024-10-01", "SOP-IT-001",
     "Vendor-Session 22:30, erlaubt 06:00–20:00, SCADA-Read auf Chromatograph.",
     "Policy nur organisatorisch vereinbart, im IAM nicht als Zeitfenster erzwungen.",
     "in_review", "major", "IT/OT Sicherheit", "Werk-01"),
    (8, "Service-Account ohne Zertifikat", "2024-03-18", "SOP-IT-001",
     "CHROM-01: Service-Account lief mit Passwort statt X.509 gemäß 4.3/4.1.",
     "Initialkonfiguration durch Dienstleister, Übergabedokument lückenhaft.",
     "closed", "major", "IT/OT Sicherheit", "Werk-01"),
    (9, "Kein Log bei Read-only-Zugriff", "2024-11-01", "SOP-IT-001",
     "SCADA Read-only für Produktionsleitung nicht in WinCC-Archive geschrieben.",
     "Fehlende Häkchen „protokolliere Operator-Sichten“ in WinCC-Projektbibliothek.",
     "open", "major", "IT/OT Sicherheit", "Werk-01"),
    (10, "Vier-Augen-Prinzip umgangen", "2024-02-14", "SOP-IT-001",
     "Admin-Change am OT-Firewall-Regelwerk (Firmware) wurde nur IT-seitig, nicht paritätisch durch QP gegengezeichnet.",
     "Doppel-Approval technisch im Change-Request nicht erzwungen; reine IT-Freigabe ausreichend konfiguriert.",
     "closed", "major", "IT/OT Sicherheit", "Werk-01"),
]

from cybrain_hyluron_seed_rows import (  # noqa: E402
    AUDIT_ROWS,
    CAPA_ROWS,
    DECISION_ROWS,
    DEV_11_45,
)
from sqlalchemy import or_  # noqa: E402

DEV_ALL: list[tuple] = DEV + DEV_11_45
assert len(DEV_ALL) == 45, len(DEV_ALL)
assert len(CAPA_ROWS) == 45, len(CAPA_ROWS)
assert len(AUDIT_ROWS) == 20, len(AUDIT_ROWS)
assert len(DECISION_ROWS) == 15, len(DECISION_ROWS)


def _sop_id(num: str) -> uuid.UUID:
    return U(f"sop/{num}")


def _sop_version_id(num: str, ver: str) -> uuid.UUID:
    return U(f"ver/{num}/{ver}")


def _dev_id(n: int) -> uuid.UUID:
    return U(f"dev/DEV-IT-{n:03d}")


def _capa_id(n: int) -> uuid.UUID:
    return U(f"capa/CAPA-IT-{n:03d}")


def _aud_id(n: int) -> uuid.UUID:
    return U(f"aud/AUD-IT-{n:03d}")


def _dec_id(n: int) -> uuid.UUID:
    return U(f"dec/DEC-IT-{n:03d}")


def _capa_status(label: str) -> str:
    return label.strip().lower().replace(" ", "_")


def wipe(db) -> None:
    sops = db.query(SOP).filter(SOP.source_system == SRC).all()
    s_ids = [s.id for s in sops]
    if not s_ids:
        return
    d_ids = [x[0] for x in db.query(Deviation.id).filter(Deviation.source_system == SRC).all()]
    c_ids = [x[0] for x in db.query(Capa.id).filter(Capa.source_system == SRC).all()]
    a_ids = [x[0] for x in db.query(AuditFinding.id).filter(AuditFinding.source_system == SRC).all()]
    dec_ids = [x[0] for x in db.query(Decision.id).filter(Decision.source_system == SRC).all()]
    v_ids = [x[0] for x in db.query(SOPVersion.id).filter(SOPVersion.sop_id.in_(s_ids)).all()]

    all_e = s_ids + d_ids + c_ids + a_ids + dec_ids + v_ids
    db.query(KnowledgeChunk).filter(
        KnowledgeChunk.tenant_id == TENANT, KnowledgeChunk.entity_id.in_(all_e)
    ).delete(synchronize_session=False)
    db.query(AILinkSuggestion).filter(
        or_(
            AILinkSuggestion.source_entity_id.in_(all_e),
            AILinkSuggestion.target_entity_id.in_(all_e),
        )
    ).delete(synchronize_session=False)
    db.query(EmbeddingJob).filter(EmbeddingJob.entity_id.in_(all_e)).delete(synchronize_session=False)

    db.query(AuditDecisionLink).filter(
        AuditDecisionLink.tenant_id == TENANT,
        or_(AuditDecisionLink.audit_finding_id.in_(a_ids), AuditDecisionLink.decision_id.in_(dec_ids)),
    ).delete(synchronize_session=False)
    db.query(CapaAuditLink).filter(
        CapaAuditLink.tenant_id == TENANT,
        or_(CapaAuditLink.capa_id.in_(c_ids), CapaAuditLink.audit_finding_id.in_(a_ids)),
    ).delete(synchronize_session=False)
    db.query(DecisionSopLink).filter(
        DecisionSopLink.tenant_id == TENANT,
        or_(DecisionSopLink.sop_id.in_(s_ids), DecisionSopLink.decision_id.in_(dec_ids)),
    ).delete(synchronize_session=False)
    db.query(DeviationCapaLink).filter(
        DeviationCapaLink.tenant_id == TENANT,
        or_(
            DeviationCapaLink.deviation_id.in_(d_ids),
            DeviationCapaLink.capa_id.in_(c_ids),
        ),
    ).delete(synchronize_session=False)
    db.query(SopDeviationLink).filter(
        SopDeviationLink.tenant_id == TENANT,
        or_(SopDeviationLink.sop_id.in_(s_ids), SopDeviationLink.deviation_id.in_(d_ids)),
    ).delete(synchronize_session=False)

    for s in sops:
        s.current_version_id = None
    db.flush()
    db.query(SOPVersion).filter(SOPVersion.sop_id.in_(s_ids)).delete(synchronize_session=False)
    if dec_ids:
        db.query(Decision).filter(Decision.id.in_(dec_ids)).delete(synchronize_session=False)
    if a_ids:
        db.query(AuditFinding).filter(AuditFinding.id.in_(a_ids)).delete(synchronize_session=False)
    if c_ids:
        db.query(Capa).filter(Capa.id.in_(c_ids)).delete(synchronize_session=False)
    if d_ids:
        db.query(Deviation).filter(Deviation.id.in_(d_ids)).delete(synchronize_session=False)
    if s_ids:
        db.query(SOP).filter(SOP.id.in_(s_ids)).delete(synchronize_session=False)
    db.commit()


def run_seed() -> None:
    db = SessionLocal()
    try:
        wipe(db)
        # SOPs + Versionen
        for spec in SOP_LIST:
            num = spec["num"]
            ver_id = _sop_version_id(num, spec["ver"])
            meta_v = "under_review" if spec.get("vstat") == "under_review" else "effective"
            meta = ver_meta(spec["ver"], num, spec["title"], meta_v, spec["dept"], spec["risk"])
            cj = tiptap(num, spec["title"], spec["body"])
            sop_row = SOP(
                id=_sop_id(num),
                tenant_id=TENANT,
                sop_number=num,
                title=spec["title"],
                department=spec["dept"],
                is_active=True,
                source_system=SRC,
            )
            db.add(sop_row)
            vrow = SOPVersion(
                id=ver_id,
                sop_id=_sop_id(num),
                version_number=spec["ver"],
                external_status=spec["vstat"],
                effective_date=ts("2024-01-01"),
                content_json=cj,
                metadata_json=meta,
            )
            db.add(vrow)
            db.flush()
            sop_row.current_version_id = ver_id
        # Deviations
        for t in DEV_ALL:
            n, title, d, s_num, desc, root, st, im, cat, site = t
            db.add(
                Deviation(
                    id=_dev_id(n),
                    tenant_id=TENANT,
                    deviation_number=f"DEV-IT-{n:03d}",
                    title=title,
                    event_date=ts(d),
                    category=cat,
                    site=site,
                    external_status=st,
                    description_text=desc,
                    root_cause_text=root,
                    impact_level=im,
                    source_system=SRC,
                )
            )
        # CAPAs
        for t in CAPA_ROWS:
            cnum, title, dnr, action, owner, due, stx = t
            db.add(
                Capa(
                    id=_capa_id(cnum),
                    tenant_id=TENANT,
                    capa_number=f"CAPA-IT-{cnum:03d}",
                    title=title,
                    external_status=_capa_status(stx),
                    action_type="corrective",
                    action_text=action,
                    owner_name=owner,
                    due_date=ts(due) if due else None,
                    effectiveness_text="Wirksamkeitsprüfung in QA-Abgeschlossenregister.",
                    source_system=SRC,
                )
            )
        # Audits
        for t in AUDIT_ROWS:
            an, name, ad, find, cpn, sev, acc = t
            ar = f"AUD-IT-{an:03d}"
            db.add(
                AuditFinding(
                    id=_aud_id(an),
                    tenant_id=TENANT,
                    audit_number=ar,
                    finding_number=ar,
                    authority="Intern/Extern",
                    site="Hauptstandort",
                    audit_date=ts(ad),
                    question_text="Audit-Checkliste: Einhaltung referenzierter SOPs, CAPA-Verknüpfung, Nachweis.",
                    finding_text=find,
                    response_text=f"CAPA-IT-{cpn:03d} verknüpft; Befund: {sev}, Status: {acc}.",
                    acceptance_status=acc,
                    source_system=SRC,
                )
            )
        # Decisions
        for t in DECISION_ROWS:
            dn, title, d, au, devcap, stmt, risk, rat, s_primary = t
            ref_dev, ref_capa = devcap
            db.add(
                Decision(
                    id=_dec_id(dn),
                    tenant_id=TENANT,
                    decision_number=f"DEC-IT-{dn:03d}",
                    title=title,
                    decision_type="quality_disposition" if "Rückruf" in title or "Deaktivierung" in title else "management",
                    decision_statement=stmt,
                    decision_date=ts(d),
                    rationale_text=rat,
                    risk_assessment_text=f"Eingestuftes Restrisiko: {risk} (Bewertungsskala 4-Klassen).",
                    final_conclusion=stmt,
                    source_system=SRC,
                )
            )
        db.flush()
        # Links SOP <-> Abweichung
        n_to_s = {r[0]: r[3] for r in DEV_ALL}
        for n in range(1, 46):
            s_num = n_to_s[n]
            db.add(
                SopDeviationLink(
                    id=U(f"link/sd/{n}"),
                    tenant_id=TENANT,
                    sop_id=_sop_id(s_num),
                    deviation_id=_dev_id(n),
                    link_reason="reference_sop",
                    confidence_score=1.0,
                    rationale_text=(
                        f"Fachliche Zuordnung: DEV-IT-{n:03d} bezieht sich explizit auf {s_num} (gleiche Domäne, "
                        "Begriffe, SOP-Nummer im Befund, Vektor-Text konsistent, deutsch, QA, OT-Scope)."
                    ),
                )
            )
        # Abweichung <-> CAPA
        for t in CAPA_ROWS:
            cnum, title, dnr, action, owner, due, stx = t
            db.add(
                DeviationCapaLink(
                    id=U(f"link/dc/{cnum}"),
                    tenant_id=TENANT,
                    deviation_id=_dev_id(dnr),
                    capa_id=_capa_id(cnum),
                    link_reason="defensive_capa",
                    confidence_score=0.99,
                    rationale_text=f"CAPA-IT-{cnum:03d} behebt/überwacht DEV-IT-{dnr:03d} (Datensatz sops_data / Erweiterung), fachidentisch, gleiche Begrifflichkeit, gleiche SOP-Referenzen, keine fachfremden Domänen (deutsch, QA, OT).",
                )
            )
        # CAPA <-> Audit
        for t in AUDIT_ROWS:
            an, name, ad, find, cpn, sev, acc = t
            db.add(
                CapaAuditLink(
                    id=U(f"link/ca/{an}"),
                    tenant_id=TENANT,
                    capa_id=_capa_id(cpn),
                    audit_finding_id=_aud_id(an),
                    link_reason="audit_cites_capa",
                    confidence_score=0.98,
                    rationale_text="Audit nennt CAPA-Nummer explizit; fachlogisch nachvollziehbar für BGE, semantische Übereinstimmung Titel/Befund/CAPA.",
                )
            )
        # Audit <-> Entscheidung
        for t in DECISION_ROWS:
            dn, title, d, au, devcap, stmt, risk, rat, s_primary = t
            db.add(
                AuditDecisionLink(
                    id=U(f"link/ad/{dn}"),
                    tenant_id=TENANT,
                    audit_finding_id=_aud_id(au),
                    decision_id=_dec_id(dn),
                    link_reason="compliance_finding_to_disposition",
                    confidence_score=0.97,
                    rationale_text="Managemententscheidung in direkter Antwortlinie auf Audit- oder Befundlage; gleiche CAPA-Referenzen, gleiche fachliche Domäne.",
                )
            )
        # Entscheidung <-> SOP
        for t in DECISION_ROWS:
            dn, title, d, au, devcap, stmt, risk, rat, s_primary = t
            s_spec = next(s for s in SOP_LIST if s["num"] == s_primary)
            v_id = _sop_version_id(s_primary, s_spec["ver"])
            db.add(
                DecisionSopLink(
                    id=U(f"link/ds/{dn}"),
                    tenant_id=TENANT,
                    decision_id=_dec_id(dn),
                    sop_id=_sop_id(s_primary),
                    sop_version_id=v_id,
                    link_reason="affected_sop",
                    confidence_score=0.99,
                    rationale_text="Entscheidung knüpft an fachlich primäre SOP, gleiche Begrifflichkeit, gleiche SOP-Nummer im Begründungstext und im CAPA-Kontext, für Vektor/Semantik und UI-Zähler (deutsch, QA, OT, IT).",
                )
            )
        db.commit()
        print("OK: Cybrain Hyluron IT/OT-Seed eingespielt: 5 SOP, 45 DEV, 45 CAPA, 20 AUD, 15 DEC, alle manuellen Links (deutsch, semantik-tauglich).")
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print("FEHLER:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
