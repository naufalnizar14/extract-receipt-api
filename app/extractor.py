"""
Azure OpenAI GPT-4.1-mini document extractor.
Reusable for any document type — swap the prompt and schema, same client.
"""

import base64
import json
import logging
import os
from typing import Any

import fitz  # pymupdf
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://arth-gpt-4o-mini.openai.azure.com")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=AZURE_OPENAI_API_VERSION,
)


def _image_to_block(file_bytes: bytes, media_type: str) -> dict:
    b64 = base64.standard_b64encode(file_bytes).decode()
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{b64}"},
    }


def _compress_image(file_bytes: bytes, max_mb: float = 19.0) -> bytes:
    """Compress image if over size limit (Azure OpenAI: 20MB per request)."""
    if len(file_bytes) / (1024 * 1024) <= max_mb:
        return file_bytes

    from io import BytesIO
    from PIL import Image

    img = Image.open(BytesIO(file_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    quality = 85
    while quality > 20:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        compressed = buf.getvalue()
        if len(compressed) / (1024 * 1024) <= max_mb:
            logger.info(f"Compressed image to {len(compressed)/(1024*1024):.2f}MB at quality {quality}")
            return compressed
        quality -= 5

    raise ValueError(f"Cannot compress image below {max_mb}MB")


def _file_to_image_blocks(file_path: str, content_type: str) -> list[dict]:
    """Convert file to list of image blocks for the OpenAI messages API."""
    if content_type == "application/pdf":
        doc = fitz.open(file_path)
        blocks = []
        for page_num, page in enumerate(doc):
            # 150 DPI is sufficient for text extraction, keeps token count low
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            blocks.append(_image_to_block(img_bytes, "image/jpeg"))
            logger.info(f"PDF page {page_num + 1}/{len(doc)} converted to image")
        doc.close()
        return blocks

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    file_bytes = _compress_image(file_bytes)
    media_type = "image/png" if content_type == "image/png" else "image/jpeg"
    return [_image_to_block(file_bytes, media_type)]


def extract_document(
    file_path: str,
    content_type: str,
    schema_name: str,
    schema: dict,
    system_prompt: str,
) -> dict[str, Any]:
    """
    Extract structured data from any document using GPT-4.1-mini vision.

    Args:
        file_path: Path to the uploaded file
        content_type: MIME type (image/jpeg, image/png, application/pdf)
        schema_name: Name for the JSON schema (e.g. "extract_receipt")
        schema: JSON Schema dict defining the expected output structure
        system_prompt: Extraction instructions specific to the document type

    Returns:
        Parsed dict matching the provided schema
    """
    image_blocks = _file_to_image_blocks(file_path, content_type)

    logger.info(f"Sending {len(image_blocks)} image block(s) to {AZURE_OPENAI_DEPLOYMENT}")

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": schema,
                "strict": True,
            },
        },
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    *image_blocks,
                    {"type": "text", "text": "Extract all information from this document."},
                ],
            },
        ],
        max_tokens=2048,
    )

    usage = response.usage
    logger.info(f"Tokens used — prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}")

    raw_content = response.choices[0].message.content
    return json.loads(raw_content)
