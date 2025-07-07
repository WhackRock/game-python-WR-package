"""
Derives [VIRTUAL, cbBTC, USDC] weights from the latest Benjamin Cowen video.

* Downloads the auto‑caption transcript (YouTube v3 API or cheap wrapper)
* Sends the transcript to GPT‑4o‑mini and requests JSON:
    { macroTone: str, riskOnOff: str, weightSignal: [0.55,0.35,0.10] }
* Validates with Pydantic; falls back to equal‑weight on any error
"""

import os, json, aiohttp, asyncio, logging
from pydantic import BaseModel, conlist
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
from typing import Tuple

CHANNEL_ID = "ASDKFJPASKJDPOAISD"                      # Your favourite YouTuber's channel ID
NUM_LLM_SIGNAL_ASSETS  = 3                             # 3 tokens: VIRTUAL, cbBTC, and USDC

class LLMSignal(BaseModel):
    weightSignal: conlist(float, min_length=3, max_length=3)

YOUTUBE_TRANSCRIPT = (
    "https://r.jina.ai/http://youtubesubtitles.com/api/"
    "v1/subtitles/%s?lang=en"                           # free transcript proxy
)

PROMPT = """You are an investment analyst. Summarise the video transcript.  
Output **only** valid JSON:
{{
  "macroTone": "<bullish|neutral|bearish>",
  "riskOnOff": "<on|off>",
  "weightSignal": [<VIRTUAL>, <cbBTC>, <USDC>]  // three decimals
}}  
The weights must sum to exactly 1.00.  Here is the transcript:"""

async def fetch_transcript(session) -> str:
    async with session.get(YOUTUBE_TRANSCRIPT % CHANNEL_ID) as r:
        data = await r.json()
        return " ".join(item["text"] for item in data["subtitles"])

# Game SDK Worker for LLM analysis
def create_signal_worker():
    """Create a Game SDK worker for analyzing YouTube transcripts"""
    
    def analyze_transcript(transcript: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Analyze YouTube transcript and return investment signal
        """
        try:
            # The Game SDK worker will process this instruction
            analysis_prompt = f"""
            You are an investment analyst. Analyze the following YouTube transcript and provide investment weights.
            
            Based on the content, determine the macro tone (bullish/neutral/bearish) and risk sentiment (on/off).
            Then provide allocation weights for three assets: VIRTUAL, cbBTC, and USDC.
            
            The weights must sum to exactly 1.00 and be formatted as decimals.
            
            Return your analysis in this exact JSON format:
            {{
                "macroTone": "bullish|neutral|bearish",
                "riskOnOff": "on|off", 
                "weightSignal": [0.XX, 0.XX, 0.XX]
            }}
            
            Transcript: {transcript}
            """
            
            return FunctionResultStatus.DONE, analysis_prompt, {"transcript": transcript}
        except Exception as e:
            return FunctionResultStatus.FAILED, f"Error analyzing transcript: {e}", {}
    
    action_space = [
        Function(
            fn_name="analyze_transcript",
            fn_description="Analyze YouTube transcript for investment signals",
            args=[Argument(name="transcript", type="str", description="YouTube transcript to analyze")],
            executable=analyze_transcript
        )
    ]
    
    def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
        if current_state is None:
            current_state = {"last_analysis": None}
        
        if function_result and function_result.fn_name == "analyze_transcript":
            current_state["last_analysis"] = function_result.info
        
        return current_state
    
    game_api_key = os.environ.get("GAME_API_KEY")
    if not game_api_key:
        raise ValueError("GAME_API_KEY environment variable is required")
    
    worker = Worker(
        api_key=game_api_key,
        description="Investment Signal Analyzer - analyzes YouTube transcripts for investment signals",
        instruction="""
        You are an investment analyst specializing in crypto and macro analysis.
        
        When given a YouTube transcript, analyze it for:
        1. Overall macro tone (bullish/neutral/bearish)
        2. Risk sentiment (on/off)
        3. Asset allocation weights for VIRTUAL, cbBTC, and USDC
        
        Always return valid JSON with the exact format requested.
        Weights must sum to 1.00 exactly.
        """,
        get_state_fn=get_state_fn,
        action_space=action_space,
        model_name="Llama-3.1-405B-Instruct"
    )
    
    return worker

async def derive_weights() -> list[float]:
    try:
        async with aiohttp.ClientSession() as sess:
            transcript = await fetch_transcript(sess)

            # Use Game SDK worker for LLM analysis
            worker = create_signal_worker()
            result = worker.run(f"Please analyze this transcript and provide investment weights: {transcript}")
            
            # Parse the result - the worker should return JSON
            # This is a simplified approach - in practice you'd need to parse the worker's response
            if "weightSignal" in result:
                parsed = json.loads(result)
                sig = LLMSignal.model_validate(parsed)
                return sig.weightSignal
            else:
                # Fallback if parsing fails
                raise Exception("Failed to parse LLM response")
                
    except Exception as e:
        logging.warning("BenFan signal fallback: %s", e)
        return [0.34, 0.33, 0.33]                   # equal‑weight fallback

# Synchronous wrapper for game framework integration
def get_target_weights_bps() -> list[int]:
    """
    Get target weights in basis points (BPS) for game framework integration.
    Returns weights for [VIRTUAL, cbBTC, USDC] tokens.
    """
    weights = asyncio.run(derive_weights())
    # Convert to basis points (multiply by 10000)
    return [int(w * 10000) for w in weights]

def get_signal_description() -> str:
    """
    Get a description of the current signal for reporting.
    """
    try:
        weights = asyncio.run(derive_weights())
        return f"Benjamin Cowen signal: VIRTUAL={weights[0]:.2%}, cbBTC={weights[1]:.2%}, USDC={weights[2]:.2%}"
    except Exception as e:
        return f"Benjamin Cowen signal (fallback): Equal weight allocation due to error: {e}"

# allow synchronous call for simple tests
if __name__ == "__main__":
    print("Testing signal generation...")
    print(f"Weights: {asyncio.run(derive_weights())}")
    print(f"Weights (BPS): {get_target_weights_bps()}")
    print(f"Description: {get_signal_description()}")