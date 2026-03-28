"""
Dummy Medical Report PDF Generator
====================================
Generates 5 realistic medical report PDFs — one per ABHA dummy patient.
These are used to test the Pre-Auth form's "Upload Medical Report" feature.

Run:
    cd dummy_data
    python generate_pdfs.py

Output: 5 PDF files in this folder.
"""

import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from fpdf import FPDF, XPos, YPos

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
DARK        = (30,  41,  59)
ACCENT      = (5,  150, 105)
SECTION_BG  = (236, 253, 245)
LABEL_CLR   = (100, 116, 139)
BORDER_CLR  = (203, 213, 225)
WHITE       = (255, 255, 255)
LIGHT_GRAY  = (248, 250, 252)


class MedicalReportPDF(FPDF):
    def __init__(self, hospital_name="City General Hospital"):
        super().__init__()
        self.hospital_name = hospital_name
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    # ------------------------------------------------------------------
    def header(self):
        # Header bar
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, 210, 22, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WHITE)
        self.cell(0, 8, self.hospital_name, align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, "Medical Consultation Report", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*LABEL_CLR)
        self.cell(0, 6,
                  f"Confidential Medical Record  |  Page {self.page_no()}",
                  align="C")

    # ------------------------------------------------------------------
    def section_title(self, title: str):
        self.ln(4)
        self.set_fill_color(*SECTION_BG)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ACCENT)
        self.cell(0, 8, f"  {title}", border="LB", fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(2)

    def field(self, label: str, value: str, full_width=True):
        width = 174 if full_width else 84
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*LABEL_CLR)
        self.cell(width, 6, label + ":", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        # Multi-line support
        self.multi_cell(width, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def field_pair(self, label1, val1, label2, val2):
        """Two fields side by side."""
        x = self.get_x()
        y = self.get_y()
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*LABEL_CLR)
        self.cell(84, 6, label1 + ":")
        self.set_x(x + 90)
        self.cell(84, 6, label2 + ":", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.cell(84, 6, val1)
        self.set_x(x + 90)
        self.cell(84, 6, val2, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def divider(self):
        self.set_draw_color(*BORDER_CLR)
        self.set_line_width(0.2)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(3)


# ---------------------------------------------------------------------------
# Patient data
# ---------------------------------------------------------------------------
PATIENTS = [
    # -----------------------------------------------------------------------
    # 1. Rahul Sharma — Acute Appendicitis → Laparoscopic Appendectomy
    # -----------------------------------------------------------------------
    {
        "filename": "rahul_sharma_appendicitis.pdf",
        "hospital": "Pune City General Hospital",
        "hospital_address": "Survey No. 14, Baner-Pashan Link Road, Baner, Pune, Maharashtra 411045",
        "rohini_id": "H01MH004521",
        "hospital_email": "info@punecitygeneral.in",
        "abha_id": "12-3456-7890-1234",
        # Section 1
        "patient_name": "Rahul Sharma",
        "age": "45 years",
        "gender": "Male",
        "dob": "12-Aug-1980",
        "contact": "9876543210",
        # Section 3 — Doctor
        "doctor_name": "Dr. Sandeep Kulkarni",
        "doctor_contact": "9823001234",
        "doctor_reg": "MH-43210",
        "specialization": "General Surgery",
        # Section 4 — Medical
        "presenting_complaints": (
            "Patient presented with severe pain in the right lower quadrant of the abdomen "
            "for the past 18 hours. Pain started around the umbilicus and migrated to the "
            "right iliac fossa. Associated nausea, one episode of vomiting, and low-grade fever."
        ),
        "duration_of_illness": "18 hours",
        "date_of_first_consultation": "24-Mar-2026",
        "past_history": "No known significant past medical or surgical history. NKDA.",
        "provisional_diagnosis": "Acute Appendicitis",
        "icd10_code": "K37 — Unspecified appendicitis",
        "clinical_findings": (
            "Temperature: 38.2°C. Pulse: 98/min. BP: 124/80 mmHg. "
            "Tenderness at McBurney's point. Rebound tenderness present. "
            "Rovsing's sign positive. Guarding in right iliac fossa. "
            "CBC: TLC 14,800 cells/mm3 (elevated). CRP: 68 mg/L. "
            "USG Abdomen: Dilated non-compressible appendix (8.2 mm), periappendiceal fat stranding."
        ),
        # Section 5 — Treatment
        "line_of_treatment": "Surgical — Laparoscopic Appendectomy under General Anaesthesia",
        "surgery_name": "Laparoscopic Appendectomy",
        "icd10_pcs": "0DTJ4ZZ — Resection of Appendix, Percutaneous Endoscopic Approach",
        # Section 6 — Admission
        "admission_date": "24-Mar-2026",
        "admission_time": "11:30 AM",
        "admission_type": "Emergency",
        # Section 8 — Cost estimate
        "costs": {
            "Room Rent / Day": "Rs. 2,500",
            "OT Charges": "Rs. 45,000",
            "Surgeon Fees": "Rs. 25,000",
            "Anaesthesia": "Rs. 10,000",
            "Medicines & Consumables": "Rs. 8,000",
            "Investigations (Pre-op labs, USG)": "Rs. 5,500",
            "Total Estimated Cost": "Rs. 96,000",
        },
    },

    # -----------------------------------------------------------------------
    # 2. Priya Menon — ACL Tear → Arthroscopic ACL Reconstruction
    # -----------------------------------------------------------------------
    {
        "filename": "priya_menon_acl_tear.pdf",
        "hospital": "Bengaluru Orthopaedic & Sports Medicine Centre",
        "hospital_address": "No. 45, 80 Feet Road, Koramangala 4th Block, Bengaluru, Karnataka 560034",
        "rohini_id": "H02KA007834",
        "hospital_email": "admissions@bosmc.co.in",
        "abha_id": "14-2345-6789-0011",
        "patient_name": "Priya Menon",
        "age": "33 years",
        "gender": "Female",
        "dob": "25-Mar-1992",
        "contact": "9845001122",
        "doctor_name": "Dr. Arjun Nair",
        "doctor_contact": "9845110022",
        "doctor_reg": "KA-28901",
        "specialization": "Orthopaedic Surgery & Sports Medicine",
        "presenting_complaints": (
            "Patient presents with pain and instability in the right knee following a sports injury "
            "sustained 3 weeks ago during a badminton match. Reports a 'popping' sensation at the "
            "time of injury, immediate swelling, and inability to bear weight. Persistent giving-way "
            "sensation and reduced range of motion on stairs."
        ),
        "duration_of_illness": "3 weeks",
        "date_of_first_consultation": "05-Mar-2026",
        "past_history": (
            "Hypertension — on Tab. Amlodipine 5 mg OD since 2020. "
            "No prior knee injuries. No history of bleeding disorders."
        ),
        "provisional_diagnosis": "Complete Tear of Anterior Cruciate Ligament (ACL), Right Knee",
        "icd10_code": "S83.501A — Sprain of anterior cruciate ligament of right knee",
        "clinical_findings": (
            "BP: 128/82 mmHg (controlled on medication). "
            "Right knee: Moderate effusion (+2). "
            "Lachman test: Grade 3 positive. Anterior drawer test: Positive. "
            "Pivot shift test: Positive. ROM: Flexion 110°, Extension -5° (lag). "
            "MRI Right Knee (10-Mar-2026): Complete tear of ACL mid-substance. "
            "Associated Grade 1 MCL sprain. Medial meniscus intact. Bone bruise lateral femoral condyle."
        ),
        "line_of_treatment": (
            "Surgical — Arthroscopic ACL Reconstruction with hamstring autograft under Spinal Anaesthesia. "
            "Pre-op physiotherapy for swelling reduction completed."
        ),
        "surgery_name": "Arthroscopic ACL Reconstruction (Hamstring Autograft)",
        "icd10_pcs": "0SGC4ZZ — Repair Right Knee Joint, Percutaneous Endoscopic Approach",
        "admission_date": "24-Mar-2026",
        "admission_time": "08:00 AM",
        "admission_type": "Elective",
        "costs": {
            "Room Rent / Day (2 days)": "Rs. 4,000",
            "OT Charges": "Rs. 75,000",
            "Surgeon Fees": "Rs. 40,000",
            "Implant (Endobutton + Screw)": "Rs. 28,000",
            "Physiotherapy (5 sessions)": "Rs. 6,000",
            "Medicines & Consumables": "Rs. 9,000",
            "Investigations (MRI, Labs)": "Rs. 12,000",
            "Total Estimated Cost": "Rs. 1,74,000",
        },
    },

    # -----------------------------------------------------------------------
    # 3. Arun Patel — Diabetic Foot Ulcer → Surgical Debridement
    # -----------------------------------------------------------------------
    {
        "filename": "arun_patel_diabetic_foot.pdf",
        "hospital": "Ahmedabad Diabetes & Endocrine Care Centre",
        "hospital_address": "Plot 7B, Satellite Road, Jodhpur Village, Ahmedabad, Gujarat 380015",
        "rohini_id": "H03GJ002198",
        "hospital_email": "care@adeccahmedabad.com",
        "abha_id": "18-9876-5432-1001",
        "patient_name": "Arun Patel",
        "age": "60 years",
        "gender": "Male",
        "dob": "04-Nov-1965",
        "contact": "9712345678",
        "doctor_name": "Dr. Meena Desai",
        "doctor_contact": "9712001234",
        "doctor_reg": "GJ-11234",
        "specialization": "Diabetology & Vascular Surgery",
        "presenting_complaints": (
            "Patient with known Type 2 Diabetes Mellitus (on Metformin 1000 mg BD) and Hypertension "
            "presents with a non-healing ulcer on the plantar surface of the right foot (Grade 3, Wagner "
            "classification) for the past 6 weeks. Reports pain, foul-smelling discharge, and progressive "
            "discolouration of surrounding skin. Inability to walk."
        ),
        "duration_of_illness": "6 weeks",
        "date_of_first_consultation": "10-Mar-2026",
        "past_history": (
            "Type 2 Diabetes Mellitus — 12 years, on Metformin 1000 mg BD + Glipizide 5 mg OD. "
            "Hypertension — on Tab. Telmisartan 40 mg OD. "
            "Peripheral neuropathy — diagnosed 2 years ago. "
            "No prior amputations or major surgeries."
        ),
        "provisional_diagnosis": (
            "Wagner Grade 3 Diabetic Foot Ulcer with Deep Tissue Infection, Right Foot. "
            "Underlying Peripheral Arterial Disease."
        ),
        "icd10_code": "E11.621 — Type 2 Diabetes with foot ulcer",
        "clinical_findings": (
            "BP: 138/86 mmHg. Blood sugar (fasting): 218 mg/dL. HbA1c: 9.2%. "
            "Right foot: 4x3 cm ulcer on plantar surface of 1st metatarsal head. "
            "Slough present, purulent discharge, surrounding erythema 3 cm. "
            "Probe-to-bone test: Positive. ABI (Ankle-Brachial Index): 0.6 (Moderate PAD). "
            "X-ray right foot: No cortical destruction (osteomyelitis ruled out at present). "
            "Wound culture: Staphylococcus aureus + Pseudomonas aeruginosa (MSSA). "
            "CBC: TLC 16,200. CRP: 112 mg/L. Albumin: 2.8 g/dL (low)."
        ),
        "line_of_treatment": (
            "Surgical debridement under Local/Spinal Anaesthesia. "
            "IV Antibiotics (Piperacillin-Tazobactam 4.5g TDS + Vancomycin 1g BD). "
            "Wound VAC therapy post-debridement. "
            "Strict glycaemic control with insulin sliding scale. "
            "Vascular surgery consult for possible revascularisation."
        ),
        "surgery_name": "Surgical Debridement of Diabetic Foot Ulcer",
        "icd10_pcs": "0HBMXZZ — Excision of Foot Skin",
        "admission_date": "24-Mar-2026",
        "admission_time": "10:00 AM",
        "admission_type": "Emergency",
        "costs": {
            "Room Rent / Day (7 days)": "Rs. 17,500",
            "OT Charges (Debridement)": "Rs. 25,000",
            "Surgeon Fees": "Rs. 20,000",
            "IV Antibiotics (7 days)": "Rs. 18,000",
            "Wound VAC Therapy": "Rs. 15,000",
            "Insulin & Consumables": "Rs. 6,000",
            "Investigations (Labs, X-ray, Culture)": "Rs. 8,500",
            "Total Estimated Cost": "Rs. 1,10,000",
        },
    },

    # -----------------------------------------------------------------------
    # 4. Sunita Rao — Cholelithiasis → Laparoscopic Cholecystectomy
    # -----------------------------------------------------------------------
    {
        "filename": "sunita_rao_gallstones.pdf",
        "hospital": "Hyderabad Care Hospitals",
        "hospital_address": "Road No. 12, Jubilee Hills, Hyderabad, Telangana 500033",
        "rohini_id": "H04TS009301",
        "hospital_email": "preauth@hyderabadcare.org",
        "abha_id": "21-1111-2222-3333",
        "patient_name": "Sunita Rao",
        "age": "37 years",
        "gender": "Female",
        "dob": "19-Jul-1988",
        "contact": "9900112233",
        "doctor_name": "Dr. Ramesh Babu",
        "doctor_contact": "9900445566",
        "doctor_reg": "TS-19876",
        "specialization": "General & Laparoscopic Surgery",
        "presenting_complaints": (
            "Patient presents with recurrent episodes of right upper quadrant pain radiating to the "
            "right shoulder for the past 4 months. Pain typically occurs 30–60 minutes after fatty "
            "meals, lasts 2–4 hours, and is associated with nausea and bloating. Most recent episode "
            "3 days ago was more severe and associated with vomiting."
        ),
        "duration_of_illness": "4 months (acute exacerbation 3 days ago)",
        "date_of_first_consultation": "21-Mar-2026",
        "past_history": (
            "No known chronic illnesses. NKDA. "
            "G2P2 — 2 normal deliveries. Last delivery 5 years ago. "
            "No prior abdominal surgeries."
        ),
        "provisional_diagnosis": (
            "Symptomatic Cholelithiasis (Gallstones) with Biliary Colic"
        ),
        "icd10_code": "K80.20 — Calculus of gallbladder without cholecystitis",
        "clinical_findings": (
            "BP: 118/74 mmHg. Afebrile. Murphy's sign: Positive. "
            "Mild tenderness in right hypochondrium. No jaundice, no palpable mass. "
            "USG Abdomen (22-Mar-2026): Multiple gallstones (largest 1.4 cm), "
            "gallbladder wall normal (3 mm), no pericholecystic fluid, CBD 5 mm (normal). "
            "LFT: Within normal limits. Amylase: 42 U/L (normal)."
        ),
        "line_of_treatment": (
            "Elective Laparoscopic Cholecystectomy under General Anaesthesia. "
            "Pre-op: NBM 8 hours, IV fluids, antibiotic prophylaxis (Cefazolin 1g IV)."
        ),
        "surgery_name": "Laparoscopic Cholecystectomy",
        "icd10_pcs": "0FT44ZZ — Resection of Gallbladder, Percutaneous Endoscopic Approach",
        "admission_date": "24-Mar-2026",
        "admission_time": "07:30 AM",
        "admission_type": "Elective",
        "costs": {
            "Room Rent / Day (2 days)": "Rs. 5,000",
            "OT Charges": "Rs. 40,000",
            "Surgeon Fees": "Rs. 22,000",
            "Anaesthesia": "Rs. 8,000",
            "Medicines & Consumables": "Rs. 6,500",
            "Investigations (USG, Labs)": "Rs. 4,500",
            "Total Estimated Cost": "Rs. 86,000",
        },
    },

    # -----------------------------------------------------------------------
    # 5. Vikram Singh — CAD → PTCA with Stenting (Angioplasty)
    # -----------------------------------------------------------------------
    {
        "filename": "vikram_singh_cad_angioplasty.pdf",
        "hospital": "Jaipur Heart Institute & Research Centre",
        "hospital_address": "C-Scheme, Sawai Ram Singh Road, Civil Lines, Jaipur, Rajasthan 302006",
        "rohini_id": "H05RJ005612",
        "hospital_email": "tpa@jaipurheartinstitute.in",
        "abha_id": "31-4444-5555-6666",
        "patient_name": "Vikram Singh",
        "age": "51 years",
        "gender": "Male",
        "dob": "30-Jan-1975",
        "contact": "9811223344",
        "doctor_name": "Dr. Pradeep Sharma",
        "doctor_contact": "9811556677",
        "doctor_reg": "RJ-30456",
        "specialization": "Interventional Cardiology",
        "presenting_complaints": (
            "Patient with known Ischemic Heart Disease and Type 2 Diabetes presents with "
            "crescendo angina — chest pain on minimal exertion and at rest for the past 5 days, "
            "associated with radiation to the left arm and jaw, diaphoresis, and dyspnoea. "
            "Two episodes of rest pain today, each lasting ~15 minutes, partially relieved by "
            "sublingual nitrates. Denies syncope or palpitations."
        ),
        "duration_of_illness": "5 days (progressive deterioration)",
        "date_of_first_consultation": "20-Mar-2026",
        "past_history": (
            "Ischemic Heart Disease — STEMI (2021), managed with thrombolysis. "
            "Type 2 Diabetes Mellitus — on Tab. Metformin 500 mg BD + Tab. Glimepiride 1 mg OD. "
            "On Aspirin 75 mg OD, Clopidogrel 75 mg OD, Atorvastatin 40 mg OD, Ramipril 5 mg OD. "
            "Non-smoker. No alcohol. Family history: Father had MI at 52."
        ),
        "provisional_diagnosis": (
            "Unstable Angina / NSTEMI — Coronary Artery Disease (LAD involvement suspected)"
        ),
        "icd10_code": "I20.0 — Unstable angina",
        "clinical_findings": (
            "BP: 148/92 mmHg. Pulse: 96/min, regular. SpO2: 97% on room air. "
            "ECG: ST depression in leads V3-V5, T-wave inversion in V4-V6. "
            "Troponin I: 0.42 ng/mL (elevated). BNP: 320 pg/mL (elevated). "
            "Echocardiography: EF 45%, anterior wall hypokinesia, no pericardial effusion. "
            "Blood sugar (fasting): 196 mg/dL. HbA1c: 8.1%. "
            "Coronary Angiography (23-Mar-2026): "
            "  - LAD: 85% stenosis at proximal segment "
            "  - LCx: 40% stenosis (non-significant) "
            "  - RCA: 30% stenosis (non-significant)"
        ),
        "line_of_treatment": (
            "Interventional — Percutaneous Transluminal Coronary Angioplasty (PTCA) with Drug-Eluting "
            "Stent (DES) placement in LAD under Local Anaesthesia + IV Sedation. "
            "Dual antiplatelet therapy (Aspirin + Ticagrelor) pre and post procedure. "
            "IV Heparin peri-procedure. "
            "Cardiac monitoring in CCU for 48 hours post-procedure."
        ),
        "surgery_name": "PTCA with Drug-Eluting Stent (DES) — LAD",
        "icd10_pcs": "027034Z — Dilation of Coronary Artery with Drug-eluting Intraluminal Device",
        "admission_date": "23-Mar-2026",
        "admission_time": "09:45 AM",
        "admission_type": "Emergency",
        "costs": {
            "CCU Charges / Day (3 days)": "Rs. 24,000",
            "Cath Lab / Procedure Charges": "Rs. 60,000",
            "Drug-Eluting Stent (DES)": "Rs. 45,000",
            "Cardiologist Fees": "Rs. 30,000",
            "IV Medications (Heparin, Tirofiban)": "Rs. 12,000",
            "Investigations (Echo, Angio, Labs)": "Rs. 18,000",
            "Total Estimated Cost": "Rs. 1,89,000",
        },
    },
]


# ---------------------------------------------------------------------------
# Build one PDF per patient
# ---------------------------------------------------------------------------
def build_pdf(p: dict, out_dir: str):
    pdf = MedicalReportPDF(hospital_name=p["hospital"])
    pdf.add_page()

    # ── Title block ────────────────────────────────────────────────────────
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 9, "MEDICAL CONSULTATION REPORT", align="C",
             fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # ── Patient info ───────────────────────────────────────────────────────
    pdf.section_title("PATIENT DEMOGRAPHICS")
    pdf.field_pair("Patient Name", p["patient_name"], "ABHA ID", p["abha_id"])
    pdf.field_pair("Age", p["age"], "Gender", p["gender"])
    pdf.field_pair("Date of Birth", p["dob"], "Contact", p["contact"])

    # ── Hospital info ──────────────────────────────────────────────────────
    pdf.section_title("HOSPITAL DETAILS")
    pdf.field("Hospital Name", p["hospital"])
    pdf.field("Hospital Address", p["hospital_address"])
    pdf.field_pair("Rohini ID", p["rohini_id"], "Hospital Email", p["hospital_email"])

    # ── Doctor info ────────────────────────────────────────────────────────
    pdf.section_title("ATTENDING PHYSICIAN")
    pdf.field_pair("Doctor Name", p["doctor_name"], "Contact", p["doctor_contact"])
    pdf.field_pair("Registration No.", p["doctor_reg"], "Specialization", p["specialization"])

    # ── History ────────────────────────────────────────────────────────────
    pdf.section_title("PRESENTING COMPLAINTS")
    pdf.field("", p["presenting_complaints"])

    pdf.field_pair(
        "Duration of Illness", p["duration_of_illness"],
        "Date of First Consultation", p["date_of_first_consultation"]
    )

    pdf.section_title("PAST MEDICAL HISTORY")
    pdf.field("", p["past_history"])

    # ── Diagnosis ──────────────────────────────────────────────────────────
    pdf.section_title("DIAGNOSIS")
    pdf.field("Provisional Diagnosis", p["provisional_diagnosis"])
    pdf.field("ICD-10 Code", p["icd10_code"])

    # ── Clinical findings ──────────────────────────────────────────────────
    pdf.section_title("CLINICAL FINDINGS & INVESTIGATIONS")
    pdf.field("", p["clinical_findings"])

    # ── Treatment ──────────────────────────────────────────────────────────
    pdf.section_title("PROPOSED LINE OF TREATMENT")
    pdf.field("", p["line_of_treatment"])
    pdf.field_pair("Surgery / Procedure Name", p["surgery_name"], "ICD-10 PCS", p["icd10_pcs"])

    # ── Admission ──────────────────────────────────────────────────────────
    pdf.section_title("ADMISSION DETAILS")
    pdf.field_pair("Admission Date", p["admission_date"], "Admission Time", p["admission_time"])
    pdf.field("Admission Type", p["admission_type"])

    # ── Cost estimate ──────────────────────────────────────────────────────
    pdf.section_title("ESTIMATED COST OF TREATMENT (INR)")
    for item, amount in p["costs"].items():
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        pdf.cell(120, 6, f"  {item}")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(54, 6, amount, align="R",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.divider()

    # ── Declaration / Signature ───────────────────────────────────────────
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*LABEL_CLR)
    pdf.multi_cell(
        0, 5,
        "I hereby certify that the above information is true and accurate to the best of my knowledge. "
        "This report is prepared for the purpose of pre-authorization of cashless hospitalization.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK)
    pdf.cell(87, 6, "_________________________")
    pdf.cell(87, 6, "_________________________", align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(87, 6, "Doctor's Signature & Stamp")
    pdf.cell(87, 6, "Hospital Authority Seal", align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    out_path = os.path.join(out_dir, p["filename"])
    pdf.output(out_path)
    print(f"  Created: {p['filename']}")


def _sanitize(obj):
    """Replace non-latin-1 characters recursively in all string values."""
    replacements = {
        "\u2014": "--",   # em dash
        "\u2013": "-",    # en dash
        "\u2019": "'",    # right single quotation
        "\u2018": "'",    # left single quotation
        "\u201c": '"',    # left double quotation
        "\u201d": '"',    # right double quotation
        "\u2022": "*",    # bullet
        "\u00b0": " deg", # degree sign
    }
    if isinstance(obj, str):
        for char, repl in replacements.items():
            obj = obj.replace(char, repl)
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\nGenerating dummy medical report PDFs in: {out_dir}\n")
    for patient in PATIENTS:
        build_pdf(_sanitize(patient), out_dir)
    print(f"\nDone - {len(PATIENTS)} PDFs generated.")
    print("\nABHA IDs for testing:")
    for p in PATIENTS:
        print(f"  {p['abha_id']}  ->  {p['patient_name']}  ({p['provisional_diagnosis'].split(',')[0]})")
