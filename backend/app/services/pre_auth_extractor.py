"""
Gemini-based extractor for pre-authorization medical fields.
Given OCR text (and optionally page images) from a clinical document,
returns a MedicalExtract with the fields needed to fill a pre-auth form.
"""
import json
import logging
from typing import List, Optional
from PIL import Image

import google.generativeai as genai

from app.config import settings
from app.models.pre_auth import MedicalExtract
from app.services.llm import GeminiExtractor   # reuse retry + clean helpers

logger = logging.getLogger(__name__)


_PROMPT_TEMPLATE = """You are a medical data extraction assistant for a hospital pre-authorization (cashless hospitalization) system.

Extract ONLY the following fields from the clinical document text below and return a single valid JSON object.

Document Text:
{text}

Return ONLY this JSON structure (use null for any field not found):
{{
  "doctor_name": "string or null",
  "doctor_contact": "string or null",
  "presenting_complaints": "string or null (chief complaints / reason for admission)",
  "duration_of_illness": "string or null (e.g. '2 days', '1 week')",
  "date_of_first_consultation": "YYYY-MM-DD or null",
  "provisional_diagnosis": "string or null (primary diagnosis text)",
  "icd10_diagnosis_code": "string or null (ICD-10-CM code — extract if printed, otherwise infer from diagnosis)",
  "clinical_findings": "string or null (examination findings, vitals, lab highlights)",
  "line_of_treatment": "string or null (Medical Management / Surgical Management / Intensive Care / Investigation)",
  "surgery_name": "string or null (name of proposed surgery/procedure if any)",
  "icd10_pcs_code": "string or null (ICD-10-PCS procedure code if applicable)",
  "past_history": "string or null (significant past medical history)"
}}

Rules:
- Extract ICD-10 diagnosis code if printed; otherwise infer from diagnosis text (e.g. Acute Appendicitis → K35.80)
- Extract ICD-10 PCS code if printed; otherwise infer from the surgery name (e.g. Laparoscopic Appendectomy → 0DTJ4ZZ)
- Do NOT guess doctor contact if not present
- Return ONLY the JSON object, no markdown, no explanation
"""

_MULTIMODAL_PROMPT_TEMPLATE = """You are a medical data extraction assistant for a hospital pre-authorization (cashless hospitalization) system.

You will receive OCR text AND page images from a clinical document.
Use images as the primary source when OCR text is noisy or incomplete.

OCR Text:
{text}

Return ONLY this JSON structure (use null for any field not found):
{{
  "doctor_name": "string or null",
  "doctor_contact": "string or null",
  "presenting_complaints": "string or null",
  "duration_of_illness": "string or null",
  "date_of_first_consultation": "YYYY-MM-DD or null",
  "provisional_diagnosis": "string or null",
  "icd10_diagnosis_code": "string or null",
  "clinical_findings": "string or null",
  "line_of_treatment": "string or null",
  "surgery_name": "string or null",
  "icd10_pcs_code": "string or null",
  "past_history": "string or null"
}}

Rules:
- Extract ICD-10 diagnosis code if printed; otherwise infer from diagnosis text
- Extract ICD-10 PCS code if printed; otherwise infer from surgery name
- Return ONLY the JSON object, no markdown, no explanation
"""


async def extract_medical_for_preauth(
    text: str,
    page_images: Optional[List[Image.Image]] = None,
) -> MedicalExtract:
    """
    Run Gemini over the OCR text (+ optional page images) and return
    the pre-auth medical fields as a MedicalExtract instance.
    """
    # Reuse GeminiExtractor's retry + clean helpers
    extractor = GeminiExtractor()

    if page_images:
        prompt = _MULTIMODAL_PROMPT_TEMPLATE.format(text=text)
        content = [prompt, *page_images]
    else:
        prompt = _PROMPT_TEMPLATE.format(text=text)
        content = prompt

    response_text = await extractor._call_gemini_with_retry(content)
    logger.info(f"Pre-auth extract Gemini response ({len(response_text)} chars)")

    cleaned = extractor._clean_json_response(response_text)
    data = json.loads(cleaned)

    extract = MedicalExtract(**{k: v for k, v in data.items() if k in MedicalExtract.model_fields})
    logger.info(f"Pre-auth extract done: diagnosis={extract.provisional_diagnosis!r}")
    return extract
