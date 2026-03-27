import io
import logging
from typing import List

import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.services.ocr_strategies.image_based import PaddleImageOCR, TesseractOCR
from app.services.ocr_strategies.quality_checker import TextQualityChecker

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract text from PDF documents using multiple methods"""
    _tesseract_ocr = TesseractOCR()

    @staticmethod
    def _score_text(text: str) -> float:
        """Score extracted text so we can prefer the strongest result."""
        if not text or not text.strip():
            return 0.0
        return TextQualityChecker.get_quality_score(text.strip())
    
    @staticmethod
    def extract_with_pdfplumber(pdf_bytes: bytes) -> str:
        """Extract text using pdfplumber (good for text-based PDFs)"""
        try:
            text_parts = []
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return ""
    
    @staticmethod
    def extract_with_pymupdf(pdf_bytes: bytes) -> str:
        """Extract embedded text using PyMuPDF."""
        try:
            text_parts = []
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text = page.get_text()
                if text:
                    text_parts.append(text)
            
            pdf_document.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ""

    @staticmethod
    def _preprocess_image(image: Image.Image) -> Image.Image:
        """Improve OCR quality before sending the image to Tesseract."""
        image = image.convert("L")
        image = ImageOps.autocontrast(image)

        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(2.2)

        sharpness = ImageEnhance.Sharpness(image)
        image = sharpness.enhance(1.8)

        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    @classmethod
    def _build_ocr_variants(cls, image: Image.Image) -> list[Image.Image]:
        """Create a few OCR-friendly variants and let quality scoring pick the winner."""
        base = cls._preprocess_image(image)
        threshold = base.point(lambda pixel: 255 if pixel > 160 else 0)
        enlarged = base.resize((base.width * 2, base.height * 2), Image.Resampling.LANCZOS)
        return [base, threshold, enlarged]

    @staticmethod
    def _crop_to_content_region(image: Image.Image) -> Image.Image:
        """
        Crop large empty margins/background before OCR.

        This helps photographed reports where the actual paper occupies only
        part of the rendered PDF page.
        """
        grayscale = image.convert("L")
        mask = grayscale.point(lambda pixel: 255 if pixel < 215 else 0)
        bbox = mask.getbbox()

        if not bbox:
            return image

        left, top, right, bottom = bbox
        padding = 30
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(image.width, right + padding)
        bottom = min(image.height, bottom + padding)

        cropped = image.crop((left, top, right, bottom))

        # Keep the original when the crop is too small to be meaningful.
        if cropped.width < image.width * 0.4 or cropped.height < image.height * 0.4:
            return image

        return cropped

    @classmethod
    def _extract_best_ocr_text_from_image(cls, image: Image.Image) -> str:
        """Try a small set of OCR configs and keep the best-looking output."""
        best_text = ""
        best_score = 0.0

        candidates = [image]
        cropped_image = cls._crop_to_content_region(image)
        if cropped_image.size != image.size:
            candidates.append(cropped_image)

        for candidate in candidates:
            if PaddleImageOCR.is_available():
                try:
                    paddle_text = PaddleImageOCR.extract_from_image(candidate)
                    paddle_score = cls._score_text(paddle_text)
                    if paddle_score > best_score:
                        best_text = paddle_text
                        best_score = paddle_score
                except Exception as e:
                    logger.warning(f"PaddleOCR failed on candidate image: {e}")

            for variant in cls._build_ocr_variants(candidate):
                for psm in ("6", "11", "4"):
                    try:
                        text = cls._tesseract_ocr.extract_from_image(variant, psm=psm)
                    except Exception as e:
                        logger.warning(f"Tesseract page OCR failed for psm={psm}: {e}")
                        continue

                    score = cls._score_text(text)
                    if score > best_score:
                        best_text = text
                        best_score = score

        return best_text

    @classmethod
    def extract_with_tesseract(cls, pdf_bytes: bytes, dpi: int = 300) -> str:
        """Run OCR on rendered PDF pages for scanned/image-based documents."""
        try:
            scale = dpi / 72.0
            matrix = fitz.Matrix(scale, scale)
            text_parts = []
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            try:
                for page_num in range(pdf_document.page_count):
                    page = pdf_document[page_num]
                    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    page_text = cls._extract_best_ocr_text_from_image(image)

                    if page_text:
                        text_parts.append(page_text)
            finally:
                pdf_document.close()

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Tesseract OCR extraction failed: {e}")
            return ""
    
    @classmethod
    def extract_text(cls, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF using multiple methods.
        Try embedded-text extraction first, then image OCR as a final fallback.
        """
        pdfplumber_text = cls.extract_with_pdfplumber(pdf_bytes)
        pymupdf_text = ""
        text = pdfplumber_text

        # Try a second embedded-text extractor and keep the better result
        if not pdfplumber_text or len(pdfplumber_text.strip()) < 50:
            logger.info("pdfplumber yielded minimal text, trying PyMuPDF")
            pymupdf_text = cls.extract_with_pymupdf(pdf_bytes)
            if cls._score_text(pymupdf_text) > cls._score_text(text):
                text = pymupdf_text

        # Real OCR fallback for scanned/image-heavy PDFs
        if not text or len(text.strip()) < 50 or not TextQualityChecker.is_good_quality(text, min_length=80):
            logger.info("Embedded text extraction yielded minimal text, trying Tesseract OCR")
            ocr_text = cls.extract_with_tesseract(pdf_bytes)
            if cls._score_text(ocr_text) > cls._score_text(text):
                text = ocr_text
        
        if not text or len(text.strip()) < 10:
            raise ValueError("Could not extract meaningful text from PDF")
        
        return text.strip()

async def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Main entry point for PDF text extraction.
    
    Args:
        pdf_bytes: PDF file as bytes
        
    Returns:
        Extracted text from PDF
        
    Raises:
        ValueError: If text extraction fails
    """
    try:
        extractor = PDFExtractor()
        text = extractor.extract_text(pdf_bytes)
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def render_pdf_pages(pdf_bytes: bytes, dpi: int = 200, max_pages: int = 5) -> List[Image.Image]:
    """
    Render PDF pages to PIL images for multimodal extraction.

    Args:
        pdf_bytes: PDF file as bytes
        dpi: Render resolution
        max_pages: Safety limit to avoid sending too many pages upstream

    Returns:
        List of rendered PIL images
    """
    images: List[Image.Image] = []
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        for page_num in range(min(pdf_document.page_count, max_pages)):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            images.append(image.copy())
            image.close()
    finally:
        pdf_document.close()

    return images
