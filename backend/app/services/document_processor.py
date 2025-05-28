import base64
import logging
import time
import traceback
import os
import psutil
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import gc
from datetime import datetime

from openai import OpenAI
from openai.types.chat import ChatCompletion
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

from app.core.config import settings
from app.models.document import ProcessingStatus
from app.db.database import SessionLocal

# Configure comprehensive logging for document processing
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)

# Processing metrics and monitoring
processing_metrics = {
    "total_documents": 0,
    "successful_documents": 0,
    "failed_documents": 0,
    "average_processing_time": 0,
    "last_reset": datetime.utcnow()
}

class DocumentProcessor:
    """
    Enhanced document processor with comprehensive logging, monitoring, and error recovery

    Features:
    - Memory-optimized PDF processing with chunking
    - Comprehensive error handling and recovery
    - Performance monitoring and metrics
    - Self-healing capabilities for common failures
    - Detailed logging for troubleshooting
    """

    def __init__(self):
        """
        Initialize document processor with enhanced monitoring
        """
        logger.info("🔧 PROCESSOR_INIT: Initializing DocumentProcessor")

        try:
            # Initialize OpenAI client with validation
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")

            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("✅ OPENAI_INIT: OpenAI client initialized successfully")

        except Exception as e:
            logger.error(f"❌ OPENAI_INIT_FAILED: {e}")
            raise

        try:
            # Initialize image preprocessor
            self.preprocessing = ImagePreprocessor()
            logger.info("✅ PREPROCESSOR_INIT: Image preprocessor initialized")

        except Exception as e:
            logger.error(f"❌ PREPROCESSOR_INIT_FAILED: {e}")
            raise

        # Processing configuration with performance tuning
        self.config = {
            "chunk_size": 3,  # Pages per chunk for memory management
            "max_image_size": (2000, 2000),  # Max image dimensions
            "dpi": 200,  # PDF to image conversion DPI
            "timeout": 60,  # OpenAI API timeout in seconds
            "retry_attempts": 3,  # Number of retry attempts
            "memory_threshold_mb": 1000  # Memory usage threshold for cleanup
        }

        logger.info(f"⚙️  PROCESSOR_CONFIG: {self.config}")

    async def process_pdf(self, pdf_path: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a PDF document with comprehensive error handling and monitoring

        Args:
            pdf_path: Path to the PDF file to process
            schema: Optional schema for structured extraction

        Returns:
            Dict containing extracted data and metadata

        Raises:
            Exception: Various processing errors with detailed context
        """
        start_time = time.time()
        process_id = f"proc_{int(time.time())}"

        logger.info(f"🚀 PDF_PROCESS_START: ID={process_id}, File='{pdf_path}', Schema={bool(schema)}")

        # Update global metrics
        processing_metrics["total_documents"] += 1

        try:
            # Pre-processing validations with detailed checks
            await self._validate_pdf_file(pdf_path, process_id)

            # Memory monitoring before processing
            memory_usage = self._get_memory_usage()
            logger.info(f"📊 MEMORY_BEFORE: {memory_usage}MB, Process={process_id}")

            # Get page count with error handling
            try:
                page_count = self._get_page_count(pdf_path)
                logger.info(f"📄 PAGE_COUNT: {page_count} pages, Process={process_id}")

                if page_count == 0:
                    raise ValueError("PDF contains no pages")

                if page_count > 50:  # Reasonable limit
                    logger.warning(f"⚠️  LARGE_DOCUMENT: {page_count} pages, Process={process_id}")

            except Exception as e:
                logger.error(f"❌ PAGE_COUNT_FAILED: {e}, Process={process_id}")
                raise ValueError(f"Cannot determine page count: {e}")

            # Process pages in chunks for memory optimization
            chunk_size = self.config["chunk_size"]
            extracted_data = []
            failed_chunks = []

            logger.info(f"🔄 CHUNK_PROCESSING: {chunk_size} pages per chunk, Process={process_id}")

            for chunk_start in range(0, page_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, page_count)
                chunk_id = f"{process_id}_chunk_{chunk_start}_{chunk_end}"

                logger.info(f"📊 CHUNK_START: Pages {chunk_start + 1}-{chunk_end}, ID={chunk_id}")

                try:
                    # Process chunk with timeout and error handling
                    chunk_data = await self._process_page_chunk_with_recovery(
                        pdf_path, chunk_start, chunk_end, schema, chunk_id
                    )

                    if chunk_data:
                        extracted_data.extend(chunk_data)
                        logger.info(f"✅ CHUNK_SUCCESS: ID={chunk_id}, DataPoints={len(chunk_data)}")
                    else:
                        logger.warning(f"⚠️  CHUNK_EMPTY: ID={chunk_id}")

                except Exception as e:
                    logger.error(f"❌ CHUNK_FAILED: ID={chunk_id}, Error={e}")
                    failed_chunks.append((chunk_start, chunk_end, str(e)))

                    # Continue processing other chunks instead of failing completely
                    continue

                # Memory cleanup and monitoring
                memory_after_chunk = self._get_memory_usage()
                if memory_after_chunk > self.config["memory_threshold_mb"]:
                    logger.warning(f"🧹 MEMORY_CLEANUP: {memory_after_chunk}MB > threshold")
                    gc.collect()

                # Brief pause between chunks to prevent overwhelming the API
                await asyncio.sleep(0.5)

            # Log chunk processing summary
            successful_chunks = len(extracted_data) if extracted_data else 0
            total_chunks = (page_count + chunk_size - 1) // chunk_size

            logger.info(f"📊 CHUNK_SUMMARY: Success={successful_chunks}/{total_chunks}, Failed={len(failed_chunks)}")

            if failed_chunks:
                logger.warning(f"⚠️  FAILED_CHUNKS: {failed_chunks}")

            # Validate we have some extracted data
            if not extracted_data:
                error_msg = "No data extracted from any page chunks"
                if failed_chunks:
                    error_msg += f". Failed chunks: {len(failed_chunks)}"
                logger.error(f"❌ NO_DATA_EXTRACTED: {error_msg}, Process={process_id}")
                raise ValueError(error_msg)

            # Merge and validate data from all pages
            try:
                logger.info(f"🔄 DATA_MERGE: Merging {len(extracted_data)} data points, Process={process_id}")
                final_data = self._merge_page_data(extracted_data, schema)

                if not final_data:
                    raise ValueError("Data merge resulted in empty dataset")

                logger.info(f"✅ DATA_MERGE_SUCCESS: {len(final_data)} final fields, Process={process_id}")

            except Exception as e:
                logger.error(f"❌ DATA_MERGE_FAILED: {e}, Process={process_id}")
                raise

            # Add processing metadata
            elapsed_time = time.time() - start_time
            final_data.update({
                "_processing_metadata": {
                    "process_id": process_id,
                    "processing_time_seconds": round(elapsed_time, 2),
                    "page_count": page_count,
                    "chunks_processed": successful_chunks,
                    "chunks_failed": len(failed_chunks),
                    "schema_used": bool(schema),
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_peak_mb": self._get_memory_usage()
                }
            })

            # Update success metrics
            processing_metrics["successful_documents"] += 1
            processing_metrics["average_processing_time"] = (
                (processing_metrics["average_processing_time"] * (processing_metrics["successful_documents"] - 1) + elapsed_time)
                / processing_metrics["successful_documents"]
            )

            logger.info(f"✅ PDF_PROCESS_SUCCESS: Process={process_id}, Time={elapsed_time:.2f}s, Fields={len(final_data)}")

            return final_data

        except Exception as e:
            # Comprehensive error handling with context
            elapsed_time = time.time() - start_time
            processing_metrics["failed_documents"] += 1

            error_context = {
                "process_id": process_id,
                "pdf_path": pdf_path,
                "elapsed_time": elapsed_time,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "memory_usage_mb": self._get_memory_usage()
            }

            logger.error(f"❌ PDF_PROCESS_FAILED: {error_context}")
            logger.error(f"🔍 PDF_PROCESS_TRACEBACK: {traceback.format_exc()}")

            # Attempt cleanup on failure
            try:
                gc.collect()
                logger.info(f"🧹 CLEANUP: Memory cleanup attempted after failure")
            except:
                pass

            raise

    async def _validate_pdf_file(self, pdf_path: str, process_id: str) -> None:
        """
        Validate PDF file exists and is accessible

        Args:
            pdf_path: Path to PDF file
            process_id: Process identifier for logging

        Raises:
            ValueError: If file validation fails
        """
        logger.debug(f"🔍 PDF_VALIDATION: Checking file '{pdf_path}', Process={process_id}")

        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(f"❌ FILE_NOT_FOUND: {error_msg}, Process={process_id}")
            raise ValueError(error_msg)

        if not os.path.isfile(pdf_path):
            error_msg = f"Path is not a file: {pdf_path}"
            logger.error(f"❌ NOT_A_FILE: {error_msg}, Process={process_id}")
            raise ValueError(error_msg)

        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            error_msg = f"PDF file is empty: {pdf_path}"
            logger.error(f"❌ EMPTY_FILE: {error_msg}, Process={process_id}")
            raise ValueError(error_msg)

        if file_size > 100 * 1024 * 1024:  # 100MB limit
            logger.warning(f"⚠️  LARGE_FILE: {file_size / 1024 / 1024:.1f}MB, Process={process_id}")

        logger.debug(f"✅ PDF_VALIDATION_SUCCESS: Size={file_size}B, Process={process_id}")

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB

        Returns:
            float: Memory usage in megabytes
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return round(memory_info.rss / 1024 / 1024, 2)
        except Exception as e:
            logger.warning(f"⚠️  MEMORY_CHECK_FAILED: {e}")
            return 0.0

    def _get_page_count(self, pdf_path: str) -> int:
        """
        Get page count from PDF with error handling

        Args:
            pdf_path: Path to PDF file

        Returns:
            int: Number of pages in PDF

        Raises:
            Exception: If page count cannot be determined
        """
        try:
            # Use pdf2image to get page count efficiently
            from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError

            try:
                images = convert_from_path(pdf_path, first_page=1, last_page=1)
                # If we can convert first page, use pdf2image to get total count
                info = convert_from_path(pdf_path, dpi=50, fmt='jpeg', thread_count=1)
                return len(info)
            except (PDFInfoNotInstalledError, PDFPageCountError):
                # Fallback to PyPDF2 if pdf2image fails
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return len(pdf_reader.pages)

        except Exception as e:
            logger.error(f"❌ PAGE_COUNT_ERROR: {e} for file {pdf_path}")
            raise

    async def _process_page_chunk_with_recovery(self, pdf_path: str, chunk_start: int,
                                              chunk_end: int, schema: Optional[Dict],
                                              chunk_id: str) -> List[Dict[str, Any]]:
        """
        Process a chunk of PDF pages with retry logic and error recovery

        Args:
            pdf_path: Path to PDF file
            chunk_start: Starting page index
            chunk_end: Ending page index
            schema: Optional extraction schema
            chunk_id: Chunk identifier for logging

        Returns:
            List of extracted data dictionaries
        """
        max_attempts = self.config["retry_attempts"]

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"🔄 CHUNK_ATTEMPT: {attempt}/{max_attempts}, ID={chunk_id}")

                # Convert PDF pages to images with memory optimization
                images = self._convert_pdf_chunk_to_images(pdf_path, chunk_start, chunk_end, chunk_id)

                if not images:
                    logger.warning(f"⚠️  NO_IMAGES: Chunk {chunk_id}")
                    return []

                # Process images with GPT-4o
                chunk_data = await self._extract_data_from_images(images, schema, chunk_id)

                logger.debug(f"✅ CHUNK_ATTEMPT_SUCCESS: Attempt {attempt}, ID={chunk_id}")
                return chunk_data

            except Exception as e:
                logger.warning(f"⚠️  CHUNK_ATTEMPT_FAILED: Attempt {attempt}/{max_attempts}, ID={chunk_id}, Error={e}")

                if attempt == max_attempts:
                    logger.error(f"❌ CHUNK_EXHAUSTED: All attempts failed for {chunk_id}")
                    raise

                # Wait before retry with exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"⏳ RETRY_WAIT: {wait_time}s before attempt {attempt + 1}, ID={chunk_id}")
                await asyncio.sleep(wait_time)

        return []

    def _convert_pdf_chunk_to_images(self, pdf_path: str, chunk_start: int,
                                   chunk_end: int, chunk_id: str) -> List[Image.Image]:
        """
        Convert PDF pages to images with memory optimization

        Args:
            pdf_path: Path to PDF file
            chunk_start: Starting page index
            chunk_end: Ending page index
            chunk_id: Chunk identifier for logging

        Returns:
            List of PIL Image objects
        """
        try:
            logger.debug(f"🖼️  IMAGE_CONVERSION: Pages {chunk_start + 1}-{chunk_end}, ID={chunk_id}")

            # Convert with optimized settings
            images = convert_from_path(
                pdf_path,
                first_page=chunk_start + 1,
                last_page=chunk_end,
                dpi=self.config["dpi"],
                fmt='RGB',
                thread_count=1  # Limit threads for memory control
            )

            # Resize images if they're too large
            max_size = self.config["max_image_size"]
            processed_images = []

            for i, img in enumerate(images):
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.debug(f"📏 IMAGE_RESIZED: Page {chunk_start + i + 1} to {img.size}")

                processed_images.append(img)

            logger.debug(f"✅ IMAGE_CONVERSION_SUCCESS: {len(processed_images)} images, ID={chunk_id}")
            return processed_images

        except Exception as e:
            logger.error(f"❌ IMAGE_CONVERSION_FAILED: {e}, ID={chunk_id}")
            raise

    async def _extract_data_from_images(self, images: List[Image.Image],
                                      schema: Optional[Dict], chunk_id: str) -> List[Dict[str, Any]]:
        """
        Extract data from images using GPT-4o Vision with error handling

        Args:
            images: List of PIL Image objects
            schema: Optional extraction schema
            chunk_id: Chunk identifier for logging

        Returns:
            List of extracted data dictionaries
        """
        try:
            logger.debug(f"🤖 GPT_EXTRACTION: {len(images)} images, ID={chunk_id}")

            extracted_data = []

            for i, image in enumerate(images):
                page_id = f"{chunk_id}_page_{i}"

                try:
                    # Convert image to base64
                    image_b64 = self._image_to_base64(image)

                    # Create extraction prompt
                    prompt = self._build_extraction_prompt(schema)

                    # Call GPT-4o Vision API with timeout
                    response = await asyncio.wait_for(
                        self._call_gpt4o_vision(image_b64, prompt, page_id),
                        timeout=self.config["timeout"]
                    )

                    if response:
                        response["page_number"] = i + 1
                        extracted_data.append(response)
                        logger.debug(f"✅ PAGE_EXTRACTION_SUCCESS: {page_id}")
                    else:
                        logger.warning(f"⚠️  PAGE_EXTRACTION_EMPTY: {page_id}")

                except Exception as e:
                    logger.error(f"❌ PAGE_EXTRACTION_FAILED: {page_id}, Error={e}")
                    # Continue with other pages instead of failing the entire chunk
                    continue

            logger.debug(f"✅ GPT_EXTRACTION_SUCCESS: {len(extracted_data)} pages, ID={chunk_id}")
            return extracted_data

        except Exception as e:
            logger.error(f"❌ GPT_EXTRACTION_FAILED: {e}, ID={chunk_id}")
            raise

    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string

        Args:
            image: PIL Image object

        Returns:
            str: Base64 encoded image
        """
        import io

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)

        # Encode to base64
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    async def _call_gpt4o_vision(self, image_b64: str, prompt: str, page_id: str) -> Dict[str, Any]:
        """
        Call GPT-4o Vision API with comprehensive error handling

        Args:
            image_b64: Base64 encoded image
            prompt: Extraction prompt
            page_id: Page identifier for logging

        Returns:
            Dict containing extracted data
        """
        try:
            logger.debug(f"🤖 GPT_API_CALL: {page_id}")

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=4096,
                    temperature=0.1
                )
            )

            if response and response.choices:
                content = response.choices[0].message.content
                if content:
                    # Parse JSON response
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # If not JSON, create a simple structure
                        return {"extracted_text": content}

            logger.warning(f"⚠️  GPT_API_EMPTY_RESPONSE: {page_id}")
            return {}

        except Exception as e:
            logger.error(f"❌ GPT_API_FAILED: {page_id}, Error={e}")
            raise

    def _build_extraction_prompt(self, schema: Optional[Dict] = None) -> str:
        """
        Build extraction prompt for GPT-4o Vision

        Args:
            schema: Optional extraction schema

        Returns:
            str: Formatted prompt
        """
        base_prompt = """
        Extract all visible text and data from this document image.
        Return the data in JSON format with clear field names.

        Focus on extracting:
        - Headers and titles
        - Form fields and their values
        - Tables and structured data
        - Important numbers and dates
        - Any key-value pairs

        Use "N/A" for missing or unclear values.
        """

        if schema:
            schema_prompt = f"\n\nPlease extract data according to this schema: {json.dumps(schema, indent=2)}"
            return base_prompt + schema_prompt

        return base_prompt

    def _merge_page_data(self, extracted_data: List[Dict[str, Any]],
                        schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Merge data from multiple pages into a single result

        Args:
            extracted_data: List of data from each page
            schema: Optional schema for merging logic

        Returns:
            Dict containing merged data
        """
        if not extracted_data:
            return {}

        if len(extracted_data) == 1:
            return extracted_data[0]

        # Merge logic: combine unique keys, prefer non-empty values
        merged = {}

        for page_data in extracted_data:
            for key, value in page_data.items():
                if key not in merged or (
                    merged[key] in [None, "", "N/A"] and
                    value not in [None, "", "N/A"]
                ):
                    merged[key] = value

        return merged

    @staticmethod
    def get_processing_metrics() -> Dict[str, Any]:
        """
        Get current processing metrics for monitoring

        Returns:
            Dict containing processing statistics
        """
        return {
            **processing_metrics,
            "success_rate": (
                processing_metrics["successful_documents"] /
                max(processing_metrics["total_documents"], 1) * 100
            ),
            "failure_rate": (
                processing_metrics["failed_documents"] /
                max(processing_metrics["total_documents"], 1) * 100
            )
        }
    
    def _get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF without loading all images"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except ImportError:
            # Fallback to pdf2image if PyMuPDF not available
            from pdf2image.exceptions import PDFInfoNotInstalledError
            try:
                import subprocess
                result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if line.startswith('Pages:'):
                        return int(line.split(':')[1].strip())
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            # Final fallback - convert first page to get info
            images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
            # Use a rough estimate based on file size if we can't get exact count
            return max(1, len(images))

    async def _process_page_chunk(self, pdf_path: str, start_page: int, end_page: int, schema: Optional[Dict]) -> List[Dict]:
        """Process a chunk of pages with memory optimization"""
        try:
            # Convert only the required pages with reduced DPI for memory efficiency
            images = convert_from_path(
                pdf_path,
                dpi=200,  # Reduced from 300 to save memory
                first_page=start_page + 1,  # pdf2image uses 1-based indexing
                last_page=end_page
            )

            chunk_data = []
            for i, image in enumerate(images):
                page_num = start_page + i + 1
                logger.info(f"Processing page {page_num}")

                # Optimize image size if too large
                image = self._optimize_image_size(image)

                # Enhance image quality
                enhanced_image = self.preprocessing.enhance(image)

                # Extract data using GPT-4o
                page_data = await self._extract_with_gpt4o(enhanced_image, schema)
                page_data['page_number'] = page_num
                chunk_data.append(page_data)

                # Clear image from memory
                del image, enhanced_image

            return chunk_data

        except Exception as e:
            logger.error(f"Error processing page chunk {start_page}-{end_page}: {str(e)}")
            raise

    def _optimize_image_size(self, image: Image.Image, max_dimension: int = 2048) -> Image.Image:
        """Optimize image size to prevent memory issues"""
        width, height = image.size

        # If image is too large, resize it
        if width > max_dimension or height > max_dimension:
            # Calculate new size maintaining aspect ratio
            if width > height:
                new_width = max_dimension
                new_height = int((height * max_dimension) / width)
            else:
                new_height = max_dimension
                new_width = int((width * max_dimension) / height)

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

        return image
    
    async def _extract_with_gpt4o(self, image: Image.Image, schema: Optional[Dict] = None) -> Dict:
        """Extract data from image using GPT-4o vision capabilities"""
        # Convert image to base64
        import io
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Build prompt
        prompt = self._build_extraction_prompt(schema)
        
        try:
            # Use sync client since OpenAI doesn't have async support
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4096,
                    temperature=0.1
                )
            )
            
            # Parse the response
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback to structured extraction
                return self._parse_unstructured_response(content)
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Fallback to OCR
            return self._fallback_ocr_extraction(image)
    
    def _build_extraction_prompt(self, schema: Optional[Dict] = None) -> str:
        """Build the extraction prompt for GPT-4o"""
        if schema:
            fields_description = json.dumps(schema, indent=2)
            return f"""
            Analyze this document image and extract all data according to this schema:
            {fields_description}
            
            Rules:
            1. Extract all visible text and data from the document
            2. Match extracted data to the schema fields
            3. For any missing or unreadable fields, use "N/A"
            4. Return the data as valid JSON matching the schema structure
            5. Include confidence scores for each field (0-1)
            
            Return only the JSON data, no explanations.
            """
        else:
            return """
            Analyze this document and extract all visible information.
            Identify the document type and all fields present.
            
            Return as JSON with this structure:
            {
                "document_type": "detected type",
                "fields": {
                    "field_name": "value",
                    ...
                },
                "confidence": {
                    "field_name": 0.95,
                    ...
                }
            }
            """
    
    def _merge_page_data(self, page_data: List[Dict], schema: Optional[Dict] = None) -> Dict:
        """Merge data from multiple pages into a single record"""
        if not page_data:
            return {}
            
        # For single page, return as is
        if len(page_data) == 1:
            return page_data[0].get('fields', page_data[0])
            
        # For multiple pages, intelligently merge
        merged = {}
        for page in page_data:
            fields = page.get('fields', page)
            for key, value in fields.items():
                if key not in merged or merged[key] == "N/A":
                    merged[key] = value
                    
        return merged
    
    def _fill_missing_fields(self, data: Dict, schema: Dict) -> Dict:
        """Fill missing fields with 'N/A'"""
        for field in schema.get('required_fields', []):
            if field not in data or not data[field]:
                data[field] = "N/A"
        return data
    
    def _calculate_confidence(self, extracted_data: List[Dict]) -> Dict:
        """Calculate average confidence scores"""
        all_scores = {}
        for page in extracted_data:
            confidence = page.get('confidence', {})
            for field, score in confidence.items():
                if field not in all_scores:
                    all_scores[field] = []
                all_scores[field].append(score)
                
        # Average scores
        avg_scores = {}
        for field, scores in all_scores.items():
            avg_scores[field] = sum(scores) / len(scores) if scores else 0.0
            
        return avg_scores
    
    def _fallback_ocr_extraction(self, image: Image.Image) -> Dict:
        """Fallback to Tesseract OCR if GPT-4o fails"""
        try:
            text = pytesseract.image_to_string(image)
            return {
                "raw_text": text,
                "fields": {},
                "extraction_method": "ocr_fallback"
            }
        except Exception as e:
            logger.error(f"OCR fallback failed: {str(e)}")
            return {"error": "extraction_failed"}
    
    def _parse_unstructured_response(self, content: str) -> Dict:
        """Parse unstructured text response into dictionary"""
        # Simple key-value extraction
        result = {}
        lines = content.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result


class ImagePreprocessor:
    """Enhance scanned document images for better OCR/AI processing"""
    
    def enhance(self, image: Image.Image) -> Image.Image:
        """Apply enhancement pipeline to improve image quality"""
        # Convert PIL to OpenCV
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply enhancements
        cv_image = self._deskew(cv_image)
        cv_image = self._remove_noise(cv_image)
        cv_image = self._enhance_contrast(cv_image)
        cv_image = self._sharpen(cv_image)
        
        # Convert back to PIL
        return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Correct image skew"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = (theta * 180 / np.pi) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)
                    
            if angles:
                median_angle = np.median(angles)
                if abs(median_angle) > 0.5:
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    image = cv2.warpAffine(image, M, (w, h), 
                                         flags=cv2.INTER_CUBIC,
                                         borderMode=cv2.BORDER_REPLICATE)
        return image
    
    def _remove_noise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from scanned document"""
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE"""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    def _sharpen(self, image: np.ndarray) -> np.ndarray:
        """Sharpen text in the image"""
        kernel = np.array([[-1,-1,-1],
                           [-1, 9,-1],
                           [-1,-1,-1]])
        return cv2.filter2D(image, -1, kernel)