# ⚖️ AI-Based Legal Reference & Retrieval System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai)
![RAG](https://img.shields.io/badge/RAG-Hybrid%20Search-green?style=for-the-badge)

A production-grade **Retrieval-Augmented Generation (RAG)** system designed to democratize access to legal knowledge. This application ingests legal documents (PDF/TXT), builds a **hybrid semantic-keyword index**, and delivers precise, cited answers to complex legal queries through a polished, professional interface.

---

## 🚀 Key Features

### 🧠 Advanced RAG Architecture
- **Hybrid Search:** Combines **Semantic Search** (using `all-MiniLM-L6-v2`) with **TF-IDF Keyword Matching** to ensure both conceptual understanding and precise statutory retrieval.
- **Smart Chunking:** Intelligently segments legal texts to preserve context.
- **Dynamic Retrieval:** Auto-detects query intent to adjust search strategies.

### 🛡️ Credible & Transparent AI
- **Inline Citations:** Every claim is backed by a specific source document `[Source: IPC-Section-302.pdf]`.
- **Hallucination Guardrails:** System prompts strictly forbid inventing case laws or statutes.
- **Confidence Scoring:** The system assesses retrieval quality before generating an answer.

### 🎨 Premium User Experience
- **Multi-Mode Interface:**
  - **Normal:** Standard Q&A.
  - **Summary:** Concise, bulleted legal briefs.
  - **ELI5:** "Explain Like I'm 5" - simplifies legal jargon for laypeople.
  - **Quiz:** Generates multiple-choice questions for law students.
  - **Drafting:** Auto-drafts legal clauses and contracts based on context.
- **Theming Engine:** Switch between *Midnight Purple*, *Deep Ocean Blue*, *Emerald NeoGlass*, and more.
- **Chat Export:** Download conversation history as formatted `.docx` files.

---

## 🛠️ System Architecture

```mermaid
graph TD
    A[User Legal Documents] -->|Upload PDF/TXT| B(Document Processor)
    B -->|Clean & Chunk| C{Hybrid Indexer}
    C -->|Embeddings| D[Vector Store (Local/FAISS)]
    C -->|TF-IDF| E[Keyword Index]
    
    U[User Query] -->|Input| F(Query Engine)
    F -->|Semantic Search| D
    F -->|Keyword Match| E
    
    D & E -->|Top-K Context| G[Context Refiner]
    G -->|Augmented Prompt| H[LLM (GPT-4o)]
    H -->|Generated Answer| I[Streamlit Interface]
```

---

## 💻 Tech Stack

- **Frontend:** Streamlit (Custom CSS for Glassmorphism/Animations)
- **Backend Logic:** Python 3.9+
- **LLM Integration:** OpenAI API (GPT-4o-mini / GPT-3.5-turbo)
- **Vector Embeddings:** `sentence-transformers` (HuggingFace)
- **Keyword Search:** `scikit-learn` (TF-IDF)
- **PDF Processing:** `pypdf`

---

## ⚡ Quick Start (End-to-End)

Follow these steps to get the system running locally in under 5 minutes.

### Prerequisites
- Python 3.8 or higher installed.
- An OpenAI API Key.

### 1. Clone the Repository
```bash
git clone https://github.com/Start-Springboard-Internship-2025/AI-Based-Legal-Retrieval-System.git
cd AI-Based-Legal-Retrieval-System
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory:
```bash
# .env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

### 5. Run the Application
```bash
streamlit run app.py
```

---

## 📖 Usage Guide

1.  **Login:** Use the default demo credentials:
    *   **Email:** `demo@legal.ai`
    *   **Password:** `demo1234`
2.  **Upload Documents:** Go to the sidebar, expand **Manage Documents**, and upload your legal PDFs (e.g., *Indian Penal Code*, *Contract Act*).
3.  **Indexing:** The system will automatically process and index the files (Watch the "Index rebuilding..." toast).
4.  **Ask Questions:** Type your query (e.g., *"What is the punishment for culpable homicide?"*).
5.  **Explore Modes:** Switch to **ELI5** to understand complex laws simply, or **Quiz** to test your knowledge.

---

## 📂 Project Structure

```
├── app.py                 # Main Streamlit Application Entrypoint
├── rag/
│   ├── answer.py          # RAG Orchestrator & LLM Interaction
│   ├── retriever.py       # Hybrid Search Implementation (Vector + Keyword)
│   └── loader.py          # Document Ingestion & Chunking Logic
├── data/                  # Local storage for docs, chunks, and user db
├── .env                   # Environment variables (API Keys)
└── requirements.txt       # Project Dependencies
```

---

## 🔮 Future Scope

- **Fine-Tuned LLM:** Training a LLaMA-based model specifically on Indian Case Law for offline capabilities.
- **Multilingual Support:** Integrating translation APIs to support queries in Hindi, Tamil, and other regional languages.
- **Live Citation Verification:** Real-time checking of citations against external legitimate databases (manupatra, scconline).

---

## 📄 License
This project is licensed under the MIT License.
