## AI Course Instructor Model

The AI Course Instructor model is designed using two different architectural approaches, each optimized for specific requirements.

### Approach 1: Cloud-Based Model
This approach leverages cloud infrastructure to enable *faster deployment, **higher scalability, and **enhanced model capabilities*. It allows seamless updates, improved performance, and the ability to integrate advanced AI services.

### Approach 2: Local LLM-Based Model
This approach runs the model locally using a *local LLM, prioritizing **privacy, data security, and offline accessibility*. It ensures that sensitive user data remains on the user's device without relying on external servers.

# Masters' Union AI Chatbot — Hackathon Submission

This repository contains two distinct implementation strategies for the Masters' Union AI Admissions Assistant. Both use **Retrieval-Augmented Generation (RAG)** to provide accurate, grounded answers about 28+ programmes.

---

## 🚀 Development Approaches

### Approach 1: Production-Ready (Cloud API) — **RECOMMENDED**
*   **Location**: `./v2_api_version`
*   **LLM**: Groq LLaMA 3.1 8B (Primary) / OpenAI GPT-4o-mini (Fallback)
*   **Performance**: Sub-second latency, advanced reasoning, and structured tree-format responses.
*   **Best for**: Production environments and high-traffic scenarios.

### Approach 2: Privacy-First (Local LLM)
*   **Location**: `./v1_local_version`
*   **LLM**: Llama 3.2 (3B) / Llama 3 (8B) via **Ollama**
*   **Performance**: Works 100% offline, zero API costs, full data privacy.
*   **Best for**: Secure internal tools or development without cloud dependencies.

---

## Features (Approach 1 - API Focused)

- **Hybrid retrieval**: FAISS (MMR semantic search) + BM25 keyword search
- **13 intent categories**: Fees, Curriculum, Admissions, Career, Placement, Immersion, Overview, Faculty, Recommendation, Greeting, Thanks, Farewell, General
- **28 programmes covered**: UG, PGP, Executive, Family Business, and Immersion programmes
- **Structured responses**: Tree-format comparisons, ALL CAPS section headers, fee highlights
- **Small-talk handling**: Greetings, farewells, and identity questions bypass RAG
- **Out-of-scope filter**: Rejects irrelevant queries (cricket, weather, jokes, etc.)
- **Programme catalogue fallback**: Hardcoded programme list injected for course-list queries
- **Multi-LLM support**: Groq LLaMA (primary) → OpenAI GPT-4o-mini → Local Ollama (Qwen)

## Quick Start (Approach 1 — API)

### 1. Install dependencies
```bash
cd v2_api_version
pip install -r requirements.txt
```

### 2. Set environment variables
```bash
# Set your API keys
export GROQ_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
```

### 3. Start the server
```bash
python app.py
```

---

## Quick Start (Approach 2 — Local)

### 1. Install dependencies
```bash
cd v1_local_version
pip install -r requirements.txt
```

### 2. Start Ollama
```bash
ollama pull llama3.2
```

### 3. Start Application
```bash
python app.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web server | Flask + flask-cors |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector store | FAISS (langchain-community) |
| Keyword search | BM25Okapi (rank-bm25) |
| Primary LLM | Groq llama-3.1-8b-instant |
| Fallback LLM | OpenAI gpt-4o-mini |
| Local LLM | Llama 3.2 via Ollama |
| PDF extraction | pdfplumber |
| Web Scraping | BeautifulSoup4 + Playwright fallback |
| Frontend | Tailwind CSS + Vanilla JS |

## Project Structure

```
hackathon_final/
├── v1_local_version/         # Approach 1: Local RAG (Ollama)
│   ├── app.py
│   ├── index.html
│   ├── src/
│   └── data/
├── v2_api_version/           # Approach 2: Cloud RAG (Groq/OpenAI)
│   ├── app.py
│   ├── index.html
│   ├── core/
│   └── scripts/
└── README.md                 # Unified Documentation
```

## API Reference (v2)

### POST /ask
Request body:
```json
{
  "query": "What is the fee for PGP TBM?",
  "history": []
}
```

Response:
```json
{
  "answer": "FEES:
PGP TBM
├─ Total Fee: ₹22,65,000
└─ Duration: 11 months",
  "category": "Fees",
  "model": "llama-3.1-8b-instant"
}
```

---

*Built for the AI Course Assistant Hackathon · Dual Architecture RAG Pipeline · Masters Union*
