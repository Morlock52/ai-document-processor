import logging
import time
from typing import Optional, Dict, Any
import os

from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from rq.job import Job

from app.db.database import SessionLocal
from app.models.document import Document, ProcessingStatus
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue(connection=redis_conn)


def process_document_task(document_id: int, schema: Optional[Dict[str, Any]] = None):
    """Background task to process a document"""
    db: Session = SessionLocal()
    start_time = time.time()

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        # Update status
        document.status = ProcessingStatus.PROCESSING
        document.progress = 0.1
        db.commit()

        # Get file path
        file_path = f"{settings.UPLOAD_DIR}/{document.filename}"

        # Process document
        processor = DocumentProcessor()

        # Convert async function to sync for RQ
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:

            def progress_cb(value: float):
                document.progress = value
                db.add(document)
                db.commit()

            result = loop.run_until_complete(
                processor.process_pdf(file_path, schema, progress_callback=progress_cb)
            )

            if result["success"]:
                # Update document with results
                document.status = ProcessingStatus.COMPLETED
                document.progress = 1.0
                document.extracted_data = result["data"]
                document.page_count = result.get("page_count", 0)
                document.confidence_scores = result.get("confidence_scores", {})
                document.schema_used = schema
                document.processing_time = time.time() - start_time
            else:
                # Handle failure
                document.status = ProcessingStatus.FAILED
                document.error_message = result.get("error", "Unknown error occurred")
                document.progress = 0.0

        except Exception as e:
            logger.error(
                f"Error processing document {document_id}: {str(e)}", exc_info=True
            )
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            document.progress = 0.0

        finally:
            loop.close()

    except Exception as e:
        logger.error(
            f"Error in background task for document {document_id}: {str(e)}",
            exc_info=True,
        )
        if "document" in locals():
            document.status = ProcessingStatus.FAILED
            document.error_message = f"Processing error: {str(e)}"

    finally:
        if "document" in locals():
            db.add(document)
            db.commit()
        db.close()


def enqueue_document_processing(
    document_id: int, schema: Optional[Dict[str, Any]] = None
) -> str:
    """Enqueue a document for processing and return the job ID"""
    job = queue.enqueue(
        "app.utils.background_tasks.process_document_task",
        document_id,
        schema,
        job_timeout=3600,  # 1 hour timeout
    )
    return job.id


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a background job"""
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
