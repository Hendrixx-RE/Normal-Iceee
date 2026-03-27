from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import ProcessResponse, HealthResponse, LabReportData, PrescriptionData
from app.services.ocr import extract_pdf_text
from app.services.llm import (
    extract_structured_data,
    extract_structured_data_batch,
    merge_lab_report_data,
    merge_prescription_data,
)
from app.services.fhir_mapper import generate_fhir_bundle
from app.services.document_splitter import split_document
from app.services.ocr_strategies.quality_checker import TextQualityChecker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
BATCH_PROCESSING_THRESHOLD = 20000  # chars — above this we split + batch
OCR_QUALITY_GOOD = 75.0             # score at which OCR text is trusted alone
OCR_QUALITY_USABLE = 40.0           # below this we ignore OCR text entirely


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Healthcare FHIR API is running",
        gemini_configured=bool(settings.GEMINI_API_KEY),
    )


@router.post("/process-pdf", response_model=ProcessResponse)
async def process_pdf(
    file: UploadFile = File(..., description="PDF file (lab report or prescription)"),
):
    """
    Process a clinical PDF and generate a FHIR R4 bundle.

    Pipeline:
        1. Validate upload.
        2. Render PDF pages → PaddleOCR text extraction.
        3. Quality-gate the OCR output:
           a. Good quality  → send text only to Gemini.
           b. Mediocre      → send text + page images (multimodal).
           c. Very poor/empty → send page images only (multimodal).
        4. For large documents, split into sections and batch process.
        5. Generate FHIR bundle from structured data.
    """
    try:
        # ------------------------------------------------------------------
        # 1. Validate upload
        # ------------------------------------------------------------------
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        pdf_bytes = await file.read()

        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        if len(pdf_bytes) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE // (1024 * 1024)}MB limit",
            )

        logger.info(f"Processing PDF: {file.filename} ({len(pdf_bytes)} bytes)")

        # ------------------------------------------------------------------
        # 2. OCR — render pages + PaddleOCR
        # ------------------------------------------------------------------
        try:
            extracted_text, page_images = await extract_pdf_text(pdf_bytes)
        except ValueError as exc:
            logger.error(f"PDF rendering failed: {exc}")
            return ProcessResponse(
                success=False,
                message="Failed to render PDF pages for OCR",
                error=str(exc),
            )
        except Exception as exc:
            logger.error(f"OCR pipeline error: {exc}", exc_info=True)
            return ProcessResponse(
                success=False,
                message="Unexpected error during OCR extraction",
                error=str(exc),
            )

        # ------------------------------------------------------------------
        # 3. Quality gate — decide multimodal strategy
        # ------------------------------------------------------------------
        quality_score = TextQualityChecker.get_quality_score(extracted_text) if extracted_text else 0.0
        logger.info(f"OCR quality score: {quality_score:.1f}/100 | text length: {len(extracted_text)} chars")

        # Decide what to send to Gemini
        if quality_score >= OCR_QUALITY_GOOD:
            # Good OCR → text-only (faster, cheaper)
            send_images = None
            logger.info("Strategy: text-only (good OCR quality)")
        elif quality_score >= OCR_QUALITY_USABLE:
            # Mediocre OCR → send text + images so Gemini can cross-reference
            send_images = page_images
            logger.info("Strategy: text + images (mediocre OCR quality)")
        else:
            # Bad/empty OCR → send images only, let Gemini read the document
            send_images = page_images
            if not extracted_text:
                extracted_text = ""
            logger.info("Strategy: images primary (poor/no OCR text)")

        # ------------------------------------------------------------------
        # 4. Structured data extraction via Gemini
        # ------------------------------------------------------------------
        use_batch = len(extracted_text) > BATCH_PROCESSING_THRESHOLD
        sections = []

        if use_batch:
            logger.info(f"Large document ({len(extracted_text)} chars) — batch processing")
            try:
                sections = split_document(extracted_text, strategy="smart")
                logger.info(f"Split into {len(sections)} sections")
            except Exception as exc:
                logger.error(f"Document splitting failed: {exc}")
                return ProcessResponse(
                    success=False,
                    message="Failed to split large document for batch processing",
                    extracted_text=extracted_text,
                    error=str(exc),
                )

            try:
                results = await extract_structured_data_batch(sections, document_type="auto")
                if not results:
                    raise ValueError("No structured data extracted from any section")

                first = results[0]
                if isinstance(first, LabReportData):
                    structured_data = merge_lab_report_data(
                        [r for r in results if isinstance(r, LabReportData)]
                    )
                    document_type = "lab_report"
                else:
                    structured_data = merge_prescription_data(
                        [r for r in results if isinstance(r, PrescriptionData)]
                    )
                    document_type = "prescription"

            except Exception as exc:
                logger.error(f"Batch LLM extraction failed: {exc}")
                return ProcessResponse(
                    success=False,
                    message="Failed to extract structured data (batch)",
                    extracted_text=extracted_text,
                    error=str(exc),
                )
        else:
            # Standard single-pass extraction
            try:
                structured_data = await extract_structured_data(
                    extracted_text,
                    document_type="auto",
                    page_images=send_images,
                )
                document_type = structured_data.document_type
                logger.info(f"Extracted structured data: {document_type}")
            except Exception as exc:
                logger.error(f"LLM extraction failed: {exc}")
                return ProcessResponse(
                    success=False,
                    message="Failed to extract structured data from document",
                    extracted_text=extracted_text,
                    error=str(exc),
                )

        # ------------------------------------------------------------------
        # 5. Generate FHIR R4 Bundle
        # ------------------------------------------------------------------
        try:
            fhir_bundle = await generate_fhir_bundle(structured_data)
            logger.info(f"FHIR bundle generated with {len(fhir_bundle.get('entry', []))} resources")
        except Exception as exc:
            logger.error(f"FHIR generation failed: {exc}")
            return ProcessResponse(
                success=False,
                message="Failed to generate FHIR bundle",
                extracted_text=extracted_text,
                error=str(exc),
            )

        # ------------------------------------------------------------------
        # 6. Success
        # ------------------------------------------------------------------
        message = f"Successfully processed {document_type}"
        if use_batch:
            message += f" (batch: {len(sections)} sections)"

        return ProcessResponse(
            success=True,
            message=message,
            extracted_text=extracted_text,
            fhir_bundle=fhir_bundle,
            document_type=document_type,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return ProcessResponse(
            success=False,
            message="An unexpected error occurred while processing the PDF",
            error=str(exc),
        )
