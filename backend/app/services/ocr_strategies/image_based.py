"""
Image-based OCR strategies.

PaddleOCR is preferred for dense scanned/photo documents. Tesseract remains
available as a fallback when PaddleOCR is not installed or fails at runtime.
"""
import io
import logging
import os
from typing import Optional

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)


class PaddleImageOCR:
    """PaddleOCR wrapper with lazy loading so the app still boots without it."""

    _ocr_instance = None
    _import_error: Optional[Exception] = None

    @classmethod
    def is_available(cls) -> bool:
        """Return True when PaddleOCR dependencies are importable."""
        if cls._ocr_instance is not None:
            return True

        if cls._import_error is not None:
            return False

        try:
            from paddleocr import PaddleOCR

            cls._ocr_instance = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                show_log=False,
            )
            logger.info("PaddleOCR initialized successfully")
            return True
        except Exception as e:
            cls._import_error = e
            logger.warning(f"PaddleOCR unavailable, falling back to Tesseract: {e}")
            return False

    @classmethod
    def extract_from_image(cls, image: Image.Image) -> str:
        """Extract text from a PIL image with PaddleOCR."""
        if not cls.is_available():
            raise ValueError("PaddleOCR is not available")

        try:
            import numpy as np

            image_array = np.array(image.convert("RGB"))
            result = cls._ocr_instance.ocr(image_array, cls=True)
            text_lines = []

            if not result:
                return ""

            for block in result:
                if not block:
                    continue
                for line in block:
                    if not line or len(line) < 2:
                        continue
                    text = line[1][0] if line[1] else ""
                    if text:
                        text_lines.append(text.strip())

            return "\n".join(text_lines).strip()
        except Exception as e:
            logger.error(f"PaddleOCR image extraction failed: {e}", exc_info=True)
            raise ValueError(f"Failed to extract text with PaddleOCR: {str(e)}")


class TesseractOCR:
    """Tesseract-based OCR fallback for scanned/image PDFs."""

    def __init__(self, tesseract_path: Optional[str] = None):
        import platform

        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = (
                tesseract_path or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """Apply lightweight preprocessing for Tesseract OCR."""
        image = image.convert("L")
        image = ImageOps.autocontrast(image)

        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(2.2)

        sharpness = ImageEnhance.Sharpness(image)
        image = sharpness.enhance(1.8)

        image = image.filter(ImageFilter.MedianFilter(size=3))
        return image

    def extract_from_image(self, image: Image.Image, psm: str = "6") -> str:
        """Extract text from a single PIL image."""
        try:
            processed_image = self.preprocess_image(image)
            return pytesseract.image_to_string(
                processed_image,
                config=f"--oem 3 --psm {psm}"
            ).strip()
        except Exception as e:
            logger.error(f"Tesseract image OCR failed: {e}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")
