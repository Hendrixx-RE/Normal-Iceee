"""
New Dummy Medical Report PDF Generator
=========================================
Generates 5 new medical report PDFs for the backend DUMMY_CASES
(STEMI, TKR, Appendicitis, Pneumonia, LSCS).

These PDFs can be uploaded to test the "Extract from Medical Report" feature
on the Pre-Auth form.

Run from any directory:
    python "dummy_data/generate_new_cases.py"

Output: 5 new PDF files in the dummy_data folder (existing files are untouched).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fpdf import FPDF, XPos, YPos

# ---------------------------------------------------------------------------
# Colour palette (matches existing generate_pdfs.py style)
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

    def header(self):
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

    def field(self, label: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*LABEL_CLR)
        if label:
            self.cell(0, 6, label + ":", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.multi_cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def field_pair(self, label1, val1, label2, val2):
        x = self.get_x()
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

    def cost_table(self, rows: list):
        for item, amount in rows:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*DARK)
            self.cell(120, 6, f"  {item}")
            self.set_font("Helvetica", "B", 9)
            self.cell(54, 6, amount, align="R",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def divider(self):
        self.set_draw_color(*BORDER_CLR)
        self.set_line_width(0.2)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(3)


# ---------------------------------------------------------------------------
# Patient data — mirrors the 5 DUMMY_CASES in backend/app/routes/pre_auth.py
# ---------------------------------------------------------------------------
PATIENTS = [
    # -------------------------------------------------------------------------
    # 1. Ramesh Kumar Sharma -- STEMI (Anterior Wall), PTCA with DES
    # -------------------------------------------------------------------------
    {
        "filename": "ramesh_sharma_stemi_ptca.pdf",
        "hospital": "Apollo Hospitals",
        "hospital_address": "Jubilee Hills, Hyderabad, Telangana 500033",
        "rohini_id": "H-AP-HYD-001",
        "hospital_email": "claims@apollohyd.com",
        "patient_name": "Ramesh Kumar Sharma",
        "age": "54 years",
        "gender": "Male",
        "dob": "15-Mar-1970",
        "contact": "9876543210",
        "policy_no": "HDFC-HI-2024-88321",
        "insured_card_id": "IC-88321-A",
        "doctor_name": "Dr. Suresh Reddy",
        "doctor_contact": "9900112233",
        "doctor_reg": "TS-56001",
        "specialization": "Interventional Cardiology",
        "presenting_complaints": (
            "Patient presented to the Emergency Department with severe crushing chest pain radiating "
            "to the left arm and jaw for the past 3 hours. Associated with profuse diaphoresis, "
            "shortness of breath, and nausea. No prior similar episodes. Reports no syncope."
        ),
        "duration_of_illness": "3 hours (acute onset)",
        "date_of_first_consultation": "28-Mar-2026",
        "past_history": (
            "No prior cardiac history. Type 2 Diabetes Mellitus -- on Tab. Metformin 500 mg BD. "
            "Non-smoker. Family history: Elder brother had MI at 58 years. NKDA."
        ),
        "provisional_diagnosis": "ST-Elevation Myocardial Infarction (Anterior Wall STEMI)",
        "icd10_code": "I21.0 -- Acute transmural myocardial infarction of anterior wall",
        "clinical_findings": (
            "BP: 90/60 mmHg (cardiogenic shock). Pulse: 110/min (irregular). SpO2: 92% on room air. "
            "ECG (12-lead): ST elevation >2mm in leads V1-V4 (anterior STEMI pattern). "
            "Troponin I: 12.4 ng/mL (markedly elevated). CK-MB: 185 U/L. "
            "Echocardiography (bedside): EF 38%, anterior wall akinesia, no effusion. "
            "Blood sugar: 224 mg/dL. Creatinine: 1.1 mg/dL. "
            "Coronary Angiography: LAD total occlusion at proximal segment (TIMI 0 flow). "
            "LCx and RCA: Non-significant disease."
        ),
        "line_of_treatment": (
            "Emergency Primary PCI -- Percutaneous Transluminal Coronary Angioplasty (PTCA) with "
            "Drug-Eluting Stent (DES, 3.5 x 28 mm Xience Sierra) in proximal LAD. "
            "Dual antiplatelet therapy: Aspirin 325 mg loading + Ticagrelor 180 mg loading. "
            "IV Heparin (unfractionated) weight-based dosing. "
            "Intra-aortic balloon pump (IABP) support during procedure. "
            "Transferred to CCU post-procedure for 72-hour monitoring."
        ),
        "surgery_name": "Primary PTCA with Drug-Eluting Stent (DES) -- Proximal LAD",
        "icd10_pcs": "027034Z -- Dilation of Coronary Artery with Drug-eluting Intraluminal Device",
        "admission_date": "28-Mar-2026",
        "admission_time": "14:30",
        "admission_type": "Emergency",
        "costs": [
            ("CCU Charges / Day x 3 days (Rs. 8,000/day)", "Rs. 24,000"),
            ("Cath Lab / Procedure Charges", "Rs. 60,000"),
            ("Drug-Eluting Stent (Xience Sierra 3.5x28mm)", "Rs. 45,000"),
            ("IABP Rental (1 day)", "Rs. 18,000"),
            ("Cardiologist Fees", "Rs. 30,000"),
            ("IV Medications (Heparin, Ticagrelor, Furosemide)", "Rs. 12,000"),
            ("Investigations (ECG, Echo, Angio, Troponin, CBC, LFT)", "Rs. 18,000"),
            ("Other Hospital Expenses", "Rs. 8,000"),
            ("Total Estimated Cost", "Rs. 2,15,000"),
        ],
    },

    # -------------------------------------------------------------------------
    # 2. Sunita Devi Agarwal -- Total Knee Replacement (TKR), Left Knee
    # -------------------------------------------------------------------------
    {
        "filename": "sunita_agarwal_tkr_knee.pdf",
        "hospital": "Fortis Memorial Research Institute",
        "hospital_address": "Sector 44, Gurugram, Haryana 122002",
        "rohini_id": "H-FR-GGN-005",
        "hospital_email": "cashless@fortishealth.com",
        "patient_name": "Sunita Devi Agarwal",
        "age": "62 years",
        "gender": "Female",
        "dob": "22-Jul-1963",
        "contact": "9811234567",
        "policy_no": "MAX-GHI-2023-44512",
        "insured_card_id": "IC-44512-B",
        "doctor_name": "Dr. Ashok Rajgopal",
        "doctor_contact": "9810099887",
        "doctor_reg": "HR-41230",
        "specialization": "Joint Replacement & Orthopaedic Surgery",
        "presenting_complaints": (
            "Patient presents with severe bilateral knee pain for the past 2 years, worse on the left. "
            "Inability to walk more than 100 metres without rest. Significant morning stiffness "
            "(>30 minutes). Climbing stairs impossible. Conservative management (physiotherapy, "
            "NSAIDs, intra-articular injections) has failed over 18 months."
        ),
        "duration_of_illness": "2 years (progressive worsening)",
        "date_of_first_consultation": "01-Mar-2026",
        "past_history": (
            "Type 2 Diabetes Mellitus -- on Tab. Metformin 1000 mg BD + Tab. Glipizide 5 mg OD. "
            "Hypertension -- on Tab. Amlodipine 5 mg OD + Tab. Losartan 50 mg OD. "
            "No prior knee surgeries. No history of DVT or bleeding disorders. "
            "Pre-op HbA1c: 7.2% (well controlled). BP: 128/78 mmHg on medication."
        ),
        "provisional_diagnosis": "Primary Osteoarthritis of Left Knee -- Grade IV (Kellgren-Lawrence)",
        "icd10_code": "M17.12 -- Primary osteoarthritis of left knee",
        "clinical_findings": (
            "Left knee: Moderate effusion (+2). Flexion: 85 degrees (painful arc). "
            "Extension deficit: -10 degrees. Crepitus: Coarse. Medial joint line tenderness. "
            "Varus deformity: 12 degrees. "
            "X-ray Left Knee (Weight-bearing, 01-Mar-2026): "
            "  Grade IV OA -- complete medial compartment joint space loss (bone-on-bone contact). "
            "  Subchondral sclerosis, large osteophytes, varus alignment. "
            "Right knee: Grade II-III OA (conservative management planned). "
            "Pre-op workup: Hb 11.2 g/dL, Coagulation: normal, ECG: normal sinus rhythm, "
            "Echo: EF 62%, Chest X-ray: clear."
        ),
        "line_of_treatment": (
            "Elective Total Knee Replacement (TKR), Left Knee, under Spinal Anaesthesia. "
            "Implant: Stryker Triathlon CR Total Knee System (posterior-stabilised). "
            "Pre-op: Cell-saver, TXA protocol, DVT prophylaxis (Enoxaparin 40 mg OD). "
            "Post-op: CPM (Continuous Passive Motion) Day 1, physiotherapy Day 1."
        ),
        "surgery_name": "Total Knee Replacement (TKR) -- Left Knee (Stryker Triathlon CR)",
        "icd10_pcs": "0SRC0J9 -- Replacement of Left Knee Joint with Synthetic Substitute, Cemented",
        "admission_date": "05-Apr-2026",
        "admission_time": "08:00",
        "admission_type": "Planned (Elective)",
        "costs": [
            ("Room Charges / Day x 5 days (Rs. 5,000/day)", "Rs. 25,000"),
            ("OT Charges", "Rs. 55,000"),
            ("Knee Implant (Stryker Triathlon CR System)", "Rs. 1,10,000"),
            ("Surgeon Fees", "Rs. 60,000"),
            ("Anaesthesia Fees", "Rs. 20,000"),
            ("Physiotherapy (In-patient, 5 sessions)", "Rs. 7,500"),
            ("Medicines, Consumables & DVT Prophylaxis", "Rs. 18,000"),
            ("Investigations (X-ray, Labs, Echo, ECG)", "Rs. 14,500"),
            ("Total Estimated Cost", "Rs. 3,10,000"),
        ],
    },

    # -------------------------------------------------------------------------
    # 3. Vikram Singh Chauhan -- Acute Appendicitis, Laparoscopic Appendicectomy
    # -------------------------------------------------------------------------
    {
        "filename": "vikram_chauhan_appendicitis.pdf",
        "hospital": "Manipal Hospitals",
        "hospital_address": "Whitefield Road, Whitefield, Bengaluru, Karnataka 560066",
        "rohini_id": "H-MN-BLR-012",
        "hospital_email": "tpa@manipalbangalore.com",
        "patient_name": "Vikram Singh Chauhan",
        "age": "28 years",
        "gender": "Male",
        "dob": "05-Nov-1997",
        "contact": "7654321098",
        "policy_no": "STAR-HI-2025-19834",
        "insured_card_id": "IC-19834-C",
        "doctor_name": "Dr. Priya Menon",
        "doctor_contact": "9845001122",
        "doctor_reg": "KA-38901",
        "specialization": "General & Laparoscopic Surgery",
        "presenting_complaints": (
            "Patient presents with acute onset of pain in the right iliac fossa for 12 hours. "
            "Pain initially diffuse around the umbilicus, subsequently migrated to the right iliac fossa. "
            "Associated with fever (101 degrees F), nausea, one episode of vomiting. Loss of appetite. "
            "No diarrhoea or urinary complaints."
        ),
        "duration_of_illness": "12 hours",
        "date_of_first_consultation": "28-Mar-2026",
        "past_history": "No significant past medical or surgical history. No known drug allergies.",
        "provisional_diagnosis": "Acute Appendicitis (Non-perforated)",
        "icd10_code": "K35.2 -- Acute appendicitis with generalised peritonitis",
        "clinical_findings": (
            "Temperature: 38.4 degrees C. Pulse: 102/min. BP: 118/76 mmHg. "
            "Tenderness at McBurney's point (right iliac fossa). "
            "Rebound tenderness present. Rovsing's sign positive. Psoas sign positive. "
            "Guarding in right iliac fossa. "
            "CBC: WBC 14,800 cells/mm3 (neutrophilic leucocytosis). CRP: 82 mg/L. "
            "USG Abdomen: Dilated non-compressible appendix (9 mm diameter), "
            "periappendiceal fat stranding, no free fluid. "
            "Alvarado Score: 8 (High probability of appendicitis)."
        ),
        "line_of_treatment": (
            "Emergency Laparoscopic Appendicectomy under General Anaesthesia. "
            "Pre-op: IV Cefuroxime 1.5g + IV Metronidazole 500 mg (antibiotic prophylaxis). "
            "Three-port laparoscopic approach (umbilical camera port, two 5mm working ports). "
            "Appendix delivered without spillage. Specimen sent for histopathology."
        ),
        "surgery_name": "Laparoscopic Appendicectomy (3-port technique)",
        "icd10_pcs": "0DTJ4ZZ -- Resection of Appendix, Percutaneous Endoscopic Approach",
        "admission_date": "28-Mar-2026",
        "admission_time": "22:15",
        "admission_type": "Emergency",
        "costs": [
            ("Room Charges / Day x 3 days (Twin-sharing, Rs. 1,800/day)", "Rs. 5,400"),
            ("OT Charges (Laparoscopic)", "Rs. 28,000"),
            ("Surgeon Fees", "Rs. 18,000"),
            ("Anaesthesia Fees", "Rs. 8,000"),
            ("Histopathology (Appendix specimen)", "Rs. 1,200"),
            ("IV Antibiotics & Consumables", "Rs. 5,800"),
            ("Investigations (USG, CBC, CRP, LFT, ECG)", "Rs. 4,600"),
            ("Total Estimated Cost", "Rs. 71,000"),
        ],
    },

    # -------------------------------------------------------------------------
    # 4. Kavita Rani Mishra -- Severe CAP (Pneumonia), Medical Management
    # -------------------------------------------------------------------------
    {
        "filename": "kavita_mishra_pneumonia_cap.pdf",
        "hospital": "Medanta The Medicity",
        "hospital_address": "CH Baktawar Singh Road, Sector 38, Gurugram, Haryana 122001",
        "rohini_id": "H-MD-GGN-002",
        "hospital_email": "cashless@medanta.org",
        "patient_name": "Kavita Rani Mishra",
        "age": "45 years",
        "gender": "Female",
        "dob": "30-Jan-1981",
        "contact": "9312456789",
        "policy_no": "BAJAJ-AHI-2024-67123",
        "insured_card_id": "IC-67123-D",
        "doctor_name": "Dr. Randeep Guleria",
        "doctor_contact": "9810055000",
        "doctor_reg": "DL-20140",
        "specialization": "Pulmonology & Critical Care Medicine",
        "presenting_complaints": (
            "Patient presents with high-grade fever (103 degrees F) for the past 4 days, "
            "progressive breathlessness at rest (MMRC Grade 3), productive cough with yellow-green "
            "purulent sputum, and right-sided pleuritic chest pain. Symptoms worsened despite "
            "oral antibiotics (Amoxicillin) prescribed at a local clinic 2 days ago."
        ),
        "duration_of_illness": "4 days",
        "date_of_first_consultation": "25-Mar-2026",
        "past_history": (
            "Type 2 Diabetes Mellitus -- diagnosed 2019, on Tab. Metformin 500 mg BD + "
            "Tab. Sitagliptin 100 mg OD. No prior pulmonary disease. "
            "Non-smoker. No history of TB. No known drug allergies."
        ),
        "provisional_diagnosis": "Severe Community-Acquired Pneumonia (CAP) -- CURB-65 Score 3",
        "icd10_code": "J18.9 -- Pneumonia, unspecified organism",
        "clinical_findings": (
            "Temperature: 39.2 degrees C. Pulse: 118/min. RR: 28/min. "
            "BP: 104/68 mmHg. SpO2: 88% on room air (requires O2 @ 4 L/min). "
            "Chest auscultation: Decreased breath sounds right lower zone, "
            "coarse crepitations right mid and lower zones, bronchial breathing. "
            "CXR (PA): Right lower lobe consolidation with air bronchograms. "
            "HRCT Chest: Lobar consolidation right lower lobe + small right pleural effusion. "
            "CBC: WBC 18,600 (neutrophilia). CRP: 248 mg/L. Procalcitonin: 3.8 ng/mL. "
            "Blood sugar: 312 mg/dL. HbA1c: 9.8% (poorly controlled). "
            "Sputum culture (preliminary): Gram-positive diplococci (Streptococcus pneumoniae suspected). "
            "Blood cultures: x2 sent. CURB-65: 3 (hospitalisation + ICU review)."
        ),
        "line_of_treatment": (
            "Admission to HDU (High Dependency Unit) for monitoring. "
            "IV Piperacillin-Tazobactam 4.5g TDS (empirical broad-spectrum cover). "
            "IV Azithromycin 500mg OD (atypical cover). "
            "Supplemental oxygen (target SpO2 >94%). "
            "IV Fluids for haemodynamic support. "
            "Strict glycaemic control: Insulin Actrapid sliding scale. "
            "Chest physiotherapy BD. "
            "Step-down to oral antibiotics after 48-72 hours clinical improvement."
        ),
        "surgery_name": "Medical Management (No Surgical Procedure Planned)",
        "icd10_pcs": "N/A -- Medical management only",
        "admission_date": "28-Mar-2026",
        "admission_time": "10:00",
        "admission_type": "Emergency",
        "costs": [
            ("HDU Charges / Day x 2 days (Rs. 6,000/day)", "Rs. 12,000"),
            ("General Ward / Day x 5 days (Rs. 2,200/day)", "Rs. 11,000"),
            ("IV Antibiotics (Pip-Taz + Azithromycin, 7 days)", "Rs. 24,000"),
            ("Insulin (Sliding Scale, 7 days)", "Rs. 3,500"),
            ("Oxygen Therapy & Nebulisation", "Rs. 4,000"),
            ("IV Fluids & Consumables", "Rs. 5,000"),
            ("Physiotherapy (Chest, 5 sessions)", "Rs. 3,500"),
            ("Investigations (CXR, HRCT, Cultures, CBC x3, CRP, LFT)", "Rs. 16,000"),
            ("Total Estimated Cost", "Rs. 79,000"),
        ],
    },

    # -------------------------------------------------------------------------
    # 5. Anjali Reddy -- Elective LSCS (Previous Caesarean Section, G2P1L1)
    # -------------------------------------------------------------------------
    {
        "filename": "anjali_reddy_lscs_maternity.pdf",
        "hospital": "Rainbow Children's Hospital",
        "hospital_address": "Road No. 10, Banjara Hills, Hyderabad, Telangana 500034",
        "rohini_id": "H-RB-HYD-008",
        "hospital_email": "tpa@rainbowhospitals.in",
        "patient_name": "Anjali Reddy",
        "age": "29 years",
        "gender": "Female",
        "dob": "12-Jun-1996",
        "contact": "9988776655",
        "policy_no": "NIAC-GHI-2022-33214",
        "insured_card_id": "IC-33214-E",
        "doctor_name": "Dr. Mohana Venugopal",
        "doctor_contact": "9849001234",
        "doctor_reg": "TS-62300",
        "specialization": "Obstetrics & Gynaecology (High-Risk Pregnancy)",
        "presenting_complaints": (
            "Patient at 38 weeks gestation (by LMP + USG dates consistent) presents for elective "
            "repeat Caesarean Section. Reports regular foetal movements. Mild Braxton-Hicks contractions "
            "but no active labour. No leaking per vaginum. No bleeding. No headache or visual disturbances."
        ),
        "duration_of_illness": "38 weeks gestation",
        "date_of_first_consultation": "28-Mar-2026 (pre-op assessment)",
        "past_history": (
            "Obstetric history: G2 P1 L1 A0. "
            "Previous LSCS (2023) -- Indication: Foetal distress, baby delivered healthy (3.1 kg). "
            "No post-operative complications. "
            "No chronic medical conditions. No known drug allergies. "
            "Current pregnancy: Registered at 8 weeks. ANC visits regular. "
            "OGTT (24 weeks): Normal. Morphology scan: Normal foetal anatomy."
        ),
        "provisional_diagnosis": "Pregnancy 38 Weeks, G2P1L1 -- Elective Repeat Lower Segment Caesarean Section (LSCS)",
        "icd10_code": "O82.0 -- Delivery by elective Caesarean section",
        "clinical_findings": (
            "BP: 114/72 mmHg. Pulse: 88/min. Weight: 72 kg (BMI 26.8). "
            "Fundal height: 36 cm (correlates with 38 weeks). Foetal lie: Cephalic. "
            "Foetal heart rate: 142/min (normal). No foetal distress. "
            "Cervix: Closed, posterior, uneffaced (not in active labour). "
            "Previous LSCS scar: Well-healed, no tenderness. "
            "USG (26-Mar-2026): Single live foetus, cephalic, AFI 14 cm (normal), "
            "EFW 2.9 kg (appropriate for gestational age), placenta anterior (Grade II). "
            "CTG: Reactive. Hb: 10.8 g/dL. Blood group: B+ ve. "
            "Coagulation: Normal. HBsAg: Negative. HIV: Non-reactive."
        ),
        "line_of_treatment": (
            "Elective Lower Segment Caesarean Section (LSCS) under Spinal Anaesthesia. "
            "Prophylactic IV Cefazolin 1g prior to skin incision. "
            "Pfannenstiel incision. Lower uterine segment transverse incision. "
            "IV Oxytocin 20 units in 500 mL RL (post-delivery, uterotonic prophylaxis). "
            "Post-op: IV analgesia, early ambulation (4-6 hours), breastfeeding support. "
            "Expected LOS: 4-5 days."
        ),
        "surgery_name": "Lower Segment Caesarean Section (LSCS) -- Elective Repeat",
        "icd10_pcs": "10D00Z1 -- Extraction of Products of Conception, Low Cervical, Open Approach",
        "admission_date": "01-Apr-2026",
        "admission_time": "07:30",
        "admission_type": "Planned (Elective)",
        "costs": [
            ("Room Charges / Day x 5 days (Twin-sharing, Rs. 2,500/day)", "Rs. 12,500"),
            ("OT Charges (LSCS)", "Rs. 30,000"),
            ("Obstetrician Fees", "Rs. 25,000"),
            ("Anaesthesia Fees (Spinal)", "Rs. 10,000"),
            ("Neonatologist Charges (Routine)", "Rs. 5,000"),
            ("Medicines, Consumables & Oxytocin Protocol", "Rs. 8,500"),
            ("Investigations (USG, CTG, CBC, Coagulation, Blood Group)", "Rs. 6,000"),
            ("Newborn Care (NBSU, Day 1-4)", "Rs. 8,000"),
            ("Total Estimated Cost", "Rs. 1,05,000"),
        ],
    },
]


# ---------------------------------------------------------------------------
# Build one PDF per patient
# ---------------------------------------------------------------------------
def build_pdf(p: dict, out_dir: str):
    pdf = MedicalReportPDF(hospital_name=p["hospital"])
    pdf.add_page()

    # Title block
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 9, "MEDICAL CONSULTATION REPORT", align="C",
             fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.section_title("PATIENT DEMOGRAPHICS")
    pdf.field_pair("Patient Name", p["patient_name"], "Age", p["age"])
    pdf.field_pair("Date of Birth", p["dob"], "Gender", p["gender"])
    pdf.field_pair("Contact No.", p["contact"], "Policy No.", p["policy_no"])
    pdf.field_pair("Insured Card ID", p["insured_card_id"], "", "")

    pdf.section_title("HOSPITAL DETAILS")
    pdf.field("Hospital Name", p["hospital"])
    pdf.field("Hospital Address", p["hospital_address"])
    pdf.field_pair("ROHINI ID", p["rohini_id"], "Hospital Email", p["hospital_email"])

    pdf.section_title("ATTENDING PHYSICIAN")
    pdf.field_pair("Doctor Name", p["doctor_name"], "Contact", p["doctor_contact"])
    pdf.field_pair("Registration No.", p["doctor_reg"], "Specialization", p["specialization"])

    pdf.section_title("PRESENTING COMPLAINTS")
    pdf.field("", p["presenting_complaints"])
    pdf.field_pair("Duration of Illness", p["duration_of_illness"],
                   "Date of First Consultation", p["date_of_first_consultation"])

    pdf.section_title("PAST MEDICAL HISTORY")
    pdf.field("", p["past_history"])

    pdf.section_title("DIAGNOSIS")
    pdf.field("Provisional Diagnosis", p["provisional_diagnosis"])
    pdf.field("ICD-10 Code", p["icd10_code"])

    pdf.section_title("CLINICAL FINDINGS & INVESTIGATIONS")
    pdf.field("", p["clinical_findings"])

    pdf.section_title("PROPOSED LINE OF TREATMENT")
    pdf.field("", p["line_of_treatment"])
    pdf.field_pair("Surgery / Procedure Name", p["surgery_name"], "ICD-10 PCS", p["icd10_pcs"])

    pdf.section_title("ADMISSION DETAILS")
    pdf.field_pair("Admission Date", p["admission_date"], "Admission Time", p["admission_time"])
    pdf.field("Admission Type", p["admission_type"])

    pdf.section_title("ESTIMATED COST OF TREATMENT (INR)")
    pdf.cost_table(p["costs"])
    pdf.divider()

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
    """Replace characters outside latin-1 so fpdf2 can encode them."""
    replacements = {
        "\u2014": "--",  "\u2013": "-",
        "\u2019": "'",   "\u2018": "'",
        "\u201c": '"',   "\u201d": '"',
        "\u2022": "*",   "\u00b0": " deg",
        "\u00e9": "e",   "\u00f3": "o",
    }
    if isinstance(obj, str):
        for char, repl in replacements.items():
            obj = obj.replace(char, repl)
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, tuple):
        return tuple(_sanitize(i) for i in obj)
    return obj


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\nGenerating new dummy medical report PDFs in: {out_dir}\n")
    for patient in PATIENTS:
        build_pdf(_sanitize(patient), out_dir)
    print(f"\nDone -- {len(PATIENTS)} new PDFs generated.")
    print("\nPatients:")
    for p in PATIENTS:
        print(f"  {p['filename']}  ->  {p['patient_name']}")
