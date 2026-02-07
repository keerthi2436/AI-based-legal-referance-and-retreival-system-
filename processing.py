# src/ingestion/processing.py

import os
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract

RAW_DIR = "data/raw"
RAW_TEXT_DIR = "data/processed/raw_text"

os.makedirs(RAW_TEXT_DIR, exist_ok=True)

def extract_pdf_content(pdf_path):
    """
    Extracts text and metadata from a PDF.
    Tries PyMuPDF first, with a fallback to pdfminer.
    """
    metadata = {}
    try:
        with fitz.open(pdf_path) as doc:
            text = "\n".join([page.get_text("text") for page in doc])
            metadata = doc.metadata  # Capture metadata here
            return text, metadata
    except Exception:
        # Fallback to pdfminer
        return pdfminer_extract(pdf_path), {}

def process_pdfs():
    """Loop through PDFs and save raw text outputs."""
    for fname in os.listdir(RAW_DIR):
        if not fname.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(RAW_DIR, fname)
        
        # Extract both text and metadata
        text, metadata = extract_pdf_content(pdf_path)

        out_path = os.path.join(
            RAW_TEXT_DIR, os.path.splitext(fname)[0] + ".txt"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[+] Saved raw text: {out_path}")
        # Here you could potentially pass the metadata to the next stage,
        # but for simplicity, we'll handle it in the manifest script
        # which is the central registry.
        
if __name__ == "__main__":
    process_pdfs()