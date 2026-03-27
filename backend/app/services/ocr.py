"""
PDF text extraction pipeline.

Pipeline:
  PDF bytes → render pages as images (PyMuPDF) → PaddleOCR → joined text

If PaddleOCR produces low-quality text, the caller can fall back to
sending the rendered page images directly to Gemini multimodal.
"""
import io
import logging
from typing import List

import fitz  # PyMuPDF – used ONLY for rendering pages to images
from PIL import Image

from app.services.ocr_strategies.image_based import PaddleOCREngine
from app.services.ocr_strategies.quality_checker import TextQualityChecker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def render_pdf_pages(
    pdf_bytes: bytes,
    dpi: int = 300,
    max_pages: int = 50,
) -> List[Image.Image]:
    """
    Render every page of a PDF to a PIL Image.

    Args:
        pdf_bytes: Raw PDF file content.
        dpi: Resolution for rendering (higher = better OCR, slower).
        max_pages: Safety cap to prevent memory issues on huge documents.

    Returns:
        List of PIL Images (RGB), one per page.

    Raises:
        ValueError: If the PDF cannot be opened or has zero pages.
    """
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Cannot open PDF: {exc}") from exc

    if pdf_document.page_count == 0:
        pdf_document.close()
        raise ValueError("PDF has zero pages")

    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    images: List[Image.Image] = []

    try:
        page_count = min(pdf_document.page_count, max_pages)
        for page_num in range(page_count):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
            images.append(img)
        logger.info(f"Rendered {len(images)}/{pdf_document.page_count} PDF pages at {dpi} DPI")
    finally:
        pdf_document.close()

    return images


# ---------------------------------------------------------------------------
# PaddleOCR text extraction from page images
# ---------------------------------------------------------------------------

def ocr_images(images: List[Image.Image]) -> str:
    """
    Run PaddleOCR on a list of page images and join the results.

    Args:
        images: List of PIL Images (one per PDF page).

    Returns:
        Combined extracted text with page breaks between pages.

    Raises:
        RuntimeError: If PaddleOCR is not available.
    """
    page_texts: List[str] = []

    for idx, img in enumerate(images):
        try:
            page_text = PaddleOCREngine.extract_text(img)
            if page_text:
                page_texts.append(page_text)
                logger.info(f"Page {idx + 1}: extracted {len(page_text)} chars")
            else:
                logger.warning(f"Page {idx + 1}: PaddleOCR returned empty text")
        except Exception as exc:
            logger.error(f"Page {idx + 1}: PaddleOCR failed — {exc}")
            # Continue with remaining pages instead of aborting entirely
            continue

    return "\n\n".join(page_texts).strip()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, List[Image.Image]]:
    """
    Main entry point for PDF text extraction.

    Returns both the extracted text AND the rendered page images so the
    caller can decide whether to use multimodal Gemini fallback.

    Pipeline:
        1. Render PDF pages to images (PyMuPDF).
        2. Run PaddleOCR on every page image.
        3. Return (text, images).

    Args:
        pdf_bytes: Raw PDF bytes.

    Returns:
        Tuple of (extracted_text, page_images).

    Raises:
        ValueError: If the PDF cannot be rendered at all.
    """
    # Step 1 — Render pages
    page_images = render_pdf_pages(pdf_bytes)

    # Step 2 — PaddleOCR
    extracted_text = ""
    try:
        extracted_text = ocr_images(page_images)
        logger.info(f"PaddleOCR total extraction: {len(extracted_text)} chars")
    except RuntimeError as exc:
        logger.error(f"PaddleOCR unavailable: {exc}")
        # extracted_text stays empty; caller will use multimodal fallback
    except Exception as exc:
        logger.error(f"PaddleOCR extraction error: {exc}")

    # Step 3 — Quality assessment
    if extracted_text:
        score = TextQualityChecker.get_quality_score(extracted_text)
        logger.info(f"OCR text quality score: {score:.1f}/100")
    else:
        logger.warning("No text extracted from PDF — multimodal fallback will be needed")

    return extracted_text, page_images
