import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class PublicCorpusDocument(Base):
    __tablename__ = "public_corpus_documents"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    corpus_type = Column(String, index=True, nullable=False)  # "CUAD_CONTRACT" or "INDIAN_SUPREME_COURT"
    title = Column(String, index=True, nullable=False)
    source_filename = Column(String, index=True, nullable=False)
    court_or_jurisdiction = Column(String, nullable=True)
    year = Column(String, nullable=True)
    citation = Column(String, nullable=True)
    parties = Column(JSON, nullable=True)
    verdict_or_outcome = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    key_clauses = Column(JSON, nullable=True)
    extracted_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

