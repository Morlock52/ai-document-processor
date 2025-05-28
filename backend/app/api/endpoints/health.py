import os
import time
import psutil
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import redis
import openai
from app.db.database import get_db
from app.core.config import settings
from app.models.document import Document, ProcessingStatus

# Configure logging for health checks
logger = logging.getLogger(__name__)

router = APIRouter()

# Global health metrics cache
health_cache = {
    "last_check": None,
    "metrics": {},
    "cache_duration": 30  # seconds
}

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint for load balancers

    Returns:
        Dict: Basic status and version info
    """
    logger.debug("🏥 HEALTH_CHECK: Basic check requested")

    return {
        "status": "healthy",
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "service": "Document Processor API",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": _get_uptime()
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check with self-healing capabilities

    Args:
        db: Database session

    Returns:
        Dict: Detailed health status including all services

    Raises:
        HTTPException: 503 if critical services are down
    """
    start_time = time.time()
    logger.info("🏥 DETAILED_HEALTH_CHECK: Starting comprehensive health assessment")

    # Check cache to avoid excessive health checks
    now = datetime.utcnow()
    if (health_cache["last_check"] and
        (now - health_cache["last_check"]).total_seconds() < health_cache["cache_duration"]):
        logger.debug("🏥 HEALTH_CACHE: Returning cached results")
        return health_cache["metrics"]

    health_status = {
        "status": "healthy",
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "service": "Document Processor API",
        "timestamp": now.isoformat(),
        "checks": {},
        "metrics": {},
        "self_healing": [],
        "warnings": []
    }

    critical_failures = []

    # 1. DATABASE HEALTH CHECK with connection pooling info
    try:
        logger.debug("🔍 HEALTH_DB: Checking database connectivity")

        # Test basic connectivity
        db_start = time.time()
        result = db.execute(text("SELECT 1")).scalar()
        db_time = time.time() - db_start

        # Test document table access
        doc_count = db.query(Document).count()
        processing_count = db.query(Document).filter(
            Document.status == ProcessingStatus.PROCESSING
        ).count()

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time * 1000, 2),
            "total_documents": doc_count,
            "processing_documents": processing_count,
            "connection_pool": _get_db_pool_info()
        }

        logger.info(f"✅ DB_HEALTHY: {doc_count} docs, {processing_count} processing, {db_time*1000:.1f}ms")

    except SQLAlchemyError as e:
        error_msg = f"Database error: {str(e)}"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": error_msg,
            "last_attempt": now.isoformat()
        }
        critical_failures.append("database")
        logger.error(f"❌ DB_UNHEALTHY: {error_msg}")

        # Self-healing: Attempt to recreate connection
        try:
            logger.info("🔄 SELF_HEAL: Attempting database reconnection")
            db.rollback()
            db.close()
            health_status["self_healing"].append("database_reconnect_attempted")
        except Exception as heal_error:
            logger.error(f"❌ HEAL_FAILED: Database reconnection failed: {heal_error}")

    # 2. REDIS HEALTH CHECK (for job queue)
    try:
        logger.debug("🔍 HEALTH_REDIS: Checking Redis connectivity")

        redis_start = time.time()
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_info = redis_client.ping()
        redis_time = time.time() - redis_start

        # Get Redis metrics
        redis_memory = redis_client.info('memory')
        queue_length = redis_client.llen('rq:queue:default') if redis_client.exists('rq:queue:default') else 0

        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(redis_time * 1000, 2),
            "queue_length": queue_length,
            "memory_used_mb": round(redis_memory.get('used_memory', 0) / 1024 / 1024, 2)
        }

        logger.info(f"✅ REDIS_HEALTHY: Queue={queue_length}, {redis_time*1000:.1f}ms")

    except Exception as e:
        error_msg = f"Redis error: {str(e)}"
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": error_msg
        }
        critical_failures.append("redis")
        logger.error(f"❌ REDIS_UNHEALTHY: {error_msg}")

    # 3. OPENAI API CHECK with rate limit info
    try:
        logger.debug("🔍 HEALTH_OPENAI: Checking OpenAI API")

        if not settings.OPENAI_API_KEY:
            health_status["checks"]["openai"] = {
                "status": "not_configured",
                "error": "API key not provided"
            }
            health_status["warnings"].append("OpenAI API key not configured")
        else:
            # Test API connectivity (lightweight call)
            openai_start = time.time()
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            # Use a simple models list call instead of actual generation
            models = client.models.list()
            openai_time = time.time() - openai_start

            health_status["checks"]["openai"] = {
                "status": "healthy",
                "response_time_ms": round(openai_time * 1000, 2),
                "models_available": len(models.data) if hasattr(models, 'data') else 0,
                "key_configured": True
            }

            logger.info(f"✅ OPENAI_HEALTHY: {openai_time*1000:.1f}ms")

    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        health_status["checks"]["openai"] = {
            "status": "unhealthy",
            "error": error_msg
        }
        critical_failures.append("openai")
        logger.error(f"❌ OPENAI_UNHEALTHY: {error_msg}")

    # 4. FILESYSTEM HEALTH CHECK
    try:
        logger.debug("🔍 HEALTH_FS: Checking filesystem")

        # Check upload directory
        upload_dir = settings.UPLOAD_DIR
        disk_usage = psutil.disk_usage(upload_dir if os.path.exists(upload_dir) else '/')

        # Count files in upload directory
        file_count = 0
        total_size = 0
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                if file.endswith('.pdf'):
                    file_path = os.path.join(upload_dir, file)
                    file_count += 1
                    total_size += os.path.getsize(file_path)

        disk_free_gb = disk_usage.free / (1024**3)
        disk_used_percent = (disk_usage.used / disk_usage.total) * 100

        health_status["checks"]["filesystem"] = {
            "status": "healthy" if disk_free_gb > 1 else "warning",
            "upload_dir": upload_dir,
            "upload_files_count": file_count,
            "upload_size_mb": round(total_size / (1024**2), 2),
            "disk_free_gb": round(disk_free_gb, 2),
            "disk_used_percent": round(disk_used_percent, 1)
        }

        if disk_free_gb < 1:
            health_status["warnings"].append(f"Low disk space: {disk_free_gb:.1f}GB free")

        logger.info(f"✅ FS_HEALTHY: {file_count} files, {disk_free_gb:.1f}GB free")

        # Self-healing: Clean old files if disk space is low
        if disk_free_gb < 0.5:  # Less than 500MB
            logger.warning("🔄 SELF_HEAL: Low disk space, cleaning old files")
            cleaned_count = await _cleanup_old_files(upload_dir)
            health_status["self_healing"].append(f"cleaned_{cleaned_count}_old_files")

    except Exception as e:
        logger.error(f"❌ FS_CHECK_FAILED: {str(e)}")
        health_status["checks"]["filesystem"] = {
            "status": "error",
            "error": str(e)
        }

    # 5. SYSTEM METRICS
    try:
        health_status["metrics"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "process_count": len(psutil.pids()),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }

        # Warnings for high resource usage
        if health_status["metrics"]["cpu_percent"] > 90:
            health_status["warnings"].append("High CPU usage")
        if health_status["metrics"]["memory_percent"] > 90:
            health_status["warnings"].append("High memory usage")

    except Exception as e:
        logger.error(f"❌ METRICS_FAILED: {str(e)}")

    # Determine overall status
    if critical_failures:
        health_status["status"] = "unhealthy"
        health_status["critical_failures"] = critical_failures
    elif health_status["warnings"]:
        health_status["status"] = "degraded"

    # Add timing info
    elapsed_time = time.time() - start_time
    health_status["check_duration_ms"] = round(elapsed_time * 1000, 2)

    # Cache results
    health_cache["last_check"] = now
    health_cache["metrics"] = health_status

    logger.info(f"🏥 HEALTH_COMPLETE: Status={health_status['status']}, Time={elapsed_time*1000:.1f}ms")

    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status

def _get_uptime() -> str:
    """Get application uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return str(timedelta(seconds=int(uptime_seconds)))
    except:
        return "unknown"

def _get_db_pool_info() -> Dict[str, Any]:
    """Get database connection pool information"""
    try:
        # This would need to be implemented based on your connection pool
        return {
            "active_connections": "unknown",
            "pool_size": "unknown"
        }
    except:
        return {}

async def _cleanup_old_files(upload_dir: str) -> int:
    """Clean up old files to free disk space"""
    try:
        cleaned_count = 0
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago

        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                os.remove(file_path)
                cleaned_count += 1

        logger.info(f"🧹 CLEANUP: Removed {cleaned_count} old files")
        return cleaned_count

    except Exception as e:
        logger.error(f"❌ CLEANUP_FAILED: {str(e)}")
        return 0