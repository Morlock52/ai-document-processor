import logging
import time
from typing import Optional, Dict, Any
import asyncio

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.document import Document, ProcessingStatus
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

logger = logging.getLogger(__name__)

if not settings.USE_SQLITE:
    from redis import Redis
    from rq import Queue
    from rq.job import Job
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue(connection=redis_conn)

async def process_document_task_async(document_id: int, schema: Optional[Dict[str, Any]] = None):
    """Asynchronous background task to process a document"""
    db: Session = SessionLocal()
    start_time = time.time()
    document = None
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        document.status = ProcessingStatus.PROCESSING
        document.progress = 0.1
        db.commit()

        file_path = f"{settings.UPLOAD_DIR}/{document.filename}"
        processor = DocumentProcessor()

        def progress_cb(value: float):
            document.progress = value
            db.commit()

        result = await processor.process_pdf(file_path, schema, progress_callback=progress_cb)

        if result["success"]:
            document.status = ProcessingStatus.COMPLETED
            document.progress = 1.0
            document.extracted_data = result["data"]
            document.page_count = result.get("page_count", 0)
            document.confidence_scores = result.get("confidence_scores", {})
            document.schema_used = schema
            document.processing_time = time.time() - start_time
        else:
            document.status = ProcessingStatus.FAILED
            document.error_message = result.get("error", "Unknown error occurred")
            document.progress = 0.0

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        if document:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            document.progress = 0.0
    finally:
        if document:
            db.commit()
        db.close()

def process_document_task(document_id: int, schema: Optional[Dict[str, Any]] = None):
    """Sync wrapper for the async task, for use with RQ"""
    asyncio.run(process_document_task_async(document_id, schema))

def enqueue_document_processing(
    document_id: int, schema: Optional[Dict[str, Any]] = None
) -> str:
    """Enqueue a document for processing and return the job ID"""
    if settings.USE_SQLITE:
        logger.info(f"Running task in-process for document {document_id}")
        asyncio.create_task(process_document_task_async(document_id, schema))
        return f"in_process_{document_id}"
    else:
        job = queue.enqueue(
            "app.utils.background_tasks.process_document_task",
            document_id,
            schema,
            job_timeout=3600,
        )
        return job.id


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a background job"""
    if settings.USE_SQLITE:
        # In-process tasks don't have job status, so we check the document status directly
        if job_id.startswith("in_process_"):
            document_id = int(job_id.split("_")[-1])
            db: Session = SessionLocal()
            document = db.query(Document).filter(Document.id == document_id).first()
            db.close()
            if document:
                return {
                    "id": job_id,
                    "status": document.status.value,
                    "result": document.extracted_data,
                    "error": document.error_message,
                    "created_at": document.created_at,
                    "started_at": document.updated_at,
                    "ended_at": document.updated_at if document.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED] else None,
                }
        return {"error": "Job not found for in-process mode", "status": "failed"}
    else:
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            return {
                "id": job.id,
                "status": job.get_status(),
                "result": job.result,
                "error": job.exc_info,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "ended_at": job.ended_at,
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
