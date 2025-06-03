"""
Derives [stETH, WBTC, USDT] weights from the latest Benjamin Cowen video.

* Downloads the auto‑caption transcript (YouTube v3 API or cheap wrapper)
* Sends the transcript to GPT‑4o‑mini and requests JSON:
    { macroTone: str, riskOnOff: str, weightSignal: [0.55,0.35,0.10] }
* Validates with Pydantic; falls back to equal‑weight on any error
"""

import os, json, aiohttp, asyncio, logging
from pydantic import BaseModel, conlist
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]          # set in env vars
CHANNEL_ID = "UCqK_GSMbpiV8spgD3ZGloSw"                # Benjamin Cowen

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
  "weightSignal": [<stETH>, <WBTC>, <USDT>]  // three decimals
}}  
The weights must sum to exactly 1.00."""

async def fetch_transcript(session) -> str:
    async with session.get(YOUTUBE_TRANSCRIPT % CHANNEL_ID) as r:
        data = await r.json()
        return " ".join(item["text"] for item in data["subtitles"])

async def derive_weights() -> list[float]:
    try:
        async with aiohttp.ClientSession() as sess:
            transcript = await fetch_transcript(sess)

            llm = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[{"role":"user", "content": PROMPT + "\n" + transcript}],
                response_format={"type":"json"},
                temperature=0.3
            )
        parsed = json.loads(llm.choices[0].message.content)
        sig    = LLMSignal.model_validate(parsed)   # raises if bad
        return sig.weightSignal
    except Exception as e:
        logging.warning("BenFan signal fallback: %s", e)
        return [0.34, 0.33, 0.33]                   # equal‑weight fallback

# allow synchronous call for simple tests
if __name__ == "__main__":
    print(asyncio.run(derive_weights()))
