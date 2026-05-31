import logging
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from config import settings

logger = logging.getLogger(__name__)

_memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer",
    k=settings.MEMORY_WINDOW,
)

SYSTEM_PROMPT = """You are an expert social media analytics assistant with deep knowledge of content strategy, audience engagement, and platform algorithms.

You have access to full transcripts and metadata for two videos:
- Video A (YouTube)
- Video B (Instagram Reel)

METADATA AVAILABLE:
- Views, likes, comments, engagement rate (likes+comments / views * 100)
- Creator name and follower count
- Upload date, video duration, hashtags
- Complete spoken transcript

RESPONSE RULES:
1. Always cite [Video A] or [Video B] when referencing content
2. Use exact numbers from metadata — never approximate
3. Quote relevant transcript snippets when analyzing content
4. Be analytically specific — avoid vague statements
5. For improvement suggestions, give concrete, actionable steps
6. If asked about engagement rate, calculate: (likes + comments) / views * 100
7. Do not ask the user to provide metadata if it appears in the retrieved context
8. If a metric is zero or unavailable, say that directly and explain how it limits the comparison
9. For comparison questions, start with the numeric winner and the main reason before giving details
10. Never treat "Unavailable" as 0. If Instagram view/follower data is unavailable, do not claim the reel had 0 views or 0 followers
11. Only calculate engagement rate when views is a positive number. If views is unavailable, say the engagement rate cannot be calculated reliably
12. Do not invent platform algorithm explanations from missing metrics. Ground every explanation in available numbers, metadata, or transcript content
13. If a metadata note says Instagram hid a field, mention that limitation briefly and compare only the available fields

Retrieved context from both videos:
{context}

Conversation history:
{chat_history}

User question: {question}

Provide a concise, production-quality answer with exact numbers, clear reasoning, and citations:"""


def build_rag_chain(vectorstore: Chroma) -> ConversationalRetrievalChain:
    logger.info("Building RAG chain with model: %s", settings.GROQ_LLM_MODEL)

    llm = ChatOpenAI(
        model=settings.GROQ_LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_BASE_URL,
        temperature=0.3,
        streaming=True,
        max_tokens=2048,
    )

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": settings.RETRIEVER_K,
            "fetch_k": settings.RETRIEVER_FETCH_K,
            "lambda_mult": 0.7,
        },
    )

    prompt = PromptTemplate(
        template=SYSTEM_PROMPT,
        input_variables=["context", "chat_history", "question"],
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=_memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=False,
    )

    logger.info("RAG chain ready")
    return chain


def reset_memory() -> None:
    _memory.clear()
    logger.info("Chat memory cleared")


def format_sources(source_documents: list) -> list[dict]:
    sources = []
    seen = set()
    for doc in source_documents:
        m = doc.metadata
        key = f"{m.get('video_id')}_{m.get('chunk_index')}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "video_id": m.get("video_id", "?"),
                "chunk_index": m.get("chunk_index", "0"),
                "total_chunks": m.get("total_chunks", "?"),
                "creator": m.get("creator", "Unknown"),
                "platform": m.get("source", "unknown"),
                "engagement_rate": m.get("engagement_rate", "0"),
                "snippet": doc.page_content[:180].strip() + "...",
            })
    return sources
