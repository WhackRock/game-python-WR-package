# WRTreasury Plugin

A GAME SDK plugin for managing WhackRock Fund smart contracts. This plugin lets AI agents automatically manage decentralized investment funds.

## What It Does

The WRTreasury plugin connects AI agents to WhackRock Fund contracts. Agents can:

- Monitor portfolio weights in real-time
- Automatically rebalance when portfolios drift from targets
- Set new target allocations for fund assets
- Track fund performance and analytics

## Key Features

- **Portfolio Monitoring**: Track current vs target asset weights
- **Auto-Rebalancing**: Rebalance when deviations exceed 1%
- **Weight Management**: Set allocations using basis points
- **GAME SDK Integration**: Ready-to-use functions for agents
- **Security**: Agent-only operations with private key protection

## Quick Start

1. Install dependencies:
```bash
pip install game-sdk web3 pydantic
```

2. Set environment variables:
```bash
export GAME_API_KEY=your_game_api_key
export FUND_CONTRACT_ADDRESS=0x...
export AGENT_PRIVATE_KEY=0x...
export WEB3_PROVIDER=https://mainnet.infura.io/v3/...
```

3. Use the basic example:
```python
from whackrock_plugin_gamesdk.whackrock_fund_manager_gamesdk import WhackRockFundManagerSDK

# Initialize SDK
fund_sdk = WhackRockFundManagerSDK(
    web3_provider=WEB3_PROVIDER,
    fund_contract_address=FUND_CONTRACT_ADDRESS,
    private_key=AGENT_PRIVATE_KEY,
    account_address=AGENT_ADDRESS
)

# Get current weights
weights = fund_sdk.get_current_weights()
print(f"Current weights: {weights}")

# Set new target weights (in basis points)
result = fund_sdk.set_target_weights(
    weights_bps=[5000, 3000, 2000],  # 50%, 30%, 20%
    rebalance_if_needed=True
)
```

## Examples

### Basic Usage
See `example/basic/example_usage.py` for:
- SDK initialization
- Portfolio monitoring
- Manual rebalancing
- GAME SDK integration

### BenFan Signal Example
See `example/benfan/` for:
- Autonomous fund manager
- YouTube transcript analysis
- LLM-based investment signals
- Automated execution

## Core Components

### WhackRockFundManagerSDK
Main class for fund operations:
- `get_current_weights()`: Get current portfolio weights
- `get_target_weights()`: Get target allocations
- `set_target_weights()`: Set new targets and optionally rebalance
- `get_fund_info()`: Get fund details and analytics

### Basis Points System
All weights use basis points (BPS):
- 1 BPS = 0.01%
- Total must sum to 10,000 BPS (100%)
- Example: [5000, 3000, 2000] = 50%, 30%, 20%

## Configuration

Required environment variables:
- `GAME_API_KEY`: Your GAME SDK API key
- `FUND_CONTRACT_ADDRESS`: WhackRock Fund contract address
- `AGENT_PRIVATE_KEY`: Agent's private key for transactions
- `WEB3_PROVIDER`: RPC endpoint for blockchain access

## Security

- All write operations require agent authorization
- Private keys stored in environment variables
- Gas limits configurable to prevent stuck transactions
- Input validation before transaction submission

## License

MIT License