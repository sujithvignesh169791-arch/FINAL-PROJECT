from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class SourceItem(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    excerpt: str
    score: Optional[float] = None

class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User legal query")
    document_id: Optional[str] = Field(default=None, description="Optional document ID to restrict search")
    session_id: Optional[str] = Field(default=None, description="Optional chat session ID for multi-turn history")

class ChatQueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    session_id: str

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    document_id: Optional[str] = None
    created_at: Optional[str] = None
    messages: List[ChatMessageResponse] = []
    model_config = ConfigDict(from_attributes=True)
