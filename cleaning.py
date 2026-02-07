# src/ingestion/cleaning.py
"""
Cleaning script: produce plain text only.
- Removes headers/footers, bullets, section/chapter numbers, headings
- Leaves only continuous text sentences
"""

import os
import re
from collections import Counter

RAW_TEXT_DIR = "data/processed/raw_text"
CLEAN_TEXT_DIR = "data/processed/clean_text"

os.makedirs(CLEAN_TEXT_DIR, exist_ok=True)

def fix_hyphenation(lines):
    """Join words broken with hyphen at line end."""
    fixed = []
    skip = False
    for i, line in enumerate(lines):
        if skip:
            skip = False
            continue
        if line.endswith("-") and i + 1 < len(lines):
            fixed.append(line[:-1] + lines[i+1].lstrip())
            skip = True
        else:
            fixed.append(line)
    return fixed

def detect_headers_footers(all_pages):
    """Find frequent top/bottom lines across pages."""
    tops, bottoms = [], []
    for page in all_pages:
        if not page: continue
        tops.append(page[0])
        bottoms.append(page[-1])
    top_counts = Counter(tops)
    bot_counts = Counter(bottoms)
    headers = {t for t, c in top_counts.items() if c > 2}
    footers = {b for b, c in bot_counts.items() if c > 2}
    return headers, footers

def process_line(line: str):
    """
    Identifies and formats headings.
    Removes bullets and numbering from regular text.
    """
    # Check for headings like CHAPTER I, SECTION 302, etc.
    if re.match(r"^(CHAPTER|SECTION|ARTICLE|PART)\b", line.strip(), flags=re.I):
        return f"\n_HEADING_ {line.strip()}\n" # Preserve heading with a marker

    # Remove bullet characters and leading numbering from regular text
    line = re.sub(r"^[\u2022\u2023\u25E6\u2043\u2219\-\●\•\▪\▫\‣]+", "", line)
    line = re.sub(r"^\s*(\(?[0-9ivxlcIVXLCa-zA-Z]+\)?[\.\)])\s*", "", line)

    return line.strip()

def clean_text(raw_text):
    pages = [p.splitlines() for p in raw_text.split("\f")]
    headers, footers = detect_headers_footers(pages)

    processed_lines = []
    for page in pages:
        for line in page:
            line = line.strip()
            if not line or line in headers or line in footers:
                continue
            processed_line = process_line(line)
            if not processed_line:
                continue
            processed_lines.append(processed_line)

    # Join and normalize, then fix hyphenation on the result
    text = " ".join(processed_lines)
    text = re.sub(r"\s+", " ", text) # Normalize spaces
    
    # Fix hyphenation on the full, processed text
    lines_for_hyphenation = text.split("\n")
    fixed_lines = fix_hyphenation(lines_for_hyphenation)
    
    return "\n".join(fixed_lines).strip()

def run_cleaning():
    for fname in os.listdir(RAW_TEXT_DIR):
        if not fname.endswith(".txt"):
            continue
        raw_path = os.path.join(RAW_TEXT_DIR, fname)
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned = clean_text(raw_text)

        out_path = os.path.join(CLEAN_TEXT_DIR, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        print(f"[+] Cleaned file saved: {out_path}")

if __name__ == "__main__":
    run_cleaning()