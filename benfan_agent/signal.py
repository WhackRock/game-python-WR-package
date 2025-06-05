"""
Enhanced signal module that tracks processed videos and derives weights from Benjamin Cowen's latest video.

* Fetches the latest video from Benjamin Cowen's channel
* Tracks processed video IDs to avoid reprocessing
* Downloads the auto-caption transcript
* Sends the transcript to GPT-4o-mini for analysis
* Returns weights for [VIRTUAL, cbBTC, USDC] and video metadata
"""

import os
import json
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, conlist
from openai import AsyncOpenAI

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = "UCqK_GSMbpiV8spgD3ZGloSw"  # Benjamin Cowen
NUM_LLM_SIGNAL_ASSETS = 3  # VIRTUAL, cbBTC, USDC

# File to store processed video IDs
PROCESSED_VIDEOS_FILE = os.path.join(os.path.dirname(__file__), "processed_videos.json")

class LLMSignal(BaseModel):
    macroTone: str
    riskOnOff: str
    weightSignal: conlist(float, min_length=3, max_length=3)

class VideoAnalysis(BaseModel):
    video_id: str
    video_title: str
    published_at: str
    macro_tone: str
    risk_on_off: str
    weights: List[float]
    analysis_summary: str

# YouTube Data API v3 endpoint to get latest video
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")  # Optional, for direct API access

# Fallback: Use jina.ai wrapper for channel videos
YOUTUBE_CHANNEL_VIDEOS = f"https://r.jina.ai/https://www.youtube.com/@IntoTheCryptoverse/videos"

# Transcript API
YOUTUBE_TRANSCRIPT = "https://r.jina.ai/http://youtubesubtitles.com/api/v1/subtitles/%s?lang=en"

ANALYSIS_PROMPT = """You are an investment analyst specializing in cryptocurrency markets. 
Analyze this Benjamin Cowen video transcript and provide investment signals.

Output **only** valid JSON:
{
  "macroTone": "<bullish|neutral|bearish>",
  "riskOnOff": "<on|off>",
  "weightSignal": [<VIRTUAL>, <cbBTC>, <USDC>],
  "analysisSummary": "<1-2 sentence summary of the key market insights>"
}

The weights must sum to exactly 1.00.
- VIRTUAL: High-risk crypto asset (increase in risk-on, bullish scenarios)
- cbBTC: Bitcoin exposure (moderate risk, increase in crypto-bullish scenarios)
- USDC: Stablecoin (increase in risk-off, bearish scenarios)

Here is the transcript:
"""

def load_processed_videos() -> Dict[str, Dict]:
    """Load the record of processed videos."""
    if os.path.exists(PROCESSED_VIDEOS_FILE):
        try:
            with open(PROCESSED_VIDEOS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Error loading processed videos: {e}")
    return {}

def save_processed_video(video_id: str, analysis: VideoAnalysis):
    """Save a processed video record."""
    processed = load_processed_videos()
    processed[video_id] = {
        "processed_at": datetime.utcnow().isoformat(),
        "video_title": analysis.video_title,
        "published_at": analysis.published_at,
        "macro_tone": analysis.macro_tone,
        "risk_on_off": analysis.risk_on_off,
        "weights": analysis.weights,
        "analysis_summary": analysis.analysis_summary
    }
    
    try:
        with open(PROCESSED_VIDEOS_FILE, 'w') as f:
            json.dump(processed, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving processed video record: {e}")

async def fetch_latest_video_id(session: aiohttp.ClientSession) -> Optional[Tuple[str, str, str]]:
    """Fetch the latest video ID, title, and published date from Benjamin Cowen's channel."""
    try:
        # Try using YouTube API if key is available
        if YOUTUBE_API_KEY:
            url = f"{YOUTUBE_API_BASE}/search"
            params = {
                "key": YOUTUBE_API_KEY,
                "channelId": CHANNEL_ID,
                "part": "snippet",
                "order": "date",
                "maxResults": 1,
                "type": "video"
            }
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("items"):
                        item = data["items"][0]
                        video_id = item["id"]["videoId"]
                        title = item["snippet"]["title"]
                        published = item["snippet"]["publishedAt"]
                        return video_id, title, published
        
        # Fallback: Parse channel page via jina.ai
        async with session.get(YOUTUBE_CHANNEL_VIDEOS) as resp:
            if resp.status == 200:
                content = await resp.text()
                # Simple parsing - look for video ID pattern
                import re
                # Match pattern like "watch?v=VIDEO_ID"
                match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', content)
                if match:
                    video_id = match.group(1)
                    # Try to extract title
                    title_match = re.search(rf'watch\?v={video_id}[^>]*>([^<]+)<', content)
                    title = title_match.group(1) if title_match else f"Video {video_id}"
                    return video_id, title, datetime.utcnow().isoformat()
                    
    except Exception as e:
        logging.error(f"Error fetching latest video: {e}")
    
    return None

async def fetch_transcript(session: aiohttp.ClientSession, video_id: str) -> Optional[str]:
    """Fetch transcript for a specific video."""
    try:
        url = YOUTUBE_TRANSCRIPT % video_id
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("subtitles"):
                    return " ".join(item["text"] for item in data["subtitles"])
    except Exception as e:
        logging.error(f"Error fetching transcript for video {video_id}: {e}")
    
    return None

async def analyze_transcript(transcript: str) -> Optional[Dict]:
    """Analyze transcript using GPT-4o-mini."""
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": ANALYSIS_PROMPT + "\n" + transcript}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate weights sum to 1.0
        weight_sum = sum(result["weightSignal"])
        if abs(weight_sum - 1.0) > 0.001:
            # Normalize weights
            result["weightSignal"] = [w / weight_sum for w in result["weightSignal"]]
        
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing transcript: {e}")
        return None

async def get_latest_video_analysis() -> Optional[VideoAnalysis]:
    """Get analysis for the latest video, or None if already processed."""
    async with aiohttp.ClientSession() as session:
        # Get latest video
        video_info = await fetch_latest_video_id(session)
        if not video_info:
            logging.error("Could not fetch latest video information")
            return None
        
        video_id, title, published = video_info
        
        # Check if already processed
        processed = load_processed_videos()
        if video_id in processed:
            logging.info(f"Video {video_id} already processed on {processed[video_id]['processed_at']}")
            return None
        
        logging.info(f"Processing new video: {title} (ID: {video_id})")
        
        # Fetch transcript
        transcript = await fetch_transcript(session, video_id)
        if not transcript:
            logging.error(f"Could not fetch transcript for video {video_id}")
            return None
        
        # Analyze transcript
        analysis = await analyze_transcript(transcript)
        if not analysis:
            logging.error(f"Could not analyze transcript for video {video_id}")
            return None
        
        # Create VideoAnalysis object
        video_analysis = VideoAnalysis(
            video_id=video_id,
            video_title=title,
            published_at=published,
            macro_tone=analysis["macroTone"],
            risk_on_off=analysis["riskOnOff"],
            weights=analysis["weightSignal"],
            analysis_summary=analysis.get("analysisSummary", "")
        )
        
        # Save as processed
        save_processed_video(video_id, video_analysis)
        
        return video_analysis

async def derive_weights() -> List[float]:
    """
    Main function called by the worker to get weights.
    Returns weights for [VIRTUAL, cbBTC, USDC] or equal weights as fallback.
    """
    try:
        analysis = await get_latest_video_analysis()
        if analysis:
            logging.info(f"Using weights from new video analysis: {analysis.weights}")
            return analysis.weights
        else:
            # No new video, return last known weights or equal weights
            processed = load_processed_videos()
            if processed:
                # Get the most recent analysis
                latest = max(processed.items(), key=lambda x: x[1]["processed_at"])
                weights = latest[1]["weights"]
                logging.info(f"No new video, using last known weights: {weights}")
                return weights
            else:
                logging.info("No video history, using equal weights")
                return [0.34, 0.33, 0.33]
                
    except Exception as e:
        logging.error(f"Error in derive_weights: {e}")
        return [0.34, 0.33, 0.33]  # Equal weight fallback

async def get_last_analysis() -> Optional[VideoAnalysis]:
    """Get the last video analysis for tweet generation."""
    processed = load_processed_videos()
    if not processed:
        return None
    
    # Get the most recent analysis
    latest_id, latest_data = max(processed.items(), key=lambda x: x[1]["processed_at"])
    
    return VideoAnalysis(
        video_id=latest_id,
        video_title=latest_data["video_title"],
        published_at=latest_data["published_at"],
        macro_tone=latest_data["macro_tone"],
        risk_on_off=latest_data["risk_on_off"],
        weights=latest_data["weights"],
        analysis_summary=latest_data["analysis_summary"]
    )

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    weights = asyncio.run(derive_weights())
    print(f"Derived weights: {weights}") 