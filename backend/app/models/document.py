from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Float, Text
from sqlalchemy.sql import func
import enum

from app.db.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_hash = Column(String(64), index=True)
    s3_key = Column(String(500))
    
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    progress = Column(Float, default=0.0)
    page_count = Column(Integer, default=0)
    
    # Extracted data
    extracted_data = Column(JSON)
    schema_used = Column(JSON)
    confidence_scores = Column(JSON)
    
    # Excel export
    excel_file_key = Column(String(500))
    excel_exported_at = Column(DateTime)
    
    # Metadata
    error_message = Column(Text)
    processing_time = Column(Float)  # in seconds
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Job tracking
    job_id = Column(String(100), nullable=True, index=True)
    
    # User info (if implementing auth)
    user_id = Column(Integer, nullable=True)