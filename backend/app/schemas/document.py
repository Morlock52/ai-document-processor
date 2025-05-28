from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.document import ProcessingStatus

class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: Optional[int] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    status: ProcessingStatus
    progress: float = 0.0
    page_count: int = 0
    s3_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentProcessRequest(BaseModel):
    schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional schema for data extraction"
    )
    template_mode: Optional[bool] = Field(
        False,
        description="Enable template mode for unified data extraction"
    )
    priority: Optional[str] = Field(
        "normal",
        description="Processing priority: low, normal, high"
    )

class ProcessingStatusResponse(BaseModel):
    document_id: int
    status: ProcessingStatus
    progress: float
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    processing_time: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]
    skip: int
    limit: int

class ExtractionSchema(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Dict[str, Dict[str, Any]]
    required_fields: List[str] = []
    
class SchemaDetectionRequest(BaseModel):
    sample_image_base64: str
    description: Optional[str] = None

class SchemaDetectionResponse(BaseModel):
    detected_type: str
    confidence: float
    suggested_schema: ExtractionSchema
    sample_extraction: Dict[str, Any]