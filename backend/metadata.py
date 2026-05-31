import os
import re
import logging
import shutil
import tempfile
import warnings
import whisper
import yt_dlp
import instaloader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from config import settings

logger = logging.getLogger(__name__)

def ytdlp_common_options() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "remote_components": ["ejs:github"],
    }
    if settings.INSTAGRAM_COOKIES_FILE:
        opts["cookiefile"] = settings.INSTAGRAM_COOKIES_FILE
    if settings.YTDLP_COOKIES_FROM_BROWSER:
        opts["cookiesfrombrowser"] = (settings.YTDLP_COOKIES_FROM_BROWSER,)
    node_path = shutil.which("node")
    if node_path:
        opts["js_runtimes"] = {"node": {"path": node_path}}
    return opts

def has_instagram_auth() -> bool:
    return bool(settings.INSTAGRAM_COOKIES_FILE or settings.YTDLP_COOKIES_FROM_BROWSER)

def extract_youtube_id(url: str) -> str:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Cannot extract YouTube video ID from URL: {url}")

def extract_instagram_shortcode(url: str) -> str:
    match = re.search(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract Instagram shortcode from URL: {url}")

def normalize_count(value):
    if value is None:
        return None
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None
    return count if count >= 0 else None

def first_available(*values):
    for value in values:
        normalized = normalize_count(value)
        if normalized is not None:
            return normalized
    return None

def first_positive_or_available(*values):
    normalized_values = [normalize_count(value) for value in values]
    for value in normalized_values:
        if value and value > 0:
            return value
    for value in normalized_values:
        if value is not None:
            return value
    return None

def instagram_metadata_note(data: dict) -> str:
    missing = []
    if data.get("views") is None:
        missing.append("views")
    if data.get("follower_count") is None:
        missing.append("follower count")
    if not missing:
        return ""
    return (
        "Instagram did not expose "
        + " and ".join(missing)
        + " from the public endpoint. Add Instagram cookies to enable authenticated extraction when available."
    )

def compute_engagement(data: dict) -> dict:
    views = normalize_count(data.get("views"))
    likes = normalize_count(data.get("likes")) or 0
    comments = normalize_count(data.get("comments")) or 0

    if views == 0 and (likes > 0 or comments > 0):
        data["views"] = None
        data["engagement_rate"] = None
        data["engagement_note"] = (
            "View count unavailable or hidden by the platform; engagement rate cannot be calculated."
        )
    elif views and views > 0:
        data["views"] = views
        data["engagement_rate"] = round((likes + comments) / views * 100, 4)
        data["engagement_note"] = ""
    else:
        data["views"] = views
        data["engagement_rate"] = 0.0 if views == 0 else None
        data["engagement_note"] = (
            "" if views == 0 else
            "View count unavailable or hidden by the platform; engagement rate cannot be calculated."
        )

    data["likes"] = likes
    data["comments"] = comments
    return data

def finalize_instagram_data(data: dict) -> dict:
    data["metadata_note"] = instagram_metadata_note(data)
    return data

def transcribe_with_whisper(url: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")
        base_opts = {
            **ytdlp_common_options(),
            "outtmpl": os.path.join(tmpdir, "audio.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
        }
        format_attempts = [
            "bestaudio[ext=m4a]/bestaudio[acodec!=none]/best[acodec!=none]/best",
            "best[acodec!=none]/best",
            None,
        ]

        last_error = None
        for fmt in format_attempts:
            ydl_opts = dict(base_opts)
            if fmt:
                ydl_opts["format"] = fmt
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                break
            except yt_dlp.utils.DownloadError as e:
                last_error = e
                logger.warning("Audio download failed with format=%s: %s", fmt or "default", e)
        else:
            raise RuntimeError(
                "Could not download audio for transcription. The video may be unavailable, "
                "region restricted, private, or blocked by YouTube/Instagram."
            ) from last_error

        if not os.path.exists(audio_path):
            raise RuntimeError("Audio extraction failed: ffmpeg did not create an mp3 file.")

        model = whisper.load_model(settings.WHISPER_MODEL)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
            result = model.transcribe(audio_path, fp16=False)
        return result["text"].strip()

def get_youtube_data(url: str) -> dict:
    logger.info("Fetching YouTube data for: %s", url)
    
    # Clean URL first
    video_id = extract_youtube_id(url)
    clean_url = f"https://www.youtube.com/watch?v={video_id}"

    # Get transcript via API (no bot detection)
    try:
        raw = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join(t["text"] for t in raw)
    except Exception as e:
        raise ValueError(f"Could not get transcript: {e}")

    # Get metadata via yt-dlp with extra options
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        # Add these to avoid bot detection
        "extractor_args": {
            "youtube": {
                "skip": ["dash", "hls"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
    except Exception as e:
        logger.warning("yt-dlp metadata failed, using defaults: %s", e)
        # Return basic data with transcript if yt-dlp fails
        info = {}

    return {
        "video_id": "A",
        "source": "youtube",
        "url": clean_url,
        "transcript": transcript,
        "views": info.get("view_count") or 0,
        "likes": info.get("like_count") or 0,
        "comments": info.get("comment_count") or 0,
        "creator": info.get("uploader") or "YouTube Creator",
        "follower_count": info.get("channel_follower_count") or 0,
        "upload_date": info.get("upload_date") or "Unknown",
        "duration": info.get("duration") or 0,
        "title": info.get("title") or "YouTube Video",
        "hashtags": (info.get("tags") or [])[:10],
        "thumbnail": info.get("thumbnail") or "",
    }

def get_instagram_data(url: str) -> dict:
    # Clean URL - remove everything after ?
    url = url.split("?")[0]
    if not url.endswith("/"):
        url += "/"
    logger.info("Fetching Instagram data for: %s", url)
    transcript = transcribe_with_whisper(url)
    yt_info = {}
    try:
        with yt_dlp.YoutubeDL(ytdlp_common_options()) as ydl:
            yt_info = ydl.extract_info(url, download=False)
    except Exception as e:
        logger.warning("yt-dlp Instagram metadata failed: %s", e)

    if not has_instagram_auth():
        logger.info("Using public Instagram metadata from yt-dlp; authenticated Instaloader is not configured")
        info = yt_info
        if not info:
            with yt_dlp.YoutubeDL(ytdlp_common_options()) as ydl:
                info = ydl.extract_info(url, download=False)
        return finalize_instagram_data({
            "video_id": "B", "source": "instagram", "url": url,
            "transcript": transcript,
            "views": normalize_count(info.get("view_count")),
            "likes": normalize_count(info.get("like_count")),
            "comments": normalize_count(info.get("comment_count")),
            "creator": info.get("uploader") or "Unknown",
            "follower_count": normalize_count(info.get("channel_follower_count")),
            "upload_date": info.get("upload_date") or "Unknown",
            "duration": info.get("duration") or 0,
            "title": (info.get("title") or "")[:120],
            "hashtags": (info.get("tags") or [])[:10],
            "thumbnail": info.get("thumbnail") or "",
        })

    try:
        L = instaloader.Instaloader(quiet=True, download_pictures=False, download_videos=False, download_video_thumbnails=False)
        shortcode = extract_instagram_shortcode(url)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        return finalize_instagram_data({
            "video_id": "B", "source": "instagram", "url": url,
            "transcript": transcript,
            "views": first_positive_or_available(post.video_view_count, yt_info.get("view_count")),
            "likes": first_available(post.likes, yt_info.get("like_count")),
            "comments": first_available(post.comments, yt_info.get("comment_count")),
            "creator": post.owner_username or yt_info.get("uploader") or "Unknown",
            "follower_count": first_available(
                getattr(post.owner_profile, "followers", None),
                yt_info.get("channel_follower_count"),
            ),
            "upload_date": str(post.date),
            "duration": post.video_duration or yt_info.get("duration") or 0,
            "title": (post.caption or yt_info.get("title") or "")[:120],
            "hashtags": (list(post.caption_hashtags) or (yt_info.get("tags") or []))[:10],
            "thumbnail": post.url or yt_info.get("thumbnail") or "",
        })
    except Exception as e:
        logger.warning("instaloader failed (%s) - using yt-dlp fallback", e)
        info = yt_info
        if not info:
            with yt_dlp.YoutubeDL(ytdlp_common_options()) as ydl:
                info = ydl.extract_info(url, download=False)
        return finalize_instagram_data({
            "video_id": "B", "source": "instagram", "url": url,
            "transcript": transcript,
            "views": normalize_count(info.get("view_count")),
            "likes": normalize_count(info.get("like_count")),
            "comments": normalize_count(info.get("comment_count")),
            "creator": info.get("uploader") or "Unknown",
            "follower_count": normalize_count(info.get("channel_follower_count")),
            "upload_date": info.get("upload_date") or "Unknown",
            "duration": info.get("duration") or 0,
            "title": (info.get("title") or "")[:120],
            "hashtags": (info.get("tags") or [])[:10],
            "thumbnail": info.get("thumbnail") or "",
        })
