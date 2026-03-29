# Normal-Ice: AI-Powered Healthcare Claim & Data Management Platform

**Normal-Ice** is an enterprise-grade healthcare management system designed to bridge the gap between clinical documentation and insurance financial workflows. By leveraging **Google Gemini AI (v2.5 Flash)** and **FastAPI**, it automates the transformation of unstructured medical documents into standardized **FHIR R4** resources while providing a unified platform for medical staff and finance managers to collaborate on claim integrity.

### Features

**Customised Forms for Insurance Firms**
<img width="1081" height="691" alt="Screenshot 2026-03-29 184112" src="https://github.com/user-attachments/assets/df8bb56e-5334-4284-b615-1759fb541420" />

**Email Intimation**
![WhatsApp Image 2026-03-29 at 6 45 37 PM](https://github.com/user-attachments/assets/32651f77-81c2-42fe-aaf6-0cd6786febf2)

---

## Key Features

### 1. Clinical-to-Financial Intelligence
- **Intelligent OCR & Structuring**: Dual-strategy extraction (DocTR + PyMuPDF) combined with Gemini 2.5 Flash to convert raw medical PDFs into structured clinical data.
- **Discrepancy & Deduction Flagging**: AI-powered evaluation of medical reports to identify clinical mismatches or potential insurance deductions *before* finalization.
- **Financial Audit Engine**: Automatically reconciles final hospital bills against pre-authorization limits and enhancement history, providing narrative justifications for every charge.

### 2. Integrated Departmental Workflows
Normal-Ice integrates the **Medical** and **Finance** departments into a single efficient ecosystem:
- **Medical Staff Portal**: Focused on patient care, document uploads, and clinical data extraction. Staff can generate standardized pre-auth forms (e.g., Medi Assist Part C) instantly.
- **Finance Manager Portal**: Focused on revenue cycle management. Finance can verify TPA payments, track settlements, and identify billing leaks.
- **Inter-departmental Relay**: Finance can relay settlement status and deduction reasons back to medical staff to improve documentation quality.

### 3. Insurance & Compliance Standards
- **Standardized Templates**: Built-in support for multiple insurance provider formats, including **Medi Assist (Part C Revised)**, **IRDAI MIS** reporting, and **NHA/PMJAY** templates.
- **FHIR R4 Compliance**: All clinical data is exported as valid FHIR bundles (Patient, Observation, Condition, MedicationRequest).
- **Per-User Tracking**: Personalized activity tracking for different roles (e.g., Dr. Sharma, TPA Manager) to ensure accountability and audit trails.

---

## Architecture & Tech Stack

- **Backend**: FastAPI (Python 3.10+), Gemini 2.5 Flash, DocTR (OCR), Supabase (PostgreSQL).
- **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons.
- **Data Standards**: FHIR R4, IRDAI Health Insurance Regulations 2016.

---

## Installation & OS-Specific Setup

### Prerequisites
- **Python 3.10+** and **Node.js 18+**
- **Google Gemini API Key** (Generative AI)
- **Supabase Account** (PostgreSQL Database)

### 1. Backend Setup (Windows/Linux/macOS)

#### **On Linux / macOS:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **On Windows:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Environment Configuration:**
Create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
FRONTEND_URL=http://localhost:5173
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

##  How to Use Normal-Ice

### Step 1: Login
Choose your role on the login page:
- **Hospital Staff**: Use credentials like `staff` / `staff123` to access the clinical upload and patient management dashboard.
- **Finance Manager**: Use credentials like `finance` / `finance123` to access the MIS reports and settlement verification portal.

### Step 2: Clinical Data Processing (Medical Staff)
1. **Upload**: Drag and drop a clinical PDF (Lab Report, Prescription, or Discharge Summary).
2. **Review**: The AI will extract data and flag any discrepancies (e.g., "Patient Name Mismatch" or "Missing ICD-10 Code").
3. **FHIR Export**: View or download the standardized FHIR R4 JSON for EMR integration.

### Step 3: Insurance Lifecycle (Medical Staff)
1. **Pre-Auth**: Fill the digital Pre-Auth form; the system will auto-populate clinical fields from the uploaded reports.
2. **Enhancement**: Request financial enhancements if the treatment plan changes (e.g., moving from Ward to ICU).
3. **Download PDF**: Generate a perfectly formatted Medi Assist Part C form for submission.

![WhatsApp Image 2026-03-29 at 4 37 29 PM(1)](https://github.com/user-attachments/assets/bcb56e70-574f-49e2-b57f-38fa37ad6b26)

### Step 4: Financial Auditing (Finance Department)
1. **Case View**: Open a case to see the full clinical history and financial trajectory.
2. **Audit Report**: Run the **AI Financial Audit** to see a charge-by-charge comparison of the "Estimated" vs. "Billed" amounts.
3. **Verify Payments**: Update settlement records with deduction amounts and TPA remarks.
4. **Relay**: The system notifies medical staff of settled claims or pending documentation needs.

### Step 5: MIS Reporting
Finance managers can download **Weekly/Monthly/Yearly MIS Reports** in Excel format, following the IRDAI standardised TPA reporting format.

---

##  Project Structure

```text
Normal-Ice/
├── backend/                # FastAPI Core
│   ├── app/
│   │   ├── routes/         # API (settlement, mis, financial_audit)
│   │   ├── services/       # AI Logic (llm.py, ocr_strategies, pdf_generator)
│   │   └── data/           # Reference Cost Estimates & Audits
├── frontend/               # React Dashboard
│   ├── src/
│   │   ├── components/     # Role-based UI (FinanceManagerPage, LoginPage)
│   │   └── services/       # API Integration
└── dummy_data/             # Sample PDFs for testing
```

---

## License
This project is for demonstration and production-ready MVP purposes. All rights reserved.

