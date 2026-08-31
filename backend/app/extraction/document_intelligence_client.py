# Wrapper around Azure AI Document Intelligence (Layout model) — whole-page OCR and single-image OCR.
#
# Only ever called for the fallback path: scanned/image-only PDF pages, or embedded
# images pulled out by image_extractor.py. Native text-layer extraction (document_extraction.py)
# never touches this module.

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from app.config import settings


class DocumentIntelligenceNotConfigured(Exception):
    """Raised when OCR is needed but no Azure Document Intelligence resource is configured."""


def _get_client() -> DocumentIntelligenceClient:
    if not settings.doc_intelligence_endpoint or not settings.doc_intelligence_key:
        raise DocumentIntelligenceNotConfigured(
            "DOC_INTELLIGENCE_ENDPOINT / DOC_INTELLIGENCE_KEY are not set — OCR fallback is unavailable"
        )
    return DocumentIntelligenceClient(
        endpoint=settings.doc_intelligence_endpoint,
        credential=AzureKeyCredential(settings.doc_intelligence_key),
    )


def ocr_document(content: bytes) -> str:
    """Whole-document OCR via the Layout model. Used for scanned/image-only PDFs."""
    client = _get_client()
    try:
        poller = client.begin_analyze_document(
            "prebuilt-layout", AnalyzeDocumentRequest(bytes_source=content)
        )
        result = poller.result()
    except HttpResponseError as exc:
        raise RuntimeError(f"Document Intelligence OCR failed: {exc.message}") from exc
    return result.content or ""


def ocr_image(content: bytes) -> str:
    """Single embedded-image OCR — used for tables-as-images inside otherwise-native documents."""
    return ocr_document(content)
