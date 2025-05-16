# 🏦 WhackRock Treasury Plugin for `game-python`

© 2025 WhackRock Labs Ltd. All rights reserved.

A reusable, permission‑less treasury layer on top of GAME, allowing agents to manage asset allocations with automated fee splits.

## 🎯 Goal

Build an open‑source system where WhackRock allocates capital to many autonomous agent vaults, each of which runs its own strategy, holds a tokenised treasury, and pays an automatic 80/20 fee split (80% to the agent's dev wallet, 20% to WRK stakers).

## 💡 Project Overview

| Layer | What it delivers |
|-------|------------------|
| **Treasury factory** | One-click deployment of **ERC‑4626** vaults that trade only whitelisted assets, charge management fees, and auto-split fees **80/20** (dev/WRK‑stakers). |
| **Agent template (Python)** | A GAME Worker that calculates new weights and calls the vault's `rebalance()`. Anyone can fork it and launch a strategy. |
| **Uniswap adapters & oracle** | On‑chain Uniswap‑V3 TWAP oracle + Universal Router wrapper for swapping any whitelisted token on **Base**—no off‑chain keepers required. |
| **Subgraph** | Records share prices for each vault, enabling trustless time-series for performance calculations. |

## 📂 Project Structure

```
game-python/
└─ plugins/
   └─ WRTreasury/
      ├─ README.md                      ← You are here
      ├─ pyproject.toml                 ← Dependencies (pip install -e .)
      ├─ .env.example                   ← Environment variables template
      ├─ whackrock_treasury_plugin_gamesdk/
      │   ├─ __init__.py                ← Registers Game‑SDK functions
      │   ├─ treasury.py                ← Web3 helpers for ERC‑4626 vault
      │   ├─ uniswap.py                 ← Universal‑Router swap builder
      │   ├─ config.py                  ← Configuration settings
      │   └─ utils.py                   ← Utility functions
      └─ examples/
          ├─ template_agent/            ← Start here for your own agent
          │   ├─ worker.py              ← Example GAME worker
          │   └─ signals.py             ← Example strategy logic
          └─ benfan_agent/              ← More complex example
              ├─ worker.py
              └─ signals.py
```

## 🚀 Quick Start

1. **Install the plugin**

```bash
cd game-python/plugins/WRTreasury
pip install -e .
```

2. **Configure Environment Variables**

Copy the example environment file and edit it with your values:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `BASE_RPC`: RPC endpoint for Base network
- `TREASURY_VAULT_ADDRESS`: Your vault contract address
- `TREASURY_SIGNER_KEY`: Private key for transactions

3. **Run the example agent**

```bash
game run examples/template_agent/worker.py
```

## ✨ Key Features

* Interact with any **WeightedTreasuryVault** clone on Base  
* One‑call helpers for `get_weights`, `set_weights`, and `rebalance`  
* Universal‑Router swap builder (Uniswap V3) with slippage control
* Token symbol resolution (use "ETH" instead of addresses)
* Comprehensive error handling and validation
* 80/20 fee split logic is handled by the vault
* Environment variable configuration via `.env` file

## 🔧 Environment Configuration

The plugin uses a `.env` file for configuration. Available settings:

| Variable | Purpose | Default |
|----------|---------|---------|
| `BASE_RPC` | Base network RPC endpoint | `https://mainnet.base.org` |
| `BASE_TESTNET_RPC` | Base testnet RPC (for development) | `https://sepolia.base.org` |
| `TREASURY_VAULT_ADDRESS` | Your vault contract address | *required* |
| `TREASURY_SIGNER_KEY` | Private key for transactions | *required* |
| `REBALANCE_THRESHOLD_BPS` | Threshold for rebalance (in basis points) | `200` (2%) |
| `DEFAULT_SLIPPAGE_BPS` | Swap slippage tolerance (in basis points) | `30` (0.3%) |
| `LOG_LEVEL` | Logging level | `INFO` |

You can also configure token addresses for your specific strategy:
```
stETH="0x1643E812aE58766192Cf7D2Cf9567dF2C37e9B7F"
WBTC="0x1A35EE4640b0A3B87705B0A4B45D227Ba60Ca2c7"
```

## 📚 API Reference

The plugin exposes the following functions through GAME SDK:

### Core Functions

- `get_current_weights(vault_addr)` - Get the current target weights from the vault
- `set_weights(vault_addr, signer_key, weights)` - Set new target weights
- `set_and_rebalance(vault_addr, signer_key, new_weights, sells, buys)` - Update weights and execute a rebalance
- `is_rebalance_needed(vault_addr, new_weights, threshold_bps)` - Check if rebalance is needed

### Helper Functions

- `estimate_swap(sell_token, buy_token, sell_amount)` - Estimate price impact and output amount
- `resolve_token_address(token_symbol_or_address)` - Convert token symbols to addresses

## 🔧 Example Usage

Here's a simple example of using the plugin in your GAME worker:

```python
from game import Worker, game_function
from whackrock_treasury_plugin_gamesdk import get_current_weights, set_and_rebalance

class MyTreasuryWorker(Worker):
    @game_function(schedule="0 */6 * * *")  # Run every 6 hours
    async def manage_treasury(self):
        # Your vault and wallet configuration
        # These can also be loaded from .env
        VAULT_ADDRESS = "0xYourVaultAddress"
        SIGNER_KEY = "your_private_key"  # Store securely!
        
        # Get current weights
        current_weights = await get_current_weights(VAULT_ADDRESS)
        
        # Calculate new target weights (your strategy logic here)
        new_weights = [7000, 3000]  # Example: 70% ETH, 30% USDC
        
        # Define what to sell and buy (simplified)
        sells = [{"token": "ETH", "amt": 100000000000000000}]  # 0.1 ETH
        buys = [{"token": "USDCb", "amt": 100000000}]  # 100 USDC (6 decimals)
        
        # Execute the rebalance
        tx_hash = await set_and_rebalance(
            VAULT_ADDRESS,
            SIGNER_KEY,
            new_weights,
            sells,
            buys
        )
        print(f"Rebalance executed: {tx_hash}")
```

## 🧩 Creating Your Own Strategy

To create your own strategy:

1. Copy the `examples/template_agent` directory
2. Create your own `.env` file with your configuration
3. Modify `signals.py` with your custom strategy logic
4. Update the `worker.py` with your vault address and configuration
5. Run your worker with `game run your_agent/worker.py`

## 🔐 Security Best Practices

- **NEVER** hardcode private keys in your code
- Always use the `.env` file or environment variables for sensitive values
- Add `.env` to your `.gitignore` to prevent committing sensitive data
- Use reasonable slippage parameters to prevent sandwich attacks
- Test thoroughly on testnet before mainnet
- Monitor your vault's performance regularly

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

© 2025 WhackRock Labs Ltd. All rights reserved.
