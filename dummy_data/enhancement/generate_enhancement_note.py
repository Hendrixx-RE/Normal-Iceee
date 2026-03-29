"""
Enhancement Request -- Doctor's Note Generator
===============================================
Generates a realistic clinical enhancement note for Rahul Sharma's case.

Scenario:
  Original pre-auth: Laparoscopic Cholecystectomy for Acute Calculous Cholecystitis
  New finding (intra-op): Small CBD stone (5 mm) found on intraoperative cholangiogram
  -- not detected on pre-admission USG.
  Requires: ERCP + CBD stone extraction + endoscopic sphincterotomy (post-op Day 2)
  Extended stay: +2 days (3 -> 5 days total)
  Updated diagnosis: K80.42 -- Calculus of common bile duct with acute cholecystitis
  Revised estimated cost: Rs1,48,500  (original pre-auth: Rs75,916)

Output:
  dummy_data/enhancement/rahul_sharma_enhancement_note.pdf

Run:
  backend\\venv\\Scripts\\python.exe dummy_data\\enhancement\\generate_enhancement_note.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fpdf import FPDF, XPos, YPos
from datetime import date

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
NAVY        = (30,  58, 138)   # blue-900
BLUE        = (37,  99, 235)   # blue-600
LIGHT_BLUE  = (219, 234, 254)  # blue-100
RED         = (185,  28,  28)  # red-700
AMBER       = (217, 119,   6)  # amber-600
AMBER_BG    = (254, 243, 199)  # amber-100
GREEN       = ( 22, 163,  74)  # green-600
GREEN_BG    = (220, 252, 231)  # green-100
DARK        = ( 15,  23,  42)  # slate-900
LABEL       = (100, 116, 139)  # slate-500
BORDER      = (203, 213, 225)  # slate-300
WHITE       = (255, 255, 255)
LIGHT_GRAY  = (248, 250, 252)  # slate-50
ALT_ROW     = (241, 245, 249)  # slate-100
TOTAL_BG    = (219, 234, 254)  # blue-100


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------
class EnhancementNotePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(16, 28, 16)

    def header(self):
        # Blue banner
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 24, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*WHITE)
        self.cell(0, 7, "Ruby Hall Clinic", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, "40 Sassoon Road, Pune, Maharashtra 411001  |  ROHINI: H-RH-PUN-003",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(4)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*LABEL)
        self.cell(
            0, 5,
            f"ENHANCEMENT REQUEST -- CONFIDENTIAL MEDICAL DOCUMENT  |  Page {self.page_no()}",
            align="C",
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def doc_title(self, title):
        self.set_fill_color(*LIGHT_GRAY)
        self.rect(16, self.get_y(), 178, 10, "F")
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*NAVY)
        self.cell(178, 10, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(2)

    def section(self, title):
        self.ln(3)
        self.set_fill_color(*BLUE)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.cell(178, 6, f"  {title.upper()}", fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(2)

    def kv(self, label, value, col_w=55):
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*LABEL)
        self.cell(col_w, 5.5, label)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*DARK)
        self.cell(0, 5.5, str(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def kv2(self, pairs, col_w=55):
        """Two key-value pairs side by side."""
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*LABEL)
        self.cell(col_w, 5.5, pairs[0][0])
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*DARK)
        self.cell(89 - col_w, 5.5, str(pairs[0][1]))
        if len(pairs) > 1:
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*LABEL)
            self.cell(col_w, 5.5, pairs[1][0])
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*DARK)
            self.cell(0, 5.5, str(pairs[1][1]))
        self.ln(5.5)

    def alert_box(self, title, lines, bg, border_clr, text_clr):
        """Coloured alert/info box."""
        self.ln(2)
        x, y = self.get_x(), self.get_y()
        line_h = 5.5
        box_h = 8 + len(lines) * line_h
        self.set_fill_color(*bg)
        self.set_draw_color(*border_clr)
        self.rect(x, y, 178, box_h, "FD")
        self.set_xy(x + 3, y + 2)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*border_clr)
        self.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(x + 3)
        for line in lines:
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*text_clr)
            self.cell(0, line_h, f"  {line}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_x(x + 3)
        self.set_text_color(*DARK)
        self.set_draw_color(*BORDER)
        self.ln(2)

    def paragraph(self, text, label=None):
        if label:
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*LABEL)
            self.cell(0, 5.5, label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*DARK)
        self.multi_cell(178, 5.5, text)
        self.ln(1)

    def cost_table(self, rows, advance, tpa_amt, patient_pay):
        """Bill / cost breakdown table."""
        headers = ["Service / Item", "Gross (Rs)", "Disc (Rs)", "Net (Rs)"]
        widths  = [100, 26, 26, 26]

        # Header row
        self.set_fill_color(*BLUE)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*WHITE)
        for h, w in zip(headers, widths):
            self.cell(w, 7, h, border=0, align="C", fill=True)
        self.ln(7)

        # Data rows
        for i, (svc, gross, disc, net) in enumerate(rows):
            bg = ALT_ROW if i % 2 else WHITE
            self.set_fill_color(*bg)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*DARK)
            self.cell(widths[0], 6, f"  {svc}", fill=True)
            self.cell(widths[1], 6, f"{gross:,.0f}", align="R", fill=True)
            self.cell(widths[2], 6, f"{disc:,.0f}",  align="R", fill=True)
            self.cell(widths[3], 6, f"{net:,.0f}",   align="R", fill=True)
            self.ln(6)

        # Totals
        gross_total = sum(r[1] for r in rows)
        disc_total  = sum(r[2] for r in rows)
        net_total   = sum(r[3] for r in rows)

        self.set_fill_color(*ALT_ROW)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*DARK)
        self.cell(widths[0], 6.5, "  GROSS TOTAL", fill=True)
        self.cell(widths[1], 6.5, f"{gross_total:,.0f}", align="R", fill=True)
        self.cell(widths[2], 6.5, f"{disc_total:,.0f}",  align="R", fill=True)
        self.cell(widths[3], 6.5, f"{net_total:,.0f}",   align="R", fill=True)
        self.ln(6.5)

        # Summary box
        self.ln(2)
        self.set_fill_color(*TOTAL_BG)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*NAVY)
        entries = [
            ("Net Total (after discount)",   f"Rs {net_total:,.0f}"),
            ("Advance Paid",                  f"Rs {advance:,.0f}"),
            ("TPA Payable Amount",            f"Rs {tpa_amt:,.0f}"),
            ("Patient Payable Amount",        f"Rs {patient_pay:,.0f}"),
        ]
        for label, val in entries:
            self.set_fill_color(*TOTAL_BG)
            self.cell(120, 7, f"  {label}", fill=True)
            self.cell(58,  7, val, align="R", fill=True)
            self.ln(7)


# ---------------------------------------------------------------------------
# Build the document
# ---------------------------------------------------------------------------
def build_enhancement_note(output_path: str):
    today = "22-Mar-2026"     # Day after post-op Day 1 -- CBD stone found intra-op,
                               # ERCP planned for Day 3
    pdf = EnhancementNotePDF()
    pdf.add_page()

    # ── Document title ───────────────────────────────────────────────────────
    pdf.doc_title("ENHANCEMENT REQUEST -- CLINICAL JUSTIFICATION NOTE")
    pdf.ln(1)

    # ── Enhancement metadata ─────────────────────────────────────────────────
    pdf.section("Enhancement Request Details")
    pdf.kv2([("Enhancement No.",    "ENH-001 / IP26001235"), ("Date of Request",  today)])
    pdf.kv2([("Pre-Auth Ref. No.",  "PA-RHC-2026-1121"),     ("TPA",              "Medi Assist Insurance TPA")])
    pdf.kv2([("Status",             "SUBMITTED -- PENDING TPA APPROVAL"), ("Priority", "URGENT")])

    # ── Patient details ──────────────────────────────────────────────────────
    pdf.section("Patient & Admission Details")
    pdf.kv2([("Patient Name",       "Rahul Sharma"),              ("UHID",         "RHC2026001234")])
    pdf.kv2([("ABHA ID",            "12-3456-7890-1234"),         ("Age / Sex",    "45 Y / Male")])
    pdf.kv2([("Date of Birth",      "12-Aug-1980"),               ("Policy No.",   "HDFC123456")])
    pdf.kv2([("Insurance Company",  "HDFC ERGO General Insurance"), ("Ward",       "Surgical Ward B, Bed 204")])
    pdf.kv2([("Admission Date",     "18-Mar-2026"),               ("Bill No.",     "IP26001235")])

    # ── Treating doctor ──────────────────────────────────────────────────────
    pdf.section("Treating Consultant")
    pdf.kv2([("Consultant Surgeon", "Dr. Sanjay Kulkarni"),       ("Reg. No.",     "MH-47821")])
    pdf.kv2([("Specialisation",     "General & Laparoscopic Surgery"), ("Dept.",   "Surgical Gastroenterology")])
    pdf.kv2([("Co-Consultant",      "Dr. Meera Joshi"),           ("Reg. No.",     "MH-63204")])
    pdf.kv2([("Co-Specialisation",  "Gastroenterology (ERCP)"),   ("Dept.",        "Gastroenterology & Hepatology")])

    # ── Original pre-auth summary ────────────────────────────────────────────
    pdf.section("Original Pre-Authorization Summary")
    pdf.kv("Original Diagnosis",    "Acute Calculous Cholecystitis with multiple gallstones (largest 14 mm)")
    pdf.kv("ICD-10 Code",           "K81.0 -- Acute cholecystitis")
    pdf.kv("Approved Procedure",    "Laparoscopic Cholecystectomy (4-port technique)")
    pdf.kv("Approved Est. Cost",    "Rs 75,916")
    pdf.kv("Approved Stay",         "3 days (18-Mar-2026 to 21-Mar-2026)")

    # ── New clinical finding (the key section) ───────────────────────────────
    pdf.section("New Clinical Findings Requiring Enhancement")

    pdf.alert_box(
        "INTRA-OPERATIVE FINDING -- INCIDENTAL CBD CALCULUS",
        [
            "During laparoscopic cholecystectomy on 19-Mar-2026, intraoperative cholangiography",
            "revealed a filling defect of 5 mm in the common bile duct (CBD) -- consistent with",
            "a CBD stone not detected on pre-operative USG abdomen.",
            "Procedure was safely completed. CBD stone requires ERCP + sphincterotomy + stone",
            "extraction, scheduled for post-op Day 3 (21-Mar-2026) by Dr. Meera Joshi.",
        ],
        AMBER_BG, AMBER, (92, 45, 0),
    )

    pdf.paragraph(
        "Pre-operative USG Abdomen (18-Mar-2026) showed no CBD dilation (CBD diameter 5.2 mm, "
        "normal range <6 mm) and no obvious filling defects. CBD stones can be isoechoic to bile "
        "and easily missed on standard USG when duct diameter is not significantly dilated. "
        "Intraoperative cholangiography -- the gold standard -- revealed the calculus. "
        "The finding is a known complication / incidental discovery, occurring in approximately "
        "10-15% of all cholecystectomy cases per published literature (Lancet 2020).",
        label="Clinical Justification:",
    )

    pdf.paragraph(
        "Pre-operative LFT showed mildly elevated bilirubin (1.8 mg/dL) and AST/ALT elevation, "
        "which in retrospect may have been an early marker of CBD obstruction. Serum amylase "
        "drawn post-op on Day 1: 210 U/L (mildly elevated, consistent with CBD stone). "
        "MRCP confirmed the calculus on Day 2 (20-Mar-2026): single CBD stone, 5 mm, "
        "lower CBD, no pneumobilia, no intrahepatic duct dilation.",
        label="Supporting Investigations:",
    )

    # ── Updated diagnosis & procedure ────────────────────────────────────────
    pdf.section("Updated Diagnosis & Treatment Plan")
    pdf.kv("Updated Diagnosis",
           "Acute Calculous Cholecystitis + Choledocholithiasis (CBD stone 5 mm)")
    pdf.kv("Updated ICD-10 Code",    "K80.42 -- Calculus of common bile duct with acute cholecystitis")
    pdf.kv("Updated ICD-10 PCS",     "0F994ZX -- Drainage of common bile duct (ERCP approach)")
    pdf.kv("Additional Procedure",   "ERCP + Endoscopic Sphincterotomy + CBD Stone Extraction")
    pdf.kv("Updated Line of Tx",     "Surgical (Lap. Cholecystectomy -- completed) + Endoscopic (ERCP -- planned 21-Mar)")
    pdf.kv("Revised Expected Stay",  "5 days (18-Mar-2026 to 23-Mar-2026) -- extension of +2 days")

    pdf.alert_box(
        "ERCP PROCEDURE PLAN",
        [
            "Date: 21-Mar-2026  |  Gastroenterologist: Dr. Meera Joshi  |  Anaesthesia: IV Sedation",
            "Procedure: Diagnostic ERCP -> Endoscopic Sphincterotomy -> Stone Extraction (Dormia basket)",
            "Estimated duration: 45-60 minutes.  Expected success rate: >95% (stone <10 mm).",
            "Post-ERCP monitoring: 24 hours.  Discharge planned: 23-Mar-2026 if no complications.",
        ],
        GREEN_BG, GREEN, (20, 80, 40),
    )

    # ── Revised cost estimate ─────────────────────────────────────────────────
    pdf.section("Revised Cost Estimate")

    bill_rows = [
        # (Service, Gross, Discount, Net)
        ("Room Charges (Surgical Ward x 5 days)",      15000.0, 1200.0, 13800.0),
        ("Admission & Nursing Charges",                  1500.0,    0.0,  1500.0),
        ("OT Charges -- Lap. Cholecystectomy",           28000.0, 2240.0, 25760.0),
        ("Surgeon Fees -- Dr. Kulkarni (Lap. Chole.)",   20000.0, 1600.0, 18400.0),
        ("Anaesthesia Fees -- Lap. Chole.",               8000.0,  640.0,  7360.0),
        ("ERCP Procedure Charges",                      25000.0, 2000.0, 23000.0),
        ("Endoscopist Fees -- Dr. Joshi (ERCP)",         15000.0, 1200.0, 13800.0),
        ("Anaesthesia / Sedation -- ERCP",                4000.0,  320.0,  3680.0),
        ("Pharmacy & Consumables",                       12000.0,  960.0, 11040.0),
        ("Pathology (CBC, LFT, Amylase, repeat)",         4800.0,  384.0,  4416.0),
        ("Radiology (USG + MRCP)",                        6500.0,  520.0,  5980.0),
        ("Histopathology (gallbladder specimen)",          1800.0,  144.0,  1656.0),
        ("Dietician & Allied Health",                     1500.0,    0.0,  1500.0),
        ("Medical Records & Admin",                        500.0,    0.0,    500.0),
    ]

    pdf.cost_table(
        rows=bill_rows,
        advance=5000.0,
        tpa_amt=138392.0,
        patient_pay=0.0,
    )

    # ── Cost comparison ───────────────────────────────────────────────────────
    pdf.ln(3)
    pdf.section("Cost Comparison -- Original vs Revised")
    pdf.kv2([("Original Pre-Auth Approved Amount",  "Rs 75,916"),
             ("Revised Total Estimated Cost",        "Rs 1,48,392")])
    pdf.kv2([("Enhancement Amount Requested",        "Rs 72,476"),
             ("% Increase over Original",            "95.5%")])
    pdf.kv("Reason for Cost Increase",
           "Additional ERCP + endoscopist + sedation + extended 2-day stay + repeat investigations")

    # ── Declaration ──────────────────────────────────────────────────────────
    pdf.section("Consultant's Declaration")
    pdf.paragraph(
        "I, Dr. Sanjay Kulkarni (MH-47821), Consultant General & Laparoscopic Surgeon at "
        "Ruby Hall Clinic, Pune, hereby certify that the above enhancement is medically "
        "necessary due to an incidental intraoperative finding of a common bile duct stone "
        "that was not apparent on pre-operative imaging. The revised treatment plan and cost "
        "estimate represent the minimum necessary care to ensure complete treatment and prevent "
        "complications including cholangitis, biliary pancreatitis, and secondary CBD obstruction. "
        "The ERCP procedure is the least invasive and most clinically appropriate intervention."
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK)
    pdf.cell(89, 5, "Consultant Surgeon Signature & Stamp")
    pdf.cell(89, 5, "Co-Consultant / ERCP Specialist Signature")
    pdf.ln(14)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*LABEL)
    pdf.cell(89, 5, "Dr. Sanjay Kulkarni -- MH-47821")
    pdf.cell(89, 5, "Dr. Meera Joshi -- MH-63204")
    pdf.ln(5)
    pdf.cell(89, 5, f"Date: {today}  |  Ruby Hall Clinic, Pune")
    pdf.cell(89, 5, f"Date: {today}  |  Ruby Hall Clinic, Pune")
    pdf.ln(10)

    # ── Hospital authorization ────────────────────────────────────────────────
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*BORDER)
    pdf.rect(16, pdf.get_y(), 178, 18, "FD")
    pdf.set_x(19)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "HOSPITAL AUTHORIZATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(19)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 5,
             "This enhancement request has been reviewed and approved for submission to TPA by the "
             "Medical Records & Insurance Department, Ruby Hall Clinic.")
    pdf.ln(10)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "rahul_sharma_enhancement_note.pdf")
    build_enhancement_note(out)
