"""
Gemini-based extractor for enhancement request fields.
Given OCR text (and optionally page images) from an enhancement document
(progress note, revised estimate, updated prescription, etc.),
returns an EnhancementExtract with clinical and revised-cost fields.
"""
import json
import logging
from typing import List, Optional
from PIL import Image

from app.models.enhancement import EnhancementExtract
from app.services.llm import GeminiExtractor

logger = logging.getLogger(__name__)


_PROMPT_TEMPLATE = """You are a medical data extraction assistant for a hospital cashless insurance system.

Extract ONLY the following fields from the clinical document below and return a single valid JSON object.
This document is an enhancement / revision request — it may be a progress note, updated estimate,
surgeon's letter, revised prescription, or any document that changes the original pre-authorization.

Document Text:
{text}

Return ONLY this JSON structure (use null for any field not found):
{{
  "reason": "string or null (brief reason why enhancement is needed, e.g. 'Diagnosis changed to...', 'Additional surgery required')",
  "clinical_justification": "string or null (detailed clinical reason from doctor's notes)",
  "updated_diagnosis": "string or null (updated/revised primary diagnosis)",
  "updated_icd10_code": "string or null (ICD-10-CM code for updated diagnosis — extract if printed, otherwise infer)",
  "updated_line_of_treatment": "string or null (revised treatment plan — medical/surgical/ICU etc.)",
  "updated_surgery_name": "string or null (name of revised or additional surgery/procedure)",
  "updated_icd10_pcs_code": "string or null (ICD-10 PCS or CPT code for revised procedure — extract if printed, otherwise infer)",
  "revised_room_rent_per_day": "number or null (revised room rent per day in INR)",
  "revised_icu_charges_per_day": "number or null (revised ICU charges per day in INR)",
  "revised_ot_charges": "number or null (revised OT/surgery charges in INR)",
  "revised_surgeon_fees": "number or null (revised surgeon/doctor fees in INR)",
  "revised_medicines_consumables": "number or null (revised medicines and consumables in INR)",
  "revised_investigations": "number or null (revised lab/imaging/investigation charges in INR)",
  "revised_total_estimated_cost": "number or null (total revised estimated cost in INR)"
}}

Rules:
- Extract ICD-10 codes if printed; otherwise infer from diagnosis/procedure names
- All monetary values must be plain numbers (no currency symbols, no commas)
- Return ONLY the JSON object, no markdown, no explanation
"""

_MULTIMODAL_PROMPT_TEMPLATE = """You are a medical data extraction assistant for a hospital cashless insurance system.

You will receive OCR text AND page images from an enhancement/revision document.
Use images as the primary source when OCR text is noisy or incomplete.

OCR Text:
{text}

Return ONLY this JSON structure (use null for any field not found):
{{
  "reason": "string or null",
  "clinical_justification": "string or null",
  "updated_diagnosis": "string or null",
  "updated_icd10_code": "string or null (extract if printed, otherwise infer from diagnosis)",
  "updated_line_of_treatment": "string or null",
  "updated_surgery_name": "string or null",
  "updated_icd10_pcs_code": "string or null (extract if printed, otherwise infer from procedure)",
  "revised_room_rent_per_day": "number or null",
  "revised_icu_charges_per_day": "number or null",
  "revised_ot_charges": "number or null",
  "revised_surgeon_fees": "number or null",
  "revised_medicines_consumables": "number or null",
  "revised_investigations": "number or null",
  "revised_total_estimated_cost": "number or null"
}}

Rules:
- Infer ICD-10 codes if not explicitly printed
- All monetary values must be plain numbers
- Return ONLY the JSON object, no markdown, no explanation
"""


async def extract_enhancement_data(
    text: str,
    page_images: Optional[List[Image.Image]] = None,
) -> EnhancementExtract:
    """
    Run Gemini over OCR text (+ optional page images) and return
    enhancement fields as an EnhancementExtract instance.
    """
    extractor = GeminiExtractor()

    if page_images:
        prompt = _MULTIMODAL_PROMPT_TEMPLATE.format(text=text)
        content = [prompt, *page_images]
    else:
        prompt = _PROMPT_TEMPLATE.format(text=text)
        content = prompt

    response_text = await extractor._call_gemini_with_retry(content)
    logger.info(f"Enhancement extract Gemini response ({len(response_text)} chars)")

    cleaned = extractor._clean_json_response(response_text)
    data = json.loads(cleaned)

    extract = EnhancementExtract(**{k: v for k, v in data.items() if k in EnhancementExtract.model_fields})
    logger.info(f"Enhancement extract done: diagnosis={extract.updated_diagnosis!r}, total={extract.revised_total_estimated_cost!r}")
    return extract
