
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Main.backend.app.models import SOP, Deviation, SopDeviationLink, DeviationCapaLink, Capa, CapaAuditLink, AuditFinding, AuditDecisionLink, Decision, DecisionSopLink

# Database connection
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cybrain_qs"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def check_sop_links():
    print("Checking SOP SOP-EXT-010...")
    sop = db.query(SOP).filter(SOP.external_id == "SOP-EXT-010").first()
    if not sop:
        print("SOP-EXT-010 not found in database.")
        # Try by number
        sop = db.query(SOP).filter(SOP.sop_number == "SOP-QA-010").first()
        if not sop:
            print("SOP-QA-010 not found in database.")
            return
        else:
            print(f"Found SOP by number: {sop.sop_number}, ID: {sop.id}, External ID: {sop.external_id}")
    else:
        print(f"Found SOP: {sop.sop_number}, ID: {sop.id}, External ID: {sop.external_id}")

    # Check Deviation Links
    dev_links = db.query(SopDeviationLink).filter(SopDeviationLink.sop_id == sop.id).all()
    print(f"Number of direct Deviation links: {len(dev_links)}")
    for link in dev_links:
        dev = db.query(Deviation).filter(Deviation.id == link.deviation_id).first()
        print(f" - Linked to Deviation: {dev.deviation_number if dev else 'Unknown'}, ID: {link.deviation_id}")

    # Check Decision Links
    dec_links = db.query(DecisionSopLink).filter(DecisionSopLink.sop_id == sop.id).all()
    print(f"Number of direct Decision links: {len(dec_links)}")

    # Check CAPAs via Deviations
    dev_ids = [l.deviation_id for l in dev_links]
    if dev_ids:
        capa_links = db.query(DeviationCapaLink).filter(DeviationCapaLink.deviation_id.in_(dev_ids)).all()
        print(f"Number of CAPA links via Deviations: {len(capa_links)}")
        for link in capa_links:
            capa = db.query(Capa).filter(Capa.id == link.capa_id).first()
            print(f"   - Linked to CAPA: {capa.capa_number if capa else 'Unknown'}")

if __name__ == "__main__":
    check_sop_links()
    db.close()
