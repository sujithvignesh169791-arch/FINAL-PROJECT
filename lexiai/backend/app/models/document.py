from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.db.base import Base
from app.models.user import generate_uuid

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    filename = Column(String)
    file_type = Column(String)
    storage_url = Column(String)
    upload_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
