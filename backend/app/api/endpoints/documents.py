import os
import hashlib
import asyncio
import io
import logging
import traceback
from typing import List, Optional
from datetime import datetime
import time

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import aiofiles
from typing import Dict, Any

from app.db.database import get_db
from app.models.document import Document, ProcessingStatus
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    ProcessingStatusResponse,
    DocumentProcessRequest
)
from app.services.document_processor import DocumentProcessor
from app.services.excel_exporter import ExcelExporter
from app.services.s3_service import S3Service
from app.core.config import settings
from app.utils.background_tasks import enqueue_document_processing, get_job_status

# Configure comprehensive logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Upload a PDF document for processing

    Args:
        file: PDF file to upload (max 100MB)
        db: Database session
        request: FastAPI request object for logging

    Returns:
        DocumentResponse: Created document metadata

    Raises:
        HTTPException: 400 for invalid files, 500 for server errors
    """
    # Start timing and logging
    start_time = time.time()
    client_ip = request.client.host if request else "unknown"

    logger.info(f"📤 UPLOAD_START: File='{file.filename}', Size={file.size}B, Client={client_ip}")

    try:
        # Input validation with detailed logging
        if not file.filename:
            logger.warning(f"❌ UPLOAD_FAILED: No filename provided, Client={client_ip}")
            raise HTTPException(status_code=400, detail="Filename is required")

        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"❌ UPLOAD_FAILED: Invalid file type '{file.filename}', Client={client_ip}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Check file size with logging
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            logger.warning(f"❌ UPLOAD_FAILED: File too large {file.size}B > {settings.MAX_UPLOAD_SIZE}B, Client={client_ip}")
            raise HTTPException(status_code=400, detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE} bytes")

        # Generate unique filename with collision detection
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file_hash}.pdf"

        logger.info(f"📝 UPLOAD_PROCESSING: Generated filename='{unique_filename}', Hash={file_hash[:8]}...")

        # Ensure upload directory exists with error handling
        try:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            logger.debug(f"📁 UPLOAD_DIR: Ensured directory exists: {settings.UPLOAD_DIR}")
        except OSError as e:
            logger.error(f"❌ UPLOAD_FAILED: Cannot create upload directory: {e}")
            raise HTTPException(status_code=500, detail="Upload directory unavailable")

        # Save file locally with progress logging
        local_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        try:
            async with aiofiles.open(local_path, 'wb') as f:
                content = await file.read()
                if not content:
                    logger.warning(f"❌ UPLOAD_FAILED: Empty file content, Client={client_ip}")
                    raise HTTPException(status_code=400, detail="File appears to be empty")

                await f.write(content)
                logger.info(f"💾 FILE_SAVED: Local path='{local_path}', Size={len(content)}B")

        except Exception as e:
            logger.error(f"❌ UPLOAD_FAILED: File save error: {e}, Client={client_ip}")
            # Cleanup partial file
            if os.path.exists(local_path):
                os.remove(local_path)
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

        # Create database record with transaction safety
        try:
            document = Document(
                filename=unique_filename,
                original_filename=file.filename,
                file_size=len(content) if 'content' in locals() else file.size,
                file_hash=file_hash,
                status=ProcessingStatus.PENDING
            )

            db.add(document)
            db.commit()
            db.refresh(document)

            logger.info(f"💾 DB_CREATED: Document ID={document.id}, Status={document.status}")

        except SQLAlchemyError as e:
            logger.error(f"❌ DB_ERROR: Failed to create document record: {e}")
            db.rollback()
            # Cleanup uploaded file
            if os.path.exists(local_path):
                os.remove(local_path)
            raise HTTPException(status_code=500, detail="Database error during upload")

        # Upload to S3 if configured (non-blocking)
        if settings.AWS_ACCESS_KEY_ID:
            try:
                logger.info(f"☁️  S3_UPLOAD_START: Document ID={document.id}")
                s3_service = S3Service()
                s3_key = f"uploads/{unique_filename}"
                await s3_service.upload_file(local_path, s3_key)

                # Update document with S3 key
                document.s3_key = s3_key
                db.commit()

                logger.info(f"☁️  S3_UPLOAD_SUCCESS: Key='{s3_key}', Document ID={document.id}")

            except Exception as e:
                # Log S3 error but don't fail the upload
                logger.warning(f"⚠️  S3_UPLOAD_FAILED: {e}, Document ID={document.id} (continuing without S3)")

        # Success logging with timing
        elapsed_time = time.time() - start_time
        logger.info(f"✅ UPLOAD_SUCCESS: Document ID={document.id}, Time={elapsed_time:.2f}s, Client={client_ip}")

        return DocumentResponse.from_orm(document)

    except HTTPException:
        # Re-raise HTTP exceptions (already logged)
        raise
    except Exception as e:
        # Log unexpected errors with full traceback
        elapsed_time = time.time() - start_time
        logger.error(f"❌ UPLOAD_ERROR: Unexpected error after {elapsed_time:.2f}s: {e}")
        logger.error(f"🔍 UPLOAD_TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")

@router.post("/process/{document_id}", response_model=Dict[str, Any])
async def process_document(
    document_id: int,
    request: DocumentProcessRequest = None,
    db: Session = Depends(get_db),
    http_request: Request = None
):
    """
    Start processing a document using background queue

    Args:
        document_id: ID of the document to process
        request: Processing options (schema, template_mode, priority)
        db: Database session
        http_request: FastAPI request object for logging

    Returns:
        Dict containing job_id, document_id, status, and message

    Raises:
        HTTPException: 404 if document not found, 500 for processing errors
    """
    start_time = time.time()
    client_ip = http_request.client.host if http_request else "unknown"

    logger.info(f"⚡ PROCESS_START: Document ID={document_id}, Client={client_ip}")

    try:
        # Validate document exists with detailed logging
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.warning(f"❌ PROCESS_FAILED: Document ID={document_id} not found, Client={client_ip}")
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info(f"📄 DOCUMENT_FOUND: ID={document_id}, Status={document.status}, File='{document.original_filename}'")

        # Validate file exists on disk
        if document.filename:
            local_path = os.path.join(settings.UPLOAD_DIR, document.filename)
            if not os.path.exists(local_path):
                logger.error(f"❌ FILE_MISSING: Document ID={document_id}, Path='{local_path}'")
                # Update document status to failed
                document.status = ProcessingStatus.FAILED
                document.error_message = "Source file not found"
                db.commit()
                raise HTTPException(status_code=400, detail="Document file not found on server")

        # Check if document is already being processed
        if document.status == ProcessingStatus.PROCESSING:
            logger.info(f"⏳ ALREADY_PROCESSING: Document ID={document_id}, Progress={document.progress}")
            return JSONResponse(
                status_code=200,
                content={
                    "document_id": document_id,
                    "status": document.status.value,
                    "progress": document.progress,
                    "job_id": document.job_id,
                    "message": "Document is already being processed"
                }
            )

        # Check if document is already completed
        if document.status == ProcessingStatus.COMPLETED:
            logger.info(f"✅ ALREADY_COMPLETED: Document ID={document_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "document_id": document_id,
                    "status": document.status.value,
                    "progress": document.progress,
                    "message": "Document processing already completed"
                }
            )

        # Log processing options
        schema = request.schema if request else None
        template_mode = request.template_mode if request else False
        priority = request.priority if request else "normal"

        logger.info(f"⚙️  PROCESS_OPTIONS: Schema={bool(schema)}, Template={template_mode}, Priority={priority}")

        try:
            # Enqueue the processing task with error handling
            logger.info(f"📋 QUEUE_START: Enqueueing document ID={document_id}")

            job_id = enqueue_document_processing(
                document_id=document_id,
                schema=schema
            )

            logger.info(f"📋 QUEUE_SUCCESS: Job ID='{job_id}' for document ID={document_id}")

        except Exception as e:
            logger.error(f"❌ QUEUE_FAILED: Error enqueueing document ID={document_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to queue document processing: {str(e)}")

        # Update document status with transaction safety
        try:
            document.status = ProcessingStatus.PROCESSING
            document.progress = 0.0
            document.job_id = job_id
            document.error_message = None  # Clear any previous errors
            db.commit()

            logger.info(f"💾 STATUS_UPDATED: Document ID={document_id}, Status={document.status}, Job='{job_id}'")

        except SQLAlchemyError as e:
            logger.error(f"❌ DB_UPDATE_FAILED: Document ID={document_id}, Error: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update document status")

        # Success response with comprehensive info
        elapsed_time = time.time() - start_time
        response_data = {
            "job_id": job_id,
            "document_id": document_id,
            "status": "queued",
            "message": "Document processing queued successfully",
            "processing_options": {
                "template_mode": template_mode,
                "has_schema": bool(schema),
                "priority": priority
            },
            "estimated_time": "30-60 seconds"  # Rough estimate
        }

        logger.info(f"✅ PROCESS_QUEUED: Document ID={document_id}, Job='{job_id}', Time={elapsed_time:.2f}s")

        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions (already logged)
        raise
    except Exception as e:
        # Handle unexpected errors with full logging
        elapsed_time = time.time() - start_time
        logger.error(f"❌ PROCESS_ERROR: Document ID={document_id}, Time={elapsed_time:.2f}s, Error: {e}")
        logger.error(f"🔍 PROCESS_TRACEBACK: {traceback.format_exc()}")

        # Attempt to mark document as failed
        try:
            if 'document' in locals() and document:
                document.status = ProcessingStatus.FAILED
                document.error_message = f"Process initialization failed: {str(e)}"
                db.commit()
                logger.info(f"🔄 STATUS_RECOVERY: Marked document ID={document_id} as failed")
        except Exception as recovery_error:
            logger.error(f"❌ RECOVERY_FAILED: Could not update document status: {recovery_error}")
            db.rollback()

        raise HTTPException(status_code=500, detail="Internal error during process initialization")

@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status_endpoint(job_id: str):
    """Get the status of a background job"""
    return get_job_status(job_id)

@router.get("/template/download/excel")
async def download_template_excel(
    document_ids: List[int] = Query(..., description="List of document IDs"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Download template Excel with unified columns from multiple documents

    Args:
        document_ids: List of document IDs to include in template
        db: Database session
        request: FastAPI request object for logging

    Returns:
        StreamingResponse: Excel file with template format

    Raises:
        HTTPException: 404 if no documents found, 400 if no data available
    """
    start_time = time.time()
    client_ip = request.client.host if request else "unknown"

    logger.info(f"📊 TEMPLATE_START: Documents={document_ids}, Count={len(document_ids)}, Client={client_ip}")

    try:
        # Validate input parameters
        if not document_ids:
            logger.warning(f"❌ TEMPLATE_FAILED: No document IDs provided, Client={client_ip}")
            raise HTTPException(status_code=400, detail="At least one document ID is required")

        if len(document_ids) > 100:  # Reasonable limit
            logger.warning(f"❌ TEMPLATE_FAILED: Too many documents {len(document_ids)}, Client={client_ip}")
            raise HTTPException(status_code=400, detail="Maximum 100 documents allowed per template")

        logger.info(f"🔍 DB_QUERY: Searching for {len(document_ids)} completed documents")

        # Query documents with detailed logging
        try:
            documents = db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.status == ProcessingStatus.COMPLETED
            ).all()

            found_ids = [doc.id for doc in documents]
            missing_ids = [doc_id for doc_id in document_ids if doc_id not in found_ids]

            logger.info(f"📄 DOCUMENTS_FOUND: Found={len(documents)}, Missing={len(missing_ids)}")

            if missing_ids:
                logger.warning(f"⚠️  MISSING_DOCS: IDs={missing_ids}")

        except SQLAlchemyError as e:
            logger.error(f"❌ DB_QUERY_FAILED: Error querying documents: {e}")
            raise HTTPException(status_code=500, detail="Database error while retrieving documents")

        if not documents:
            logger.warning(f"❌ TEMPLATE_FAILED: No completed documents found for IDs={document_ids}")
            raise HTTPException(status_code=404, detail="No completed documents found")

        # Collect and analyze extracted data
        all_field_names = set()
        template_data = []
        docs_with_data = 0
        docs_without_data = 0

        logger.info(f"🔄 DATA_EXTRACTION: Processing {len(documents)} documents")

        for doc in documents:
            if doc.extracted_data:
                docs_with_data += 1
                logger.debug(f"📊 PROCESSING_DOC: ID={doc.id}, Fields={len(doc.extracted_data)}")

                # Extract field names from the document (skip metadata fields)
                doc_fields = [key for key in doc.extracted_data.keys() if not key.startswith('_')]
                all_field_names.update(doc_fields)

                # Create row with document data
                row_data = {'_source_document': doc.original_filename}
                for field in doc.extracted_data:
                    if not field.startswith('_'):
                        # Clean and validate field data
                        value = doc.extracted_data[field]
                        if isinstance(value, (dict, list)):
                            value = str(value)  # Convert complex types to string
                        row_data[field] = value

                template_data.append(row_data)
            else:
                docs_without_data += 1
                logger.warning(f"⚠️  NO_DATA: Document ID={doc.id} has no extracted data")

        logger.info(f"📊 DATA_SUMMARY: WithData={docs_with_data}, WithoutData={docs_without_data}, Fields={len(all_field_names)}")

        if not template_data:
            logger.warning(f"❌ TEMPLATE_FAILED: No extracted data available for template")
            raise HTTPException(status_code=400, detail="No extracted data available for template")

        if not all_field_names:
            logger.warning(f"❌ TEMPLATE_FAILED: No field names found in extracted data")
            raise HTTPException(status_code=400, detail="No field names found in documents")

        # Export to Excel with comprehensive error handling
        try:
            logger.info(f"📊 EXCEL_EXPORT_START: Rows={len(template_data)}, Columns={len(all_field_names)}")

            exporter = ExcelExporter()
            excel_data = await exporter.export_template(template_data, sorted(all_field_names))

            if not excel_data:
                logger.error(f"❌ EXCEL_EXPORT_FAILED: Empty Excel data returned")
                raise HTTPException(status_code=500, detail="Failed to generate Excel file")

            logger.info(f"✅ EXCEL_EXPORT_SUCCESS: Size={len(excel_data)}B")

        except Exception as e:
            logger.error(f"❌ EXCEL_EXPORT_ERROR: {e}")
            logger.error(f"🔍 EXCEL_TRACEBACK: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

        # Generate filename with timestamp and metadata
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"template_export_{timestamp}_{len(documents)}docs_{len(all_field_names)}fields.xlsx"

        # Success logging with comprehensive metrics
        elapsed_time = time.time() - start_time
        logger.info(f"✅ TEMPLATE_SUCCESS: File='{filename}', Time={elapsed_time:.2f}s, Size={len(excel_data)}B")
        logger.info(f"📊 TEMPLATE_METRICS: Documents={len(documents)}, Fields={len(all_field_names)}, Rows={len(template_data)}")

        # Return Excel file as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Document-Count": str(len(documents)),
                "X-Field-Count": str(len(all_field_names)),
                "X-Generation-Time": f"{elapsed_time:.2f}s"
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions (already logged)
        raise
    except Exception as e:
        # Handle unexpected errors with full logging
        elapsed_time = time.time() - start_time
        logger.error(f"❌ TEMPLATE_ERROR: Unexpected error after {elapsed_time:.2f}s: {e}")
        logger.error(f"🔍 TEMPLATE_TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal error during template generation")

@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get the processing status of a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return ProcessingStatusResponse(
        document_id=document.id,
        status=document.status,
        progress=document.progress,
        error_message=document.error_message,
        page_count=document.page_count,
        processing_time=document.processing_time,
        extracted_data=document.extracted_data
    )

@router.get("/{document_id}/download/excel")
async def download_excel(
    document_id: int,
    include_metadata: bool = Query(True, description="Include metadata sheet"),
    db: Session = Depends(get_db)
):
    """Download extracted data as Excel file"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    if not document.extracted_data:
        raise HTTPException(status_code=400, detail="No data available for export")
    
    # Export to Excel
    exporter = ExcelExporter()
    excel_data = await exporter.export_to_excel(
        [document.extracted_data],
        include_metadata=include_metadata
    )
    
    # Update export timestamp
    document.excel_exported_at = datetime.utcnow()
    db.commit()
    
    # Return file
    filename = f"{document.original_filename.replace('.pdf', '')}_extracted.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[ProcessingStatus] = None,
    db: Session = Depends(get_db)
):
    """List all documents with pagination"""
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status)
    
    total = query.count()
    documents = query.offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        skip=skip,
        limit=limit
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document and its associated files"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete local file
    local_path = os.path.join(settings.UPLOAD_DIR, document.filename)
    if os.path.exists(local_path):
        os.remove(local_path)
    
    # Delete from S3
    if document.s3_key and settings.AWS_ACCESS_KEY_ID:
        s3_service = S3Service()
        await s3_service.delete_file(document.s3_key)
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@router.post("/batch-process", response_model=Dict[str, Any])
async def batch_process_documents(
    document_ids: List[int],
    schema: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Process multiple documents in batch using RQ"""
    if not document_ids:
        raise HTTPException(status_code=400, detail="No document IDs provided")
    
    # Get documents
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    if len(documents) != len(document_ids):
        found_ids = {doc.id for doc in documents}
        not_found = [doc_id for doc_id in document_ids if doc_id not in found_ids]
        raise HTTPException(status_code=404, detail=f"Documents not found: {not_found}")
    
    job_ids = []
    
    # Start processing each document
    for doc in documents:
        if doc.status != ProcessingStatus.PROCESSING:
            try:
                job_id = enqueue_document_processing(
                    document_id=doc.id,
                    schema=schema
                )
                doc.status = ProcessingStatus.PROCESSING
                doc.progress = 0.0
                doc.job_id = job_id
                job_ids.append(job_id)
            except Exception as e:
                logger.error(f"Failed to enqueue document {doc.id}: {str(e)}")
    
    db.commit()
    
    return {
        "status": "queued",
        "message": f"Queued {len(job_ids)} documents for processing",
        "job_ids": job_ids,
        "document_ids": [doc.id for doc in documents if doc.status == ProcessingStatus.PROCESSING]
    }

@router.get("/batch/download/excel")
async def batch_download_excel(
    document_ids: List[int] = Query(..., description="List of document IDs"),
    db: Session = Depends(get_db)
):
    """Download multiple documents as a single Excel file"""
    documents = db.query(Document).filter(
        Document.id.in_(document_ids),
        Document.status == ProcessingStatus.COMPLETED
    ).all()

    if not documents:
        raise HTTPException(status_code=404, detail="No completed documents found")

    # Collect all extracted data
    all_data = []
    for doc in documents:
        if doc.extracted_data:
            data = doc.extracted_data.copy()
            data['_source_document'] = doc.original_filename
            all_data.append(data)

    if not all_data:
        raise HTTPException(status_code=400, detail="No data available for export")

    # Export to Excel
    exporter = ExcelExporter()
    excel_data = await exporter.export_batch(all_data)

    # Return file
    filename = f"batch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

