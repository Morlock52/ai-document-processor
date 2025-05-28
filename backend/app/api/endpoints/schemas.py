from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.document import (
    ExtractionSchema,
    SchemaDetectionRequest,
    SchemaDetectionResponse
)
from app.services.schema_detector import SchemaDetector

router = APIRouter()

# Predefined schemas
PREDEFINED_SCHEMAS = {
    "invoice": {
        "name": "Invoice",
        "description": "Standard invoice data extraction",
        "fields": {
            "invoice_number": {"type": "string", "description": "Invoice number"},
            "invoice_date": {"type": "date", "description": "Invoice date"},
            "due_date": {"type": "date", "description": "Payment due date"},
            "vendor_name": {"type": "string", "description": "Vendor/supplier name"},
            "vendor_address": {"type": "string", "description": "Vendor address"},
            "customer_name": {"type": "string", "description": "Customer name"},
            "customer_address": {"type": "string", "description": "Customer address"},
            "subtotal": {"type": "number", "description": "Subtotal amount"},
            "tax": {"type": "number", "description": "Tax amount"},
            "total": {"type": "number", "description": "Total amount"},
            "line_items": {"type": "array", "description": "Invoice line items"}
        },
        "required_fields": ["invoice_number", "invoice_date", "vendor_name", "total"]
    },
    "receipt": {
        "name": "Receipt",
        "description": "Receipt data extraction",
        "fields": {
            "store_name": {"type": "string", "description": "Store name"},
            "store_address": {"type": "string", "description": "Store address"},
            "transaction_date": {"type": "datetime", "description": "Transaction date and time"},
            "receipt_number": {"type": "string", "description": "Receipt number"},
            "items": {"type": "array", "description": "Purchased items"},
            "subtotal": {"type": "number", "description": "Subtotal"},
            "tax": {"type": "number", "description": "Tax amount"},
            "total": {"type": "number", "description": "Total amount"},
            "payment_method": {"type": "string", "description": "Payment method"}
        },
        "required_fields": ["store_name", "transaction_date", "total"]
    },
    "form": {
        "name": "Generic Form",
        "description": "Generic form data extraction",
        "fields": {
            "form_title": {"type": "string", "description": "Form title"},
            "form_number": {"type": "string", "description": "Form number"},
            "date": {"type": "date", "description": "Date"},
            "name": {"type": "string", "description": "Name"},
            "address": {"type": "string", "description": "Address"},
            "phone": {"type": "string", "description": "Phone number"},
            "email": {"type": "string", "description": "Email address"},
            "signature": {"type": "boolean", "description": "Signature present"}
        },
        "required_fields": ["name"]
    }
}

@router.get("/", response_model=List[ExtractionSchema])
async def list_schemas():
    """List all available extraction schemas"""
    return [ExtractionSchema(**schema) for schema in PREDEFINED_SCHEMAS.values()]

@router.get("/{schema_type}", response_model=ExtractionSchema)
async def get_schema(schema_type: str):
    """Get a specific extraction schema"""
    if schema_type not in PREDEFINED_SCHEMAS:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    return ExtractionSchema(**PREDEFINED_SCHEMAS[schema_type])

@router.post("/detect", response_model=SchemaDetectionResponse)
async def detect_schema(request: SchemaDetectionRequest):
    """Detect the appropriate schema for a document sample"""
    detector = SchemaDetector()
    result = await detector.detect_form_type(
        request.sample_image_base64,
        request.description
    )
    
    return result

@router.post("/custom", response_model=ExtractionSchema)
async def create_custom_schema(schema: ExtractionSchema):
    """Create a custom extraction schema (in-memory only for now)"""
    # In a production system, this would save to a database
    return schema