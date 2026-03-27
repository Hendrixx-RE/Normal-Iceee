"""
OCR Strategy — PaddleOCR engine and text quality checker.
"""
from .image_based import PaddleOCREngine
from .quality_checker import TextQualityChecker

__all__ = ["PaddleOCREngine", "TextQualityChecker"]
