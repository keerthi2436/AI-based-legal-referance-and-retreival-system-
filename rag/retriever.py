# rag/retriever.py
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .loader import build_chunks

import streamlit as st

import numpy as np
import logging
from .loader import build_chunks

logger = logging.getLogger(__name__)

# Try importing SentenceTransformer for semantic search
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL = "all-MiniLM-L6-v2" # Fast & good quality
    HAS_SEMANTIC = True
except ImportError:
    SentenceTransformer = None
    HAS_SEMANTIC = False

class HybridIndex:
    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.chunks: List[Dict] = []
        
        self.embedder = None
        self.doc_embeddings = None

    def fit(self, chunks: List[Dict]):
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        
        # 1. TF-IDF (Keyword)
        try:
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                max_df=0.95,
                ngram_range=(1, 2),
                sublinear_tf=True
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        except Exception as e:
            logger.error(f"TF-IDF failed: {e}")

        # 2. Semantic (Vector)
        if HAS_SEMANTIC:
            try:
                # Lazy load model
                if not self.embedder:
                    self.embedder = SentenceTransformer(EMBEDDING_MODEL)
                
                # Embed all chunks (may take a moment for large docs, but okay for typical RAG demos)
                # Normalize embeddings for cosine similarity
                self.doc_embeddings = self.embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            except Exception as e:
                logger.error(f"Semantic embedding failed: {e}")
                self.doc_embeddings = None

    def query(self, q: str, top_k: int = 8) -> List[Tuple[float, Dict]]:
        if not self.chunks:
            return []
        
        # Calculate scores
        scores = np.zeros(len(self.chunks))
        
        # A. Semantic Score
        if self.doc_embeddings is not None and self.embedder is not None:
            q_vec = self.embedder.encode([q], convert_to_numpy=True, normalize_embeddings=True)
            # Dot product since vectors are normalized = cosine similarity
            sem_scores = np.dot(self.doc_embeddings, q_vec[0])
            scores += (sem_scores * 0.7) # Weight semantic higher
            
        # B. Keyword Score (TF-IDF)
        if self.vectorizer is not None and self.tfidf_matrix is not None:
            q_tfidf = self.vectorizer.transform([q])
            # Cosine similarity for sparse matrix
            tfidf_scores = cosine_similarity(q_tfidf, self.tfidf_matrix)[0]
            scores += (tfidf_scores * 0.3) # Weight keywords lower but still useful for specific terms

        # Get top K
        # argsort gives ascending, so we take last top_k and reverse
        if len(scores) == 0:
            return []
            
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for i in top_indices:
            if scores[i] > 0.0: # Filter out zero matches
                results.append((float(scores[i]), self.chunks[i]))
        
        return results

import pickle
import os

INDEX_FILE = "data/index.pkl"

@st.cache_resource(show_spinner="Loading index...")
def get_or_create_index() -> HybridIndex:
    # 1. Try loading from disk
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "rb") as f:
                idx = pickle.load(f)
            logger.info(f"Loaded index from disk: {len(idx.chunks)} chunks")
            return idx
        except Exception as e:
            logger.warning(f"Failed to load cached index: {e}")

    # 2. Build from scratch
    idx = HybridIndex()
    try:
        chunks = build_chunks()
        if chunks:
            idx.fit(chunks)
            # Save to disk
            with open(INDEX_FILE, "wb") as f:
                pickle.dump(idx, f)
            logger.info("Saved new index to disk.")
    except Exception as e:
        logger.error(f"Index build failed: {e}")
    return idx

def clear_index_cache():
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
    st.cache_resource.clear()
