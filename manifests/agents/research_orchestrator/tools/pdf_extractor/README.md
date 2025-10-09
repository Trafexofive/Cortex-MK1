# PDF Extractor Tool

**PDF text extraction with optional OCR support**

## Overview

Extracts text from PDF files. Supports both simple text extraction and OCR for scanned documents. This is a local tool for the research_orchestrator agent.

## Operations

- Simple text extraction from text-based PDFs
- OCR extraction for scanned/image-based PDFs

## Usage

```bash
# Simple extraction
python3 scripts/pdf_extractor.py '{"pdf_path": "/path/to/document.pdf"}'

# With OCR
python3 scripts/pdf_extractor.py '{
  "pdf_path": "/path/to/scanned.pdf",
  "use_ocr": true
}'

# Health check
python3 scripts/pdf_extractor.py --health-check
```

## Output

```json
{
  "success": true,
  "text": "Extracted text content...",
  "pdf_path": "/path/to/document.pdf",
  "method": "simple",
  "character_count": 1234
}
```

## Production Integration

For production use, integrate with:
- **PyPDF2** or **pdfplumber** - For text extraction
- **pytesseract** + **Tesseract OCR** - For OCR support
- **pdf2image** - For PDF to image conversion

Install dependencies:
```bash
pip install PyPDF2 pdfplumber pytesseract pdf2image
```

## Current Implementation

The current implementation is a placeholder that demonstrates the interface. In production, replace with actual PDF parsing libraries.

## Manifest

- **Path:** `agents/research_orchestrator/tools/pdf_extractor/tool.yml`
- **Version:** 1.0
- **State:** stable
- **Author:** PRAETORIAN_CHIMERA
