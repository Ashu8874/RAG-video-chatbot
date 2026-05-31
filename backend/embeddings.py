import os
import shutil
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from chromadb.config import Settings as ChromaSettings
from config import settings

logger = logging.getLogger(__name__)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

_embeddings_instance = None

def display_metric(value, suffix: str = "") -> str:
    if value is None or value == "":
        return "Unavailable"
    return f"{value}{suffix}"

def metadata_value(value) -> str:
    return "" if value is None else str(value)

def format_video_context(video_data: dict) -> str:
    hashtags = ", ".join(video_data.get("hashtags") or []) or "None"
    engagement_note = video_data.get("engagement_note") or ""
    metadata_note = video_data.get("metadata_note") or ""
    return "\n".join([
        f"Video {video_data['video_id']} metadata:",
        f"- Platform: {video_data['source']}",
        f"- Title: {video_data['title']}",
        f"- Creator: {video_data['creator']}",
        f"- Follower count: {display_metric(video_data.get('follower_count'))}",
        f"- Views: {display_metric(video_data.get('views'))}",
        f"- Likes: {display_metric(video_data.get('likes'))}",
        f"- Comments: {display_metric(video_data.get('comments'))}",
        f"- Engagement rate: {display_metric(video_data.get('engagement_rate'), '%')}",
        f"- Engagement note: {engagement_note or 'None'}",
        f"- Metadata note: {metadata_note or 'None'}",
        f"- Upload date: {video_data['upload_date']}",
        f"- Duration seconds: {display_metric(video_data.get('duration'))}",
        f"- Hashtags: {hashtags}",
        f"- URL: {video_data['url']}",
    ])

def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info("Loading embedding model: %s", settings.EMBED_MODEL)
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBED_MODEL,
            model_kwargs={"device": settings.EMBED_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_instance

def create_documents(video_data: dict) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    meta = {
        "video_id": video_data["video_id"],
        "source": video_data["source"],
        "creator": video_data["creator"],
        "views": metadata_value(video_data.get("views")),
        "likes": metadata_value(video_data.get("likes")),
        "comments": metadata_value(video_data.get("comments")),
        "engagement_rate": metadata_value(video_data.get("engagement_rate")),
        "engagement_note": video_data.get("engagement_note") or "",
        "metadata_note": video_data.get("metadata_note") or "",
        "follower_count": metadata_value(video_data.get("follower_count")),
        "upload_date": str(video_data["upload_date"]),
        "duration": metadata_value(video_data.get("duration")),
        "title": video_data["title"],
        "hashtags": ", ".join(video_data["hashtags"]),
        "url": video_data["url"],
    }
    metadata_context = format_video_context(video_data)
    transcript = video_data.get("transcript") or "Transcript unavailable."
    docs = splitter.create_documents(texts=[transcript], metadatas=[meta])
    metadata_doc = Document(
        page_content=metadata_context,
        metadata={**meta, "chunk_index": "metadata", "total_chunks": str(len(docs))},
    )
    for i, doc in enumerate(docs):
        doc.page_content = (
            f"{metadata_context}\n\n"
            f"Transcript chunk {i + 1} of {len(docs)}:\n"
            f"{doc.page_content}"
        )
        doc.metadata["chunk_index"] = str(i)
        doc.metadata["total_chunks"] = str(len(docs))
    logger.info("Video %s: %d chunks created", video_data["video_id"], len(docs))
    return [metadata_doc, *docs]

def create_comparison_document(video_data_list: list[dict]) -> Document:
    context_blocks = [format_video_context(video_data) for video_data in video_data_list]
    lines = ["Combined comparison metadata for Video A and Video B:"]

    by_id = {video_data["video_id"]: video_data for video_data in video_data_list}
    video_a = by_id.get("A")
    video_b = by_id.get("B")
    if video_a and video_b:
        lines.extend([
            "",
            "Direct comparison:",
            f"- Video A engagement rate: {display_metric(video_a.get('engagement_rate'), '%')}",
            f"- Video B engagement rate: {display_metric(video_b.get('engagement_rate'), '%')}",
            f"- Video A views/likes/comments: {display_metric(video_a.get('views'))} / {display_metric(video_a.get('likes'))} / {display_metric(video_a.get('comments'))}",
            f"- Video B views/likes/comments: {display_metric(video_b.get('views'))} / {display_metric(video_b.get('likes'))} / {display_metric(video_b.get('comments'))}",
            f"- Video A creator/followers: {video_a['creator']} / {display_metric(video_a.get('follower_count'))}",
            f"- Video B creator/followers: {video_b['creator']} / {display_metric(video_b.get('follower_count'))}",
            f"- Video A engagement note: {video_a.get('engagement_note') or 'None'}",
            f"- Video B engagement note: {video_b.get('engagement_note') or 'None'}",
            f"- Video A metadata note: {video_a.get('metadata_note') or 'None'}",
            f"- Video B metadata note: {video_b.get('metadata_note') or 'None'}",
        ])

    page_content = "\n\n".join([*context_blocks, "\n".join(lines)])
    return Document(
        page_content=page_content,
        metadata={
            "video_id": "comparison",
            "source": "comparison",
            "creator": "combined",
            "views": "",
            "likes": "",
            "comments": "",
            "engagement_rate": "",
            "engagement_note": "",
            "metadata_note": "",
            "follower_count": "",
            "upload_date": "",
            "duration": "",
            "title": "Video A vs Video B metadata comparison",
            "hashtags": "",
            "url": "",
            "chunk_index": "metadata",
            "total_chunks": "1",
        },
    )

def build_vectorstore(video_data_list: list[dict]) -> Chroma:
    all_docs = [create_comparison_document(video_data_list)]
    for vd in video_data_list:
        all_docs.extend(create_documents(vd))

    persist_dir = settings.CHROMA_PERSIST_DIR
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    logger.info("Embedding %d chunks into ChromaDB...", len(all_docs))
    vectorstore = Chroma.from_documents(
        documents=all_docs,
        embedding=get_embeddings(),
        persist_directory=persist_dir,
        client_settings=ChromaSettings(anonymized_telemetry=False),
    )
    logger.info("ChromaDB build complete")
    return vectorstore

def load_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIR,
        embedding_function=get_embeddings(),
        client_settings=ChromaSettings(anonymized_telemetry=False),
    )
