import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_LLM_MODEL: str = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "65536"))

    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    EMBED_DEVICE: str = os.getenv("EMBED_DEVICE", "cpu")

    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

    INSTAGRAM_COOKIES_FILE: str = os.getenv("INSTAGRAM_COOKIES_FILE", "")
    YTDLP_COOKIES_FROM_BROWSER: str = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    CHUNK_SIZE: int = 300
    CHUNK_OVERLAP: int = 50
    RETRIEVER_K: int = 6
    RETRIEVER_FETCH_K: int = 12
    MEMORY_WINDOW: int = 10

settings = Settings()
