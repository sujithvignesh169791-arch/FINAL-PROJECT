from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Text
from app.db.base import Base
from app.models.user import generate_uuid

class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    summary = Column(String)
    risk_score = Column(Float)
    extracted_entities = Column(JSON)
    clauses = Column(JSON)
    extracted_text = Column(Text)
    page_text = Column(JSON)
    processing_method = Column(String)
    processing_error = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
