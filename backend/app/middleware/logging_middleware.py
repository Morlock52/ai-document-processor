import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(
            f"--> {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception as e:
            logger.error(
                f"Request error: {request.method} {request.url.path}: {e}"
            )
            raise
        finally:
            duration = time.time() - start_time
            logger.info(
                f"<-- {request.method} {request.url.path} "
                f"status={locals().get('status', 'error')} "
                f"time={duration:.2f}s"
            )
