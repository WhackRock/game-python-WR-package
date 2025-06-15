# WhackRock Treasury Plugin for GAME SDK

This plugin enables AI agents to manage WhackRock investment funds through the GAME framework by Virtuals Protocol.

## Overview

The WhackRock Treasury Plugin provides a comprehensive interface for AI agents to:
- 📊 Monitor portfolio composition and NAV
- ⚖️ Set target portfolio weights
- 🔄 Trigger automatic rebalancing
- 💰 Collect management fees
- 📈 Track fund performance

## Installation

```bash
pip install whackrock-treasury-plugin
```

Or install from source:
```bash
cd plugins/WRTreasury
pip install -e .
```

## Quick Start

### 1. Initialize the Plugin

```python
from whackrock_plugin_gamesdk import WhackRockPlugin

# Initialize with your fund details
plugin = WhackRockPlugin(
    rpc_url="https://mainnet.base.org",  # Base mainnet RPC
    fund_address="0x...",  # Your WhackRockFund address
    private_key="0x..."    # Agent's private key (optional for read-only)
)
```

### 2. Use with GAME SDK

```python
from whackrock_plugin_gamesdk import get_whackrock_functions

# Get GAME-compatible functions
functions = get_whackrock_functions(
    rpc_url="https://mainnet.base.org",
    fund_address="0x...",
    private_key="0x..."
)

# Add to your agent's function list
agent.add_functions(functions)
```

## Available Functions

### Read Functions

#### `get_current_portfolio()`
Get the current portfolio composition with weights.

```python
result = plugin.get_current_composition()
# Returns:
# {
#     'status': 'success',
#     'composition': [
#         {'symbol': 'WETH', 'weight_bps': 3000, 'weight_percent': 30},
#         {'symbol': 'USDC', 'weight_bps': 7000, 'weight_percent': 70}
#     ]
# }
```

#### `get_fund_nav()`
Get the fund's total Net Asset Value.

```python
nav_weth = plugin.get_total_nav_weth()
nav_usdc = plugin.get_total_nav_usdc()
```

#### `check_rebalance_needed()`
Check if portfolio needs rebalancing based on deviation from targets.

```python
result = plugin.calculate_rebalance_needed()
# Returns:
# {
#     'needs_rebalance': True,
#     'max_deviation_percent': 2.5,
#     'deviations': [...]
# }
```

### Write Functions

#### `set_portfolio_weights(weights)`
Set target portfolio weights (must sum to 10000 basis points).

```python
# Set 40% WETH, 30% PRIME, 30% USDC
weights = [4000, 3000, 3000]
result = plugin.set_target_weights(weights)
```

#### `set_weights_and_rebalance(weights)`
Set weights and automatically rebalance if needed.

```python
weights = [4000, 3000, 3000]
result = plugin.set_weights_and_rebalance(weights)
```

#### `rebalance_portfolio()`
Manually trigger portfolio rebalancing.

```python
result = plugin.trigger_rebalance()
```

#### `collect_management_fees()`
Collect accrued management fees.

```python
result = plugin.collect_management_fee()
```

## Integration Examples

### Example 1: Basic Portfolio Management Agent

```python
from game_sdk.game import Agent
from whackrock_plugin_gamesdk import get_whackrock_functions

class PortfolioAgent(Agent):
    def __init__(self, fund_address, private_key):
        super().__init__()
        
        # Add WhackRock functions
        self.functions = get_whackrock_functions(
            rpc_url="https://mainnet.base.org",
            fund_address=fund_address,
            private_key=private_key
        )
    
    async def manage_portfolio(self):
        # Check if rebalancing is needed
        result = await self.execute_function("check_rebalance_needed")
        
        if result['needs_rebalance']:
            # Trigger rebalance
            await self.execute_function("rebalance_portfolio")
```

### Example 2: Dynamic Weight Adjustment

```python
async def adjust_weights_based_on_market(agent):
    # Get current NAV
    nav = await agent.execute_function("get_fund_nav")
    
    # Example: Risk-off if NAV drops
    if nav['usdc']['nav_usdc'] < 100000:  # Less than $100k
        # Increase USDC allocation
        weights = [2000, 3000, 5000]  # 20% WETH, 30% PRIME, 50% USDC
    else:
        # Risk-on allocation
        weights = [4000, 4000, 2000]  # 40% WETH, 40% PRIME, 20% USDC
    
    # Set new weights and rebalance
    await agent.execute_function("set_weights_and_rebalance", weights=weights)
```

### Example 3: Signal-Based Rebalancing

See the included `example/signal.py` for an advanced example that:
- Fetches Benjamin Cowen's latest video transcript
- Uses GPT-4 to analyze market sentiment
- Adjusts portfolio weights based on AI analysis

## Fund Requirements

To use this plugin, ensure:
1. The agent address is set as the fund's agent via `setAgent()`
2. The fund has sufficient assets for rebalancing
3. Target tokens are in the registry's allowlist

## Error Handling

All functions return a standardized response format:

```python
# Success
{
    'status': 'success',
    'data': {...}
}

# Error
{
    'status': 'error',
    'error': 'Error message'
}
```

## Gas Optimization

- Use `set_weights_and_rebalance()` instead of separate calls
- Batch operations when possible
- Monitor gas prices before rebalancing

## Security Considerations

1. **Private Key Security**: Never expose private keys in code
2. **Access Control**: Only the designated agent can manage the fund
3. **Validation**: All weights must sum to exactly 10000 basis points
4. **Slippage Protection**: Built-in slippage protection on swaps

## Support

- Documentation: [docs.whackrock.ai](https://docs.whackrock.ai)
- Discord: [Join our community](https://discord.gg/whackrock)
- GitHub: [github.com/whackrock](https://github.com/whackrock)

## License

MIT License - see LICENSE file for details