from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_status: str
    file_size: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentJobResponse(BaseModel):
    job_id: str
    document_id: str
    status: str
    message: Optional[str] = None
