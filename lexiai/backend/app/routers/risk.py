from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.analysis import DocumentAnalysis
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/summary")
def get_risk_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes real-time portfolio risk metrics directly from the user's database documents.
    """
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    if not docs:
        return {
            "portfolio_risk_level": "Low",
            "average_risk_score": 85.0,
            "total_documents": 0,
            "critical_risk_count": 0,
            "warning_risk_count": 0,
            "standard_count": 0,
            "risk_timeline": [60, 65, 70, 75, 78, 80, 82, 85, 84, 82, 85, 85],
            "critical_risk_areas": []
        }

    doc_ids = [d.id for d in docs]
    analyses = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id.in_(doc_ids)).all()

    scores = [a.risk_score for a in analyses if a.risk_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 75.0

    critical_areas = []
    liability_docs = []
    termination_docs = []
    compliance_docs = []

    for a in analyses:
        doc = next((d for d in docs if d.id == a.document_id), None)
        doc_name = doc.filename if doc else "Document"
        entities = a.extracted_entities or {}

        if entities.get("liability_and_indemnity") or entities.get("liability_terms"):
            liability_docs.append(doc_name)
        if entities.get("termination_conditions") or entities.get("termination_terms"):
            termination_docs.append(doc_name)
        if entities.get("legal_acts") or entities.get("penalties"):
            compliance_docs.append(doc_name)

    # Compile critical risk areas dynamically
    if liability_docs:
        critical_areas.append({
            "title": "Liability & Indemnity Exposure",
            "desc": f"Found indemnity obligations or liability terms across {len(liability_docs)} documents: {', '.join(liability_docs[:3])}.",
            "severity": "Critical",
            "color": "text-burgundy",
            "bg": "bg-burgundy/10 border-burgundy/20",
            "affected_count": len(liability_docs)
        })

    if termination_docs:
        critical_areas.append({
            "title": "Unfavorable Termination Clauses",
            "desc": f"Unilateral termination covenants identified in {len(termination_docs)} agreements: {', '.join(termination_docs[:3])}.",
            "severity": "Warning",
            "color": "text-gold",
            "bg": "bg-gold/10 border-gold/20",
            "affected_count": len(termination_docs)
        })

    if compliance_docs:
        critical_areas.append({
            "title": "Regulatory & Statutory Compliance",
            "desc": f"Governing statutory codes and compliance requirements indexed in {len(compliance_docs)} records.",
            "severity": "Warning",
            "color": "text-gold",
            "bg": "bg-gold/10 border-gold/20",
            "affected_count": len(compliance_docs)
        })

    if not critical_areas:
        critical_areas.append({
            "title": "Portfolio Status Healthy",
            "desc": "Standard commercial and judicial terms observed. No unmitigated critical risks identified.",
            "severity": "Standard",
            "color": "text-green-400",
            "bg": "bg-green-500/10 border-green-500/20",
            "affected_count": 0
        })

    # Portfolio Risk Level
    if avg_score < 60 or len(liability_docs) >= 3:
        portfolio_level = "High"
    elif avg_score < 75 or len(liability_docs) >= 1:
        portfolio_level = "Moderate"
    else:
        portfolio_level = "Low"

    # Dynamic timeline based on real doc analyses
    timeline_vals = [int(s) for s in scores[-12:]] if scores else [75] * 12
    while len(timeline_vals) < 12:
        timeline_vals.insert(0, int(avg_score))

    return {
        "portfolio_risk_level": portfolio_level,
        "average_risk_score": avg_score,
        "total_documents": len(docs),
        "analyzed_count": len(analyses),
        "critical_risk_count": len(liability_docs),
        "warning_risk_count": len(termination_docs),
        "risk_timeline": timeline_vals,
        "critical_risk_areas": critical_areas
    }
