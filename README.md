# 🎙️ Real-Time Meeting Assistant

A privacy-first, real-time meeting assistant built with **FastAPI**, **React**, and **Google Gemini 3.5 Flash**. This application captures live meeting audio, provides real-time bilingual (Tamil & English code-mixed) transcription, and uses a Retrieval-Augmented Generation (RAG) pipeline to generate precise meeting minutes and answer contextual questions.

## ✨ Features

- **Live Transcription (30s Buffered):** High-accuracy Speech-to-Text handling complex Tanglish (Tamil + English) code-mixing.
- **Intelligent RAG Pipeline:** Context-aware Q&A using **ChromaDB** to query ongoing meeting topics.
- **Automated Meeting Minutes:** Generates structured Action Items, Key Decisions, and Overviews instantly.
- **Bulletproof Architecture:** - Thread-safe WebSocket streaming.
  - Exponential Backoff for API rate limits (429/503 handling).
  - Built-in "Kill Switch" to prevent zombie threads during client disconnects.

## 🛠️ Tech Stack

- **Frontend:** React.js, Vite, Tailwind CSS, WebSockets
- **Backend:** Python, FastAPI, Uvicorn, AsyncIO
- **Intelligence Layer:** Google Gemini 3.5 Flash API
- **Vector Database:** ChromaDB (Local Persistence)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- A Google Gemini API Key

### 1. Backend Setup
Navigate to the root directory and set up the Python environment:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn websockets chromadb google-genai pydantic

# Create a .env file and add your API key (Do not commit this file!)
echo 'GEMINI_API_KEY="AIzaSyYourKeyHere..."' > .env