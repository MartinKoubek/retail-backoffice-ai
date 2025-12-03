# Retail Back-Office AI Automation Demo — Requirements Document

## 1. Project Overview
The goal of this demo project is to showcase a small, functional AI-powered system that automates back-office retail workflows.  
The system should demonstrate:

- Document ingestion  
- AI-driven data extraction  
- Automated rule-based validation  
- AI-assisted corrections  
- Final structured output and reporting  

The demo must be small enough to run locally or on a simple web deployment, but professional enough to demonstrate practical business value.

## 2. Objectives
The demo should clearly show how AI can:

1. Reduce manual administrative work
2. Extract structured information from unstructured documents
3. Detect errors and inconsistencies
4. Propose corrections or missing data
5. Generate a final summarized report

The target audience is retail/fleet/logistics process teams evaluating AI automation.

## 3. Functional Requirements

### 3.1 Document Upload
- User can upload a document (PDF, image, or plain text).
- System must accept at least these formats: `.pdf`, `.png`, `.jpg`, `.txt`.

### 3.2 AI Data Extraction
The system must extract structured fields from the document, including:

- Document date  
- Document ID or reference number  
- Supplier or sender name  
- List of items:
  - SKU / product code  
  - Name (if present)  
  - Quantity  
  - Price (optional)

Output must be provided as **JSON**.

### 3.3 Validation Rules
The system must evaluate the extracted data using simple rule-based checks:

- Check if mandatory fields are missing (date, ID, SKU, quantity).
- Check if quantities are > 0.
- Check for inconsistent or incomplete item lines.
- Validate SKU against a small local product catalog (CSV).
- Identify anomalies or suspicious values (e.g., quantity too large).

Validation results must be returned as a list of **errors** and **warnings**.

### 3.4 AI Correction Suggestions
The system must use an LLM to propose corrections, such as:

- Guessing missing fields based on context.
- Suggesting corrections for suspicious or incomplete items.
- Recommending a next action (approve, reject, request correction).

Suggestions must be human-readable and appear in the UI.

### 3.5 Report Generation
The system must generate a final report containing:

- Extracted data (JSON)
- All detected validation issues
- AI recommendations
- A short summary of the document

Report can be delivered as:
- HTML on-screen output, **and optionally**
- Downloadable PDF or JSON file.

### 3.6 Minimal User Interface (UI)
The UI must include:

- File upload control
- “Process Document” button
- Panels for:
  - Extracted data  
  - Validation results  
  - AI suggestions  
  - Final report  

UI frameworks allowed:
- Streamlit (preferred for speed)  
- Gradio  
- Or minimal HTML+FastAPI  

## 4. Non-Functional Requirements

### 4.1 Simplicity
- The system must be small, easy to run, and demonstration-friendly.
- No complex infrastructure or external databases.

### 4.2 Transparency
- Every stage must clearly show **what the system did**:
  - What was extracted  
  - What rules failed  
  - What AI suggested  

### 4.3 Portability
- The project must run locally using Python 3.10+.
- All dependencies must be declared in `requirements.txt`.

### 4.4 AI Model Usage
Allowed:
- OpenAI (GPT-4o mini, GPT-4o)
- Anthropic  
- Mistral  
- Or any locally runnable LLM via API

AI calls must be isolated inside a single module (for easy replacement).

## 5. Inputs & Outputs

### Input
- User-uploaded document
- Optional: local CSV `products.csv` for SKU validation

### Output
- Extracted structured JSON  
- Validation errors & warnings  
- AI suggestions  
- Final HTML/PDF report  

## 6. Acceptance Criteria
The demo is considered complete if:

1. A document can be uploaded and processed end-to-end.  
2. The system extracts structured data into JSON.  
3. At least 3–5 validation rules execute correctly.  
4. The AI produces meaningful suggestions for fixing issues.  
5. A final combined report is presented to the user.  
6. The entire project runs from a single command (e.g., `streamlit run app.py`).  
7. Repository contains:
   - `README.md`  
   - `requirements.md`  
   - `requirements.txt`  
   - sample documents  
   - clear folder structure  

## 7. Deliverables
- Source code  
- Working local demo  
- `README.md` with:
  - setup steps  
  - screenshots  
  - explanation of business value  
