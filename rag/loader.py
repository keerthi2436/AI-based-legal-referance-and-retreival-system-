# rag/loader.py
# Loads PDF/TXT files from data/docs, cleans, and chunks them.

from typing import List, Dict
import os, re
from pypdf import PdfReader

DOCS_DIR = "data/docs"

def read_txt(fp: str) -> str:
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_pdf(fp: str) -> str:
    reader = PdfReader(fp)
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts)

def load_corpus() -> List[Dict]:
    """
    Returns list of {id, source, text}
    """
    os.makedirs(DOCS_DIR, exist_ok=True)
    corpus = []
    idx = 0
    for root, _, files in os.walk(DOCS_DIR):
        for name in files:
            fp = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            try:
                if ext == ".txt":
                    raw = read_txt(fp)
                elif ext == ".pdf":
                    raw = read_pdf(fp)
                else:
                    continue
                text = normalize_text(raw)
                if text.strip():
                    corpus.append({"id": f"doc-{idx}", "source": fp, "text": text})
                    idx += 1
            except Exception as e:
                # skip unreadable files
                print(f"[loader] Skipped {fp}: {e}")
    return corpus

def normalize_text(s: str) -> str:
    s = s.replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def chunk_text(text: str, chunk_tokens: int = 180, overlap: int = 30) -> List[str]:
    """
    Simple whitespace 'token' chunker. Adjust sizes as needed.
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_tokens]
        chunks.append(" ".join(chunk))
        i += max(1, chunk_tokens - overlap)
    return chunks

def build_chunks() -> List[Dict]:
    """
    Returns list of chunks:
    [{ 'chunk_id', 'doc_id', 'source', 'text' }]
    """
    items = load_corpus()
    chunks = []
    c = 0
    for doc in items:
        parts = chunk_text(doc["text"])
        for p in parts:
            chunks.append({
                "chunk_id": f"chunk-{c}",
                "doc_id": doc["id"],
                "source": doc["source"],
                "text": p
            })
            c += 1
    return chunks
