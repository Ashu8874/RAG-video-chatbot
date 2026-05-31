from pydantic import BaseModel, HttpUrl
from typing import Optional

class IngestRequest(BaseModel):
    youtube_url: str
    instagram_url: str

class ChatRequest(BaseModel):
    question: str

class VideoMeta(BaseModel):
    video_id: str
    source: str
    url: str
    title: str
    creator: str
    follower_count: int
    views: int
    likes: int
    comments: int
    engagement_rate: float
    upload_date: str
    duration: int
    hashtags: list[str]
    thumbnail: str

class IngestResponse(BaseModel):
    video_a: dict
    video_b: dict

class SourceCitation(BaseModel):
    video_id: str
    chunk_index: str
    creator: str
    platform: str
    engagement_rate: str
    snippet: str

class HealthResponse(BaseModel):
    status: str
    chain_ready: bool
    model: str
    embed_model: str
