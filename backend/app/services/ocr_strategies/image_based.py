"""
Image-based OCR using doctr (python-doctr).

doctr is the sole OCR engine. It is lazily initialized on first use
so the application boots quickly even if model weights need downloading.

Only used for image-based (scanned) PDFs — text-based PDFs are handled
natively by PyMuPDF and never reach this engine.
"""
import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class DocTROCREngine:
    """Singleton doctr OCR wrapper with lazy initialization."""

    _instance = None
    _init_error: Optional[Exception] = None

    @classmethod
    def get_instance(cls):
        """Return the doctr predictor, creating it on first call."""
        if cls._instance is not None:
            return cls._instance

        if cls._init_error is not None:
            raise RuntimeError(
                f"doctr failed to initialize previously: {cls._init_error}"
            )

        try:
            from doctr.models import ocr_predictor

            cls._instance = ocr_predictor(
                det_arch="db_resnet50",
                reco_arch="crnn_vgg16_bn",
                pretrained=True,
                assume_straight_pages=True,  # medical docs are always upright — faster
            )
            logger.info("doctr OCR engine initialized successfully")
            return cls._instance
        except Exception as exc:
            cls._init_error = exc
            logger.error(f"doctr initialization failed: {exc}")
            raise RuntimeError(f"doctr initialization failed: {exc}") from exc

    @classmethod
    def is_available(cls) -> bool:
        """Check whether doctr can be initialized."""
        if cls._instance is not None:
            return True
        if cls._init_error is not None:
            return False
        try:
            cls.get_instance()
            return True
        except Exception:
            return False

    @classmethod
    def extract_text(cls, image: Image.Image) -> str:
        """
        Extract text from a PIL Image using doctr.

        Args:
            image: PIL Image (any mode — will be converted to RGB).

        Returns:
            Extracted text as a single string with lines joined by newlines.

        Raises:
            RuntimeError: If doctr is not available.
        """
        predictor = cls.get_instance()

        # doctr expects a list of numpy uint8 arrays (one per page)
        img_array = np.array(image.convert("RGB"), dtype=np.uint8)
        result = predictor([img_array])

        text_lines: list[str] = []
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    line_text = " ".join(
                        word.value for word in line.words if word.value.strip()
                    )
                    if line_text.strip():
                        text_lines.append(line_text.strip())

        return "\n".join(text_lines).strip()


# ---------------------------------------------------------------------------
# Backwards-compatible alias — ocr.py and main.py import PaddleOCREngine
# ---------------------------------------------------------------------------
PaddleOCREngine = DocTROCREngine
