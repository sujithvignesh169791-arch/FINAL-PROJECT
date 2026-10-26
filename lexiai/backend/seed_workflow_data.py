"""
LEXIAI Real-Time Workflow Data Seeder
Populates the database with real-world legal workflow matters, contracts,
structured AI analyses, risk metrics, and chat sessions.
"""

import uuid
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.analysis import DocumentAnalysis
from app.models.chat import ChatSession, ChatMessage
from app.ai.legal_analysis import generate_fallback_analysis

def seed_workflow():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("SEEDING REAL-TIME WORKFLOW DATA FOR LEXIAI")
        print("=" * 60)

        # 1. Identify or create primary counsel users
        active_users = db.query(User).filter(User.email.in_([
            "sujithvignesh169791@gmail.com",
            "counsel@lexiai.com",
            "jane.doe@lexiai.com"
        ])).all()

        user_ids = [u.id for u in active_users]
        if not user_ids:
            # Create default counsel user if not exists
            new_user = User(
                email="sujithvignesh169791@gmail.com",
                hashed_password="demo_hashed_password"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_ids.append(new_user.id)

        target_user_id = user_ids[0]
        print(f"Targeting User ID: {target_user_id}")

        # 2. Enrich all existing documents that lack structured analysis
        existing_docs = db.query(Document).filter(Document.user_id == target_user_id).all()
        print(f"Enriching {len(existing_docs)} existing documents for active user...")

        for doc in existing_docs:
            analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == doc.id).first()
            if not analysis:
                analysis = DocumentAnalysis(document_id=doc.id)
                db.add(analysis)

            # Generate structured analysis if missing
            if not analysis.summary or not analysis.clauses or not analysis.risk_score:
                text_to_analyze = analysis.extracted_text or f"Legal Document {doc.filename}. Standard commercial covenants apply."
                res = generate_fallback_analysis(text_to_analyze, doc.filename)
                
                analysis.summary = res.executive_summary
                analysis.risk_score = res.risk_score or 75.0
                analysis.clauses = [c.model_dump() for c in res.clauses]
                analysis.extracted_entities = {
                    "executive_summary": res.executive_summary,
                    "important_points": res.important_points,
                    "parties": res.parties,
                    "organizations": res.organizations,
                    "dates": res.dates,
                    "legal_acts": res.legal_acts,
                    "legal_sections": res.legal_sections,
                    "payment_terms": res.payment_terms,
                    "penalties": res.penalties,
                    "termination_conditions": res.termination_conditions,
                    "termination_terms": res.termination_conditions,
                    "liability_and_indemnity": res.liability_and_indemnity,
                    "liability_terms": res.liability_and_indemnity,
                    "confidentiality": res.confidentiality,
                    "confidentiality_terms": res.confidentiality,
                    "dispute_resolution": res.dispute_resolution,
                    "jurisdiction": res.jurisdiction,
                    "obligations": res.obligations,
                }
                analysis.processing_method = "intelligent_engine"
                doc.upload_status = "completed"
                print(f"  -> Generated complete analysis for: {doc.filename}")

        # 3. Add High-Value Commercial Matters if not already present
        sample_matters = [
            {
                "filename": "Master_Software_Services_Agreement_TechCorp.pdf",
                "file_type": "pdf",
                "risk_score": 68.0,
                "summary": "Master Services Agreement between TechCorp Global and Apex Logistics. Identifies commercial SaaS delivery, Net 30 payments, uncapped IP indemnification, and mutual 12-month trailing fee liability caps.",
                "parties": ["TechCorp Global Solutions Inc.", "Apex Logistics International Corp."],
                "dates": ["2026-10-15", "2026-11-01"],
                "clauses": [
                    {
                        "clause_type": "Liability",
                        "title": "Limitation of Liability Cap",
                        "text": "Aggregate liability shall not exceed fees paid in preceding 12 months, with carve-outs for confidentiality breaches and indemnification.",
                        "source_page": 4
                    },
                    {
                        "clause_type": "Payment",
                        "title": "Invoicing & Net 30 Terms",
                        "text": "Invoices are payable within 30 days of receipt. Late payments incur 1.0% monthly interest.",
                        "source_page": 2
                    },
                    {
                        "clause_type": "Termination",
                        "title": "Termination for Convenience",
                        "text": "Customer may terminate upon 60 days prior written notice, subject to paying completed milestones.",
                        "source_page": 3
                    }
                ],
                "entities": {
                    "parties": ["TechCorp Global Solutions Inc.", "Apex Logistics International Corp."],
                    "dates": ["October 15, 2026", "November 1, 2026"],
                    "payment_terms": ["Net 30 days upon invoice receipt"],
                    "termination_conditions": ["60 days prior written notice for convenience"],
                    "liability_and_indemnity": ["Uncapped IP indemnification obligations", "Mutual 12-month trailing fee liability cap"],
                    "jurisdiction": ["State of Delaware Courts", "American Arbitration Association New York"],
                    "obligations": ["Deliver scalable cloud infrastructure deliverables", "Timely payment of milestone billings"]
                }
            },
            {
                "filename": "Commercial_Office_Lease_Beacon_Tower.pdf",
                "file_type": "pdf",
                "risk_score": 84.0,
                "summary": "Commercial real estate lease for Suite 1400 at Beacon Tower. Establishes a 5-year tenancy, 3% annual rent escalations, standard tenant maintenance covenants, and security deposit terms.",
                "parties": ["Beacon Tower Holdings LLC (Landlord)", "Lexi Partners LLP (Tenant)"],
                "dates": ["2026-09-01", "2031-08-31"],
                "clauses": [
                    {
                        "clause_type": "Payment",
                        "title": "Base Rent & Annual Escalation",
                        "text": "Base rent of $18,500 monthly due on the 1st of each calendar month with 3% annual compounding escalation.",
                        "source_page": 2
                    },
                    {
                        "clause_type": "Termination",
                        "title": "Default & Remedy Notice",
                        "text": "Landlord may terminate lease upon 15 days written notice for monetary default if unpaid.",
                        "source_page": 6
                    }
                ],
                "entities": {
                    "parties": ["Beacon Tower Holdings LLC", "Lexi Partners LLP"],
                    "dates": ["September 1, 2026", "August 31, 2031"],
                    "payment_terms": ["$18,500 monthly due on 1st of month with 3% annual escalation"],
                    "termination_conditions": ["15 days written notice for monetary default"],
                    "liability_and_indemnity": ["Tenant indemnifies Landlord against invitee injuries on premises"],
                    "jurisdiction": ["County of New York, State of New York"],
                    "obligations": ["Maintain commercial general liability insurance of $2,000,000"]
                }
            }
        ]

        for matter in sample_matters:
            existing = db.query(Document).filter(
                Document.user_id == target_user_id,
                Document.filename == matter["filename"]
            ).first()

            if not existing:
                new_doc = Document(
                    user_id=target_user_id,
                    filename=matter["filename"],
                    file_type=matter["file_type"],
                    storage_url=f"uploads/{matter['filename']}",
                    upload_status="completed",
                    created_at=datetime.utcnow() - timedelta(days=2)
                )
                db.add(new_doc)
                db.commit()
                db.refresh(new_doc)

                analysis = DocumentAnalysis(
                    document_id=new_doc.id,
                    summary=matter["summary"],
                    risk_score=matter["risk_score"],
                    clauses=matter["clauses"],
                    extracted_entities=matter["entities"],
                    extracted_text=f"{matter['filename']}\n\n{matter['summary']}",
                    processing_method="ai_provider",
                    created_at=datetime.utcnow() - timedelta(days=2)
                )
                db.add(analysis)
                print(f"  -> Created workflow matter: {matter['filename']}")

        # 4. Seed Chat Sessions & Grounded Q&A
        chat_doc = db.query(Document).filter(Document.user_id == target_user_id).first()
        doc_ref_id = chat_doc.id if chat_doc else None

        existing_session = db.query(ChatSession).filter(ChatSession.user_id == target_user_id).first()
        if not existing_session:
            session = ChatSession(
                user_id=target_user_id,
                document_id=doc_ref_id,
                title="Contractual Liability & Risk Assessment"
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            messages = [
                ("user", "What are the primary risk provisions identified in our uploaded contracts?"),
                ("assistant", "Based on analysis of your active matters, two primary risk areas require counsel attention:\n1. TechCorp Agreement contains an uncapped IP indemnity clause in Section 6(a).\n2. Commercial Office Lease requires 15 days cure notice for default with no tenant grace period.\nOther commercial covenants adhere to standard market practices."),
                ("user", "Are there any jurisdiction or dispute resolution conflicts?"),
                ("assistant", "The TechCorp Agreement is governed by Delaware law with AAA arbitration in New York, while the Beacon Tower Lease specifies exclusive jurisdiction in New York State Supreme Court. Both clauses are enforceable and forum-aligned.")
            ]

            for role, content in messages:
                msg = ChatMessage(
                    session_id=session.id,
                    role=role,
                    content=content
                )
                db.add(msg)
            print("  -> Seeded interactive legal assistant Q&A chat session.")

        db.commit()
        print("=" * 60)
        print("REAL-TIME WORKFLOW DATA SEEDING COMPLETE!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_workflow()
