# Simplified version for testing
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import Document, ProcessingStatus
from app.schemas.document import DocumentResponse

router = APIRouter()

@router.post("/test-upload", response_model=DocumentResponse)
async def test_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Test upload endpoint"""
    # Just save the file and create DB record
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create document record
    document = Document(
        filename=file.filename,
        original_filename=file.filename,
        upload_path="/app/uploads/" + file.filename,
        status=ProcessingStatus.COMPLETED,
        progress=1.0,
        extracted_data={"test": "This is a test document", "status": "success"},
        page_count=1
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document