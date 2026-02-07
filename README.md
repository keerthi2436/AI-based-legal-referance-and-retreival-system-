# Hybrid Retrieval-Augmented Generation (RAG) for Legal Text Analytics

### Abstract
This project implements a state-of-the-art **Retrieval-Augmented Generation (RAG)** pipeline tailored for the precision-critical domain of legal analytics. By fusing **dense vector retrieval** (semantic understanding) with **sparse TF-IDF retrieval** (exact keyword matching), the system overcomes the limitations of traditional search methods in handling complex statutory language. The architecture integrates **GPT-4o** for generation, ensuring high-fidelity, citation-backed responses suitable for legal professionals and researchers.

---

## 🏛️ 1. System Architecture

The proposed architecture adopts a **bi-encoder dual-path retrieval strategy**, optimized for high recall and precision.

![System Architecture](assets/architecture.png)

### 1.1 Methodology
The core retrieval mechanism, $S_{hybrid}$, combines semantic similarity scores ($S_{sem}$) and lexical overlap scores ($S_{lex}$) using a weighted linear combination:

$$ S_{hybrid}(q, d) = \alpha \cdot S_{sem}(q, d) + (1 - \alpha) \cdot S_{lex}(q, d) $$

Where:
-   $S_{sem}(q, d)$: Cosine similarity between query embedding $\vec{v}_q$ and document embedding $\vec{v}_d$ (via `all-MiniLM-L6-v2`).
-   $S_{lex}(q, d)$: TF-IDF similarity focusing on rare legal terminologies (e.g., *mens rea*, *res judicata*).
-   $\alpha$: A tunable hyperparameter (default $\alpha=0.7$) balancing semantic nuance vs. keyword precision.

---

## 🔬 2. Research Contributions

### 2.1 Hybrid Indexing Strategy
Unlike standard vector-only RAG systems which often fail to retrieve exact statutory clauses (e.g., "Section 302 IPC"), our hybrid approach ensures:
*   **Semantic Capture:** Understands intent (e.g., "What happens if I kill someone by mistake?" maps to *Culpable Homicide*).
*   **Lexical Anchor:** Retrieves exact matches for case citations and section numbers.

### 2.2 Hallucination Mitigation (Citation-Aware Generation)
We enforce a strict **Evidence-Based Generation (EBG)** protocol. The LLM is constrained via system prompts to generate answers *only* from retrieved contexts $C = \{c_1, c_2, ..., c_k\}$.
*   **Constraint:** If $Answer \notin C$, output "Insufficient Context".
*   **Traceability:** Every assertion is suffixed with a unique source identifier $[Source\_ID]$.

---

## 🚀 3. Implementation Details

### 3.1 Tech Stack
| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **LLM** | GPT-4o-mini | High reasoning capability with lower latency. |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dimensional dense vectors; SOTA for sentence similarity. |
| **Vector Store** | In-Memory / FAISS | Low-latency approximate nearest neighbor (ANN) search. |
| **Frontend** | Streamlit | Rapid prototyping of research interfaces. |

### 3.2 Preprocessing Pipeline
1.  **PDF Ingestion:** `pypdf` extracts raw text from diverse legal documents.
2.  **Normalization:** Regex-based cleaning removes header/footer noise and corrects OCR errors.
3.  **Semantic Chunking:** Text is segmented into 512-token overlapping windows to preserve local context.

---

## ⚡ 4. Setup & Reproducibility
(Follow these steps to replicate the experimental environment)

### Prerequisites
*   Python 3.9+ environment
*   Access to OpenAI API

### Installation
```bash
# Clone the repository
git clone https://github.com/keerthi2436/AI-based-legal-referance-and-retreival-system-
cd AI-based-legal-referance-and-retreival-system-

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create a `.env` file for API credentials:
```bash
OPENAI_API_KEY=sk-proj-...
```

### Execution
```bash
streamlit run app.py
```

---

## 📊 5. Future Research Directions
*   **Cross-Encoder Re-ranking:** Implementing a BERT-based re-ranker to refine the top-k results from the bi-encoder stage.
*   **LegalBERT Fine-tuning:** Replacing generic sentence transformers with domain-specific models pre-trained on Indian Case Law.
*   **Graph RAG:** Utilizing Knowledge Graphs to map inter-statutory relationships.

---

## 📚 References
1.  **Lewis et al. (2020).** Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS*.
2.  **Reimers & Gurevych (2019).** Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP*.
3.  **Chalkidis et al. (2020).** LEGAL-BERT: The Muppets straight out of Law School. *Findings of EMNLP*.

---
**Author:** Keerthi  
**Institution:** Springboard Internship 2025  
