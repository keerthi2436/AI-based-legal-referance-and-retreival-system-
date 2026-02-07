# src/ingestion/chunker.py
"""
Chunking script: breaks cleaned text into section-wise chunks.
- Reads files from data/processed/clean_text/
- Splits text by the _HEADING_ marker.
- Saves each chunk to data/chunks/
- Creates a manifest.json file mapping original documents to their chunks.
"""

import os
import json

CLEAN_TEXT_DIR = "data/processed/clean_text"
CHUNKS_DIR = "data/chunks"
CHUNK_MANIFEST_FILE = "data/chunk_manifest.json"

os.makedirs(CHUNKS_DIR, exist_ok=True)

def create_chunks(cleaned_file_path):
    """Reads a cleaned text file and splits it into chunks."""
    with open(cleaned_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the content by the heading marker
    # The first element will be the text before the first heading, which we can ignore or label as a preamble
    sections = content.split("\n_HEADING_ ")[1:]
    
    # Extract the base filename
    base_name = os.path.splitext(os.path.basename(cleaned_file_path))[0]
    
    chunks = []
    for i, section in enumerate(sections):
        # The first line of the section is the heading, the rest is the content
        heading_line, *rest_of_content = section.split("\n", 1)
        
        chunk_content = heading_line + "\n" + "".join(rest_of_content)
        chunk_filename = f"{base_name}_chunk_{i+1}.txt"
        chunk_path = os.path.join(CHUNKS_DIR, chunk_filename)
        
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk_content.strip())
            
        chunks.append({
            "chunk_filename": chunk_filename,
            "chunk_path": chunk_path,
            "heading": heading_line.strip(),
            "start_index": content.find(heading_line) # Simple index for tracking
        })
        
    return chunks

def run_chunking():
    all_chunk_mappings = {}
    for fname in os.listdir(CLEAN_TEXT_DIR):
        if not fname.endswith(".txt"):
            continue
            
        cleaned_path = os.path.join(CLEAN_TEXT_DIR, fname)
        
        # Create chunks for the current file
        document_chunks = create_chunks(cleaned_path)
        
        # Add the mapping to the main dictionary
        all_chunk_mappings[fname] = document_chunks
        
        print(f"[+] Chunked {fname} into {len(document_chunks)} sections.")

    # Write the final manifest file
    with open(CHUNK_MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunk_mappings, f, indent=4)
        
    print(f"[+] Chunk manifest created at {CHUNK_MANIFEST_FILE}")

if __name__ == "__main__":
    run_chunking()