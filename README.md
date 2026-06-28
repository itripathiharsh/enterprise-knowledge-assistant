# Enterprise Knowledge Assistant

An intelligent, full-stack RAG (Retrieval-Augmented Generation) application designed for enterprise teams. This system allows users to securely upload internal documents, automatically process and index them into a vector database, and ask complex natural language questions against their private knowledge base.

## 🚀 Key Features

*   **Multi-Format Document Ingestion:** Native support for PDF, DOCX, TXT, CSV, and XLSX files. Automatically handles OCR for scanned pages and extracts tabular data.
*   **Advanced RAG Pipeline:** Utilizes Hybrid Search (dense + sparse) combined with a Cross-Encoder Re-ranker to guarantee highly relevant context retrieval.
*   **Streaming Responses:** Real-time answer generation using Server-Sent Events (SSE) with "thinking" indicators for better user experience.
*   **Source Citations:** Every answer includes exact source citations and document previews so users can verify the information.
*   **Automated Evaluation (RAGAS):** A built-in synthetic evaluation dashboard that auto-generated test questions and grades the RAG engine's Semantic Similarity and Source Attribution Accuracy.
*   **User Isolation:** JWT-based authentication ensures that users can only search, view, and interact with the documents they have personally uploaded.
*   **Resilient AI:** Primary LLM inference powered by Groq (Llama 3), with a seamless fallback to Google Gemini to bypass rate limits without user interruption.

## 🛠️ Tech Stack

### Frontend
*   **Framework:** [Next.js 14](https://nextjs.org/) (App Router)
*   **UI Library:** React, TypeScript, TailwindCSS
*   **Icons & Components:** Lucide React, Custom UI components

### Backend
*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Vector Database:** [ChromaDB](https://www.trychroma.com/) (Local persistent storage)
*   **Embeddings:** `all-MiniLM-L6-v2` via SentenceTransformers
*   **LLM Providers:** Groq (`llama-3.3-70b-versatile`) & Google Gemini (`gemini-2.5-flash`)
*   **Document Processing:** PyMuPDF (fitz), pandas, python-docx

## 📂 Project Structure

*   `/frontend` - The Next.js web application.
*   `/backend` - The FastAPI server and AI/RAG engine.

## 🚀 Deployment Targets

This repository is pre-configured for modern PaaS deployment:
*   **Frontend:** Ready for 1-click deployment on [Vercel](https://vercel.com).
*   **Backend:** Configured with a `Procfile` and `railway.json` for seamless deployment on [Railway](https://railway.app). 

## ⚙️ Environment Variables

To run this project, you will need the following API keys configured in your backend `.env` file:
*   `GROQ_API_KEY`
*   `GEMINI_API_KEY`
*   `JWT_SECRET`
