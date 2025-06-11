from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
import os


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Document Processor API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BACKEND_PORT", os.getenv("PORT", "8000")))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8000",
        "http://localhost:8001",
        f"http://localhost:{os.getenv('FRONTEND_PORT', '3000')}",
        f"http://localhost:{os.getenv('BACKEND_PORT', '8000')}",
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://docuser:docpass@localhost:{os.getenv('POSTGRES_PORT', '5432')}/docprocessor",
    )

    # Redis
    REDIS_URL: str = os.getenv(
        "REDIS_URL", f"redis://localhost:{os.getenv('REDIS_PORT', '6379')}"
    )

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "document-processor")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # File upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    UPLOAD_DIR: str = "/app/uploads"

    # Processing
    MAX_PAGES_PER_DOCUMENT: int = 100
    PROCESSING_TIMEOUT: int = 300  # 5 minutes

    class Config:
        case_sensitive = True
        env_file = ".env"
        # Also load from .env.ports if it exists
        env_file_encoding = "utf-8"

    def __init__(self, **values):
        super().__init__(**values)
        # Load additional env files
        if os.path.exists(".env.ports"):
            from dotenv import load_dotenv

            load_dotenv(".env.ports", override=True)


settings = Settings()
