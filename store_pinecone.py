import os
import pandas as pd
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec, PodSpec
from pathlib import Path # ADDED: For robust path handling
import json 
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
DIMENSION = 384 
BATCH_SIZE = 100 
BASE_DIR = Path(__file__).parent
INPUT_CSV_PATH = BASE_DIR / "chunks" / "chunks_with_embeddings.csv"
def upload_to_pinecone():
    """Connects to Pinecone, manages the index, and uploads the vectors/embeddings."""
    try:
        chunks_df = pd.read_csv(INPUT_CSV_PATH, converters={'embedding': json.loads})
    except FileNotFoundError:
        print(f"ERROR: File not found at the expected path: {INPUT_CSV_PATH.resolve()}")
        print("Please run 'python embedder.py' first to create the file.")
        return
    except pd.errors.EmptyDataError:
        print(f"ERROR: The file at {INPUT_CSV_PATH.resolve()} is empty. No documents were processed.")
        return
    if chunks_df.empty:
        print(f"ERROR: No valid data found in '{INPUT_CSV_PATH.name}'. Ensure your documents were processed correctly.")
        return
    print("Initializing Pinecone connection...")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    except Exception as e:
        print(f"FATAL ERROR: Failed to initialize Pinecone. Check API Key/Environment in .env. Details: {e}")
        return
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME} (Dimension: {DIMENSION})...")
        spec = ServerlessSpec(cloud='aws', region='us-east-1') 
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=DIMENSION,
            metric='cosine',
            spec=spec
        )
        print("Index created successfully.")
    index = pc.Index(PINECONE_INDEX_NAME)
    vectors_to_upsert = []
    for _, chunk in chunks_df.iterrows():
        vector_id = chunk["id"]
        vector_values = chunk["embedding"] 
        metadata = {
            "text": chunk["text"],
            "source": chunk["source"],
            "page": int(chunk["page"])  # FIXED: Convert to integer explicitly
        }
        vectors_to_upsert.append((vector_id, vector_values, metadata))
    print(f"Uploading {len(vectors_to_upsert)} vectors to Pinecone...")
    for i in range(0, len(vectors_to_upsert), BATCH_SIZE):
        batch = vectors_to_upsert[i:i + BATCH_SIZE]
        index.upsert(vectors=batch)
        if (i // BATCH_SIZE + 1) % 5 == 0:
            print(f"--- Uploaded batch {i // BATCH_SIZE + 1} ---")
    stats = index.describe_index_stats()
    print(f"\nUpload complete. Total vectors in index: {stats.total_vector_count}")
if __name__ == "__main__":
    upload_to_pinecone()