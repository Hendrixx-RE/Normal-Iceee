# Healthcare FHIR MVP - Instructional Context

This document provides a comprehensive overview of the Healthcare FHIR MVP project to guide AI interactions and development.

## 📋 Project Overview

The **Healthcare FHIR MVP** is an AI-powered clinical data processing system. It specializes in converting unstructured PDF documents (specifically Lab Reports and Prescriptions) into standardized **FHIR R4 (Fast Healthcare Interoperability Resources)** bundles.

### Core Objectives
- **PDF Extraction**: Dual-strategy OCR (text-based and image-based) to extract raw text from clinical PDFs.
- **AI Structured Extraction**: Using **Gemini 2.5 Flash** to parse raw medical text into structured JSON.
- **FHIR R4 Mapping**: Converting structured medical data into valid FHIR R4 resources.
- **Batch Processing**: Handling large documents (40+ pages) by splitting them into manageable chunks.

### Tech Stack
- **Backend**: Python 3.10+, FastAPI, Google Gemini AI (Generative AI SDK), pdfplumber, PyMuPDF, fhir.resources.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Axios.

---

## 🏗️ Architecture & Project Structure

The project follows a monorepo structure with clear separation between the backend and frontend.

### Backend (`/backend`)
- **`app/main.py`**: FastAPI application entry point and CORS configuration.
- **`app/config.py`**: Configuration settings (Gemini model, file limits, environment variables).
- **`app/routes/process.py`**: Primary API endpoints (`/api/health` and `/api/process-pdf`).
- **`app/services/`**: Core business logic:
    - `ocr.py`: Dual-strategy PDF text extraction.
    - `llm.py`: Gemini AI integration, prompts, and structured data extraction.
    - `fhir_mapper.py`: Logic to transform structured data into FHIR R4 bundles.
    - `document_splitter.py`: Smart document splitting for large file batch processing.
- **`app/models/schemas.py`**: Pydantic v2 models for data validation and API responses.

### Frontend (`/frontend`)
- **`src/App.tsx`**: Main application component and state management.
- **`src/components/`**: UI components (FileUpload, ResultsView, JsonViewer).
- **`src/services/api.ts`**: Axios client for backend communication.

---

## 🔄 Data Processing Pipeline

When a PDF is uploaded to `/api/process-pdf`, it follows this workflow:

1.  **Validation**: File type (.pdf) and size (max 10MB) checks.
2.  **OCR Extraction (`ocr.py`)**:
    - **Strategy 1 (pdfplumber)**: Fast extraction for text-based PDFs.
    - **Strategy 2 (PyMuPDF)**: Fallback for scanned/image-based PDFs if Strategy 1 yields < 50 characters.
3.  **Batch Detection**: If extracted text > **20,000 characters**, it triggers the batch processing flow.
4.  **Smart Splitting (`document_splitter.py`)**:
    - Priority: Marker-based (e.g., "END OF REPORT") -> Page-break -> Size-based (15,000 chars per chunk).
5.  **AI Extraction (`llm.py`)**: 
    - Uses `gemini-2.5-flash` with temperature `0.1`.
    - Automatically detects if the document is a `lab_report` or `prescription` based on keywords.
6.  **FHIR Mapping (`fhir_mapper.py`)**:
    - **Lab Reports**: Generates Patient, Practitioner, Organization, Observation, DiagnosticReport, and Condition.
    - **Prescriptions**: Generates Patient, Practitioner, Organization, Medication, MedicationRequest, and Condition.
7.  **Merging**: If batch processed, structured data and FHIR bundles are merged before the final response.

---

## 🚀 Building and Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
# Create .env with GEMINI_API_KEY
python -m app.main
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ Development Conventions

### Backend
- **Asynchronous Programming**: Use `async`/`await` for all I/O bound operations.
- **Data Validation**: Use Pydantic models in `schemas.py` for all structured data.
- **Logging**: Follow the format established in `main.py`.
- **JSON Mode**: LLM prompts are designed to return raw JSON; ensure `response_mime_type: "application/json"` is used in Gemini config.

### Frontend
- **TypeScript**: Strictly type all props, state, and API responses.
- **Tailwind CSS**: Follow dark mode patterns (e.g., `dark:bg-slate-950`).
- **State**: Use React `useState` for UI states (processing, results, errors).

---

## 🔑 Key Files & Entry Points

- **API Entry**: `backend/app/main.py`
- **Processing Logic**: `backend/app/routes/process.py`
- **AI Prompt Logic**: `backend/app/services/llm.py`
- **FHIR Generation**: `backend/app/services/fhir_mapper.py`
- **Frontend Entry**: `frontend/src/App.tsx`

---

## 📝 Important Notes for AI Interactions
- **API Keys**: Never hardcode keys. Use `.env` files.
- **FHIR Standards**: Adhere strictly to FHIR R4 specifications.
- **Thresholds**: Batch processing starts at **20,000 chars**; LLM chunks are capped at **15,000 chars**.
- **OCR Logic**: If extraction is poor, check `backend/app/services/ocr_strategies/` for advanced image-based OCR options.
