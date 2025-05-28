import json
import logging
from typing import Dict, Any
import base64
from io import BytesIO
from PIL import Image

from openai import OpenAI
from app.core.config import settings
from app.schemas.document import SchemaDetectionResponse, ExtractionSchema

logger = logging.getLogger(__name__)

class SchemaDetector:
    """Automatically detect document type and appropriate extraction schema"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def detect_form_type(self, sample_image_base64: str, description: str = None) -> SchemaDetectionResponse:
        """Analyze a sample image to detect form type and suggest schema"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(sample_image_base64)
            image = Image.open(BytesIO(image_data))
            
            # Build prompt
            prompt = self._build_detection_prompt(description)
            
            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{sample_image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.1
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Create response
            schema = ExtractionSchema(
                name=result["detected_type"],
                description=result.get("description", ""),
                fields=result["fields"],
                required_fields=result.get("required_fields", [])
            )
            
            return SchemaDetectionResponse(
                detected_type=result["detected_type"],
                confidence=result.get("confidence", 0.9),
                suggested_schema=schema,
                sample_extraction=result.get("sample_extraction", {})
            )
            
        except Exception as e:
            logger.error(f"Error detecting schema: {str(e)}")
            # Return a generic form schema as fallback
            return self._get_fallback_schema()
    
    def _build_detection_prompt(self, description: str = None) -> str:
        """Build the prompt for schema detection"""
        base_prompt = """
        Analyze this document image and:
        1. Identify the document type (e.g., invoice, receipt, application form, report, etc.)
        2. List all visible fields and their data types
        3. Determine which fields are required vs optional
        4. Provide a sample extraction of visible data
        
        Return the analysis as JSON with this structure:
        {
            "detected_type": "document type name",
            "description": "brief description of the document",
            "confidence": 0.95,
            "fields": {
                "field_name": {
                    "type": "string|number|date|boolean|array",
                    "description": "what this field contains"
                }
            },
            "required_fields": ["field1", "field2"],
            "sample_extraction": {
                "field_name": "extracted value"
            }
        }
        """
        
        if description:
            base_prompt += f"\n\nAdditional context: {description}"
            
        return base_prompt
    
    def _get_fallback_schema(self) -> SchemaDetectionResponse:
        """Return a generic fallback schema"""
        schema = ExtractionSchema(
            name="Generic Document",
            description="Generic document schema",
            fields={
                "text_content": {"type": "string", "description": "Full text content"},
                "date": {"type": "date", "description": "Document date"},
                "title": {"type": "string", "description": "Document title"}
            },
            required_fields=[]
        )
        
        return SchemaDetectionResponse(
            detected_type="generic",
            confidence=0.5,
            suggested_schema=schema,
            sample_extraction={}
        )