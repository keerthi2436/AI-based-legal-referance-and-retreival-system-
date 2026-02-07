import os
import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from pathlib import Path 
import glob 
load_dotenv()
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 80))

BASE_DIR = Path(__file__).parent 
DATA_DIR = BASE_DIR / "data" / "processed" / "raw_text" 
OUTPUT_CSV_PATH = BASE_DIR / "chunks" / "chunks_with_embeddings.csv" 

def load_documents_and_chunk(data_dir):
    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    text_files = glob.glob(str(data_dir / "*.txt"))
    if not text_files:
        print(f"ERROR: '{data_dir.resolve()}' exists, but contains no .txt files to process.")
        return []
    for file_path_str in text_files:
        file_path = Path(file_path_str)
        filename = file_path.name
        print(f"Processing: {filename}")
        try:
            text_content = file_path.read_text(encoding='utf-8')
            docs = text_splitter.create_documents([text_content], 
                                                metadatas=[{"source": filename, "page": 0}])

            for i, doc in enumerate(docs):
                chunk_id = f"{filename.replace('.', '-')}-{i}" 
                all_chunks.append({
                    "id": chunk_id,
                    "text": doc.page_content,
                    "source": filename,
                    "page": i + 1 # Use chunk index as a pseudo-page number
                })
        except Exception as e:
            print(f"Failed to read or process {filename}: {e}")
            continue
    return all_chunks
def create_and_save_embeddings(chunks):
    """Initializes the embedding model, creates vectors, and saves them locally."""
    if not chunks:
        return
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    os.makedirs(OUTPUT_CSV_PATH.parent, exist_ok=True)
    df = pd.DataFrame(chunks)
    df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Successfully generated and saved {len(chunks)} embeddings to {OUTPUT_CSV_PATH.resolve()}")
if __name__ == "__main__":
    document_chunks = load_documents_and_chunk(DATA_DIR)
    create_and_save_embeddings(document_chunks)
    print("\nEmbedding generation pipeline finished. Next: Upload to Pinecone.")