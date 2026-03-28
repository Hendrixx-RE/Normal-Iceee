"""
Gemini-based extractor for discharge summary and final bill fields.
Given OCR text (and optionally page images) from a discharge document,
returns a DischargeExtract with cost and clinical fields.
"""
import json
import logging
from typing import List, Optional
from PIL import Image

from app.models.discharge import DischargeExtract
from app.services.llm import GeminiExtractor

logger = logging.getLogger(__name__)


_PROMPT_TEMPLATE = """You are a medical data extraction assistant for a hospital cashless settlement system.

Extract ONLY the following fields from the discharge summary / final hospital bill text below and return a single valid JSON object.

Document Text:
{text}

Return ONLY this JSON structure (use null for any field not found):
{{
  "discharge_date": "YYYY-MM-DD or null",
  "final_diagnosis": "string or null (primary confirmed diagnosis at discharge)",
  "final_icd10_codes": "string or null (ICD-10-CM code — extract if printed, otherwise infer from final diagnosis)",
  "procedure_codes": "string or null (ICD-10 PCS or CPT codes for procedures performed — extract if printed, otherwise infer from procedures/surgeries mentioned)",
  "room_charges": "number or null (total room/bed charges in INR)",
  "icu_charges": "number or null (total ICU charges in INR)",
  "surgery_charges": "number or null (OT/surgery/procedure charges in INR)",
  "medicine_charges": "number or null (medicines and consumables charges in INR)",
  "investigation_charges": "number or null (lab, imaging, diagnostics charges in INR)",
  "other_charges": "number or null (any other charges not in the above categories in INR)",
  "total_bill_amount": "number or null (grand total of final hospital bill in INR)"
}}

Rules:
- Extract ICD-10-CM diagnosis codes if printed; otherwise infer from the final diagnosis text
- Extract ICD-10 PCS or CPT procedure codes if printed; otherwise infer from surgery/procedure names
- All monetary values must be plain numbers (no currency symbols, no commas)
- Return ONLY the JSON object, no markdown, no explanation
"""

_MULTIMODAL_PROMPT_TEMPLATE = """You are a medical data extraction assistant for a hospital cashless settlement system.

You will receive OCR text AND page images from a discharge summary / final bill.
Use images as the primary source when OCR text is noisy or incomplete.

OCR Text:
{text}

Return ONLY this JSON structure (use null for any field not found):
{{
  "discharge_date": "YYYY-MM-DD or null",
  "final_diagnosis": "string or null",
  "final_icd10_codes": "string or null (ICD-10-CM — extract if printed, otherwise infer)",
  "procedure_codes": "string or null (ICD-10 PCS/CPT — extract if printed, otherwise infer)",
  "room_charges": "number or null",
  "icu_charges": "number or null",
  "surgery_charges": "number or null",
  "medicine_charges": "number or null",
  "investigation_charges": "number or null",
  "other_charges": "number or null",
  "total_bill_amount": "number or null"
}}

Rules:
- Infer ICD-10 codes if not explicitly printed
- All monetary values must be plain numbers
- Return ONLY the JSON object, no markdown, no explanation
"""


async def extract_discharge_data(
    text: str,
    page_images: Optional[List[Image.Image]] = None,
) -> DischargeExtract:
    """
    Run Gemini over the OCR text (+ optional page images) and return
    discharge/billing fields as a DischargeExtract instance.
    """
    extractor = GeminiExtractor()

    if page_images:
        prompt = _MULTIMODAL_PROMPT_TEMPLATE.format(text=text)
        content = [prompt, *page_images]
    else:
        prompt = _PROMPT_TEMPLATE.format(text=text)
        content = prompt

    response_text = await extractor._call_gemini_with_retry(content)
    logger.info(f"Discharge extract Gemini response ({len(response_text)} chars)")

    cleaned = extractor._clean_json_response(response_text)
    data = json.loads(cleaned)

    extract = DischargeExtract(**{k: v for k, v in data.items() if k in DischargeExtract.model_fields})
    logger.info(f"Discharge extract done: diagnosis={extract.final_diagnosis!r}, total={extract.total_bill_amount!r}")
    return extract
