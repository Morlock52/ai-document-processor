import os
import logging
import sys
import time
import signal
import threading
import traceback
import gc
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

try:
    import psutil
except ImportError:
    psutil = None

from redis import Redis, ConnectionError as RedisConnectionError
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enhanced logging configuration with detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(process)d:%(thread)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('worker.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Worker monitoring and health check variables
HEALTH_CHECK_INTERVAL = 30  # seconds
MAX_MEMORY_MB = 1024  # 1GB memory limit
MAX_CONSECUTIVE_FAILURES = 5
REDIS_RECONNECT_ATTEMPTS = 3
REDIS_RECONNECT_DELAY = 5  # seconds

class WorkerHealthMonitor:
    """
    🏥 Comprehensive worker health monitoring and self-healing system
    Monitors memory usage, Redis connectivity, job processing, and system health
    """

    def __init__(self, worker: Worker, redis_conn: Redis):
        self.worker = worker
        self.redis_conn = redis_conn
        self.start_time = datetime.now()
        self.consecutive_failures = 0
        self.last_successful_job = datetime.now()
        self.total_jobs_processed = 0
        self.total_jobs_failed = 0
        self.is_monitoring = True
        self.monitor_thread: Optional[threading.Thread] = None

        logger.info("🏥 MONITOR_INIT: Worker health monitoring system initialized")

    def start_monitoring(self):
        """Start the health monitoring thread"""
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🏥 MONITOR_START: Health monitoring thread started")

    def stop_monitoring(self):
        """Stop the health monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🏥 MONITOR_STOP: Health monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop with comprehensive health checks"""
        while self.is_monitoring:
            try:
                self._perform_health_check()
                time.sleep(HEALTH_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"🚨 MONITOR_ERROR: Health check failed: {e}")
                logger.error(f"🔍 MONITOR_TRACE: {traceback.format_exc()}")
                time.sleep(HEALTH_CHECK_INTERVAL)

    def _perform_health_check(self):
        """
        🔍 Comprehensive health check with self-healing capabilities
        Monitors memory, Redis, job processing, and system resources
        """
        current_time = datetime.now()
        uptime = current_time - self.start_time

        # Memory usage check with cleanup
        memory_usage = self._check_memory_usage()

        # Redis connectivity check with reconnection
        redis_healthy = self._check_redis_connectivity()

        # Worker status check
        worker_status = self._check_worker_status()

        # Job processing health check
        job_health = self._check_job_processing_health(current_time)

        # System resource check (if psutil available)
        system_health = self._check_system_resources()

        # Log comprehensive health status
        logger.info(
            f"🏥 HEALTH_CHECK: "
            f"Uptime={uptime}, "
            f"Memory={memory_usage['usage_mb']:.1f}MB/{memory_usage['limit_mb']}MB, "
            f"Redis={'✅' if redis_healthy else '❌'}, "
            f"Worker={'✅' if worker_status['healthy'] else '❌'}, "
            f"Jobs=✅{self.total_jobs_processed}/❌{self.total_jobs_failed}, "
            f"Failures={self.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}, "
            f"LastJob={job_health['last_job_ago']:.1f}min, "
            f"System={system_health['status']}"
        )

        # Self-healing actions
        self._perform_self_healing(memory_usage, redis_healthy, worker_status, job_health, system_health)

    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check and manage memory usage with automatic cleanup"""
        if not psutil:
            return {"usage_mb": 0, "limit_mb": MAX_MEMORY_MB, "healthy": True}

        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            result = {
                "usage_mb": memory_mb,
                "limit_mb": MAX_MEMORY_MB,
                "healthy": memory_mb < MAX_MEMORY_MB,
                "percent": (memory_mb / MAX_MEMORY_MB) * 100
            }

            # Memory cleanup if approaching limit
            if memory_mb > MAX_MEMORY_MB * 0.8:
                logger.warning(f"⚠️ MEMORY_HIGH: {memory_mb:.1f}MB (80% of limit), triggering cleanup")
                gc.collect()

            if memory_mb > MAX_MEMORY_MB:
                logger.error(f"🚨 MEMORY_CRITICAL: {memory_mb:.1f}MB exceeds limit of {MAX_MEMORY_MB}MB")

            return result

        except Exception as e:
            logger.error(f"❌ MEMORY_CHECK_FAILED: {e}")
            return {"usage_mb": 0, "limit_mb": MAX_MEMORY_MB, "healthy": False}

    def _check_redis_connectivity(self) -> bool:
        """Check Redis connectivity with automatic reconnection"""
        try:
            # Test Redis connection with timeout
            self.redis_conn.ping()
            return True

        except RedisConnectionError as e:
            logger.error(f"❌ REDIS_DISCONNECTED: {e}")
            return self._attempt_redis_reconnection()
        except Exception as e:
            logger.error(f"❌ REDIS_ERROR: {e}")
            return False

    def _attempt_redis_reconnection(self) -> bool:
        """Attempt to reconnect to Redis with exponential backoff"""
        for attempt in range(1, REDIS_RECONNECT_ATTEMPTS + 1):
            try:
                logger.info(f"🔄 REDIS_RECONNECT: Attempt {attempt}/{REDIS_RECONNECT_ATTEMPTS}")

                # Create new connection
                redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
                new_conn = Redis.from_url(redis_url, socket_timeout=10, socket_connect_timeout=10)
                new_conn.ping()

                # Update connection
                self.redis_conn = new_conn
                logger.info("✅ REDIS_RECONNECTED: Successfully reconnected to Redis")
                return True

            except Exception as e:
                wait_time = REDIS_RECONNECT_DELAY * (2 ** (attempt - 1))
                logger.error(f"❌ REDIS_RECONNECT_FAILED: Attempt {attempt} failed: {e}, waiting {wait_time}s")
                time.sleep(wait_time)

        logger.error("🚨 REDIS_RECONNECT_EXHAUSTED: All reconnection attempts failed")
        return False

    def _check_worker_status(self) -> Dict[str, Any]:
        """Check worker status and health"""
        try:
            # Check if worker is still alive and responsive
            worker_state = getattr(self.worker, 'state', 'unknown')
            is_busy = getattr(self.worker, 'get_current_job', lambda: None)() is not None

            return {
                "healthy": True,
                "state": worker_state,
                "busy": is_busy,
                "pid": os.getpid()
            }

        except Exception as e:
            logger.error(f"❌ WORKER_STATUS_CHECK_FAILED: {e}")
            return {"healthy": False, "state": "error", "busy": False, "pid": os.getpid()}

    def _check_job_processing_health(self, current_time: datetime) -> Dict[str, Any]:
        """Check job processing patterns and detect stalls"""
        last_job_ago = (current_time - self.last_successful_job).total_seconds() / 60  # minutes

        # Check for job processing stalls
        job_stalled = last_job_ago > 60  # No successful job in 1 hour

        # Calculate success rate
        total_jobs = self.total_jobs_processed + self.total_jobs_failed
        success_rate = (self.total_jobs_processed / total_jobs * 100) if total_jobs > 0 else 100

        return {
            "last_job_ago": last_job_ago,
            "stalled": job_stalled,
            "success_rate": success_rate,
            "total_processed": self.total_jobs_processed,
            "total_failed": self.total_jobs_failed
        }

    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources (CPU, disk) if available"""
        if not psutil:
            return {"status": "unavailable", "details": "psutil not available"}

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Disk usage for worker directory
            disk_usage = psutil.disk_usage(Path(__file__).parent)
            disk_free_gb = disk_usage.free / (1024**3)

            # Load average (Unix systems)
            try:
                load_avg = os.getloadavg()
                load_1min = load_avg[0]
            except (OSError, AttributeError):
                load_1min = 0

            status = "healthy"
            if cpu_percent > 90:
                status = "high_cpu"
            elif disk_free_gb < 1:  # Less than 1GB free
                status = "low_disk"
            elif load_1min > psutil.cpu_count() * 2:
                status = "high_load"

            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "disk_free_gb": disk_free_gb,
                "load_1min": load_1min,
                "details": f"CPU:{cpu_percent:.1f}% Disk:{disk_free_gb:.1f}GB Load:{load_1min:.1f}"
            }

        except Exception as e:
            logger.error(f"❌ SYSTEM_CHECK_FAILED: {e}")
            return {"status": "error", "details": str(e)}

    def _perform_self_healing(self, memory_usage: Dict, redis_healthy: bool,
                             worker_status: Dict, job_health: Dict, system_health: Dict):
        """
        🔄 Perform self-healing actions based on health check results
        Implements automatic recovery for common failure scenarios
        """
        healing_actions = []

        # Memory-based healing
        if not memory_usage["healthy"]:
            logger.warning("🔄 SELF_HEAL: Memory limit exceeded, forcing garbage collection")
            gc.collect()
            healing_actions.append("memory_cleanup")

        # Redis connectivity healing
        if not redis_healthy:
            logger.warning("🔄 SELF_HEAL: Redis connection lost, worker may need restart")
            healing_actions.append("redis_reconnect_attempted")

        # Job processing stall healing
        if job_health["stalled"]:
            logger.warning(f"🔄 SELF_HEAL: Job processing stalled ({job_health['last_job_ago']:.1f}min)")
            # Could implement job queue cleanup here
            healing_actions.append("job_stall_detected")

        # Consecutive failure healing
        if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.error(
                f"🚨 SELF_HEAL: Too many consecutive failures ({self.consecutive_failures}), "
                "worker may need restart"
            )
            healing_actions.append("failure_threshold_exceeded")

        # System resource healing
        if system_health["status"] == "low_disk":
            logger.warning("🔄 SELF_HEAL: Low disk space detected")
            # Could implement log rotation or temp file cleanup
            healing_actions.append("disk_cleanup_needed")

        if healing_actions:
            logger.info(f"🔄 SELF_HEAL: Actions taken: {', '.join(healing_actions)}")

    def record_job_success(self):
        """Record successful job completion"""
        self.total_jobs_processed += 1
        self.last_successful_job = datetime.now()
        self.consecutive_failures = 0
        logger.debug("✅ JOB_SUCCESS: Job completed successfully")

    def record_job_failure(self, error: Exception):
        """Record job failure with error details"""
        self.total_jobs_failed += 1
        self.consecutive_failures += 1
        logger.error(f"❌ JOB_FAILED: {error}")
        logger.error(f"🔍 JOB_TRACE: {traceback.format_exc()}")

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary for external monitoring"""
        current_time = datetime.now()
        uptime = current_time - self.start_time

        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_jobs_processed": self.total_jobs_processed,
            "total_jobs_failed": self.total_jobs_failed,
            "consecutive_failures": self.consecutive_failures,
            "last_successful_job": self.last_successful_job.isoformat(),
            "memory_usage": self._check_memory_usage(),
            "redis_healthy": self._check_redis_connectivity(),
            "worker_status": self._check_worker_status(),
            "system_health": self._check_system_resources()
        }

class EnhancedWorker(Worker):
    """
    🚀 Enhanced RQ Worker with comprehensive monitoring and error recovery
    Extends the base RQ Worker with health monitoring and self-healing capabilities
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.health_monitor: Optional[WorkerHealthMonitor] = None

    def setup_health_monitoring(self, redis_conn: Redis):
        """Initialize and start health monitoring"""
        self.health_monitor = WorkerHealthMonitor(self, redis_conn)
        self.health_monitor.start_monitoring()

    def perform_job(self, job, queue):
        """
        Override job execution with enhanced error handling and monitoring
        Wraps the original perform_job with comprehensive logging and error recovery
        """
        job_id = job.id if job else "unknown"
        job_func = getattr(job, 'func_name', 'unknown') if job else "unknown"

        logger.info(f"🚀 JOB_START: ID={job_id}, Function={job_func}")

        start_time = time.time()

        try:
            # Execute the job with timing
            result = super().perform_job(job, queue)

            # Record success metrics
            execution_time = time.time() - start_time
            logger.info(f"✅ JOB_COMPLETE: ID={job_id}, Time={execution_time:.2f}s")

            if self.health_monitor:
                self.health_monitor.record_job_success()

            return result

        except Exception as e:
            # Record failure metrics
            execution_time = time.time() - start_time
            logger.error(f"❌ JOB_FAILED: ID={job_id}, Time={execution_time:.2f}s, Error={e}")
            logger.error(f"🔍 JOB_ERROR_TRACE: {traceback.format_exc()}")

            if self.health_monitor:
                self.health_monitor.record_job_failure(e)

            # Re-raise the exception to maintain RQ behavior
            raise

    def cleanup(self):
        """Enhanced cleanup with health monitor shutdown"""
        logger.info("🛑 WORKER_SHUTDOWN: Starting cleanup process")

        if self.health_monitor:
            self.health_monitor.stop_monitoring()

        # Call parent cleanup
        super().cleanup()

        logger.info("🛑 WORKER_SHUTDOWN: Cleanup completed")

def setup_signal_handlers(worker: EnhancedWorker):
    """
    🛡️ Setup signal handlers for graceful shutdown
    Ensures proper cleanup when worker receives termination signals
    """
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info(f"🛑 SIGNAL_RECEIVED: {signal_name} ({signum}), initiating graceful shutdown")

        # Set worker to stop accepting new jobs
        worker.should_run_maintenance_tasks = False

        # Trigger cleanup
        worker.cleanup()

        logger.info(f"🛑 SIGNAL_HANDLED: Graceful shutdown completed for {signal_name}")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("🛡️ SIGNAL_HANDLERS: Registered SIGTERM and SIGINT handlers")

def validate_environment() -> Dict[str, Any]:
    """
    🔍 Validate environment configuration and dependencies
    Checks required environment variables and system dependencies
    """
    validation_results = {
        "redis_url": os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        "python_version": sys.version,
        "worker_directory": str(Path(__file__).parent),
        "psutil_available": psutil is not None,
        "issues": []
    }

    # Check Redis URL format
    redis_url = validation_results["redis_url"]
    if not redis_url.startswith(('redis://', 'rediss://')):
        validation_results["issues"].append(f"Invalid Redis URL format: {redis_url}")

    # Check Python version (should be 3.7+)
    if sys.version_info < (3, 7):
        validation_results["issues"].append(f"Python 3.7+ required, got {sys.version}")

    # Check write permissions for log files
    try:
        test_log_path = Path(__file__).parent / "test_write.log"
        test_log_path.write_text("test")
        test_log_path.unlink()
    except Exception as e:
        validation_results["issues"].append(f"Cannot write log files: {e}")

    # Check if psutil is available for system monitoring
    if not psutil:
        validation_results["issues"].append("psutil not available - system monitoring limited")

    return validation_results

def start_worker():
    """
    🚀 Enhanced worker startup with comprehensive initialization
    Includes environment validation, health monitoring, and error recovery
    """
    worker_start_time = datetime.now()
    logger.info("🚀 WORKER_INIT: Starting enhanced document processing worker")

    # Validate environment before starting
    logger.info("🔍 WORKER_INIT: Validating environment configuration")
    env_validation = validate_environment()

    if env_validation["issues"]:
        logger.warning(f"⚠️ WORKER_INIT: Environment issues detected: {env_validation['issues']}")
        # Continue anyway but log the issues

    logger.info(f"🔍 WORKER_INIT: Environment validated - Redis: {env_validation['redis_url'][:20]}...")

    # Initialize Redis connection with retry logic
    redis_url = env_validation["redis_url"]
    redis_conn = None

    for attempt in range(1, REDIS_RECONNECT_ATTEMPTS + 1):
        try:
            logger.info(f"🔗 REDIS_CONNECT: Attempt {attempt}/{REDIS_RECONNECT_ATTEMPTS} to {redis_url[:30]}...")

            redis_conn = Redis.from_url(
                redis_url,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # Test connection
            redis_conn.ping()
            logger.info("✅ REDIS_CONNECTED: Successfully connected to Redis")
            break

        except Exception as e:
            wait_time = REDIS_RECONNECT_DELAY * (2 ** (attempt - 1))
            logger.error(f"❌ REDIS_CONNECT_FAILED: Attempt {attempt} failed: {e}")

            if attempt < REDIS_RECONNECT_ATTEMPTS:
                logger.info(f"🔄 REDIS_RETRY: Waiting {wait_time}s before retry")
                time.sleep(wait_time)
            else:
                logger.error("🚨 REDIS_CONNECT_EXHAUSTED: All connection attempts failed")
                raise

    # Initialize queue and worker
    try:
        logger.info("🔧 WORKER_INIT: Initializing job queue and worker")

        queue = Queue('default', connection=redis_conn)
        worker = EnhancedWorker([queue], connection=redis_conn)

        # Setup health monitoring
        worker.setup_health_monitoring(redis_conn)

        # Setup signal handlers for graceful shutdown
        setup_signal_handlers(worker)

        # Log startup completion
        startup_time = datetime.now() - worker_start_time
        logger.info(
            f"🚀 WORKER_READY: Enhanced worker started successfully in {startup_time.total_seconds():.2f}s"
        )

        # Start the worker event loop
        logger.info("🔄 WORKER_LOOP: Starting job processing loop")
        with Connection(redis_conn):
            worker.work(logging_level='INFO')

    except KeyboardInterrupt:
        logger.info("🛑 WORKER_INTERRUPTED: Received keyboard interrupt")
        worker.cleanup()
    except Exception as e:
        logger.error(f"🚨 WORKER_ERROR: Fatal error in worker: {e}")
        logger.error(f"🔍 WORKER_TRACE: {traceback.format_exc()}")

        if worker and hasattr(worker, 'cleanup'):
            worker.cleanup()

        raise
    finally:
        logger.info("🛑 WORKER_SHUTDOWN: Worker process terminating")

if __name__ == '__main__':
    """
    📋 Main entry point with comprehensive error handling
    Handles all startup failures and ensures proper logging
    """
    try:
        # Set process title for easier identification
        try:
            import setproctitle
            setproctitle.setproctitle('document-processor-worker')
        except ImportError:
            pass  # setproctitle is optional

        logger.info(f"🚀 MAIN: Starting document processing worker (PID: {os.getpid()})")
        start_worker()

    except KeyboardInterrupt:
        logger.info("🛑 MAIN: Graceful shutdown via keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        logger.error(f"🚨 MAIN: Fatal startup error: {e}")
        logger.error(f"🔍 MAIN_TRACE: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info("🛑 MAIN: Worker process terminated")
