# LEXIAI Backend - Phase 2 Plan (Document Ingestion)

## 1. Current Implementation
- **Frontend**: `src/app/(app)/upload/page.tsx` and `src/app/(app)/documents/page.tsx` are using mock state/arrays. No actual backend integration is present.
- **Backend**: Basic auth is working. The `documents.py` router and `document_service.py` are empty placeholders. The `Document` and `DocumentAnalysis` models exist but need fields for full text and processing status details.

## 2. Files to Modify
- `backend/app/models/analysis.py`: Add `extracted_text`, `page_text`, `processing_method`, and `processing_error`.
- `backend/app/schemas/document.py`: Define request/response schemas for document endpoints.
- `backend/app/routers/documents.py`: Implement the endpoints (`/upload`, `/`, `/{document_id}`, `/jobs/{job_id}`).
- `backend/app/services/document_service.py`: Implement parsing logic (PDF, DOCX, TXT, OCR).
- `backend/requirements.txt`: Add PyMuPDF, python-docx, pytesseract, Pillow.
- `backend/app/main.py`: Ensure `documents` router is included.
- `src/app/(app)/upload/page.tsx`: Connect to the real upload endpoint.
- `src/app/(app)/documents/page.tsx`: Fetch real documents.

## 3. Files to Create
- `backend/tests/test_documents.py`: Unit tests for the new ingestion pipeline.

## 4. Dependencies Required
- `pymupdf` (for PDF text extraction)
- `python-docx` (for DOCX extraction)
- `pytesseract` and `Pillow` (for OCR on scanned PDFs)
- `python-multipart` (already in requirements, needed for `UploadFile`)

## 5. Database Changes
- Extend `DocumentAnalysis` with:
  - `extracted_text` (String/Text)
  - `page_text` (JSON)
  - `processing_method` (String)
  - `processing_error` (String)

## 6. Upload Flow
1. User drops a file in the UI (`/upload`).
2. Frontend sends `multipart/form-data` to `POST /api/v1/documents/upload`.
3. Backend validates MIME/extension/size, saves file securely to `uploads/` with a UUID filename, creates a `Document` with status `processing`, and returns the `document_id`.
4. Backend triggers a background task in `document_service.py` to:
   - Extract text (via `pymupdf`, `python-docx`, or standard `open()`).
   - If PDF has < 50 chars, trigger Tesseract OCR (gracefully fail if tesseract is missing).
   - Create `DocumentAnalysis` with the extracted text.
   - Update `Document` status to `completed` (or `failed`).
5. Frontend polls `GET /api/v1/documents/jobs/{document_id}`. Once completed, redirects to analysis/dashboard.
