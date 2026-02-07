# src/ingestion/manifest.py
"""
Manifest script:
- Copies original PDFs into secure repository
- Records source metadata (hash, size, title, date, headings) into manifest.jsonl
"""

import os
import shutil
import hashlib
import json
import fitz # PyMuPDF is used to extract metadata directly
import re

RAW_DIR = "data/raw"
REPO_DIR = "data/repo/originals"
CLEAN_TEXT_DIR = "data/processed/clean_text"
MANIFEST_FILE = "data/processed/manifest.jsonl"

# Ensure all necessary directories exist
os.makedirs(REPO_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MANIFEST_FILE), exist_ok=True)

def sha256_file(path):
    """Compute sha256 checksum for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        # Read the file in chunks for memory efficiency
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_pdf_metadata(pdf_path):
    """Extract standard metadata (title, date) from a PDF using PyMuPDF."""
    metadata = {}
    try:
        with fitz.open(pdf_path) as doc:
            meta = doc.metadata
            metadata["title"] = meta.get("title", None)
            metadata["date"] = meta.get("creationDate", None)
    except Exception:
        # Fails gracefully if the file is corrupted or metadata can't be read
        pass
    return metadata

def extract_headings_from_text(text_path):
    """
    Extract headings from the cleaned text file by looking for the special marker
    added by the cleaning script.
    """
    headings = []
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Find all lines that start with the special heading marker
            for line in content.splitlines():
                if line.startswith("_HEADING_"):
                    # Remove the marker and strip whitespace to get the clean heading
                    headings.append(line.replace("_HEADING_", "").strip())
    return headings

def build_manifest():
    manifest_entries = []

    for fname in os.listdir(RAW_DIR):
        if not fname.lower().endswith(".pdf"):
            continue

        raw_path = os.path.join(RAW_DIR, fname)
        repo_path = os.path.join(REPO_DIR, fname)

        # Copy PDF to secure repository if not already copied
        if not os.path.exists(repo_path):
            shutil.copy2(raw_path, repo_path)

        # Calculate integrity metrics (hash + size)
        file_hash = sha256_file(repo_path)
        size_bytes = os.path.getsize(repo_path)

        # Determine the expected path for the cleaned text
        clean_txt_path = os.path.join(
            CLEAN_TEXT_DIR, os.path.splitext(fname)[0] + ".txt"
        )

        # Extract metadata and headings
        doc_metadata = extract_pdf_metadata(raw_path)
        extracted_headings = extract_headings_from_text(clean_txt_path)

        # Construct the manifest entry
        entry = {
            "filename": fname,
            "repo_path": repo_path,
            "sha256": file_hash,
            "size_bytes": size_bytes,
            "clean_text_path": clean_txt_path if os.path.exists(clean_txt_path) else None,
            "metadata": {
                "title": doc_metadata.get("title"),
                "date": doc_metadata.get("date"),
                "court": None, # Placeholder for manual or advanced extraction
                "headings": extracted_headings 
            }
        }
        
        manifest_entries.append(entry)

    # Write all entries into a JSONL file
    with open(MANIFEST_FILE, "w", encoding="utf-8") as mf:
        for e in manifest_entries:
            # Write each entry as a single JSON line
            mf.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"[+] Manifest created with {len(manifest_entries)} entries at {MANIFEST_FILE}")

if __name__ == "__main__":
    build_manifest()