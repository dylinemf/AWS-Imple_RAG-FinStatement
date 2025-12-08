from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = []


class DocumentSource(BaseModel):
    content: str
    page: int
    score: float
    metadata: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    answer: str
    sources: List[DocumentSource]
    processing_time: float


class DocumentInfo(BaseModel):
    filename: str
    upload_date: datetime
    chunks_count: int
    status: str


class DocumentsResponse(BaseModel):
    documents: List[DocumentInfo]


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_count: int
    processing_time: float


class ChunkInfo(BaseModel):
    id: str
    content: str
    page: int
    metadata: Dict[str, Any]


class ChunksResponse(BaseModel):
    chunks: List[ChunkInfo]
    total_count: int 