# Video RAG Analyst

Video RAG Analyst is a small full-stack app for comparing a YouTube video with
an Instagram post or reel. It pulls transcript and metadata, builds a local
vector index, and lets you ask questions about content, engagement, and creator
performance.

The project is split into a FastAPI backend and a React/Vite frontend.

## What It Does

- Accepts one YouTube URL and one Instagram URL
- Extracts transcripts from captions when available, with Whisper fallback
- Collects public metadata such as views, likes, comments, creator, duration,
  upload date, hashtags, and thumbnail when the platform exposes it
- Computes engagement rate when view count is available
- Stores transcript chunks and metadata in a local Chroma vector store
- Answers comparison questions through a LangChain retrieval chain
- Streams chat responses to the frontend

Instagram does not always expose view count or follower count through public
endpoints. In those cases the app keeps those fields as unavailable instead of
treating them as zero.

## Stack

- Frontend: React, Vite
- Backend: FastAPI, Python 3.11
- Retrieval: LangChain, Chroma
- Embeddings: `BAAI/bge-small-en-v1.5`
- Transcription fallback: Whisper
- Metadata extraction: `yt-dlp`, `instaloader`
- LLM endpoint: Groq-compatible OpenAI API

## Project Structure

```text
backend/
  main.py          FastAPI app and API routes
  metadata.py      YouTube/Instagram extraction and transcript handling
  embeddings.py    document creation and Chroma vector store setup
  rag_chain.py     retrieval chain and response formatting
  config.py        environment configuration
  models.py        request/response models

frontend/
  src/
    App.jsx
    components/
    hooks/
    utils/
```

## Setup

Install system dependencies:

```bash
brew install python@3.11 ffmpeg node
```

Create a Groq API key from `console.groq.com`, then configure the backend:

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Optional Instagram cookie settings can improve metadata extraction when public
Instagram pages hide some fields:

```env
YTDLP_COOKIES_FROM_BROWSER=brave
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Notes

- First ingest can be slow because Whisper and the embedding model may need to
  download/load model files.
- If a platform hides a metric, the UI and chat response show it as unavailable.
- Re-ingest videos after changing metadata extraction settings; the vector store
  is rebuilt from the latest extracted data.
