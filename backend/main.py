import json
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models import IngestRequest, ChatRequest, HealthResponse
from metadata import get_youtube_data, get_instagram_data, compute_engagement
from embeddings import build_vectorstore
from rag_chain import build_rag_chain, reset_memory, format_sources

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

rag_chain = None
video_metadata: dict = {}

def format_engagement_log(value) -> str:
    return f"{value}%" if value is not None else "Unavailable"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG Video Chatbot starting up...")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="RAG Video Chatbot API",
    description="LangChain + Groq + ChromaDB powered video analytics chatbot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "chain_ready": rag_chain is not None,
        "model": settings.GROQ_LLM_MODEL,
        "base_url": settings.GROQ_BASE_URL,
        "embed_model": settings.EMBED_MODEL,
    }


@app.post("/ingest")
async def ingest(req: IngestRequest):
    global rag_chain, video_metadata

    try:
        logger.info("Starting ingest pipeline...")

        loop = asyncio.get_event_loop()

        yt_data = await loop.run_in_executor(None, get_youtube_data, req.youtube_url)
        yt_data = compute_engagement(yt_data)
        logger.info("YouTube data fetched. Engagement: %s", format_engagement_log(yt_data["engagement_rate"]))

        ig_data = await loop.run_in_executor(None, get_instagram_data, req.instagram_url)
        ig_data = compute_engagement(ig_data)
        logger.info("Instagram data fetched. Engagement: %s", format_engagement_log(ig_data["engagement_rate"]))

        vectorstore = await loop.run_in_executor(
            None, build_vectorstore, [yt_data, ig_data]
        )

        rag_chain = build_rag_chain(vectorstore)
        reset_memory()

        video_metadata = {
            "video_a": {k: v for k, v in yt_data.items() if k != "transcript"},
            "video_b": {k: v for k, v in ig_data.items() if k != "transcript"},
        }

        logger.info("Ingest complete!")
        return video_metadata

    except Exception as e:
        logger.exception("Ingest failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(req: ChatRequest):
    if rag_chain is None:
        raise HTTPException(status_code=400, detail="No videos loaded. Call /ingest first.")

    async def event_stream():
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: rag_chain.invoke({"question": req.question})
            )

            answer: str = result.get("answer", "")
            source_docs = result.get("source_documents", [])
            sources = format_sources(source_docs)

            for word in answer.split(" "):
                payload = json.dumps({"type": "token", "content": word + " "})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0.015)

            yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Chat error: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/metadata")
async def get_metadata():
    if not video_metadata:
        raise HTTPException(status_code=404, detail="No videos loaded yet")
    return video_metadata


@app.post("/reset")
async def reset():
    reset_memory()
    return {"status": "ok", "message": "Chat memory cleared"}
