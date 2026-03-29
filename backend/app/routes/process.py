import gc

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import ProcessResponse, HealthResponse, LabReportData, PrescriptionData
from app.services.ocr import extract_pdf_text, render_gemini_thumbnails
from app.services.file_extractor import get_file_type, is_supported, extract_non_pdf
from app.services.llm import (
    extract_structured_data,
    extract_structured_data_batch,
    merge_lab_report_data,
    merge_prescription_data,
)
from app.services.fhir_mapper import generate_fhir_bundle
from app.services.document_splitter import split_document
from app.services.ocr_strategies.quality_checker import TextQualityChecker
from app.services.patient_store import patient_store
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
BATCH_PROCESSING_THRESHOLD = 20000  # chars — above this we split + batch
OCR_QUALITY_GOOD = 75.0             # text-only to Gemini
OCR_QUALITY_USABLE = 40.0           # below this → images-only to Gemini


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
    file: UploadFile = File(..., description="Clinical document — PDF, image, Word, Excel, or CSV"),
):
    """
    Process a clinical document and generate a FHIR R4 bundle.

    Supported formats: PDF, JPG/PNG/WEBP/TIFF (images), DOCX (Word), XLSX/XLS (Excel), CSV.

    Pipeline:
        1. Validate upload & detect file type.
        2. Extract text (PDF → PyMuPDF+doctr, image → doctr OCR + Gemini fallback,
           Word/Excel/CSV → native parsing).
        3. Quality-gate (PDF only) — render thumbnails if OCR is poor.
        4. Extract structured data via Gemini.
        5. Generate FHIR bundle.
        6. Persist patient record.
    """
    try:
        # ------------------------------------------------------------------
        # 1. Validate upload
        # ------------------------------------------------------------------
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if not is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported file type. Accepted: PDF, JPG, PNG, WEBP, TIFF, "
                    "DOCX, XLSX, XLS, CSV"
                ),
            )

        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        if len(file_bytes) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE // (1024 * 1024)}MB limit",
            )

        file_type = get_file_type(file.filename)
        logger.info(f"Processing {file_type.upper()}: {file.filename} ({len(file_bytes)} bytes)")

        # ------------------------------------------------------------------
        # 2. Text / image extraction (branched by file type)
        # ------------------------------------------------------------------
        extracted_text = ""
        send_images = None

        if file_type == 'pdf':
            try:
                extracted_text, pdf_bytes_ref = await extract_pdf_text(file_bytes)
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

            # ----------------------------------------------------------------
            # 3. Quality gate (PDF only) — decide if we need Gemini multimodal
            # ----------------------------------------------------------------
            quality_score = TextQualityChecker.get_quality_score(extracted_text) if extracted_text else 0.0
            logger.info(f"OCR quality: {quality_score:.1f}/100 | {len(extracted_text)} chars")

            if quality_score >= OCR_QUALITY_GOOD:
                logger.info("Strategy: text-only (good OCR)")
            elif quality_score >= OCR_QUALITY_USABLE:
                logger.info("Strategy: text + thumbnails (mediocre OCR)")
                send_images = render_gemini_thumbnails(pdf_bytes_ref)
            else:
                logger.info("Strategy: thumbnails primary (poor/no OCR)")
                send_images = render_gemini_thumbnails(pdf_bytes_ref)

            del pdf_bytes_ref
            gc.collect()

        else:
            # Non-PDF: image, docx, excel, csv
            try:
                extracted_text, send_images = extract_non_pdf(file_bytes, file.filename)
            except Exception as exc:
                logger.error(f"File extraction failed: {exc}", exc_info=True)
                return ProcessResponse(
                    success=False,
                    message=f"Failed to extract content from {file_type.upper()} file",
                    error=str(exc),
                )
            # No quality gate for non-PDF — trust what we got
            logger.info(f"Non-PDF extraction: {len(extracted_text)} chars, images={send_images is not None}")

        # ------------------------------------------------------------------
        # 4. Structured data extraction via Gemini
        # ------------------------------------------------------------------
        use_batch = len(extracted_text) > BATCH_PROCESSING_THRESHOLD
        sections = []

        if use_batch:
            logger.info(f"Large document ({len(extracted_text)} chars) — batch processing")

            # Free thumbnails before batch — batch uses text only
            if send_images:
                for img in send_images:
                    img.close()
                del send_images
                send_images = None
                gc.collect()

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
            finally:
                # Free thumbnail images after Gemini call
                if send_images:
                    for img in send_images:
                        img.close()
                    del send_images
                    gc.collect()

        # ------------------------------------------------------------------
        # 5. Generate FHIR R4 Bundle + billing completeness check
        # ------------------------------------------------------------------
        try:
            fhir_bundle, billing_flags = await generate_fhir_bundle(structured_data)
            critical = sum(1 for f in billing_flags if f.severity == "critical")
            warning  = sum(1 for f in billing_flags if f.severity == "warning")
            logger.info(
                f"FHIR bundle: {len(fhir_bundle.get('entry', []))} resources | "
                f"billing flags: {critical} critical, {warning} warning"
            )
        except Exception as exc:
            logger.error(f"FHIR generation failed: {exc}")
            return ProcessResponse(
                success=False,
                message="Failed to generate FHIR bundle",
                extracted_text=extracted_text,
                error=str(exc),
            )

        # ------------------------------------------------------------------
        # 6. Persist to Supabase
        # ------------------------------------------------------------------
        patient_id     = None
        patient_action = None
        try:
            patient_id, patient_action = patient_store.save_patient(
                structured_data=structured_data,
                fhir_bundle=fhir_bundle,
                billing_flags=billing_flags,
                filename=file.filename or "unknown",
                extracted_text=extracted_text,
            )
            logger.info(f"Patient record {patient_action}: {patient_id}")
        except Exception as exc:
            # Storage failure must never block the main response
            logger.error(f"Patient store save failed (non-fatal): {exc}")

        # ------------------------------------------------------------------
        # 7. Success
        # ------------------------------------------------------------------
        message = f"Successfully processed {document_type} ({file_type.upper()})"
        if use_batch:
            message += f" (batch: {len(sections)} sections)"

        return ProcessResponse(
            success=True,
            message=message,
            extracted_text=extracted_text,
            fhir_bundle=fhir_bundle,
            document_type=document_type,
            billing_flags=billing_flags,
            patient_id=patient_id,
            patient_action=patient_action,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return ProcessResponse(
            success=False,
            message="An unexpected error occurred while processing the document",
            error=str(exc),
        )
