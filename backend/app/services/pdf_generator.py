"""
Pre-Authorization PDF Generator
Produces a form matching the Medi Assist 'Part C (Revised)' layout exactly.
"""
from fpdf import FPDF, XPos, YPos
from typing import Optional
from app.models.pre_auth import PreAuthRequest, REQUIRED_FIELDS
import logging

logger = logging.getLogger(__name__)

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
DARK       = (30,  41,  59)
SECTION_BG = (30,  41,  59)
LIGHT_BG   = (248, 250, 252)
MISSING_BG = (254, 242, 242)
MISSING_FG = (220, 38,  38)
GRAY       = (100, 116, 139)
BORDER_CLR = (180, 180, 180)


class MediAssistPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=12)
        self.set_margins(10, 28, 10)

    def header(self):
        self.set_y(8)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*DARK)
        self.cell(0, 5, "REQUEST FOR CASHLESS HOSPITALISATION FOR HEALTH INSURANCE POLICY",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 5, "PART C (Revised)", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 4, "TO BE FILLED IN BLOCK LETTERS", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.set_draw_color(*BORDER_CLR)
        self.line(10, self.get_y(), 200, self.get_y())

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 4,
                  "Page " + str(self.page_no()) + " of 2  |  Medi Assist Insurance TPA Pvt Ltd  |  Version: 25.06.2019",
                  align="C")

    def sf(self, size=9, bold=False):
        self.set_font("Helvetica", "B" if bold else "", size)

    def section_bar(self, title):
        self.ln(2)
        self.set_fill_color(*SECTION_BG)
        self.set_text_color(*WHITE)
        self.sf(8, bold=True)
        self.cell(0, 6, "  " + title, fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(1)

    def val_box(self, value, w, h=6, required=False, eol=False):
        is_missing = required and (not value and value != 0)
        txt = str(value) if (value is not None and str(value).strip()) else ""
        if is_missing:
            self.set_fill_color(*MISSING_BG)
            self.set_draw_color(*MISSING_FG)
            self.set_text_color(*MISSING_FG)
            self.sf(7)
            self.cell(w, h, "REQUIRED", border=1, fill=True,
                      new_x=XPos.LMARGIN if eol else XPos.RIGHT,
                      new_y=YPos.NEXT if eol else YPos.TOP)
        else:
            self.set_fill_color(*LIGHT_BG)
            self.set_draw_color(*BORDER_CLR)
            self.set_text_color(*DARK)
            self.sf(8)
            self.cell(w, h, txt, border=1, fill=True,
                      new_x=XPos.LMARGIN if eol else XPos.RIGHT,
                      new_y=YPos.NEXT if eol else YPos.TOP)
        self.set_draw_color(*BORDER_CLR)
        self.set_text_color(*DARK)

    def mbox(self, value, w, h=10, required=False):
        is_missing = required and not value
        txt = str(value) if value else ""
        if is_missing:
            self.set_fill_color(*MISSING_BG)
            self.set_draw_color(*MISSING_FG)
            self.set_text_color(*MISSING_FG)
            self.sf(7)
            self.multi_cell(w, 4, "[ REQUIRED - NOT FILLED ]",
                            border=1, fill=True,
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.set_fill_color(*LIGHT_BG)
            self.set_draw_color(*BORDER_CLR)
            self.set_text_color(*DARK)
            self.sf(8)
            self.multi_cell(w, 4, txt, border=1, fill=True,
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BORDER_CLR)
        self.set_text_color(*DARK)

    def chk(self, label, checked, gap=4):
        bx, by = self.get_x(), self.get_y()
        self.set_draw_color(*BORDER_CLR)
        self.rect(bx, by + 0.8, 3.5, 3.5)
        if checked:
            self.set_xy(bx, by)
            self.sf(9, bold=True)
            self.set_text_color(5, 150, 105)
            self.cell(3.5, 5, "X")
            self.set_text_color(*DARK)
        self.set_xy(bx + 4, by)
        self.sf(8)
        self.cell(0, 5, label)
        self.set_xy(bx + 4 + self.get_string_width(label) + gap, by)

    def lbl(self, text, w=0):
        self.sf(7, bold=True)
        self.set_text_color(*GRAY)
        if w:
            self.cell(w, 6, text)
        else:
            self.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)

    def rs_row(self, label, value, lw=112):
        self.sf(8)
        self.set_text_color(*GRAY)
        self.cell(lw, 6, label + ":")
        self.set_text_color(*DARK)
        self.sf(8, bold=True)
        self.cell(12, 6, "Rs.")
        self.val_box((str(int(value)) if value == int(value) else str(value)) if value is not None else "", w=36, h=6, eol=True)

    def chronic_row(self, label, checked, since):
        x, y = self.get_x(), self.get_y()
        self.set_draw_color(*BORDER_CLR)
        self.rect(x, y + 0.8, 3.5, 3.5)
        if checked:
            self.set_xy(x, y)
            self.sf(9, bold=True)
            self.set_text_color(5, 150, 105)
            self.cell(3.5, 5, "X")
            self.set_text_color(*DARK)
        self.set_xy(x + 4.5, y)
        self.sf(8)
        self.cell(75, 5, label)
        self.sf(7)
        self.set_text_color(*GRAY)
        self.cell(14, 5, "Since:")
        self.set_text_color(*DARK)
        self.val_box(since or "", w=30, h=5, eol=True)


def generate_pre_auth_pdf(pre_auth: PreAuthRequest, pre_auth_id: str = "") -> bytes:
    req = set(REQUIRED_FIELDS)
    def r(f): return f in req

    pdf = MediAssistPDF()

    # =========================================================
    # PAGE 1
    # =========================================================
    pdf.add_page()

    # Hospital block
    pdf.lbl("Name of the hospital:", 38)
    pdf.val_box(pre_auth.hospital_name, w=152, required=r("hospital_name"), eol=True)

    pdf.lbl("Hospital location:", 32)
    pdf.val_box(pre_auth.hospital_location, w=104, eol=False)
    pdf.lbl("  Hospital ID:", 24)
    pdf.val_box(pre_auth.hospital_id, w=30, eol=True)

    pdf.lbl("Hospital email ID:", 32)
    pdf.val_box(pre_auth.hospital_email, w=104, eol=False)
    pdf.lbl("  ROHINI ID:", 24)
    pdf.val_box(pre_auth.rohini_id, w=30, required=r("rohini_id"), eol=True)

    # TPA
    pdf.section_bar("DETAILS OF THIRD PARTY ADMINISTRATOR")
    pdf.sf(8)
    pdf.cell(65, 5, "a) Name of TPA:  Medi Assist Insurance TPA Pvt Ltd")
    pdf.cell(55, 5, "b) Phone no.:  080 22068666")
    pdf.cell(0,  5, "c) Toll Free Fax:  1800 425 9559",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    # Patient
    pdf.section_bar("DETAILS OF THE PATIENT  (TO BE FILLED BY INSURED / PATIENT)")

    pdf.lbl("a) Name of the patient:", 46)
    pdf.val_box(pre_auth.patient_name, w=144, required=r("patient_name"), eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(18, 6, "b) Gender:")
    pdf.set_text_color(*DARK)
    for g in ["Male", "Female", "Third gender"]:
        pdf.chk(g, pre_auth.gender == g, gap=6)
    pdf.set_text_color(*GRAY)
    pdf.cell(18, 6, "c) Contact no.:")
    pdf.val_box(pre_auth.contact, 34, required=r("contact"), eol=False)
    pdf.cell(22, 6, "  d) Alt. contact no.:")
    pdf.val_box(pre_auth.alternate_contact, 26, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(14, 6, "e) Age:")
    pdf.val_box(pre_auth.age, 12, eol=False)
    pdf.cell(8, 6, " Yrs")
    pdf.val_box(pre_auth.age_months, 10, eol=False)
    pdf.cell(14, 6, " Months")
    pdf.cell(20, 6, "f) Date of birth:")
    pdf.val_box(pre_auth.date_of_birth, 30, eol=False)
    pdf.cell(18, 6, "  g) Insurer ID:")
    pdf.val_box(pre_auth.insured_card_id, 34, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(46, 6, "h) Policy no. / Name of corporate:")
    pdf.val_box(pre_auth.policy_no, 64, required=r("policy_no"), eol=False)
    pdf.cell(18, 6, "  i) Employee ID:")
    pdf.val_box(pre_auth.employee_id, 42, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(66, 6, "j) Currently other medical claim / health insurance:")
    pdf.set_text_color(*DARK)
    pdf.chk("Yes", pre_auth.other_insurance is True, gap=4)
    pdf.chk("No",  pre_auth.other_insurance is False, gap=6)
    pdf.set_text_color(*GRAY)
    pdf.cell(18, 6, "j.1) Insurer:")
    pdf.val_box(pre_auth.other_insurance_insurer, 50, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(26, 5, "j.2) Give details:")
    pdf.val_box(pre_auth.other_insurance_details, 164, h=5, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(56, 6, "k) Family physician (if yes) Name:")
    pdf.val_box(pre_auth.family_physician_name, 68, eol=False)
    pdf.cell(20, 6, "  k.1) Contact no.:")
    pdf.val_box(pre_auth.family_physician_contact, 26, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(46, 6, "L) Occupation of insured patient:")
    pdf.val_box(pre_auth.occupation, 144, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(44, 5, "m) Address of insured patient:")
    pdf.set_text_color(*DARK)
    pdf.mbox(pre_auth.patient_address, w=146, h=10)

    # Doctor / Hospital
    pdf.section_bar("TO BE FILLED BY THE TREATING DOCTOR / HOSPITAL")

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(36, 6, "a) Name of treating doctor:")
    pdf.val_box(pre_auth.doctor_name, 96, required=r("doctor_name"), eol=False)
    pdf.cell(18, 6, "  b) Contact no.:")
    pdf.val_box(pre_auth.doctor_contact, 40, eol=True)

    # complaints + findings side by side
    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(90, 5, "c) Name of Illness / disease with presenting complaints:")
    pdf.cell(0,  5, "d) Relevant clinical findings:",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    x, y = pdf.get_x(), pdf.get_y()
    W = 89
    pdf.set_fill_color(*(MISSING_BG if r("presenting_complaints") and not pre_auth.presenting_complaints else LIGHT_BG))
    pdf.set_draw_color(*(MISSING_FG if r("presenting_complaints") and not pre_auth.presenting_complaints else BORDER_CLR))
    pdf.set_text_color(*(MISSING_FG if r("presenting_complaints") and not pre_auth.presenting_complaints else DARK))
    pdf.sf(8)
    pdf.multi_cell(W, 4,
                   pre_auth.presenting_complaints or ("[ REQUIRED ]" if r("presenting_complaints") else ""),
                   border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    y_after_left = pdf.get_y()
    pdf.set_xy(x + W + 2, y)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*BORDER_CLR)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(W - 2, 4, pre_auth.clinical_findings or "",
                   border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_y(max(y_after_left, pdf.get_y()))

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(30, 6, "e) Duration:")
    pdf.val_box(pre_auth.duration_of_illness, 28, eol=False)
    pdf.cell(38, 6, "  e.1) First consultation:")
    pdf.val_box(pre_auth.date_of_first_consultation, 30, eol=False)
    pdf.cell(32, 6, "  e.2) Past history:")
    pdf.val_box(pre_auth.past_history, 32, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(34, 6, "f) Provisional diagnosis:")
    pdf.val_box(pre_auth.provisional_diagnosis, 102,
                required=r("provisional_diagnosis"), eol=False)
    pdf.cell(18, 6, "  f.1) ICD-10 code:")
    pdf.val_box(pre_auth.icd10_diagnosis_code, 26,
                required=r("icd10_diagnosis_code"), eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(44, 6, "g) Proposed line of treatment:")
    pdf.set_text_color(*DARK)
    pdf.chk("Medical management",  pre_auth.treatment_medical_management,  gap=4)
    pdf.chk("Surgical management", pre_auth.treatment_surgical,             gap=4)
    pdf.chk("Intensive care",      pre_auth.treatment_intensive_care,       gap=4)
    pdf.chk("Investigation",       pre_auth.treatment_investigation,        gap=4)
    pdf.chk("Non-Allopathic treatment", pre_auth.treatment_non_allopathic,  gap=2)
    pdf.ln(6)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(86, 5, "h) If investigation / medical management, provide details:")
    pdf.cell(0,  5, "h.1) Route of drug administration:",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    x, y = pdf.get_x(), pdf.get_y()
    pdf.mbox(pre_auth.medical_management_details, w=84, h=10)
    pdf.set_xy(x + 86, y)
    for route in ["IV", "Oral", "Other"]:
        pdf.chk(route, pre_auth.route_of_drug_administration == route, gap=5)
    pdf.set_y(max(y + 10, pdf.get_y()))

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(40, 6, "i) If Surgical, name of surgery:")
    pdf.val_box(pre_auth.surgery_name, 102, eol=False)
    pdf.cell(18, 6, "  i.1) ICD-10 PCS:")
    pdf.val_box(pre_auth.icd10_pcs_code, 30, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(90, 5, "j) If other treatments provide details:")
    pdf.cell(0,  5, "k) How did injury occur:",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    x, y = pdf.get_x(), pdf.get_y()
    pdf.mbox(pre_auth.other_treatment_details, w=88, h=10)
    pdf.set_xy(x + 90, y)
    pdf.mbox(pre_auth.injury_details, w=100, h=10)
    pdf.set_y(max(y + 10, pdf.get_y()))

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(34, 5, "L) In case of accident:")
    pdf.set_text_color(*DARK)
    pdf.chk("Is it RTA:", pre_auth.is_rta is True, gap=2)
    pdf.chk("Yes", pre_auth.is_rta is True, gap=2)
    pdf.chk("No",  pre_auth.is_rta is False, gap=4)
    pdf.set_text_color(*GRAY)
    pdf.cell(20, 5, "ii. Date of injury:")
    pdf.val_box(pre_auth.date_of_injury, 24, eol=False)
    pdf.cell(28, 5, "  iii. Reported to Police:")
    pdf.chk("Yes", pre_auth.reported_to_police is True, gap=2)
    pdf.chk("No",  pre_auth.reported_to_police is False, gap=4)
    pdf.cell(14, 5, "iv. FIR no.:")
    pdf.val_box(pre_auth.fir_no, 14, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(60, 5, "v. Injury/Disease caused due to substance abuse / alcohol:")
    pdf.set_text_color(*DARK)
    pdf.chk("Yes", pre_auth.substance_abuse is True, gap=2)
    pdf.chk("No",  pre_auth.substance_abuse is False, gap=6)
    pdf.set_text_color(*GRAY)
    pdf.cell(44, 5, "vi. Test conducted to establish this:")
    pdf.set_text_color(*DARK)
    pdf.chk("Yes", pre_auth.substance_abuse_test_done is True, gap=2)
    pdf.chk("No",  pre_auth.substance_abuse_test_done is False, gap=2)
    pdf.ln(6)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(34, 5, "m) In case of maternity:")
    pdf.set_text_color(*DARK)
    for lbl_m, val_m in [("G", pre_auth.maternity_g), ("P", pre_auth.maternity_p),
                          ("L", pre_auth.maternity_l), ("A", pre_auth.maternity_a)]:
        pdf.cell(6, 5, lbl_m)
        pdf.val_box(val_m, 14, eol=False)
    pdf.set_text_color(*GRAY)
    pdf.cell(30, 5, "  n) Expected date of delivery:")
    pdf.val_box(pre_auth.expected_delivery_date, 30, eol=True)

    # Admission
    pdf.section_bar("DETAILS OF THE PATIENT ADMITTED")
    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(32, 6, "a) Date of admission:")
    pdf.val_box(pre_auth.admission_date, 32, required=r("admission_date"), eol=False)
    pdf.cell(28, 6, "  b) Time of admission:")
    pdf.val_box(pre_auth.admission_time, 22, eol=False)
    pdf.cell(14, 6, "  c) Type:")
    pdf.set_text_color(*DARK)
    pdf.chk("Emergency", pre_auth.admission_type == "Emergency", gap=4)
    pdf.chk("Planned",   pre_auth.admission_type == "Planned",   gap=2)
    pdf.ln(6)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(46, 6, "d) Expected no. of days stay in hospital:")
    pdf.val_box(pre_auth.expected_days_in_hospital, 18, eol=False)
    pdf.cell(26, 6, "  e) Days in ICU:")
    pdf.val_box(pre_auth.days_in_icu, 18, eol=False)
    pdf.cell(22, 6, "  f) Room type:")
    pdf.val_box(pre_auth.room_type, 40, eol=True)

    # =========================================================
    # PAGE 2
    # =========================================================
    pdf.add_page()

    pdf.section_bar("ESTIMATED COST OF HOSPITALIZATION")
    for label, val in [
        ("g) Per Day Room Rent + Nursing & Service charges + Patient's Diet", pre_auth.room_rent_per_day),
        ("h) Expected cost for investigation + diagnostics",                   pre_auth.investigation_diagnostics_cost),
        ("i) ICU Charges",                                                     pre_auth.icu_charges_per_day),
        ("j) OT Charges",                                                      pre_auth.ot_charges),
        ("k) Professional fees (Surgeon + Anaesthetist + Consultation charges)", pre_auth.professional_fees),
        ("L) Medicines + Consumables + cost of Implants",                      pre_auth.medicines_consumables),
        ("m) Other hospital expenses if any",                                  pre_auth.other_hospital_expenses),
        ("n) All inclusive package charges if any applicable",                 pre_auth.package_charges),
    ]:
        pdf.rs_row(label, val)

    pdf.ln(1)
    pdf.set_fill_color(*SECTION_BG)
    pdf.set_text_color(*WHITE)
    pdf.sf(9, bold=True)
    pdf.cell(112, 7, "  o) Sum Total expected cost of hospitalization", fill=True)
    pdf.cell(12,  7, "Rs.", fill=True)
    if pre_auth.total_estimated_cost:
        total_txt = str(int(pre_auth.total_estimated_cost)) if pre_auth.total_estimated_cost == int(pre_auth.total_estimated_cost) else str(pre_auth.total_estimated_cost)
    else:
        total_txt = "[ REQUIRED ]"
    pdf.set_text_color(*(WHITE if pre_auth.total_estimated_cost else MISSING_FG))
    pdf.cell(36, 7, total_txt, border=1, fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(2)

    pdf.section_bar("p. MANDATORY PAST HISTORY OF CHRONIC ILLNESS  (If yes, since Month/Year)")
    for label, chk_val, since in [
        ("1. Diabetes",                          pre_auth.diabetes,           pre_auth.diabetes_since),
        ("2. Heart Disease",                     pre_auth.heart_disease,      pre_auth.heart_disease_since),
        ("3. Hypertension",                      pre_auth.hypertension,       pre_auth.hypertension_since),
        ("4. Hyperlipidemias",                   pre_auth.hyperlipidemias,    pre_auth.hyperlipidemias_since),
        ("5. Osteoarthritis",                    pre_auth.osteoarthritis,     pre_auth.osteoarthritis_since),
        ("6. Asthma / COPD / Bronchitis",        pre_auth.asthma_copd,        pre_auth.asthma_copd_since),
        ("7. Cancer",                            pre_auth.cancer,             pre_auth.cancer_since),
        ("8. Alcohol or drug abuse",             pre_auth.alcohol_drug_abuse, pre_auth.alcohol_drug_abuse_since),
        ("9. Any HIV or STD / related ailments", pre_auth.hiv_std,            pre_auth.hiv_std_since),
    ]:
        pdf.chronic_row(label, chk_val, since)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(38, 5, "10. Any other ailment give details:")
    pdf.set_text_color(*DARK)
    pdf.mbox(pre_auth.other_conditions, w=152, h=8)
    pdf.ln(2)

    pdf.section_bar("DECLARATION  (PLEASE READ VERY CAREFULLY)")
    pdf.sf(7)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4,
        "We confirm having read, understood and agreed to the declaration of this form. "
        "I agree to allow the hospital to submit all original documents pertaining to "
        "hospitalization to the Insurer/TPA after discharge. I agree to sign on the Final Bill "
        "& the Discharge Summary before my discharge. Payment to hospital is governed by the "
        "terms and conditions of the policy. All non-medical expenses and amounts over the "
        "limit authorized by the Insurer/TPA will be paid by me. I hereby declare to abide by "
        "the terms and conditions of the policy and if at any time the facts disclosed by me "
        "are found to be false or incorrect I forfeit my claim.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_text_color(*DARK)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(36, 6, "a) Name of treating doctor:")
    pdf.val_box(pre_auth.doctor_name, 66, eol=False)
    pdf.cell(26, 6, "  b) Qualification:")
    pdf.val_box(pre_auth.doctor_qualification, 52, eol=True)
    pdf.cell(56, 6, "c) Registration No. with State code:")
    pdf.val_box(pre_auth.doctor_registration_no, 60, eol=True)
    pdf.set_text_color(*DARK)

    pdf.sf(8, bold=True)
    pdf.set_text_color(*SECTION_BG)
    pdf.cell(0, 5, "DECLARATION BY THE PATIENT / REPRESENTATIVE",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(1)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(40, 6, "a) Patient's / Insured's name:")
    pdf.val_box(pre_auth.patient_name, 150, required=r("patient_name"), eol=True)
    pdf.cell(18, 6, "b) Contact number:")
    pdf.val_box(pre_auth.contact, 40, required=r("contact"), eol=False)
    pdf.cell(32, 6, "  c) Email ID (Optional):")
    pdf.val_box(pre_auth.patient_email, 80, eol=True)

    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(40, 5, "d) Patient's / Insured's signature:")
    pdf.set_text_color(*DARK)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*BORDER_CLR)
    pdf.cell(56, 16, "", border=1, fill=True)
    pdf.cell(14, 5, "   Date:")
    pdf.val_box("", 28, eol=False)
    pdf.cell(10, 5, "  Time:")
    pdf.val_box("", 22, eol=True)
    pdf.ln(3)

    pdf.sf(8, bold=True)
    pdf.set_text_color(*SECTION_BG)
    pdf.cell(0, 5, "HOSPITAL DECLARATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(60, 60, 60)
    pdf.sf(7)
    pdf.multi_cell(0, 4,
        "We have no objection to any authorized TPA / Insurance Company official verifying "
        "documents pertaining to hospitalization. All valid original documents duly "
        "countersigned by the insured / patient as per the checklist will be sent to TPA / "
        "Insurance Company within 7 days of the patient's discharge. We agree that TPA / "
        "Insurance Company will not be liable to make payment in the event of any discrepancy "
        "between the facts in this form and discharge summary or other documents. The patient "
        "declaration has been signed by the patient or by his representative in our presence. "
        "We will abide by the terms and conditions agreed in the MOU.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_text_color(*DARK)

    pdf.sf(8, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(95, 5, "Hospital seal:")
    pdf.cell(0,  5, "Doctor's signature:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*BORDER_CLR)
    pdf.cell(90, 18, "", border=1, fill=True)
    pdf.cell(5,  18, "")
    pdf.cell(85, 18, "", border=1, fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.sf(7, bold=True)
    pdf.set_text_color(*GRAY)
    pdf.cell(14, 5, "Date:")
    pdf.val_box("", 30, eol=False)
    pdf.cell(14, 5, "  Time:")
    pdf.val_box("", 20, eol=True)

    return bytes(pdf.output())
