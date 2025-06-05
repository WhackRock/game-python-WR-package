# BenFan Agent

A GAME agent that automatically manages WhackRock funds based on Benjamin Cowen's market analysis videos and posts updates to Twitter.

## Features

- **Automated Video Analysis**: Monitors Benjamin Cowen's YouTube channel for new videos
- **Market Sentiment Extraction**: Uses GPT-4o-mini to analyze video transcripts and derive market sentiment
- **Dynamic Portfolio Weights**: Generates portfolio weights for VIRTUAL, cbBTC, and USDC based on market analysis
- **Fund Management**: Automatically rebalances WhackRock funds when weights deviate by more than 2%
- **Twitter Integration**: Posts detailed tweets about rebalancing actions with market context
- **Video Tracking**: Maintains a history of processed videos to avoid duplicate processing

## Architecture

### Components

1. **signal.py**: Enhanced signal module that:
   - Fetches latest videos from Benjamin Cowen's channel
   - Downloads and analyzes transcripts using OpenAI
   - Tracks processed videos in `processed_videos.json`
   - Derives portfolio weights based on market sentiment

2. **worker.py**: Main worker that:
   - Checks for new videos daily
   - Manages fund portfolio hourly
   - Executes rebalancing when needed
   - Posts tweets about rebalancing actions

## Setup

### Prerequisites

1. **Environment Variables**:
   ```bash
   # Required
   OPENAI_API_KEY=your_openai_api_key
   WHACKROCK_FUND_ADDRESS=0xYourFundAddress
   GAME_TWITTER_ACCESS_TOKEN=your_game_twitter_token
   
   # Optional
   YOUTUBE_API_KEY=your_youtube_api_key  # For direct YouTube API access
   TWITTER_ENABLED=true  # Set to false to disable Twitter posting
   ```

2. **Dependencies**:
   - game-python-sdk
   - whackrock_plugin_gamesdk
   - twitter_plugin_gamesdk
   - openai
   - aiohttp
   - pydantic

### Installation

1. Clone the repository and navigate to the agent directory:
   ```bash
   cd game-python-WR-package/benfan_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env` file

4. Deploy your WhackRock fund and update `WHACKROCK_FUND_ADDRESS`

## Usage

### Running the Agent

```python
from benfan_agent import BenFanWorker

# Initialize and run the worker
worker = BenFanWorker()
# The worker will automatically execute scheduled tasks
```

### Scheduled Tasks

1. **Daily Video Check** (midnight UTC):
   - Checks for new Benjamin Cowen videos
   - Processes transcript if new video found
   - Updates weights based on analysis

2. **Hourly Portfolio Management**:
   - Fetches current fund composition
   - Compares with target weights
   - Rebalances if deviation > 2%
   - Posts tweet about rebalancing

### Manual Testing

Test the signal module:
```bash
python signal.py
```

Test the worker:
```bash
python worker.py
```

## Portfolio Strategy

The agent derives weights for three assets based on market sentiment:

- **VIRTUAL**: High-risk crypto asset
  - Increased in bullish, risk-on scenarios
  - Decreased in bearish, risk-off scenarios

- **cbBTC**: Bitcoin exposure (moderate risk)
  - Increased in crypto-bullish scenarios
  - Moderate allocation in neutral conditions

- **USDC**: Stablecoin (safe haven)
  - Increased in bearish, risk-off scenarios
  - Minimal allocation in bullish conditions

## Tweet Format

When rebalancing occurs, the agent posts tweets with:
- Video title and market analysis
- Market sentiment (BULLISH/NEUTRAL/BEARISH)
- Risk status (ON/OFF)
- Old vs new portfolio weights
- Key market insights from the video

Example tweet:
```
🎯 WhackRock Fund Rebalanced!

Based on @intothecryptoverse latest: "Bitcoin At Critical Juncture"

Market view: BEARISH | Risk: OFF

Old → New weights:
• $VIRTUAL: 40.0% → 20.0%
• $cbBTC: 35.0% → 30.0%
• $USDC: 25.0% → 50.0%

Bitcoin showing weakness at key resistance levels, suggesting caution.

#DeFi #WhackRock #BenCowen
```

## Data Storage

The agent stores processed video data in `processed_videos.json`:
```json
{
  "VIDEO_ID": {
    "processed_at": "2024-01-15T10:30:00",
    "video_title": "Bitcoin Analysis",
    "published_at": "2024-01-15T08:00:00",
    "macro_tone": "bearish",
    "risk_on_off": "off",
    "weights": [0.2, 0.3, 0.5],
    "analysis_summary": "Market showing signs of weakness..."
  }
}
```

## Error Handling

- Falls back to equal weights (34%, 33%, 33%) if analysis fails
- Continues using last known weights if no new videos
- Logs all errors for debugging
- Twitter posting failures don't affect fund management

## Security Considerations

- Never commit API keys or sensitive addresses
- Use environment variables for all credentials
- Validate all weight calculations sum to exactly 100%
- Implement proper access controls on the fund contract

## Future Enhancements

- Support for more assets
- Multiple YouTube channels
- Advanced technical analysis integration
- Backtesting capabilities
- Performance tracking and reporting 