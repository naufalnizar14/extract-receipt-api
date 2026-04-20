import logging
import os
import tempfile
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.extractor import AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT
from app.models import DocumentResponse, EmailExtraction, EmailResponse, InvoiceExtraction, InvoiceResponse, ReceiptExtraction, ReceiptResponse
from app.prompts import SUPPORTED_DOC_TYPES
from app.utils import extract_any_document, extract_email, extract_invoice, extract_receipt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Extraction API",
    description="AI-powered document extraction using Azure OpenAI GPT-4.1. "
                "Supports receipts, invoices, bank statements, and emails.",
    version="2.0.0",
)

ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/pdf",
]


def _validate_file(file: UploadFile, content: bytes) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {ALLOWED_CONTENT_TYPES}",
        )
    size_mb = len(content) / (1024 * 1024)
    if file.content_type == "application/pdf" and size_mb > 500:
        raise HTTPException(status_code=400, detail=f"PDF too large: {size_mb:.1f}MB (max 500MB)")
    if file.content_type != "application/pdf" and size_mb > 20:
        raise HTTPException(status_code=400, detail=f"Image too large: {size_mb:.1f}MB (max 20MB)")


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Document Extraction API",
        "version": "2.0.0",
        "model": AZURE_OPENAI_DEPLOYMENT,
        "supported_document_types": SUPPORTED_DOC_TYPES,
    }


@app.get("/health")
def health_check():
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    configured = bool(AZURE_OPENAI_ENDPOINT and api_key)
    return {
        "status": "healthy" if configured else "degraded",
        "azure_openai": configured,
        "endpoint": AZURE_OPENAI_ENDPOINT,
        "deployment": AZURE_OPENAI_DEPLOYMENT,
        "error": None if configured else "AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not set",
    }


@app.post("/extract", response_model=ReceiptResponse)
async def extract(
    file: UploadFile = File(...),
    document_type: Literal["receipt", "invoice", "statement", "email"] = "receipt",
):
    """
    Extract structured data from a document.

    - **file**: JPG, PNG, or PDF
    - **document_type**: receipt (default), invoice, statement, or email

    For receipts, returns a fully validated ReceiptResponse.
    For other types, returns a DocumentResponse with the raw extracted fields.
    """
    temp_path = None
    try:
        content = await file.read()
        _validate_file(file, content)

        suffix = os.path.splitext(file.filename or "file")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_path = tmp.name

        logger.info(f"Processing '{file.filename}' as document_type='{document_type}'")

        if document_type == "receipt":
            result = extract_receipt(temp_path, file.content_type)
            if result["success"]:
                return ReceiptResponse(
                    success=True,
                    receipt_data=ReceiptExtraction(**result["receipt_data"]),
                    raw_data=result.get("raw_data"),
                    validation_warnings=result.get("validation_warnings"),
                )
            return ReceiptResponse(success=False, error=result.get("error", "Extraction failed"))

        elif document_type == "invoice":
            result = extract_invoice(temp_path, file.content_type)
            if result["success"]:
                return InvoiceResponse(
                    success=True,
                    invoice_data=InvoiceExtraction(**result["invoice_data"]),
                    raw_data=result.get("raw_data"),
                    validation_warnings=result.get("validation_warnings"),
                )
            return InvoiceResponse(success=False, error=result.get("error", "Extraction failed"))

        elif document_type == "email":
            result = extract_email(temp_path, file.content_type)
            if result["success"]:
                return EmailResponse(
                    success=True,
                    email_data=EmailExtraction(**result["email_data"]),
                    raw_data=result.get("email_data"),
                )
            return EmailResponse(success=False, error=result.get("error", "Extraction failed"))

        else:
            result = extract_any_document(temp_path, file.content_type, document_type)
            if not result["success"]:
                return JSONResponse(content={
                    "success": False,
                    "document_type": document_type,
                    "error": result.get("error", "Extraction failed"),
                })
            return JSONResponse(content={
                "success": True,
                "document_type": document_type,
                "data": result.get("data"),
                "validation_warnings": result.get("validation_warnings"),
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return ReceiptResponse(success=False, error=f"Processing failed: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@app.post("/extract/raw")
async def extract_raw(
    file: UploadFile = File(...),
    document_type: Literal["receipt", "invoice", "statement", "email"] = "receipt",
):
    """
    Returns the raw GPT-4.1-mini JSON output without validation or normalisation.
    Useful for debugging prompts and schemas.
    """
    temp_path = None
    try:
        content = await file.read()
        _validate_file(file, content)

        suffix = os.path.splitext(file.filename or "file")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_path = tmp.name

        from app.extractor import extract_document
        from app.prompts import DOC_TYPE_CONFIG
        system_prompt, schema_name, schema = DOC_TYPE_CONFIG[document_type]
        raw = extract_document(temp_path, file.content_type, schema_name, schema, system_prompt)

        return {"success": True, "document_type": document_type, "raw": raw}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Raw extraction failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
